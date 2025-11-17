# Setup project path for consistent imports
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.app.api.endpoints import auth, chat, feedback, health
from src.app.config.service_config import settings
from src.app.database.database import Base, engine
from src.app.utils.logger_utils import get_logger, setup_logging

# Setup logging
setup_logging(settings.log_level, settings.log_file)
logger = get_logger(__name__)

def display_chromadb_documents():
    """Display information about documents available in ChromaDB"""
    try:
        import chromadb
        from pathlib import Path
        
        # Connect to ChromaDB
        chromadb_path = Path(PROJECT_ROOT) / "data" / "chromadb"
        client = chromadb.PersistentClient(path=str(chromadb_path))
        
        logger.info("=" * 80)
        logger.info("📚 CHROMADB DOCUMENT INVENTORY")
        logger.info("=" * 80)
        
        try:
            # Get the collection
            collection = client.get_collection(name=settings.chromadb_collection_name)
            total_chunks = collection.count()
            
            if total_chunks == 0:
                logger.info("📭 No documents found in ChromaDB collection")
                logger.info("   Use the ingestion API to add documents: http://localhost:8000/docs")
                logger.info("=" * 80)
                return
            
            # Get all documents with metadata
            results = collection.get(include=["metadatas"])
            
            # Group by unique document titles
            documents = {}
            for metadata in results["metadatas"]:
                source_title = metadata.get("source_title", metadata.get("file_name", "Unknown"))
                doc_type = metadata.get("document_type", "unknown")
                file_ext = metadata.get("file_extension", "unknown")
                
                if source_title not in documents:
                    documents[source_title] = {
                        "title": source_title,
                        "type": doc_type,
                        "extension": file_ext,
                        "chunk_count": 0,
                        "pages": set()
                    }
                
                documents[source_title]["chunk_count"] += 1
                
                # Collect page numbers if available
                page_num = metadata.get("page_number")
                if page_num and page_num != "unknown":
                    documents[source_title]["pages"].add(page_num)
            
            # Display summary
            logger.info(f"📊 Total Chunks: {total_chunks}")
            logger.info(f"📄 Unique Documents: {len(documents)}")
            logger.info(f"🗂️ Collection: '{settings.chromadb_collection_name}'")
            logger.info("-" * 80)
            
            # Display each document
            for i, (title, info) in enumerate(documents.items(), 1):
                pages_info = ""
                if info["pages"]:
                    sorted_pages = sorted(list(info["pages"]))
                    if len(sorted_pages) > 5:
                        pages_info = f" (Pages: {sorted_pages[0]}-{sorted_pages[-1]})"
                    else:
                        pages_info = f" (Pages: {', '.join(map(str, sorted_pages))})"
                
                # Truncate long titles for better display
                display_title = title if len(title) <= 60 else title[:57] + "..."
                
                logger.info(f"📖 {i:2d}. {display_title}")
                logger.info(f"      Type: {info['type']} | Format: {info['extension']} | Chunks: {info['chunk_count']}{pages_info}")
            
            logger.info("=" * 80)
            logger.info(f"✅ Banking Bot can answer questions about these {len(documents)} documents")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Collection '{settings.chromadb_collection_name}' not found: {str(e)}")
            logger.info("   Use the ingestion API to create and populate the collection")
            logger.info("   Ingestion API: http://localhost:8000/docs")
            logger.info("=" * 80)
            
    except Exception as e:
        logger.error(f"❌ Failed to connect to ChromaDB: {str(e)}")
        logger.info("=" * 80)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Banking Bot API...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise
    
    # Display ChromaDB document inventory
    display_chromadb_documents()
    
    # Initialize agents and services (agents are now created per-user)
    try:
        from src.app.agents.banking_agent import get_banking_agent

        # Test agent creation with a demo user
        test_agent = get_banking_agent("demo_user")
        logger.info("Banking agent factory initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize banking agent factory: {str(e)}")
        raise
    
    logger.info("Banking Bot API startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Banking Bot API...")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Banking Bot API - An intelligent banking assistant powered by LangChain and LangGraph.
    
    Features:
    - Account balance inquiries
    - Transaction history
    - Credit card information
    - Bank policies and procedures
    - Fee structures and benefits
    - Personalized chat experience with memory
    - Real-time streaming responses
    - User feedback system
    """,
    lifespan=lifespan,
    docs_url="/docs",  # Always enable docs for development
    redoc_url="/redoc"  # Always enable redoc for development
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(health.router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback

    # Get the full exception traceback for better debugging
    exc_traceback = traceback.format_exc()
    
    # Handle different types of exceptions
    if isinstance(exc, (TypeError, AttributeError)):
        logger.error(f"Unhandled exception: [{type(exc).__name__}(\"{str(exc)}\")]")
        logger.error(f"Full traceback:\n{exc_traceback}")
    else:
        logger.error(f"Unhandled exception: {str(exc)}")
        logger.error(f"Full traceback:\n{exc_traceback}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
            "error_type": type(exc).__name__
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Banking Bot API",
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/health",
        "chat_endpoint": "/chat",
        "auth_endpoint": "/auth"
    }

# Development server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=2024,  # Changed to port 2024 for agent chat UI compatibility
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
