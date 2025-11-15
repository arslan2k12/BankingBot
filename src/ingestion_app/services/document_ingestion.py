from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import chromadb
from chromadb.config import Settings
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

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
        """Load a document from file path and return LangChain Document objects"""
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == ".pdf":
                loader = PyPDFLoader(file_path)
                documents = loader.load()
            elif file_extension == ".docx":
                loader = Docx2txtLoader(file_path)
                documents = loader.load()
            elif file_extension == ".txt":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Create LangChain Document for text files
                documents = [Document(
                    page_content=content,
                    metadata={
                        "source": file_path,
                        "document_type": document_type,
                        "file_name": Path(file_path).name,
                        "file_extension": file_extension
                    }
                )]
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Add metadata to all documents
            for doc in documents:
                if not isinstance(doc, Document):
                    # Convert to proper Document if needed
                    doc = Document(page_content=doc.page_content, metadata=doc.metadata)
                
                doc.metadata.update({
                    "document_type": document_type,
                    "file_name": Path(file_path).name,
                    "file_extension": file_extension
                })
            
            logger.info(f"Loaded {len(documents)} documents from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split LangChain documents into chunks"""
        try:
            # Use the text splitter's split_documents method for proper Document handling
            chunked_docs = self.text_splitter.split_documents(documents)
            
            # Add chunk-specific metadata
            for i, chunk_doc in enumerate(chunked_docs):
                chunk_doc.metadata.update({
                    "chunk_index": i,
                    "chunk_id": str(uuid.uuid4()),
                })
            
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
        """Ingest all documents from a directory"""
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
            
            logger.info(f"Found {len(files)} documents to ingest from {directory_path}")
            
            # Process each file
            for file_path in files:
                result = await self.ingest_document(str(file_path), document_type)
                results.append(result)
            
            # Summary
            successful = len([r for r in results if r.get("status") == "success"])
            failed = len(results) - successful
            
            logger.info(f"Directory ingestion completed: {successful} successful, {failed} failed")
            
            return results
            
        except Exception as e:
            logger.error(f"Directory ingestion failed for {directory_path}: {str(e)}")
            return [{
                "directory": directory_path,
                "status": "failed",
                "error": str(e)
            }]
    
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
