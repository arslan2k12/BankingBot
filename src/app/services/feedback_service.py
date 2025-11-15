from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.database_models import ChatHistory, User, Feedback
from ..models.api_models import FeedbackCreate, FeedbackResponse
from ..utils.logger_utils import get_logger

logger = get_logger(__name__)

class FeedbackService:
    """Service for handling user feedback on chat responses"""
    
    async def submit_feedback(
        self, 
        feedback: FeedbackCreate, 
        user: User, 
        db: Session
    ) -> Optional[FeedbackResponse]:
        """Submit feedback for a chat response"""
        try:
            # Verify the chat history belongs to the user
            chat_history = db.query(ChatHistory).filter(
                ChatHistory.id == feedback.chat_history_id,
                ChatHistory.user_id == user.id
            ).first()
            
            if not chat_history:
                logger.warning(f"Chat history {feedback.chat_history_id} not found for user {user.user_id}")
                return None
            
            # Check if feedback already exists for this chat
            existing_feedback = db.query(Feedback).filter(
                Feedback.chat_history_id == feedback.chat_history_id
            ).first()
            
            if existing_feedback:
                # Update existing feedback
                existing_feedback.rating = feedback.rating
                existing_feedback.comments = feedback.comments
                existing_feedback.updated_at = datetime.now()
                db.commit()
                db.refresh(existing_feedback)
                
                logger.info(f"Updated feedback for chat {feedback.chat_history_id} by user {user.user_id}")
                
                return FeedbackResponse(
                    id=existing_feedback.id,
                    rating=existing_feedback.rating,
                    comments=existing_feedback.comments,
                    created_at=existing_feedback.created_at
                )
            else:
                # Create new feedback
                new_feedback = Feedback(
                    chat_history_id=feedback.chat_history_id,
                    rating=feedback.rating,
                    comments=feedback.comments
                )
                
                db.add(new_feedback)
                db.commit()
                db.refresh(new_feedback)
                
                logger.info(f"Created new feedback for chat {feedback.chat_history_id} by user {user.user_id}")
                
                return FeedbackResponse(
                    id=new_feedback.id,
                    rating=new_feedback.rating,
                    comments=new_feedback.comments,
                    created_at=new_feedback.created_at
                )
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            db.rollback()
            return None
    
    def get_feedback_stats(self, user: User, db: Session) -> dict:
        """Get feedback statistics for a user"""
        try:
            # Get all feedback for user's chats
            feedback_query = db.query(Feedback).join(ChatHistory).filter(
                ChatHistory.user_id == user.id
            )
            
            total_feedback = feedback_query.count()
            thumbs_up = feedback_query.filter(Feedback.rating == 2).count()
            thumbs_down = feedback_query.filter(Feedback.rating == 1).count()
            
            stats = {
                "total_feedback": total_feedback,
                "thumbs_up": thumbs_up,
                "thumbs_down": thumbs_down,
                "satisfaction_rate": (thumbs_up / total_feedback * 100) if total_feedback > 0 else 0
            }
            
            logger.info(f"Retrieved feedback stats for user {user.user_id}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting feedback stats: {str(e)}")
            return {
                "total_feedback": 0,
                "thumbs_up": 0,
                "thumbs_down": 0,
                "satisfaction_rate": 0
            }
    
    def get_recent_feedback(
        self, 
        user: User, 
        limit: int = 10, 
        db: Session = None
    ) -> List[dict]:
        """Get recent feedback with chat context"""
        try:
            # Get recent feedback with chat history
            feedback_with_chat = db.query(Feedback, ChatHistory).join(
                ChatHistory, Feedback.chat_history_id == ChatHistory.id
            ).filter(
                ChatHistory.user_id == user.id
            ).order_by(Feedback.created_at.desc()).limit(limit).all()
            
            result = []
            for feedback, chat in feedback_with_chat:
                result.append({
                    "feedback_id": feedback.id,
                    "rating": feedback.rating,
                    "comments": feedback.comments,
                    "created_at": feedback.created_at,
                    "chat_thread_id": chat.chat_thread_id,
                    "user_query": chat.user_query[:100] + "..." if len(chat.user_query) > 100 else chat.user_query,
                    "bot_response": chat.bot_response[:100] + "..." if len(chat.bot_response) > 100 else chat.bot_response
                })
            
            logger.info(f"Retrieved {len(result)} recent feedback items for user {user.user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting recent feedback: {str(e)}")
            return []

# Global feedback service instance
feedback_service = FeedbackService()
