from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Setup project path for consistent imports
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.app.config.service_config import settings
from src.app.utils.logger_utils import setup_logging, get_logger
from src.ingestion_app.api.endpoints import documents

# Setup logging
setup_logging(settings.log_level, settings.log_file)
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Document Ingestion API...")
    
    # Initialize ChromaDB
    try:
        from .services.document_ingestion import document_ingestion_service
        # Test connection
        _ = document_ingestion_service._get_collection()
        logger.info("ChromaDB connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {str(e)}")
        raise
    
    logger.info("Document Ingestion API startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Document Ingestion API...")

# Create FastAPI app
app = FastAPI(
    title="Banking Bot Document Ingestion API",
    version=settings.app_version,
    description="""
    Document Ingestion API for Banking Bot - Process and store bank policies and credit card benefits.
    
    Features:
    - PDF, DOCX, and TXT document processing
    - Automatic chunking and embedding
    - ChromaDB vector storage
    - Batch document processing
    - Document management (list, delete)
    """,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
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
app.include_router(documents.router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Banking Bot Document Ingestion API",
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else None,
        "supported_formats": ["PDF", "DOCX", "TXT"],
        "endpoints": {
            "upload_single": "/documents/upload",
            "upload_multiple": "/documents/upload-multiple",
            "ingest_directory": "/documents/ingest-directory",
            "list_documents": "/documents/list",
            "delete_document": "/documents/document/{file_name}",
            "health": "/documents/health"
        }
    }

# Development server
if __name__ == "__main__":
    uvicorn.run(
        "ingestion_main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
