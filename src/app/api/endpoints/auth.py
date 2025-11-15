from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database.database import get_db
from ...models.api_models import UserCreate, UserLogin, UserResponse, Token
from ...utils.auth_utils import AuthService
from ...models.database_models import User
from ...utils.logger_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        user = AuthService.create_user(
            db=db,
            user_id=user_data.user_id,
            password=user_data.password,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        return UserResponse(
            id=user.id,
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            created_at=user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return JWT token"""
    try:
        token = AuthService.login(
            db=db,
            user_id=user_credentials.user_id,
            password=user_credentials.password
        )
        return token
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        user_id=current_user.user_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Refresh access token for authenticated user"""
    try:
        # Create new token with extended expiration
        from datetime import timedelta
        access_token_expires = timedelta(minutes=300)  # 5 hours
        access_token = AuthService.create_access_token(
            data={"sub": current_user.user_id}, 
            expires_delta=access_token_expires
        )
        
        logger.info(f"Token refreshed for user: {current_user.user_id}")
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=300 * 60  # 5 hours in seconds
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )

@router.post("/logout")
async def logout_user():
    """Logout user (client-side token removal)"""
    return {"message": "Successfully logged out. Please remove the token from client storage."}
