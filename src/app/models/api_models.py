from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# User models
class UserCreate(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    user_id: str
    password: str

class UserResponse(BaseModel):
    id: int
    user_id: str
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Chat models
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    chat_thread_id: Optional[str] = None

class EvaluationScore(BaseModel):
    accuracy: int = Field(..., ge=1, le=5, description="How accurate the response is (1-5)")
    completeness: int = Field(..., ge=1, le=5, description="How complete the response is (1-5)")
    context_adherence: int = Field(..., ge=1, le=5, description="How well the response adheres to context (1-5)")
    professional_quality: int = Field(..., ge=1, le=5, description="Professional quality of the response (1-5)")
    overall_score: float = Field(..., ge=1.0, le=5.0, description="Overall average score")
    reasoning: str = Field(..., description="Detailed reasoning for the scores")
    confidence_level: str = Field(..., description="HIGH, MEDIUM, or LOW confidence")

class ChatResponse(BaseModel):
    response: str
    chat_thread_id: str
    query_type: Optional[str]
    tools_used: Optional[List[str]]
    response_time_ms: Optional[int]
    evaluation: Optional[EvaluationScore] = None

class ChatHistoryResponse(BaseModel):
    id: int
    chat_thread_id: str
    user_query: str
    bot_response: str
    query_type: Optional[str]
    tools_used: Optional[str]
    response_time_ms: Optional[int]
    created_at: datetime
    feedback: Optional["FeedbackResponse"] = None

    class Config:
        from_attributes = True

# Account models
class AccountResponse(BaseModel):
    id: int
    account_number: str
    account_type: str
    balance: float
    currency: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Transaction models
class TransactionResponse(BaseModel):
    id: int
    transaction_id: str
    transaction_type: str
    amount: float
    description: Optional[str]
    category: Optional[str]
    merchant: Optional[str]
    transaction_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class TransactionQuery(BaseModel):
    limit: Optional[int] = Field(default=10, ge=1, le=100)
    account_number: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    transaction_type: Optional[str] = None
    category: Optional[str] = None

# Credit Card models
class CreditCardResponse(BaseModel):
    id: int
    card_number: str
    card_type: str
    credit_limit: float
    current_balance: float
    available_credit: Optional[float]
    minimum_payment: float
    due_date: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

# Feedback models
class FeedbackCreate(BaseModel):
    chat_history_id: int
    rating: int = Field(..., ge=1, le=2)  # 1 = thumbs down, 2 = thumbs up
    comments: Optional[str] = Field(None, max_length=1000)

class FeedbackResponse(BaseModel):
    id: int
    rating: int
    comments: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Tool response models
class ToolResponse(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Agent state models
class AgentState(BaseModel):
    messages: List[Dict[str, Any]]
    user_id: str
    chat_thread_id: str
    current_step: str
    tools_used: List[str] = []
    context: Dict[str, Any] = {}

# Authentication models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[str] = None

# Health check model
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database_status: str
    chromadb_status: str

# Error models
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime

# Document ingestion models
class DocumentIngestRequest(BaseModel):
    file_name: str
    document_type: str = Field(..., description="Type of document (policy, credit_card_benefits, etc.)")
    
class DocumentIngestResponse(BaseModel):
    success: bool
    message: str
    chunks_created: int
    document_id: str
