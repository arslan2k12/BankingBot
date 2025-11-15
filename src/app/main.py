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
