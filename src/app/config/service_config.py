from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    # API Settings
    app_name: str = "Banking Bot API"
    app_version: str = "1.0.0"
    debug: bool = True  # Enable for development and API documentation
    
    # Database
    database_url: str = "sqlite:///./data/banking_bot.db"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_temperature: float = 0.1
    max_tokens: int = 4000
    
    # ChromaDB
    chromadb_path: str = "./data/chromadb"
    chromadb_collection_name: str = "bank_documents"
    
    # Authentication
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 300
    
    # LangGraph
    langraph_memory_type: str = "in_memory"  # or "sqlite" for persistent memory
    langraph_checkpoint_path: str = "./data/checkpoints"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/banking_bot.log"
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # File upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = ["pdf", "docx", "txt"]
    
    # CORS
    allowed_origins: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:2024",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:2024",
    ]
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )

# Create global settings instance
settings = Settings()

# Ensure required directories exist
import pathlib
pathlib.Path("./data").mkdir(exist_ok=True)
pathlib.Path("./logs").mkdir(exist_ok=True)
pathlib.Path(settings.chromadb_path).mkdir(parents=True, exist_ok=True)
pathlib.Path(settings.langraph_checkpoint_path).mkdir(parents=True, exist_ok=True)
