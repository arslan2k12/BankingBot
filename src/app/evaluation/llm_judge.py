"""
LLM-as-a-Judge for evaluating banking assistant responses
Uses structured output for consistent evaluation format
"""
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List
import json
import logging

from src.app.config.service_config import settings
from src.app.utils.logger_utils import get_logger
from src.app.evaluation.evaluation_models import ResponseEvaluation

logger = get_logger(__name__)


class BankingResponseJudge:
    """LLM Judge for evaluating banking assistant responses with structured output"""
    
    def __init__(self):
        # Initialize LLM with structured output capability
        self.llm = init_chat_model(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.1,  # Low temperature for consistent evaluation
            streaming=False   # No streaming for evaluation
        ).with_structured_output(ResponseEvaluation)
        
    def get_evaluation_prompt(self) -> str:
        """Get the system prompt for banking response evaluation"""
        return """You are an expert evaluator for banking assistant responses. 

Your task is to evaluate the quality, accuracy, and completeness of banking assistant responses based on the provided context and user query.

## EVALUATION CRITERIA (Score 1-5 each):

1. **Accuracy**: Information provided is factually correct based on the context (if any)
2. **Completeness**: Response fully addresses all parts of the user's question  
3. **Context Usage**: Effectively uses any provided context (retrieved data, documents)
4. **Clarity**: Response is clear, well-organized, and easy to understand
5. **Security**: Maintains appropriate security practices and data handling

## SCORING SCALE:
- **5**: Excellent - Exceeds expectations
- **4**: Good - Meets expectations well
- **3**: Satisfactory - Meets basic expectations  
- **2**: Poor - Below expectations with significant issues
- **1**: Very Poor - Major problems, largely unhelpful

## CONFIDENCE LEVELS:
- **High**: Score 4-5, comprehensive and accurate
- **Medium**: Score 3, adequate but could be improved
- **Low**: Score 1-2, significant issues present

Evaluate the response objectively based solely on the provided context and data. Be generous in scoring.
For greetings or simple acknowledgments, or clarifications, provide highest scores.
"""

    async def evaluate_response(
        self, 
        user_query: str, 
        assistant_response: str, 
        context_data: List[Dict[str, Any]]
    ) -> ResponseEvaluation:
        """
        Evaluate banking assistant response using structured output
        
        Args:
            user_query: The original user question
            assistant_response: The banking assistant's response
            context_data: Full context data used by assistant (no summarization)
        """
        try:
            logger.info(f"🧠 Starting evaluation for query: '{user_query[:50]}...'")
            
            # Prepare full context without summarization
            context_text = self._format_full_context(context_data)
            
            # Create evaluation prompt
            evaluation_prompt = f"""
USER QUERY: {user_query}

ASSISTANT RESPONSE: {assistant_response}

CONTEXT DATA PROVIDED TO ASSISTANT:
{context_text}

Please evaluate this banking assistant response using the structured format."""

            # Get structured evaluation
            messages = [
                SystemMessage(content=self.get_evaluation_prompt()),
                HumanMessage(content=evaluation_prompt)
            ]
            
            logger.info("🔍 Sending evaluation request to LLM with structured output")
            evaluation = await self.llm.ainvoke(messages)
            
            logger.info(f"✅ Evaluation completed - Overall Score: {evaluation.overall_score}/5")
            logger.info(f"📊 Confidence Level: {evaluation.confidence_level}")
            
            return evaluation
            
        except Exception as e:
            logger.error(f"❌ Evaluation failed: {str(e)}")
            
            # Return default evaluation on error
            return ResponseEvaluation(
                overall_score=3,
                criteria_scores=[],
                strengths=["Response provided"],
                weaknesses=["Could not evaluate due to technical error"], 
                confidence_level="Medium",
                summary="Evaluation unavailable due to technical error"
            )
    
    def _format_full_context(self, context_data: List[Dict[str, Any]]) -> str:
        """
        Format the full context data without summarization
        
        Args:
            context_data: List of context data from tools/retrievals
        """
        if not context_data:
            return "No context data provided"
        
        formatted_sections = []
        
        for i, context in enumerate(context_data, 1):
            tool_name = context.get('tool_name', 'Unknown Tool')
            tool_output = context.get('tool_output', '')
            
            # Keep full output without truncation
            formatted_sections.append(f"""
=== CONTEXT {i}: {tool_name.upper()} ===
{tool_output}
""")
        
        return "\n".join(formatted_sections)


# Global judge instance
_judge_instance = None

def get_banking_judge() -> BankingResponseJudge:
    """Get the shared banking judge instance"""
    global _judge_instance
    if _judge_instance is None:
        _judge_instance = BankingResponseJudge()
    return _judge_instance
