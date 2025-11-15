from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..config.service_config import settings
from ..database.database import get_db
from ..models.database_models import User
from ..models.api_models import Token, TokenData
from ..utils.logger_utils import get_logger

logger = get_logger(__name__)

# Password hashing using SHA256
import hashlib

# Bearer token scheme
security = HTTPBearer()

class AuthService:
    """Authentication service for user login and token management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password"""
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> TokenData:
        """Verify and decode a JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            token_data = TokenData(user_id=user_id)
        except JWTError:
            raise credentials_exception
        
        return token_data
    
    @staticmethod
    def authenticate_user(db: Session, user_id: str, password: str) -> Union[User, bool]:
        """Authenticate a user with user_id and password"""
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                logger.warning(f"Authentication failed: User not found - {user_id}")
                return False
            
            if not user.is_active:
                logger.warning(f"Authentication failed: Inactive user - {user_id}")
                return False
            
            if not AuthService.verify_password(password, user.password_hash):
                logger.warning(f"Authentication failed: Invalid password - {user_id}")
                return False
            
            logger.info(f"User authenticated successfully - {user_id}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    @staticmethod
    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> User:
        """Get the current authenticated user from token"""
        token = credentials.credentials
        token_data = AuthService.verify_token(token)
        
        user = db.query(User).filter(User.user_id == token_data.user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    @staticmethod
    def get_optional_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
    ) -> Optional[User]:
        """Get the current user if authenticated, otherwise None"""
        if not credentials:
            return None
        
        try:
            return AuthService.get_current_user(credentials, db)
        except HTTPException:
            return None
    
    @staticmethod
    def create_user(db: Session, user_id: str, password: str, email: Optional[str] = None,
                   first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.user_id == user_id).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User ID already registered"
                )
            
            # Check email if provided
            if email:
                existing_email = db.query(User).filter(User.email == email).first()
                if existing_email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
            
            # Create new user
            hashed_password = AuthService.get_password_hash(password)
            db_user = User(
                user_id=user_id,
                password_hash=hashed_password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"New user created successfully - {user_id}")
            return db_user
            
        except Exception as e:
            db.rollback()
            logger.error(f"User creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
    
    @staticmethod
    def login(db: Session, user_id: str, password: str) -> Token:
        """Login user and return JWT token"""
        user = AuthService.authenticate_user(db, user_id, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect user ID or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = AuthService.create_access_token(
            data={"sub": user.user_id}, expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60  # Convert to seconds
        )

# Global auth service instance
auth_service = AuthService()
