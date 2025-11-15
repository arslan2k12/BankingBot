"""
LLM-as-a-Judge Evaluator for Banking Agent Responses
Evaluates response accuracy, completeness, and adherence to retrieved context.
"""

from typing import Dict, Any, List
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
import json
from datetime import datetime

from src.app.config.service_config import settings
from src.app.utils.logger_utils import get_logger

logger = get_logger(__name__)


class BankingResponseJudge:
    """LLM-as-a-Judge for evaluating banking agent responses"""
    
    def __init__(self):
        self.llm = init_chat_model(
            model=settings.openai_model,  # Use same model for consistency
            api_key=settings.openai_api_key,
            temperature=0.1  # Lower temperature for more consistent evaluation
        )
    
    def get_evaluation_prompt(self) -> str:
        """System prompt for the LLM judge"""
        return """You are an expert evaluator for banking customer service responses. Your job is to assess the quality of AI assistant responses to banking queries.

## EVALUATION CRITERIA

**Accuracy (1-5):**
- 5: Information is completely accurate based on retrieved context
- 4: Mostly accurate with minor inconsistencies
- 3: Generally accurate but missing some details
- 2: Some inaccuracies or misinterpretations
- 1: Significant inaccuracies or wrong information

**Completeness (1-5):**
- 5: Fully addresses all parts of the user's question
- 4: Addresses most parts with minor gaps
- 3: Addresses main question but misses some aspects
- 2: Partial answer, significant gaps
- 1: Incomplete or doesn't address the main question

## OUTPUT FORMAT

Provide your evaluation as a JSON object:
```json
{
    "overall_score": 4.2,
    "accuracy": 5,
    "completeness": 4,
    "explanation": "Brief explanation of the evaluation",
}
```

## INSTRUCTIONS

1. Compare the response against the user query and any retrieved context
2. Check if all user questions were addressed
3. Verify accuracy of financial data and policy information, if provided in context
4. Assess professional banking communication standards
5. For irrelevant information, ensure the response guides the user back to banking topics. For greeting or closing statements, score based on professionalism and tone.
6. Return only the JSON object as specified
7. Do not include any relevant metadata (e.g., user ID, session ID) in the evaluation
"""

    async def evaluate_response(
        self,
        user_query: str,
        agent_response: str,
        context_data: List[Dict[str, Any]],
        tools_used: List[str]
    ) -> Dict[str, Any]:
        """Evaluate a banking agent response"""
        
        try:
            # Prepare context summary
            context_summary = self._prepare_context_summary(context_data, tools_used)
            
            # Create evaluation message
            evaluation_input = f"""
## USER QUERY
{user_query}

## AGENT RESPONSE
{agent_response}

## RETRIEVED CONTEXT
{context_summary}

## TOOLS USED
{', '.join(tools_used) if tools_used else 'None'}

Please evaluate this banking agent response according to the criteria provided.
"""

            messages = [
                SystemMessage(content=self.get_evaluation_prompt()),
                HumanMessage(content=evaluation_input)
            ]
            
            # Get evaluation from judge LLM
            response = await self.llm.ainvoke(messages)
            
            # Parse the JSON response
            evaluation = self._parse_evaluation_response(response.content)
            
            # Add metadata
            evaluation.update({
                "timestamp": datetime.now().isoformat(),
                "evaluator_model": settings.openai_model,
                "context_items_count": len(context_data),
                "tools_used_count": len(tools_used)
            })
            
            logger.info(f"Response evaluated - Overall Score: {evaluation.get('overall_score', 'N/A')}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            return self._create_fallback_evaluation(str(e))
    
    def _prepare_context_summary(self, context_data: List[Dict[str, Any]], tools_used: List[str]) -> str:
        """Prepare a summary of the context used for the response"""
        if not context_data:
            return "No context data provided"
        
        summaries = []
        for i, context in enumerate(context_data, 1):
            if isinstance(context, dict):
                # Handle different context types
                if "accounts" in context:
                    account_count = len(context["accounts"])
                    total_balance = context.get("total_balance", 0)
                    summaries.append(f"Context {i}: Account data - {account_count} accounts, total balance: ${total_balance:,.2f}")
                
                elif "transactions" in context:
                    tx_count = len(context["transactions"])
                    summaries.append(f"Context {i}: Transaction data - {tx_count} transactions")
                
                elif "credit_cards" in context:
                    card_count = len(context["credit_cards"])
                    summaries.append(f"Context {i}: Credit card data - {card_count} cards")
                
                elif "results" in context:
                    doc_count = len(context.get("results", []))
                    summaries.append(f"Context {i}: Document search - {doc_count} documents found")
                
                else:
                    # Generic context
                    keys = list(context.keys())[:3]  # First 3 keys
                    summaries.append(f"Context {i}: Data with keys: {', '.join(keys)}")
            else:
                summaries.append(f"Context {i}: {str(context)[:100]}...")
        
        return "\n".join(summaries)
    
    def _parse_evaluation_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the JSON evaluation response from the judge LLM"""
        try:
            # Try to extract JSON from the response
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
            else:
                json_content = response_content.strip()
            
            evaluation = json.loads(json_content)
            
            # Validate required fields
            required_fields = ["overall_score", "accuracy", "completeness", "context_adherence", "professional_quality"]
            for field in required_fields:
                if field not in evaluation:
                    evaluation[field] = 3  # Default middle score
            
            # Ensure scores are in valid range
            for score_field in required_fields:
                score = evaluation.get(score_field, 3)
                evaluation[score_field] = max(1, min(5, score))
            
            # Calculate overall score if not provided
            if "overall_score" not in evaluation or evaluation["overall_score"] == 3:
                scores = [evaluation[field] for field in required_fields[1:]]  # Exclude overall_score
                evaluation["overall_score"] = round(sum(scores) / len(scores), 1)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Failed to parse evaluation response: {str(e)}")
            return self._create_fallback_evaluation(f"Parse error: {str(e)}")
    
    def _create_fallback_evaluation(self, error_message: str) -> Dict[str, Any]:
        """Create a fallback evaluation when the judge fails"""
        return {
            "overall_score": 3.0,
            "accuracy": 3,
            "completeness": 3,
            "context_adherence": 3,
            "professional_quality": 3,
            "explanation": f"Evaluation failed: {error_message}",
            "strengths": ["Response provided"],
            "improvements": ["Evaluation system needs attention"],
            "error": True,
            "timestamp": datetime.now().isoformat()
        }


# Global judge instance
_judge_instance = None

def get_banking_judge() -> BankingResponseJudge:
    """Get the shared banking response judge instance"""
    global _judge_instance
    if _judge_instance is None:
        _judge_instance = BankingResponseJudge()
    return _judge_instance
