from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from enum import Enum

class QueryType(str, Enum):
    """Types of banking queries"""
    ACCOUNT_BALANCE = "account_balance"
    TRANSACTION_HISTORY = "transaction_history"
    CREDIT_CARD_INFO = "credit_card_info"
    GENERAL_BANKING = "general_banking"
    POLICY_QUESTION = "policy_question"
    FEE_STRUCTURE = "fee_structure"
    ACCOUNT_INFO = "account_info"

class ToolUsed(str, Enum):
    """Tools that can be used by the agent"""
    SQL_RETRIEVAL = "sql_retrieval_tool"
    DOCUMENT_RETRIEVAL = "document_retrieval_tool"
    NONE = "none"

class ConfidenceLevel(str, Enum):
    """Confidence levels for responses"""
    HIGH = "high"
    MEDIUM = "medium"  
    LOW = "low"

class BankingResponse(BaseModel):
    """Structured response from the banking agent"""
    response: str = Field(description="The main response to the user's query")
    query_type: QueryType = Field(description="The type of query that was processed")
    tools_used: List[ToolUsed] = Field(description="List of tools that were used to generate the response")
    confidence: ConfidenceLevel = Field(description="Confidence level in the response accuracy")
    requires_authentication: bool = Field(description="Whether the query required user authentication")
    data_sources: List[str] = Field(description="Sources of data used (e.g., 'customer_database', 'policy_documents')")
    follow_up_suggestions: Optional[List[str]] = Field(default=None, description="Suggested follow-up questions or actions")
    warnings: Optional[List[str]] = Field(default=None, description="Any warnings or important notices")

class AccountBalanceInfo(BaseModel):
    """Structured account balance information"""
    account_number: str
    account_type: str
    balance: float
    currency: str
    as_of_date: datetime

class TransactionInfo(BaseModel):
    """Structured transaction information"""
    transaction_id: str
    amount: float
    transaction_type: str
    description: str
    date: datetime
    merchant: Optional[str] = None
    category: Optional[str] = None

class CreditCardInfo(BaseModel):
    """Structured credit card information"""
    card_type: str
    credit_limit: float
    current_balance: float
    available_credit: float
    minimum_payment: float
    due_date: Optional[datetime] = None
    utilization_rate: float

class BankingData(BaseModel):
    """Structured banking data response"""
    account_balances: Optional[List[AccountBalanceInfo]] = None
    transactions: Optional[List[TransactionInfo]] = None
    credit_cards: Optional[List[CreditCardInfo]] = None
    total_balance: Optional[float] = None

class DocumentInfo(BaseModel):
    """Information about retrieved documents"""
    document_name: str
    content_snippet: str
    relevance_score: float
    document_type: str

class AgentState(BaseModel):
    """State of the banking agent during processing"""
    user_id: str
    query: str
    query_type: Optional[QueryType] = None
    requires_customer_data: bool = False
    tools_to_use: List[ToolUsed] = []
    context: Dict[str, Any] = {}
    
class ChatContext(BaseModel):
    """Context for chat history and memory"""
    user_id: str
    chat_thread_id: str
    conversation_history: List[Dict[str, Any]] = []
    user_preferences: Dict[str, Any] = {}
    session_data: Dict[str, Any] = {}
