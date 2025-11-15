from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...database.database import get_db
from ...models.api_models import FeedbackCreate, FeedbackResponse
from ...models.database_models import User, Feedback, ChatHistory
from ...utils.auth_utils import AuthService
from ...utils.logger_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for a chat response"""
    try:
        # Verify that the chat history belongs to the current user
        chat_history = db.query(ChatHistory).filter(
            ChatHistory.id == feedback_data.chat_history_id,
            ChatHistory.user_id == current_user.id
        ).first()
        
        if not chat_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat history not found or doesn't belong to current user"
            )
        
        # Check if feedback already exists
        existing_feedback = db.query(Feedback).filter(
            Feedback.chat_history_id == feedback_data.chat_history_id,
            Feedback.user_id == current_user.id
        ).first()
        
        if existing_feedback:
            # Update existing feedback
            existing_feedback.rating = feedback_data.rating
            existing_feedback.comments = feedback_data.comments
            db.commit()
            db.refresh(existing_feedback)
            
            logger.info(f"Feedback updated for chat {feedback_data.chat_history_id} by user {current_user.user_id}")
            return FeedbackResponse(
                id=existing_feedback.id,
                rating=existing_feedback.rating,
                comments=existing_feedback.comments,
                created_at=existing_feedback.created_at
            )
        else:
            # Create new feedback
            feedback = Feedback(
                user_id=current_user.id,
                chat_history_id=feedback_data.chat_history_id,
                rating=feedback_data.rating,
                comments=feedback_data.comments
            )
            
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            
            logger.info(f"New feedback submitted for chat {feedback_data.chat_history_id} by user {current_user.user_id}")
            return FeedbackResponse(
                id=feedback.id,
                rating=feedback.rating,
                comments=feedback.comments,
                created_at=feedback.created_at
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("/chat/{chat_history_id}", response_model=FeedbackResponse)
async def get_feedback(
    chat_history_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get feedback for a specific chat response"""
    try:
        # Verify that the chat history belongs to the current user
        chat_history = db.query(ChatHistory).filter(
            ChatHistory.id == chat_history_id,
            ChatHistory.user_id == current_user.id
        ).first()
        
        if not chat_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat history not found or doesn't belong to current user"
            )
        
        # Get feedback
        feedback = db.query(Feedback).filter(
            Feedback.chat_history_id == chat_history_id,
            Feedback.user_id == current_user.id
        ).first()
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No feedback found for this chat"
            )
        
        return FeedbackResponse(
            id=feedback.id,
            rating=feedback.rating,
            comments=feedback.comments,
            created_at=feedback.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback: {str(e)}"
        )
