from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    accounts = relationship("Account", back_populates="user")
    chat_histories = relationship("ChatHistory", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_number = Column(String(20), unique=True, index=True, nullable=False)
    account_type = Column(String(20), nullable=False)  # checking, savings, credit
    balance = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # debit, credit
    amount = Column(Float, nullable=False)
    description = Column(String(255))
    category = Column(String(50))
    merchant = Column(String(100))
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="transactions")

class CreditCard(Base):
    __tablename__ = "credit_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_number = Column(String(20), unique=True, index=True, nullable=False)
    card_type = Column(String(30), nullable=False)  # Premium, Gold, Platinum, etc.
    credit_limit = Column(Float, nullable=False)
    current_balance = Column(Float, default=0.0)
    available_credit = Column(Float)
    minimum_payment = Column(Float, default=0.0)
    due_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_thread_id = Column(String(100), index=True, nullable=False)
    user_query = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    query_type = Column(String(50))  # account_info, transaction, policy, general
    tools_used = Column(String(255))  # JSON string of tools used
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_histories")
    feedbacks = relationship("Feedback", back_populates="chat_message")

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_history_id = Column(Integer, ForeignKey("chat_history.id"), nullable=False)
    rating = Column(Integer)  # 1 (thumbs down) or 2 (thumbs up)
    comments = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="feedbacks")
    chat_message = relationship("ChatHistory", back_populates="feedbacks")

class BotLog(Base):
    __tablename__ = "bot_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    chat_thread_id = Column(String(100), index=True)
    log_level = Column(String(10), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    error_details = Column(Text)
    endpoint = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String(255), nullable=False)
    chunk_id = Column(String(100), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    doc_metadata = Column("metadata", Text)  # Map to 'metadata' column but use 'doc_metadata' attribute
    created_at = Column(DateTime, server_default=func.now())
