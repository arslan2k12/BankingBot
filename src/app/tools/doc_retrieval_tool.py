from langchain.tools import tool
from typing import Optional
import json
import chromadb
import os
from pathlib import Path
from langchain_openai import OpenAIEmbeddings

import logging

# Setup logging for document tool
logger = logging.getLogger(__name__)

@tool
def search_bank_documents(query: str) -> str:
    """Search through bank policies, credit card benefits, and other banking documents.
    
    Use this tool for queries about:
    - Bank policies and procedures
    - Credit card benefits and features
    - Fee structures and charges
    - General banking information
    - Terms and conditions
    
    Args:
        query: Clear description of what information you're looking for
    
    Returns:
        JSON string with relevant document information
    """
    logger.info(f"🔍 TOOL CALLED: search_bank_documents with query: '{query}'")
    
    try:
        # Import settings to get the correct collection name
        from src.app.config.service_config import settings
        
        PROJECT_ROOT = Path(__file__).parents[3]
        chromadb_path = PROJECT_ROOT / "data" / "chromadb"
        
        logger.info(f"📂 Connecting to ChromaDB at: {chromadb_path}")
        logger.info(f"🗂️ Looking for collection: '{settings.chromadb_collection_name}'")
        
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=str(chromadb_path))
        
        # List all collections to debug
        all_collections = client.list_collections()
        collection_names = [col.name for col in all_collections]
        logger.info(f"🗃️ Available collections: {collection_names}")
        
        # Get the collection
        try:
            collection = client.get_collection(name=settings.chromadb_collection_name)
            collection_count = collection.count()
            logger.info(f"✅ Found collection '{settings.chromadb_collection_name}' with {collection_count} documents")
        except Exception as e:
            logger.error(f"❌ Failed to get collection '{settings.chromadb_collection_name}': {str(e)}")
            logger.info(f"🔍 Available collections: {collection_names}")
            return json.dumps({
                "error": f"Collection '{settings.chromadb_collection_name}' does not exist. Available: {collection_names}",
                "query": query,
                "chromadb_path": str(chromadb_path),
                "collection_name_used": settings.chromadb_collection_name
            })
        
        if collection_count == 0:
            logger.warning(f"⚠️ Collection '{settings.chromadb_collection_name}' is empty")
            return json.dumps({
                "results": [],
                "message": f"Collection '{settings.chromadb_collection_name}' exists but is empty. Run document ingestion first.",
                "collection_count": collection_count
            })
        
        # Generate query embedding using the same model used for ingestion
        logger.info(f"🧠 Generating query embedding using OpenAI model: {settings.openai_embedding_model}")
        embeddings_model = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key
        )
        query_embedding = embeddings_model.embed_query(query)
        logger.info(f"✅ Generated query embedding with {len(query_embedding)} dimensions")
        
        # Search for similar documents using the embedding
        logger.info(f"🔎 Searching for top 5 similar documents...")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        
        if not results['documents'] or not results['documents'][0]:
            logger.warning("❌ No documents found matching the query")
            return json.dumps({
                "results": [],
                "message": "No relevant documents found for your query.",
                "collection_count": collection_count
            })
        
        documents_found = len(results['documents'][0])
        logger.info(f"✅ Found {documents_found} relevant documents")
        
        formatted_results = []
        documents = results['documents'][0]
        metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(documents)
        distances = results['distances'][0] if results['distances'] else [0.0] * len(documents)
        
        logger.info("📄 Processing retrieved documents:")
        for i, doc in enumerate(documents):
            relevance_score = round(1 - distances[i], 3) if i < len(distances) else 0.0
            doc_length = len(doc)
            metadata = metadatas[i] if i < len(metadatas) else {}
            logger.info(f"   📃 Document {i+1}: {doc_length} chars, relevance: {relevance_score}")
            logger.info(f"       Metadata: {metadata}")
            
            formatted_results.append({
                "content": doc,
                "metadata": metadata,
                "relevance_score": relevance_score
            })
        
        logger.info(f"📤 Returning {len(formatted_results)} formatted documents")
        response = {
            "results": formatted_results,
            "total_found": len(formatted_results),
            "query": query,
            "collection_name": settings.chromadb_collection_name,
            "collection_count": collection_count
        }
        
        return json.dumps(response, default=str)
        
    except Exception as e:
        logger.error(f"❌ DOCUMENT SEARCH ERROR: {str(e)}")
        import traceback
        logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
        return json.dumps({
            "error": f"Document search failed: {str(e)}",
            "query": query,
            "traceback": traceback.format_exc()
        })
