from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import os
from pathlib import Path

# Get database path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATABASE_PATH = BASE_DIR / "data" / "banking_bot.db"
DATABASE_PATH.parent.mkdir(exist_ok=True)

# Database URL
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
        "timeout": 20,
    },
    echo=False,  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
