from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from ...database.database import get_db
from ...models.api_models import ChatMessage, ChatResponse, ChatHistoryResponse
from ...services.chat_service import chat_service
from ...utils.auth_utils import AuthService
from ...models.database_models import User
from ...utils.logger_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])



@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to the banking agent and get a response"""
    try:
        response = await chat_service.process_message(message, current_user, db)
        return response
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@router.post("/stream")
async def stream_message(
    message: ChatMessage,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Stream a response from the banking agent in real-time using LangGraph's native streaming"""
    try:
        async def generate_stream():
            """Generator function for streaming response"""
            try:
                async for chunk in chat_service.stream_message(message, current_user, db):
                    # Convert chunk to JSON and add newline for SSE format
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                logger.error(f"Error in stream generator: {str(e)}")
                error_chunk = {
                    "type": "error",
                    "message": f"Streaming error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except Exception as e:
        logger.error(f"Error streaming message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream message: {str(e)}"
        )

@router.get("/history", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    chat_thread_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat history for the current user"""
    try:
        if limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit cannot exceed 100"
            )
        
        history = chat_service.get_chat_history(current_user, chat_thread_id, limit, db)
        return history
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )

@router.get("/threads")
async def get_user_threads(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat threads for the current user"""
    try:
        threads = chat_service.get_user_threads(current_user, db)
        return {"threads": threads}
    except Exception as e:
        logger.error(f"Error retrieving user threads: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user threads: {str(e)}"
        )

@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific chat thread for the current user"""
    try:
        success = chat_service.delete_thread(current_user, thread_id, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found or not owned by user"
            )
        return {"message": "Thread deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting thread: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete thread: {str(e)}"
        )

@router.delete("/threads")
async def delete_all_threads(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete all chat threads for the current user"""
    try:
        count = chat_service.delete_all_threads(current_user, db)
        return {"message": f"Deleted {count} threads successfully", "deleted_count": count}
    except Exception as e:
        logger.error(f"Error deleting all threads: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete all threads: {str(e)}"
        )

