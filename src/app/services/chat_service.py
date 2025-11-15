from typing import List, Dict, Any, Optional, AsyncIterator
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import uuid
import json

from ..agents.banking_agent import get_banking_agent
from ..workflows.banking_workflow import get_banking_workflow
from ..models.database_models import ChatHistory, User, BotLog
from ..models.api_models import ChatMessage, ChatResponse, ChatHistoryResponse, EvaluationScore
from ..utils.logger_utils import get_logger

logger = get_logger(__name__)

class ChatService:
    """Service for handling chat interactions with the banking agent"""
    
    def __init__(self):
        # Note: We now create agents per-user for better security and state management
        pass
    
    async def process_message(
        self, 
        message: ChatMessage, 
        user: User, 
        db: Session
    ) -> ChatResponse:
        """Process a chat message and return response with evaluation"""
        try:
            # Generate chat_thread_id if not provided
            chat_thread_id = message.chat_thread_id or str(uuid.uuid4())
            
            # Log the incoming message
            await self._log_bot_interaction(
                db, user.id, chat_thread_id, "INFO", 
                f"Processing message with evaluation: {message.message[:100]}..."
            )
            
            # Use the banking workflow with evaluation
            workflow = SimpleBankingAgentWithJudge(user.user_id)
            start_time = datetime.now()
            
            # Get response with evaluation
            result = await workflow.process_message(
                message=message.message,
                thread_id=chat_thread_id,
                user_id=user.user_id
            )
            
            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Extract data from result
            bot_response = result.get("response", "I apologize, but I couldn't process your request.")
            tools_used = result.get("tools_used", [])
            query_type = "banking_query"
            evaluation_data = result.get("evaluation")
            
            # Create evaluation score object if available
            evaluation_score = None
            if evaluation_data:
                evaluation_score = EvaluationScore(
                    accuracy=evaluation_data.get("accuracy", 3),
                    completeness=evaluation_data.get("completeness", 3),
                    context_adherence=evaluation_data.get("context_adherence", 3),  
                    professional_quality=evaluation_data.get("professional_quality", 3),
                    overall_score=evaluation_data.get("overall_score", 3.0),
                    reasoning=evaluation_data.get("reasoning", "Evaluation completed"),
                    confidence_level=evaluation_data.get("confidence_level", "MEDIUM")
                )
            
            # Save to database
            chat_history = ChatHistory(
                user_id=user.id,
                chat_thread_id=chat_thread_id,
                user_query=message.message,
                bot_response=bot_response,
                query_type=query_type,
                tools_used=json.dumps(tools_used),
                response_time_ms=response_time_ms
            )
            
            db.add(chat_history)
            db.commit()
            db.refresh(chat_history)
            
            # Log successful interaction with evaluation
            await self._log_bot_interaction(
                db, user.id, chat_thread_id, "INFO", 
                f"Response with evaluation generated successfully in {response_time_ms}ms. Score: {evaluation_data.get('overall_score', 'N/A') if evaluation_data else 'N/A'}"
            )
            
            return ChatResponse(
                response=bot_response,
                chat_thread_id=chat_thread_id,
                query_type=query_type,
                tools_used=tools_used,
                response_time_ms=response_time_ms,
                evaluation=evaluation_score
            )
            
        except Exception as e:
            logger.error(f"Chat processing error: {str(e)}")
            
            # Log the error
            await self._log_bot_interaction(
                db, user.id, chat_thread_id, "ERROR", 
                f"Chat processing with evaluation failed: {str(e)}"
            )
            
            # Return error response
            return ChatResponse(
                response="I apologize, but I encountered an error while processing your request. Please try again later.",
                chat_thread_id=chat_thread_id or str(uuid.uuid4()),
                query_type="general_banking",
                tools_used=[],
                response_time_ms=0,
                evaluation=None
            )
    
    async def stream_message(
        self,
        message: ChatMessage,
        user: User,
        db: Session
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream chat response in real-time with evaluation using banking workflow"""
        chat_thread_id = message.chat_thread_id or str(uuid.uuid4())
        
        try:
            # Log the streaming request
            await self._log_bot_interaction(
                db, user.id, chat_thread_id, "INFO", 
                f"Starting streaming response with evaluation for: {message.message[:100]}..."
            )
            
            # Use the new banking workflow with evaluation
            workflow = get_banking_workflow()
            
            # Stream response using the workflow - evaluation runs AFTER streaming
            full_response = ""
            tools_used = []
            query_type = "banking_query"
            evaluation_data = None
            
            async for chunk in workflow.stream_with_evaluation(
                message.message,
                chat_thread_id,
                user.user_id
            ):
                # Yield the chunk to the client IMMEDIATELY
                yield chunk
                
                # Collect data for database storage based on chunk type
                chunk_type = chunk.get("type", "")
                
                if chunk_type == "reasoning_token":
                    # Accumulate LLM response tokens
                    full_response += chunk.get("content", "")
                
                elif chunk_type == "react_step":
                    phase = chunk.get("phase", "")
                    if phase == "ACTION":
                        # Track tool usage
                        details = chunk.get("details", {})
                        tool_name = details.get("tool_name")
                        if tool_name and tool_name not in tools_used:
                            tools_used.append(tool_name)
                    
                    elif phase == "FINAL_ANSWER":
                        # Extract final answer
                        details = chunk.get("details", {})
                        final_answer = details.get("final_answer", "")
                        if final_answer:
                            full_response = final_answer
                
                elif chunk_type == "evaluation_complete":
                    # Capture evaluation data - this arrives AFTER streaming is done
                    evaluation_data = chunk.get("evaluation", {})
            
            # Save the complete conversation to database
            if full_response:
                chat_history = ChatHistory(
                    user_id=user.id,
                    chat_thread_id=chat_thread_id,
                    user_query=message.message,
                    bot_response=full_response,
                    query_type=query_type,
                    tools_used=json.dumps(tools_used),
                    response_time_ms=0  # Not applicable for streaming
                )
                
                db.add(chat_history)
                db.commit()
                
                # Log successful interaction with evaluation
                evaluation_score = evaluation_data.get("overall_score", "N/A") if evaluation_data else "N/A"
                await self._log_bot_interaction(
                    db, user.id, chat_thread_id, "INFO", 
                    f"Streaming completed successfully with {len(tools_used)} tools used. Evaluation score: {evaluation_score}"
                )
            
            # Send completion event with evaluation summary ONLY if we have evaluation data
            # (The banking agent already sends its own completion event)
            if evaluation_data:
                completion_event = {
                    "type": "completion",
                    "chat_thread_id": chat_thread_id,
                    "tools_used": tools_used,
                    "response_length": len(full_response),
                    "timestamp": datetime.now().isoformat(),
                    "evaluation_summary": {
                        "overall_score": evaluation_data.get("overall_score"),
                        "confidence_level": evaluation_data.get("confidence_level"),
                        "summary": evaluation_data.get("summary"),
                        "criteria_scores": evaluation_data.get("criteria_scores", []),
                        "strengths": evaluation_data.get("strengths", []),
                        "weaknesses": evaluation_data.get("weaknesses", [])
                    }
                }
                yield completion_event
            
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            
            # Log the error
            await self._log_bot_interaction(
                db, user.id, chat_thread_id, "ERROR", 
                f"Streaming with evaluation failed: {str(e)}"
            )
            
            # Send error event
            yield {
                "type": "error",
                "message": f"Streaming error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_chat_history(
        self, 
        user: User, 
        chat_thread_id: Optional[str], 
        limit: int,
        db: Session
    ) -> List[ChatHistoryResponse]:
        """Get chat history for a user"""
        try:
            query = db.query(ChatHistory).filter(ChatHistory.user_id == user.id)
            
            if chat_thread_id:
                query = query.filter(ChatHistory.chat_thread_id == chat_thread_id)
            
            chat_histories = query.order_by(desc(ChatHistory.created_at)).limit(limit).all()
            
            # Convert to response format
            response_list = []
            for chat in chat_histories:
                response_list.append(ChatHistoryResponse(
                    id=chat.id,
                    chat_thread_id=chat.chat_thread_id,
                    user_query=chat.user_query,
                    bot_response=chat.bot_response,
                    query_type=chat.query_type,
                    tools_used=chat.tools_used,
                    response_time_ms=chat.response_time_ms,
                    created_at=chat.created_at
                ))
            
            logger.info(f"Retrieved {len(response_list)} chat history items for user {user.user_id}")
            return response_list
            
        except Exception as e:
            logger.error(f"Error retrieving chat history: {str(e)}")
            return []
    
    def get_user_threads(self, user: User, db: Session) -> List[Dict[str, Any]]:
        """Get all chat threads for a user"""
        try:
            # Get distinct thread IDs with latest message info
            query = db.query(
                ChatHistory.chat_thread_id,
                ChatHistory.created_at,
                ChatHistory.user_query
            ).filter(
                ChatHistory.user_id == user.id
            ).order_by(desc(ChatHistory.created_at))
            
            threads = {}
            for chat_thread_id, created_at, user_query in query:
                if chat_thread_id not in threads:
                    threads[chat_thread_id] = {
                        "chat_thread_id": chat_thread_id,
                        "last_message": user_query[:100] + "..." if len(user_query) > 100 else user_query,
                        "last_activity": created_at,
                        "message_count": 0
                    }
                threads[chat_thread_id]["message_count"] += 1
            
            # Convert to list and sort by last activity
            thread_list = list(threads.values())
            thread_list.sort(key=lambda x: x["last_activity"], reverse=True)
            
            logger.info(f"Retrieved {len(thread_list)} threads for user {user.user_id}")
            return thread_list
            
        except Exception as e:
            logger.error(f"Error retrieving user threads: {str(e)}")
            return []

    def delete_thread(self, user: User, thread_id: str, db: Session) -> bool:
        """Delete a specific chat thread for a user"""
        try:
            # Delete all chat history entries for this thread and user
            deleted_count = db.query(ChatHistory).filter(
                ChatHistory.user_id == user.id,
                ChatHistory.chat_thread_id == thread_id
            ).delete()
            
            # Delete related bot logs
            db.query(BotLog).filter(
                BotLog.user_id == user.id,
                BotLog.chat_thread_id == thread_id
            ).delete()
            
            db.commit()
            
            logger.info(f"Deleted thread {thread_id} for user {user.user_id}, removed {deleted_count} entries")
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting thread {thread_id}: {str(e)}")
            db.rollback()
            return False

    def delete_all_threads(self, user: User, db: Session) -> int:
        """Delete all chat threads for a user"""
        try:
            # Delete all chat history entries for this user
            deleted_count = db.query(ChatHistory).filter(
                ChatHistory.user_id == user.id
            ).delete()
            
            # Delete related bot logs
            db.query(BotLog).filter(
                BotLog.user_id == user.id
            ).delete()
            
            db.commit()
            
            logger.info(f"Deleted all threads for user {user.user_id}, removed {deleted_count} entries")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting all threads for user {user.user_id}: {str(e)}")
            db.rollback()
            return 0

    async def _log_bot_interaction(
        self, 
        db: Session, 
        user_id: int, 
        chat_thread_id: str, 
        log_level: str, 
        message: str
    ):
        """Log bot interaction to database"""
        try:
            bot_log = BotLog(
                user_id=user_id,
                chat_thread_id=chat_thread_id,
                log_level=log_level,
                message=message
            )
            
            db.add(bot_log)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log bot interaction: {str(e)}")

# Global chat service instance
chat_service = ChatService()
