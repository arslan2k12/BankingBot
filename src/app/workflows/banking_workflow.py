"""
Banking Workflow with LLM-as-a-Judge Evaluation
Ensures evaluation runs AFTER response is streamed to user
"""
from typing import Dict, Any, List, Optional, AsyncIterator
import json
import logging
import asyncio

from ..agents.banking_agent import get_banking_agent
from ..evaluation.llm_judge import get_banking_judge
from ..models.api_models import ChatMessage
from ..utils.logger_utils import get_logger

logger = get_logger(__name__)


class BankingWorkflow:
    """
    Simple banking workflow that streams response first, then evaluates
    User gets immediate response, evaluation happens after streaming completes
    """
    
    def __init__(self):
        self.banking_agent = get_banking_agent("system")
        self.judge = get_banking_judge()
    
    async def stream_with_evaluation(
        self, 
        message: str,
        chat_thread_id: str,
        user_id: str = "system"
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream response immediately using original ReAct format, then run evaluation after streaming completes
        """
        logger.info(f"🚀 Starting banking workflow for user {user_id}")
        
        response_content = ""
        context_data = []
        
        try:
            # Phase 1: Stream banking agent response with ORIGINAL ReAct format
            logger.info("📨 Streaming banking agent response...")
            async for chunk in self.banking_agent.stream_response(
                message, 
                chat_thread_id, 
                user_id
            ):
                # Collect response content and context for evaluation
                if chunk.get("type") == "react_step" and chunk.get("phase") == "FINAL_ANSWER":
                    response_content = chunk.get("details", {}).get("final_answer", "")
                
                elif chunk.get("type") == "react_step" and chunk.get("phase") == "OBSERVATION":
                    # Collect context from tool executions
                    context_data.append({
                        "tool_name": chunk.get("details", {}).get("tool_name", "unknown"),
                        "tool_output": chunk.get("content", "")
                    })
                
                # Forward the ORIGINAL chunk format (preserve all ReAct steps)
                yield chunk
            
            logger.info("✅ Banking agent streaming complete")
            
            # Phase 2: Run evaluation after streaming completes
            if response_content:
                logger.info("🔍 Running LLM-as-a-Judge evaluation...")
                evaluation_result = await self.judge.evaluate_response(
                    user_query=message,
                    assistant_response=response_content,
                    context_data=context_data  # Full context, no summarization
                )
                
                # Convert Pydantic model to dict for JSON serialization
                evaluation_dict = evaluation_result.dict() if evaluation_result else None
                
                # Send evaluation results
                yield {
                    "type": "evaluation_complete",
                    "evaluation": evaluation_dict
                }
                
                logger.info(f"✅ Evaluation complete - Score: {evaluation_result.overall_score}/5")
            else:
                logger.warning("⚠️ No response content to evaluate")
            
        except Exception as e:
            logger.error(f"❌ Banking workflow error: {str(e)}")
            yield {
                "type": "error",
                "content": f"Workflow error: {str(e)}"
            }


# Global workflow instance
_workflow_instance = None

def get_banking_workflow() -> BankingWorkflow:
    """Get the shared banking workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = BankingWorkflow()
    return _workflow_instance
