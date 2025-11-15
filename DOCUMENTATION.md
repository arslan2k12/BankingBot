# Banking Bot API - Complete Module Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Modules](#core-modules)
3. [Database Models](#database-models)
4. [API Models](#api-models)
5. [Agent Models](#agent-models)
6. [Services](#services)
7. [Tools](#tools)
8. [Agents](#agents)
9. [Utilities](#utilities)
10. [Configuration](#configuration)
11. [API Endpoints](#api-endpoints)

## Architecture Overview

The Banking Bot is built using a modular architecture with clear separation of concerns:

```
Banking Bot System
├── FastAPI Application (Port 2024)
├── LangGraph Agent with Tools
├── SQLite Database (Customer Data)
├── ChromaDB Vector Store (Documents)
├── Authentication System (JWT)
└── Document Ingestion Pipeline
```

## Project Structure and Import Strategy

### Consistent Import Paths

All modules use a consistent import strategy by adding the project root to Python path:

```python
# At the top of every module file
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Adjust levels as needed
sys.path.insert(0, str(PROJECT_ROOT))

# Now all imports use absolute paths from project root
from src.app.config.service_config import settings
from src.app.models.agent_models import BankingResponse
from src.ingestion_app.services.document_ingestion import DocumentIngestionService
```

### Module Organization

- **`src/app/`** - Main banking bot application
- **`src/ingestion_app/`** - Data creation and document ingestion
- **`src/utils/`** - Shared utilities across applications

## Core Modules

### src/app/main.py
**Main FastAPI Application**

```python
class FastAPI:
    """Main application instance with CORS, middleware, and route registration"""
```

**Key Functions:**
- `lifespan()` - Application startup/shutdown lifecycle management
- Global exception handler for error management
- CORS configuration for frontend integration
- Router registration for all endpoints

**Configuration:**
- Runs on port 2024 for agent chat UI compatibility
- Automatic API documentation at `/docs`
- Health monitoring and structured logging

---

## Database Models

### src/app/models/database_models.py
**SQLAlchemy ORM Models for Database Schema**

#### User Model
```python
class User(Base):
    """User account model with authentication and profile information"""
    
    # Attributes
    id: int              # Primary key
    user_id: str         # Unique username (50 chars)
    password_hash: str   # Bcrypt hashed password
    email: str           # User email (optional)
    first_name: str      # User's first name
    last_name: str       # User's last name
    is_active: bool      # Account active status
    created_at: datetime # Account creation timestamp
    updated_at: datetime # Last update timestamp
    
    # Relationships
    accounts: List[Account]        # User's bank accounts
    chat_histories: List[ChatHistory] # Chat conversation history
    feedbacks: List[Feedback]      # User feedback on responses
```

#### Account Model
```python
class Account(Base):
    """Bank account model for storing customer account information"""
    
    # Attributes
    id: int              # Primary key
    user_id: int         # Foreign key to User
    account_number: str  # Unique account number (20 chars)
    account_type: str    # Account type (checking, savings, credit)
    balance: float       # Current account balance
    currency: str        # Currency code (default: USD)
    is_active: bool      # Account active status
    created_at: datetime # Account creation date
    updated_at: datetime # Last update timestamp
    
    # Relationships
    user: User                    # Account owner
    transactions: List[Transaction] # Account transactions
```

#### Transaction Model
```python
class Transaction(Base):
    """Transaction model for storing banking transaction history"""
    
    # Attributes
    id: int              # Primary key
    account_id: int      # Foreign key to Account
    transaction_id: str  # Unique transaction identifier
    transaction_type: str # Type: debit or credit
    amount: float        # Transaction amount
    description: str     # Transaction description
    category: str        # Transaction category
    merchant: str        # Merchant name
    transaction_date: datetime # When transaction occurred
    created_at: datetime # Record creation timestamp
    
    # Relationships
    account: Account     # Associated account
```

#### CreditCard Model
```python
class CreditCard(Base):
    """Credit card model for storing customer credit card information"""
    
    # Attributes
    id: int              # Primary key
    user_id: int         # Foreign key to User
    card_number: str     # Masked card number
    card_type: str       # Card type (Premium, Gold, Student)
    credit_limit: float  # Maximum credit limit
    current_balance: float # Current outstanding balance
    available_credit: float # Available credit remaining
    minimum_payment: float # Minimum payment due
    due_date: datetime   # Payment due date
    is_active: bool      # Card active status
    created_at: datetime # Card creation date
    updated_at: datetime # Last update timestamp
```

#### ChatHistory Model
```python
class ChatHistory(Base):
    """Chat conversation history model"""
    
    # Attributes
    id: int              # Primary key
    user_id: int         # Foreign key to User
    chat_thread_id: str  # Thread identifier for conversation grouping
    user_query: str      # User's original question
    bot_response: str    # Agent's response
    query_type: str      # Classified query type
    tools_used: str      # JSON string of tools used
    response_time_ms: int # Response generation time
    created_at: datetime # Conversation timestamp
    
    # Relationships
    user: User           # User who sent the message
    feedbacks: List[Feedback] # Feedback on this response
```

#### Feedback Model
```python
class Feedback(Base):
    """User feedback model for response quality tracking"""
    
    # Attributes
    id: int              # Primary key
    user_id: int         # Foreign key to User
    chat_history_id: int # Foreign key to ChatHistory
    rating: int          # Rating: 1 (thumbs down) or 2 (thumbs up)
    comments: str        # Optional feedback comments
    created_at: datetime # Feedback submission timestamp
    
    # Relationships
    user: User           # User who provided feedback
    chat_message: ChatHistory # Associated chat message
```

#### BotLog Model
```python
class BotLog(Base):
    """System logging model for debugging and monitoring"""
    
    # Attributes
    id: int              # Primary key
    user_id: int         # Associated user (optional)
    chat_thread_id: str  # Associated conversation thread
    log_level: str       # Log level (INFO, WARNING, ERROR)
    message: str         # Log message
    error_details: str   # Detailed error information
    endpoint: str        # API endpoint that generated log
    ip_address: str      # Client IP address
    user_agent: str      # Client user agent
    created_at: datetime # Log timestamp
```

---

## API Models

### src/app/models/api_models.py
**Pydantic Models for API Request/Response Validation**

#### User Management Models
```python
class UserCreate(BaseModel):
    """Request model for user registration"""
    user_id: str         # Username (3-50 characters)
    password: str        # Password (minimum 6 characters)
    email: str           # Email address (optional)
    first_name: str      # First name (optional)
    last_name: str       # Last name (optional)

class UserLogin(BaseModel):
    """Request model for user authentication"""
    user_id: str         # Username
    password: str        # Password

class UserResponse(BaseModel):
    """Response model for user information"""
    id: int              # User database ID
    user_id: str         # Username
    email: str           # Email address
    first_name: str      # First name
    last_name: str       # Last name
    is_active: bool      # Account status
    created_at: datetime # Registration date
```

#### Chat Models
```python
class ChatMessage(BaseModel):
    """Request model for chat messages"""
    message: str         # User message (1-5000 characters)
    chat_thread_id: str  # Optional thread ID for conversation continuity

class ChatResponse(BaseModel):
    """Response model for agent responses"""
    response: str        # Agent's response text
    chat_thread_id: str  # Conversation thread identifier
    query_type: str      # Classified query type
    tools_used: List[str] # Tools used to generate response
    response_time_ms: int # Response generation time

class ChatHistoryResponse(BaseModel):
    """Response model for chat history retrieval"""
    id: int              # Chat record ID
    chat_thread_id: str  # Thread identifier
    user_query: str      # Original user question
    bot_response: str    # Agent response
    query_type: str      # Query classification
    tools_used: str      # Tools used (JSON string)
    response_time_ms: int # Response time
    created_at: datetime # Conversation timestamp
    feedback: FeedbackResponse # Associated feedback (optional)
```

#### Authentication Models
```python
class Token(BaseModel):
    """JWT token response model"""
    access_token: str    # JWT access token
    token_type: str      # Token type (bearer)
    expires_in: int      # Token expiration time in seconds

class TokenData(BaseModel):
    """Token payload data model"""
    user_id: str         # Authenticated user ID
```

---

## Agent Models

### src/app/models/agent_models.py
**Pydantic Models for Agent Structured Output**

#### Query Classification
```python
class QueryType(str, Enum):
    """Enumeration of banking query types"""
    ACCOUNT_BALANCE = "account_balance"      # Balance inquiries
    TRANSACTION_HISTORY = "transaction_history" # Transaction requests
    CREDIT_CARD_INFO = "credit_card_info"    # Credit card information
    GENERAL_BANKING = "general_banking"      # General banking questions
    POLICY_QUESTION = "policy_question"      # Policy and procedure questions
    FEE_STRUCTURE = "fee_structure"          # Fee and rate inquiries
    ACCOUNT_INFO = "account_info"            # Account details

class ToolUsed(str, Enum):
    """Tools available to the agent"""
    SQL_RETRIEVAL = "sql_retrieval_tool"     # Database queries
    DOCUMENT_RETRIEVAL = "document_retrieval_tool" # Vector search
    NONE = "none"                            # No tools used

class ConfidenceLevel(str, Enum):
    """Agent confidence in response accuracy"""
    HIGH = "high"        # High confidence (>90%)
    MEDIUM = "medium"    # Medium confidence (70-90%)
    LOW = "low"          # Low confidence (<70%)
```

#### Structured Response Model
```python
class BankingResponse(BaseModel):
    """Structured response from the banking agent (used with ToolStrategy)"""
    response: str                    # Main response text
    query_type: QueryType           # Classified query type
    tools_used: List[ToolUsed]      # Tools used for response
    confidence: ConfidenceLevel     # Response confidence level
    requires_authentication: bool   # Whether query needed auth data
    data_sources: List[str]         # Data sources used
    follow_up_suggestions: List[str] # Suggested follow-up questions
    warnings: List[str]             # Important notices or warnings
```

#### Context Models
```python
class AgentState(BaseModel):
    """Agent processing state during conversation"""
    user_id: str                    # Current user
    query: str                      # User's query
    query_type: QueryType           # Classified query type
    requires_customer_data: bool    # Whether personal data is needed
    tools_to_use: List[ToolUsed]    # Tools selected for execution
    context: Dict[str, Any]         # Additional context data

class ChatContext(BaseModel):
    """Chat conversation context for memory management"""
    user_id: str                    # User identifier
    chat_thread_id: str             # Conversation thread
    conversation_history: List[Dict] # Previous messages
    user_preferences: Dict[str, Any] # User preferences
    session_data: Dict[str, Any]    # Session-specific data
```

---

## Services

### src/app/services/chat_service.py
**Core Chat Service for Agent Interaction**

```python
class ChatService:
    """Service for handling chat interactions with the banking agent"""
    
    def __init__(self):
        """Initialize chat service with banking agent"""
        self.agent = get_banking_agent()
    
    async def process_message(self, message: ChatMessage, user: User, db: Session) -> ChatResponse:
        """
        Process a chat message and return structured response
        
        Args:
            message: User's chat message
            user: Authenticated user object
            db: Database session
            
        Returns:
            ChatResponse: Structured agent response with metadata
            
        Process:
        1. Generate or use existing chat_thread_id
        2. Create user context with profile information
        3. Send to banking agent for processing
        4. Extract structured response and metadata
        5. Save conversation to database
        6. Return formatted response
        """
    
    async def stream_message(self, message: ChatMessage, user: User, db: Session) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream chat response in real-time for live updates
        
        Args:
            message: User's chat message
            user: Authenticated user object
            db: Database session
            
        Yields:
            Dict: Streaming events including:
                - message_chunk: Partial response text
                - tool_call: Tool execution events
                - structured_response: Final structured data
                - completion: End of stream marker
                - error: Error events
        """
    
    def get_chat_history(self, user: User, chat_thread_id: str, limit: int, db: Session) -> List[ChatHistoryResponse]:
        """
        Retrieve chat history for a user and optional thread
        
        Args:
            user: User object
            chat_thread_id: Optional thread filter
            limit: Maximum number of messages (max 100)
            db: Database session
            
        Returns:
            List[ChatHistoryResponse]: Ordered chat history
        """
    
    def get_user_threads(self, user: User, db: Session) -> List[Dict[str, Any]]:
        """
        Get all chat threads for a user with summary information
        
        Returns:
            List containing thread metadata:
            - chat_thread_id: Thread identifier
            - last_message: Preview of last message
            - last_activity: Timestamp of last activity
            - message_count: Number of messages in thread
        """
```

---

## Tools

### src/app/tools/sql_retrieval_tool.py
**LangChain Tool for Database Queries**

```python
class SQLRetrievalTool(BaseTool):
    """LangChain tool for retrieving customer banking data from SQLite database"""
    
    name: str = "sql_retrieval_tool"
    description: str = """
    Retrieve customer banking information from the SQLite database.
    Use this tool for queries about:
    - Account balances and details
    - Recent transactions with filtering
    - Credit card information and utilization
    - Personal banking data
    """
    args_schema = SQLRetrievalInput
    
    def _run(self, query_type: str, user_id: str, account_number: str = None, 
             limit: int = 10, filters: Dict[str, Any] = None) -> str:
        """
        Execute SQL retrieval based on query type
        
        Args:
            query_type: Type of query ('balance', 'transactions', 'credit_card', 'account_info')
            user_id: User identifier for data filtering
            account_number: Optional specific account filter
            limit: Number of results to return
            filters: Additional filters (date range, amounts, categories)
            
        Returns:
            str: JSON-formatted results with requested data
            
        Query Types:
        - 'balance': Account balances and totals
        - 'transactions': Transaction history with filtering
        - 'credit_card': Credit card details and utilization
        - 'account_info': Comprehensive account information
        """
    
    def _get_account_balances(self, db: Session, user_id: int, account_number: str) -> Dict[str, Any]:
        """Retrieve account balance information for user"""
    
    def _get_transactions(self, db: Session, user_id: int, account_number: str, 
                         limit: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve transaction history with optional filtering"""
    
    def _get_credit_card_info(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Retrieve credit card information and utilization"""
    
    def _get_account_info(self, db: Session, user_id: int, account_number: str) -> Dict[str, Any]:
        """Retrieve comprehensive account information with recent transactions"""
```

### src/app/tools/doc_retrieval_tool.py
**LangChain Tool for Document Vector Search**

```python
class DocumentRetrievalTool(BaseTool):
    """LangChain tool for retrieving relevant documents from ChromaDB vector store"""
    
    name: str = "document_retrieval_tool"
    description: str = """
    Retrieve relevant bank policy and credit card benefit documents.
    Use this tool for queries about:
    - Bank policies and procedures
    - Credit card benefits and features
    - Fee structures and charges
    - General banking information
    - Terms and conditions
    """
    args_schema = DocumentRetrievalInput
    
    def _run(self, query: str, num_results: int = 5, document_type: str = None) -> str:
        """
        Execute document retrieval using vector similarity search
        
        Args:
            query: User's question or search query
            num_results: Number of relevant documents to retrieve (max 20)
            document_type: Optional filter by document type
            
        Returns:
            str: JSON-formatted results with relevant document chunks
            
        Process:
        1. Connect to ChromaDB collection
        2. Perform vector similarity search
        3. Filter by document type if specified
        4. Rank results by relevance score
        5. Return high-quality matches (>0.3 similarity)
        """
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check ChromaDB health and document availability
        
        Returns:
            Dict containing:
            - status: healthy/unhealthy
            - total_documents: Number of documents in collection
            - collection_name: ChromaDB collection name
            - can_query: Whether queries can be executed
        """
```

---

## Agents

### src/app/agents/banking_agent.py
**Main Banking Agent using LangGraph create_agent**

```python
class BankingAgent:
    """Banking chatbot agent using create_agent with structured output and streaming"""
    
    def __init__(self):
        """
        Initialize banking agent with:
        - OpenAI GPT-4o model with streaming
        - SQL and document retrieval tools
        - Memory management with MemorySaver
        - Structured output using ToolStrategy
        """
        self.model = self._init_model()      # ChatOpenAI instance
        self.tools = self._init_tools()      # List of LangChain tools
        self.memory = MemorySaver()          # LangGraph memory management
        self.agent = self._create_agent()    # create_agent instance
    
    def _create_agent(self):
        """
        Create the banking agent using LangGraph's create_agent
        
        Configuration:
        - Model: OpenAI GPT-4o with streaming enabled
        - Tools: SQL retrieval and document retrieval
        - System Prompt: Banking-specific instructions
        - Response Format: ToolStrategy with BankingResponse schema
        - Checkpointer: MemorySaver for conversation persistence
        
        Returns:
            LangGraph agent with structured output capabilities
        """
    
    async def chat(self, message: str, user_id: str, chat_thread_id: str, 
                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a chat message and return structured response
        
        Args:
            message: User's message
            user_id: User identifier
            chat_thread_id: Conversation thread ID
            context: Additional context (user profile, preferences)
            
        Returns:
            Dict containing:
            - response: Agent's text response
            - query_type: Classified query type
            - tools_used: List of tools used
            - confidence: Response confidence level
            - data_sources: Sources of information used
            - follow_up_suggestions: Suggested next questions
            - warnings: Important notices
            - metadata: Response time, thread ID, etc.
            
        Process:
        1. Create thread ID for memory: f"{chat_thread_id}_{user_id}"
        2. Prepare input with user message and context
        3. Invoke agent with structured output
        4. Extract and format structured response
        5. Add metadata (timing, thread info)
        6. Return comprehensive response dictionary
        """
    
    async def stream_chat(self, message: str, user_id: str, chat_thread_id: str,
                          context: Dict[str, Any] = None) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream chat response in real-time
        
        Yields different event types:
        - message_chunk: Partial response text for real-time display
        - tool_call: Tool execution events with names and arguments
        - structured_response: Final structured data when complete
        - error: Error events if processing fails
        
        Benefits:
        - Real-time user feedback
        - Progressive response building
        - Tool execution visibility
        - Better user experience for long responses
        """
    
    def get_conversation_history(self, user_id: str, chat_thread_id: str) -> List[Dict[str, Any]]:
        """Retrieve conversation history from memory checkpoints"""
    
    def clear_conversation_history(self, user_id: str, chat_thread_id: str) -> bool:
        """Clear conversation history for a specific thread"""

def get_banking_agent() -> BankingAgent:
    """Global singleton accessor for banking agent instance"""
```

---

## Utilities

### src/app/utils/auth_utils.py
**Authentication and Authorization Utilities**

```python
class AuthService:
    """Authentication service for user login and token management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against bcrypt hash"""
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate bcrypt hash for password"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Token payload data (typically {"sub": user_id})
            expires_delta: Optional custom expiration time
            
        Returns:
            str: Encoded JWT token
            
        Configuration:
        - Algorithm: HS256
        - Secret: From settings.SECRET_KEY
        - Default expiration: settings.access_token_expire_minutes
        """
    
    @staticmethod
    def verify_token(token: str) -> TokenData:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData: Decoded token data
            
        Raises:
            HTTPException: If token is invalid or expired
        """
    
    @staticmethod
    def authenticate_user(db: Session, user_id: str, password: str) -> Union[User, bool]:
        """
        Authenticate user with credentials
        
        Process:
        1. Find user by user_id
        2. Check if account is active
        3. Verify password hash
        4. Return User object or False
        """
    
    @staticmethod
    def get_current_user(credentials: HTTPAuthorizationCredentials, db: Session) -> User:
        """
        FastAPI dependency to get current authenticated user
        
        Process:
        1. Extract token from Authorization header
        2. Verify and decode token
        3. Lookup user in database
        4. Validate user is active
        5. Return User object
        
        Usage:
            @app.get("/protected")
            def protected_endpoint(user: User = Depends(AuthService.get_current_user)):
                return {"user_id": user.user_id}
        """
    
    @staticmethod
    def create_user(db: Session, user_id: str, password: str, 
                   email: str = None, first_name: str = None, 
                   last_name: str = None) -> User:
        """
        Create new user account
        
        Validation:
        - Unique user_id and email
        - Password hashing with bcrypt
        - Default active status
        
        Returns:
            User: Created user object
            
        Raises:
            HTTPException: If user_id or email already exists
        """
    
    @staticmethod
    def login(db: Session, user_id: str, password: str) -> Token:
        """
        User login with token generation
        
        Returns:
            Token: JWT token with expiration info
        """
```

### src/app/utils/logger_utils.py
**Structured Logging Utilities**

```python
def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    Setup structured logging configuration with JSON output
    
    Features:
    - Structured JSON logging
    - Console and file output
    - Timestamp and log level inclusion
    - Exception stack traces
    - Unicode support
    """

def get_logger(name: str):
    """Get a structured logger instance for a module"""
```

---

## Configuration

### src/app/config/service_config.py
**Application Configuration Management**

```python
class Settings(BaseSettings):
    """Pydantic settings model for configuration management"""
    
    # API Settings
    app_name: str = "Banking Bot API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database Configuration
    database_url: str = "sqlite:///./data/banking_bot.db"
    
    # OpenAI Configuration
    openai_api_key: str = ""                    # Required: OpenAI API key
    openai_model: str = "gpt-4o"               # GPT model to use
    openai_embedding_model: str = "text-embedding-3-large"
    openai_temperature: float = 0.1             # Model temperature
    max_tokens: int = 4000                      # Max response tokens
    
    # ChromaDB Configuration
    chromadb_path: str = "./data/chromadb"      # Vector database path
    chromadb_collection_name: str = "bank_documents"
    
    # Authentication Configuration
    secret_key: str = "change-in-production"    # JWT secret key
    algorithm: str = "HS256"                    # JWT algorithm
    access_token_expire_minutes: int = 30       # Token expiration
    
    # CORS Configuration
    allowed_origins: list = [                   # Frontend origins
        "http://localhost:3000",
        "http://localhost:2024",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:2024"
    ]
    
    class Config:
        env_file = ".env"                       # Environment file
        case_sensitive = False                  # Case-insensitive env vars
```

---

## API Endpoints

### Authentication Endpoints (/auth)

#### POST /auth/register
Register a new user account
- **Request Body**: `UserCreate`
- **Response**: `UserResponse`
- **Validation**: Unique user_id and email

#### POST /auth/login  
Authenticate user and return JWT token
- **Request Body**: `UserLogin`
- **Response**: `Token`

#### GET /auth/me
Get current authenticated user information
- **Authorization**: Bearer token required
- **Response**: `UserResponse`

### Chat Endpoints (/chat)

#### POST /chat/message
Send message to banking agent
- **Authorization**: Bearer token required
- **Request Body**: `ChatMessage`
- **Response**: `ChatResponse`
- **Process**: Query classification → Tool selection → Structured response

#### POST /chat/stream
Stream response from banking agent
- **Authorization**: Bearer token required
- **Request Body**: `ChatMessage`
- **Response**: Server-Sent Events with streaming data

#### GET /chat/history
Retrieve chat history
- **Authorization**: Bearer token required
- **Query Parameters**: 
  - `chat_thread_id` (optional): Filter by thread
  - `limit` (optional): Maximum results (default: 50, max: 100)
- **Response**: `List[ChatHistoryResponse]`

#### GET /chat/threads
Get all chat threads for user
- **Authorization**: Bearer token required
- **Response**: Thread summary with last activity

### Feedback Endpoints (/feedback)

#### POST /feedback/
Submit feedback for a chat response
- **Authorization**: Bearer token required
- **Request Body**: `FeedbackCreate`
- **Response**: `FeedbackResponse`
- **Validation**: User owns the referenced chat message

#### GET /feedback/chat/{chat_history_id}
Get feedback for specific chat message
- **Authorization**: Bearer token required
- **Response**: `FeedbackResponse`

### Health Endpoints (/health)

#### GET /health/
Overall system health check
- **Response**: `HealthResponse` with database and ChromaDB status

#### GET /health/database
Detailed database health and statistics

#### GET /health/chromadb
Detailed ChromaDB health and document counts

---

## Ingestion App

### src/ingestion_app/create_sample_data.py
**Database and ChromaDB initialization script**

```python
def create_sample_data():
    """Create sample banking data for testing including SQLite and ChromaDB setup"""
```

**Key Functions:**
- Creates SQLite database with sample users, accounts, transactions, credit cards
- Uses ingestion service to create ChromaDB with document embeddings
- Loads environment variables from project root
- Handles OpenAI API quota gracefully

**Usage:**
```bash
python src/ingestion_app/create_sample_data.py
```

### src/ingestion_app/services/document_ingestion.py
**Document processing and ChromaDB management service**

```python
class DocumentIngestionService:
    """Service for ingesting, chunking, and embedding documents into ChromaDB"""
```

**Key Methods:**
- `load_document()` - Load PDF, DOCX, or TXT files
- `chunk_documents()` - Split documents into overlapping chunks
- `embed_and_store()` - Generate embeddings and store in ChromaDB
- `ingest_document()` - Complete ingestion pipeline
- `list_documents()` - List all documents in collection
- `delete_document()` - Remove document and all chunks

## Document Ingestion API

### Document Endpoints (/documents)

#### POST /documents/upload
Upload and ingest single document
- **Request**: Multipart form with file and document_type
- **Supported**: PDF, DOCX, TXT files
- **Process**: Upload → Text extraction → Chunking → Embedding → ChromaDB storage

#### POST /documents/upload-multiple
Upload and ingest multiple documents
- **Request**: Multiple files with document_type

#### POST /documents/ingest-directory
Ingest all documents from directory path
- **Request**: Directory path and document_type

#### GET /documents/list
List all documents in vector database
- **Response**: Document metadata and chunk counts

#### DELETE /documents/document/{file_name}
Delete document and all chunks from vector database

---

## Updated File Organization Summary

### Current Structure
```
BankingBot/
├── src/
│   ├── utils/
│   │   └── path_setup.py           # Project path utilities
│   ├── app/                        # Main banking bot application (port 2024)
│   │   ├── main.py                # FastAPI server
│   │   ├── agents/                # Banking agent with LangGraph
│   │   ├── tools/                 # SQL and document retrieval tools
│   │   ├── services/              # Chat and business logic
│   │   ├── api/endpoints/         # REST API routes
│   │   ├── models/                # Data models (DB, API, Agent)
│   │   ├── config/                # Configuration management
│   │   ├── database/              # Database connection and setup
│   │   └── utils/                 # Authentication and logging
│   └── ingestion_app/             # Data creation and document processing
│       ├── create_sample_data.py  # Database and ChromaDB initialization
│       ├── ingestion_main.py      # Document ingestion API server
│       ├── services/              # Document processing services
│       └── api/endpoints/         # Document management endpoints
├── data/
│   ├── banking_bot.db            # SQLite database
│   ├── chromadb/                 # ChromaDB vector database
│   └── sample_documents/         # Source documents for ingestion
├── .env                          # Environment configuration
├── requirements.txt              # Python dependencies
├── DOCUMENTATION.md              # This comprehensive documentation
├── STEP_BY_STEP_GUIDE.md         # Integration setup guide
└── README.md                     # Project overview and quick start
```

### Key Improvements Made

1. **Consistent Import Paths**: All modules use absolute imports from project root
2. **Clear Separation**: Data/ingestion functionality moved to `ingestion_app`
3. **Port Configuration**: Main API runs on port 2024 for Agent Chat UI compatibility
4. **Centralized Configuration**: Environment variables loaded from project root
5. **Modular Architecture**: Each app has its own services, endpoints, and utilities

This documentation provides comprehensive coverage of all modules, classes, methods, and their purposes in the Banking Bot system. Each component is designed for scalability, maintainability, and clear separation of concerns.
