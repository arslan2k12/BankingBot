from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from ...database.database import get_db, engine
from ...models.api_models import HealthResponse
import chromadb
from pathlib import Path
from ...config.service_config import settings
from ...utils.logger_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        database_status = f"unhealthy: {str(e)}"
    
    # Test ChromaDB connection
    try:
        PROJECT_ROOT = Path(__file__).parents[4]
        client = chromadb.PersistentClient(
            path=str(PROJECT_ROOT / "data" / "chromadb")
        )
        
        # Try to get the collection, create if it doesn't exist
        try:
            collection = client.get_collection(name="bank_documents")
            collection_count = collection.count()
            chromadb_status = "healthy"
            logger.info(f"ChromaDB health check passed: {collection_count} documents")
        except Exception as get_error:
            # Collection might not exist, try with the alternative name
            try:
                collection = client.get_collection(name="banking_documents")
                collection_count = collection.count()
                chromadb_status = "healthy"
                logger.info(f"ChromaDB health check passed: {collection_count} documents")
            except Exception as alt_error:
                # List all collections to see what exists
                collections = client.list_collections()
                collection_names = [c.name for c in collections]
                logger.info(f"Available collections: {collection_names}")
                if collection_names:
                    # Use the first available collection for health check
                    collection = collections[0]
                    collection_count = collection.count()
                    chromadb_status = "healthy"
                    logger.info(f"ChromaDB health check passed using collection '{collection.name}': {collection_count} documents")
                else:
                    chromadb_status = f"unhealthy: No collections found. Available: {collection_names}"
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {str(e)}")
        chromadb_status = f"unhealthy: {str(e)}"
    
    overall_status = "healthy" if database_status == "healthy" and chromadb_status == "healthy" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version=settings.app_version,
        database_status=database_status,
        chromadb_status=chromadb_status
    )

@router.get("/database")
async def database_health(db: Session = Depends(get_db)):
    """Detailed database health check"""
    try:
        # Test basic connectivity
        db.execute(text("SELECT 1"))
        
        # Test table access
        from ...models.database_models import User, ChatHistory, Feedback
        user_count = db.query(User).count()
        chat_count = db.query(ChatHistory).count()
        feedback_count = db.query(Feedback).count()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "statistics": {
                "total_users": user_count,
                "total_chats": chat_count,
                "total_feedback": feedback_count
            },
            "database_url": settings.database_url.split("///")[0] + "///*****"  # Hide full path
        }
    except Exception as e:
        logger.error(f"Database detailed health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e)
        }

@router.get("/chromadb")
async def chromadb_health():
    """Detailed ChromaDB health check"""
    try:
        PROJECT_ROOT = Path(__file__).parents[4]
        client = chromadb.PersistentClient(
            path=str(PROJECT_ROOT / "data" / "chromadb")
        )
        
        # List all collections first
        collections = client.list_collections()
        collection_names = [c.name for c in collections]
        
        if not collections:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now(),
                "error": "No collections found",
                "available_collections": collection_names,
                "chromadb_path": str(PROJECT_ROOT / "data" / "chromadb")
            }
        
        # Use the first available collection
        collection = collections[0]
        collection_count = collection.count()
        
        # Test query capability
        can_query = True
        query_error = None
        try:
            results = collection.query(query_texts=["test"], n_results=1)
            if not results or not results.get('documents'):
                can_query = False
                query_error = "No documents returned from query"
        except Exception as qe:
            can_query = False
            query_error = str(qe)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "collection_name": collection.name,
            "total_documents": collection_count,
            "can_query": can_query,
            "query_error": query_error,
            "available_collections": collection_names,
            "chromadb_path": str(PROJECT_ROOT / "data" / "chromadb")
        }
    except Exception as e:
        logger.error(f"ChromaDB detailed health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e)
        }
