from langchain_core.documents import Document
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import chromadb
from chromadb.config import Settings
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup project path for consistent imports
import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.app.config.service_config import settings
from src.app.utils.logger_utils import get_logger

logger = get_logger(__name__)

class DocumentIngestionService:
    """Service for ingesting, chunking, and embedding documents into ChromaDB"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        self._client = None
        self._collection = None
    
    def _get_client(self):
        """Get or create ChromaDB client"""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=settings.chromadb_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        return self._client
    
    def _get_collection(self):
        """Get or create the documents collection"""
        if self._collection is None:
            client = self._get_client()
            logger.info(f"🔗 Getting/creating ChromaDB collection: '{settings.chromadb_collection_name}'")
            try:
                self._collection = client.get_collection(
                    name=settings.chromadb_collection_name
                )
                logger.info(f"✅ Found existing collection: '{settings.chromadb_collection_name}'")
                logger.info(f"📊 Collection count: {self._collection.count()}")
            except Exception as e:
                # Collection doesn't exist, create it
                logger.info(f"🆕 Collection doesn't exist, creating: '{settings.chromadb_collection_name}'")
                logger.info(f"🔍 Error when trying to get collection: {str(e)}")
                self._collection = client.create_collection(
                    name=settings.chromadb_collection_name,
                    metadata={"description": "Bank policies and credit card benefits documents"}
                )
                logger.info(f"✅ Created new collection: '{settings.chromadb_collection_name}'")
        return self._collection
    
    def load_document(self, file_path: str, document_type: str = "policy") -> List[Document]:
        """Load a document from file path and return LangChain Document objects with enhanced metadata"""
        try:
            file_path = Path(file_path)
            file_extension = file_path.suffix.lower()
            file_name = file_path.name
            file_stem = file_path.stem  # Filename without extension
            
            if file_extension == ".pdf":
                logger.info(f"Processing PDF with PyMuPDF: {file_name}")
                documents = self._process_pdf_with_pymupdf(file_path, file_stem, file_name, document_type)
                    
            elif file_extension == ".docx":
                loader = Docx2txtLoader(str(file_path))
                documents = loader.load()
                
                # Enhance DOCX documents
                for doc in documents:
                    doc.metadata.update({
                        "source_title": file_stem,
                        "source_file": file_name,
                        "document_type": document_type,
                        "file_name": file_name,
                        "file_extension": file_extension,
                        "source_path": str(file_path)
                    })
                    
                    # Add source info to content
                    doc.page_content = f"[Source: {file_stem}]\n\n{doc.page_content}"
                    
            elif file_extension == ".txt":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create enhanced Document for text files
                documents = [Document(
                    page_content=f"[Source: {file_stem}]\n\n{content}",
                    metadata={
                        "source": str(file_path),
                        "source_title": file_stem,
                        "source_file": file_name,
                        "document_type": document_type,
                        "file_name": file_name,
                        "file_extension": file_extension,
                        "source_path": str(file_path)
                    }
                )]
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            logger.info(f"Loaded {len(documents)} pages/sections from {file_name}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise
    
    def _process_pdf_with_pymupdf(self, file_path: Path, file_stem: str, file_name: str, document_type: str) -> List[Document]:
        """Process PDF using PyMuPDF to convert each page to markdown"""
        documents = []
        
        # Clean up the document title for display
        display_title = file_stem.replace('_', ' ').replace('-', ' ').title()
        
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(str(file_path))
            logger.info(f"📄 PDF opened successfully: {len(pdf_document)} pages")
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                page_number = page_num + 1
                
                # Extract text and convert to markdown
                try:
                    # Get markdown from PyMuPDF
                    markdown_text = page.get_textpage().extractTEXT()
                    
                    # Create structured markdown with required headers
                    structured_markdown = self._create_structured_markdown(
                        raw_text=markdown_text,
                        display_title=display_title,
                        page_number=page_number
                    )
                    
                    # Create Document object
                    doc = Document(
                        page_content=structured_markdown,
                        metadata={
                            "source_title": file_stem,
                            "source_file": file_name,
                            "page_number": page_number,
                            "document_type": document_type,
                            "file_name": file_name,
                            "file_extension": ".pdf",
                            "source_path": str(file_path),
                            "chunk_type": "page_based",
                            "format": "markdown"
                        }
                    )
                    
                    documents.append(doc)
                    logger.debug(f"   ✅ Page {page_number} processed")
                    
                except Exception as e:
                    logger.error(f"   ❌ Error processing page {page_number}: {str(e)}")
                    # Create a fallback document with error info
                    fallback_doc = Document(
                        page_content=f"# Title: {display_title}\n## Page No. {page_number}\n### Error Processing Page\nError: {str(e)}",
                        metadata={
                            "source_title": file_stem,
                            "source_file": file_name,
                            "page_number": page_number,
                            "document_type": document_type,
                            "file_name": file_name,
                            "file_extension": ".pdf",
                            "source_path": str(file_path),
                            "chunk_type": "page_based",
                            "format": "markdown",
                            "processing_error": str(e)
                        }
                    )
                    documents.append(fallback_doc)
            
            pdf_document.close()
            logger.info(f"✅ PDF processing completed: {len(documents)} pages processed")
            
        except Exception as e:
            logger.error(f"❌ Failed to open PDF {file_path}: {str(e)}")
            raise
        
        return documents
    
    def _create_structured_markdown(self, raw_text: str, display_title: str, page_number: int) -> str:
        """Create structured markdown with proper headers"""
        
        # Start with required header structure
        markdown_content = f"# Title: {display_title}\n"
        markdown_content += f"## Page No. {page_number}\n"
        
        if not raw_text.strip():
            return markdown_content + "### No Content\n*This page appears to be empty or contains only images.*"
        
        # Process the raw text into structured content
        lines = raw_text.strip().split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Convert content based on simple heuristics
            if self._looks_like_major_heading(line):
                processed_lines.append(f"### {line}")
            elif self._looks_like_minor_heading(line):
                processed_lines.append(f"#### {line}")
            elif self._looks_like_list_item(line):
                processed_lines.append(f"* {line}")
            else:
                processed_lines.append(line)
        
        # Add processed content
        if processed_lines:
            markdown_content += "\n".join(processed_lines)
        else:
            markdown_content += "### Content\n" + raw_text
        
        return markdown_content
    
    def _looks_like_major_heading(self, line: str) -> bool:
        """Simple heuristic for major headings"""
        return (len(line) < 80 and 
                (line.isupper() or 
                 any(keyword in line.upper() for keyword in ['WELCOME', 'BENEFITS', 'FEATURES', 'IMPORTANT', 'TABLE OF CONTENTS'])))
    
    def _looks_like_minor_heading(self, line: str) -> bool:
        """Simple heuristic for minor headings"""
        return (len(line) < 50 and ':' in line and not line.startswith('*') and not line.startswith('-'))
    
    def _looks_like_list_item(self, line: str) -> bool:
        """Simple heuristic for list items"""
        return (line.startswith('•') or line.startswith('-') or line.startswith('*') or 
                (len(line) < 100 and '...' in line))
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Process documents into chunks - for PDFs, each page is already a chunk"""
        try:
            chunked_docs = []
            
            for i, doc in enumerate(documents):
                # Check if this is already a page-based chunk (PDF)
                if doc.metadata.get("chunk_type") == "page_based":
                    # PDF pages are already properly formatted, just add chunk metadata
                    doc.metadata.update({
                        "chunk_index": i,
                        "chunk_id": str(uuid.uuid4()),
                    })
                    chunked_docs.append(doc)
                else:
                    # For non-PDF documents, use text splitting
                    split_docs = self.text_splitter.split_documents([doc])
                    
                    for j, chunk_doc in enumerate(split_docs):
                        # Get source information from metadata
                        source_title = chunk_doc.metadata.get("source_title", "Unknown Source")
                        page_number = chunk_doc.metadata.get("page_number", "Unknown Page")
                        
                        # Add source information at the top of the chunk content for non-PDF
                        source_header = f"[Source: {source_title}, Page: {page_number}]\n\n"
                        chunk_doc.page_content = source_header + chunk_doc.page_content
                        
                        # Add chunk-specific metadata
                        chunk_doc.metadata.update({
                            "chunk_index": len(chunked_docs),
                            "chunk_id": str(uuid.uuid4()),
                        })
                        
                        chunked_docs.append(chunk_doc)
            
            logger.info(f"Created {len(chunked_docs)} chunks from {len(documents)} documents")
            return chunked_docs
            
        except Exception as e:
            logger.error(f"Error chunking documents: {str(e)}")
            raise
    
    async def embed_and_store(self, chunks: List[Document]) -> Dict[str, Any]:
        """Embed Document chunks and store in ChromaDB"""
        try:
            collection = self._get_collection()
            
            # Prepare data for ChromaDB from Document objects
            documents = []
            metadatas = []
            ids = []
            
            for chunk in chunks:
                documents.append(chunk.page_content)
                metadatas.append(chunk.metadata)
                ids.append(chunk.metadata["chunk_id"])
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} chunks...")
            embeddings = await self.embeddings.aembed_documents(documents)
            
            # Store in ChromaDB
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully stored {len(chunks)} chunks in ChromaDB")
            
            return {
                "chunks_stored": len(chunks),
                "collection_name": settings.chromadb_collection_name,
                "total_documents_in_collection": collection.count()
            }
            
        except Exception as e:
            logger.error(f"Error embedding and storing chunks: {str(e)}")
            raise
    
    async def ingest_document(
        self, 
        file_path: str, 
        document_type: str = "policy"
    ) -> Dict[str, Any]:
        """Complete document ingestion pipeline"""
        try:
            logger.info(f"🚀 STARTING DOCUMENT INGESTION: {file_path}")
            logger.info(f"📋 Document type: {document_type}")
            logger.info(f"🗂️ Collection name: {settings.chromadb_collection_name}")
            logger.info(f"📍 ChromaDB path: {settings.chromadb_path}")
            
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            logger.info(f"✅ File exists, size: {os.path.getsize(file_path)} bytes")
            
            # Load document
            logger.info(f"📄 Loading document...")
            documents = self.load_document(file_path, document_type)
            logger.info(f"✅ Loaded {len(documents)} document(s)")
            
            # Chunk documents
            logger.info(f"✂️ Chunking documents...")
            chunks = self.chunk_documents(documents)
            logger.info(f"✅ Created {len(chunks)} chunks")
            
            # Embed and store
            logger.info(f"🧠 Embedding and storing chunks...")
            result = await self.embed_and_store(chunks)
            logger.info(f"✅ Stored {result.get('chunks_stored', 0)} chunks in collection")
            
            # Add file info to result
            result.update({
                "file_name": Path(file_path).name,
                "document_type": document_type,
                "original_documents": len(documents),
                "status": "success"
            })
            
            logger.info(f"🎉 DOCUMENT INGESTION COMPLETED: {file_path}")
            logger.info(f"📊 Final collection count: {result.get('total_documents_in_collection', 0)}")
            return result
            
        except Exception as e:
            logger.error(f"❌ DOCUMENT INGESTION FAILED: {file_path}")
            logger.error(f"💥 Error: {str(e)}")
            import traceback
            logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
            return {
                "file_name": Path(file_path).name if file_path else "unknown",
                "status": "failed",
                "error": str(e)
            }
    
    async def ingest_directory(
        self, 
        directory_path: str, 
        document_type: str = "policy"
    ) -> List[Dict[str, Any]]:
        """Ingest all documents from a directory with enhanced metadata"""
        try:
            directory = Path(directory_path)
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            results = []
            supported_extensions = [".pdf", ".docx", ".txt"]
            
            # Find all supported files
            files = []
            for ext in supported_extensions:
                files.extend(directory.glob(f"*{ext}"))
            
            logger.info(f"🗂️ Found {len(files)} documents to ingest from {directory_path}")
            
            # Process each file
            for file_path in files:
                logger.info(f"📄 Processing: {file_path.name}")
                result = await self.ingest_document(str(file_path), document_type)
                results.append(result)
            
            # Summary
            successful = len([r for r in results if r.get("status") == "success"])
            failed = len(results) - successful
            total_chunks = sum(r.get("chunks_stored", 0) for r in results if r.get("status") == "success")
            
            logger.info(f"📊 Directory ingestion completed:")
            logger.info(f"   ✅ {successful} files successful")
            logger.info(f"   ❌ {failed} files failed") 
            logger.info(f"   📝 {total_chunks} total chunks created")
            
            return results
            
        except Exception as e:
            logger.error(f"Directory ingestion failed for {directory_path}: {str(e)}")
            return [{
                "directory": directory_path,
                "status": "failed",
                "error": str(e)
            }]
    
    async def ingest_pdfs_from_directory(
        self, 
        directory_path: str, 
        document_type: str = "scotia_document"
    ) -> Dict[str, Any]:
        """Specialized method for ingesting multiple PDFs with detailed source tracking"""
        try:
            directory = Path(directory_path)
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            # Find all PDF files
            pdf_files = list(directory.glob("*.pdf"))
            
            if not pdf_files:
                return {
                    "status": "no_files",
                    "message": f"No PDF files found in {directory_path}",
                    "directory": str(directory)
                }
            
            logger.info(f"📁 Processing {len(pdf_files)} PDF files from {directory}")
            
            all_results = []
            total_chunks = 0
            total_pages = 0
            
            for pdf_file in pdf_files:
                logger.info(f"📄 Processing PDF: {pdf_file.name}")
                
                try:
                    # Load the PDF with enhanced metadata
                    documents = self.load_document(str(pdf_file), document_type)
                    total_pages += len(documents)
                    
                    # Chunk the documents
                    chunks = self.chunk_documents(documents)
                    total_chunks += len(chunks)
                    
                    # Embed and store
                    store_result = await self.embed_and_store(chunks)
                    
                    result = {
                        "file_name": pdf_file.name,
                        "status": "success",
                        "pages": len(documents),
                        "chunks": len(chunks),
                        "document_type": document_type
                    }
                    
                    logger.info(f"   ✅ {pdf_file.name}: {len(documents)} pages → {len(chunks)} chunks")
                    
                except Exception as e:
                    result = {
                        "file_name": pdf_file.name,
                        "status": "failed",
                        "error": str(e),
                        "document_type": document_type
                    }
                    logger.error(f"   ❌ {pdf_file.name}: {str(e)}")
                
                all_results.append(result)
            
            # Summary statistics
            successful_files = [r for r in all_results if r["status"] == "success"]
            failed_files = [r for r in all_results if r["status"] == "failed"]
            
            summary = {
                "status": "completed",
                "directory": str(directory),
                "total_files": len(pdf_files),
                "successful_files": len(successful_files),
                "failed_files": len(failed_files),
                "total_pages": total_pages,
                "total_chunks": total_chunks,
                "document_type": document_type,
                "results": all_results
            }
            
            logger.info(f"🎉 PDF Directory Ingestion Summary:")
            logger.info(f"   📁 Directory: {directory}")
            logger.info(f"   📄 Files processed: {len(pdf_files)}")
            logger.info(f"   ✅ Successful: {len(successful_files)}")
            logger.info(f"   ❌ Failed: {len(failed_files)}")
            logger.info(f"   📄 Total pages: {total_pages}")
            logger.info(f"   📝 Total chunks: {total_chunks}")
            
            return summary
            
        except Exception as e:
            logger.error(f"PDF directory ingestion failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "directory": str(directory_path)
            }
    
    def list_documents(self) -> Dict[str, Any]:
        """List all documents in the collection"""
        try:
            collection = self._get_collection()
            
            # Get all documents
            results = collection.get(include=["metadatas"])
            
            # Group by document
            documents = {}
            for metadata in results["metadatas"]:
                file_name = metadata.get("file_name", "unknown")
                doc_type = metadata.get("document_type", "unknown")
                
                if file_name not in documents:
                    documents[file_name] = {
                        "file_name": file_name,
                        "document_type": doc_type,
                        "chunk_count": 0,
                        "file_extension": metadata.get("file_extension", "unknown")
                    }
                
                documents[file_name]["chunk_count"] += 1
            
            return {
                "total_documents": len(documents),
                "total_chunks": collection.count(),
                "documents": list(documents.values())
            }
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "documents": [],
                "error": str(e)
            }
    
    def delete_document(self, file_name: str) -> Dict[str, Any]:
        """Delete all chunks of a specific document"""
        try:
            collection = self._get_collection()
            
            # Find all chunks for this document
            results = collection.get(
                where={"file_name": file_name},
                include=["metadatas"]
            )
            
            if not results["ids"]:
                return {
                    "status": "not_found",
                    "message": f"No document found with name: {file_name}"
                }
            
            # Delete the chunks
            collection.delete(ids=results["ids"])
            
            logger.info(f"Deleted {len(results['ids'])} chunks for document {file_name}")
            
            return {
                "status": "success",
                "deleted_chunks": len(results["ids"]),
                "file_name": file_name
            }
            
        except Exception as e:
            logger.error(f"Error deleting document {file_name}: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "file_name": file_name
            }
    
    def clear_collection(self) -> Dict[str, Any]:
        """Clear all documents from the ChromaDB collection without deleting the collection itself"""
        try:
            collection_name = settings.chromadb_collection_name
            
            try:
                # Try to get existing collection
                collection = self._get_collection()
                collection_count = collection.count()
                
                if collection_count > 0:
                    # Get all document IDs
                    all_docs = collection.get(include=[])
                    all_ids = all_docs["ids"]
                    
                    # Delete all documents from the collection (but keep the collection)
                    collection.delete(ids=all_ids)
                    
                    logger.info(f"Cleared all documents from ChromaDB collection '{collection_name}' ({collection_count} chunks)")
                    
                    return {
                        "status": "success",
                        "cleared_chunks": collection_count,
                        "collection_name": collection_name
                    }
                else:
                    return {
                        "status": "empty",
                        "message": "Collection was already empty",
                        "collection_name": collection_name
                    }
                    
            except Exception as e:
                # Collection doesn't exist or other error
                logger.info(f"Collection '{collection_name}' does not exist or error occurred: {str(e)}")
                return {
                    "status": "not_found",
                    "message": f"Collection does not exist: {str(e)}",
                    "collection_name": collection_name
                }
                
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "collection_name": settings.chromadb_collection_name
            }

# Global service instance
document_ingestion_service = DocumentIngestionService()
