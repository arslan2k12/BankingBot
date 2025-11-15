"""
LangGraph Workflow: Banking Agent + LLM Judge
Orchestrates the banking response generation and evaluation pipeline.
"""

from typing import Dict, Any, List, AsyncIterator, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
import json
import asyncio
from datetime import datetime

from src.app.agents.banking_agent import BankingAgent
from src.app.agents.response_judge import get_banking_judge
from src.app.utils.logger_utils import get_logger

logger = get_logger(__name__)


class BankingWorkflowState(TypedDict):
    """State for the banking workflow"""
    user_query: str
    user_id: str
    thread_id: str
    agent_response: str
    context_data: List[Dict[str, Any]]
    tools_used: List[str]
    evaluation: Dict[str, Any]
    streaming_events: List[Dict[str, Any]]
    workflow_status: str


class BankingAgentWithJudge:
    """Enhanced banking agent with LLM-as-a-Judge evaluation"""
    
    def __init__(self):
        self.banking_agent = BankingAgent()
        self.judge = get_banking_judge()
        self.workflow = self._create_workflow()
        
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        
        # Define the workflow
        workflow = StateGraph(BankingWorkflowState)
        
        # Add nodes
        workflow.add_node("banking_agent", self._banking_agent_node)
        workflow.add_node("judge_evaluation", self._judge_evaluation_node)
        
        # Define the flow
        workflow.set_entry_point("banking_agent")
        workflow.add_edge("banking_agent", "judge_evaluation")
        workflow.add_edge("judge_evaluation", END)
        
        # Compile with checkpointer for conversation memory
        return workflow.compile(checkpointer=InMemorySaver())
    
    async def _banking_agent_node(self, state: BankingWorkflowState) -> Dict[str, Any]:
        """Execute the banking agent and collect context"""
        logger.info(f"Banking agent processing query for user {state['user_id']}")
        
        try:
            # Store streaming events and collect context
            streaming_events = []
            context_data = []
            tools_used = []
            final_response = ""
            
            # Stream the banking agent response
            async for event in self.banking_agent.stream_response(
                state["user_query"], 
                state["thread_id"], 
                state["user_id"]
            ):
                streaming_events.append(event)
                
                # Extract context from tool observations
                if event.get("type") == "react_step" and event.get("phase") == "OBSERVATION":
                    tool_name = event.get("details", {}).get("tool_name", "unknown")
                    if tool_name not in tools_used:
                        tools_used.append(tool_name)
                    
                    # Try to extract context data (this is a simplified approach)
                    result_preview = event.get("details", {}).get("result_preview", "")
                    if "Retrieved:" in result_preview:
                        # This is a tool result - we'd need to access the actual data
                        # For now, we'll use a placeholder
                        context_data.append({"tool": tool_name, "preview": result_preview})
                
                # Extract final response
                if event.get("type") == "react_step" and event.get("phase") == "FINAL_ANSWER":
                    final_response = event.get("details", {}).get("final_answer", "")
            
            return {
                "agent_response": final_response,
                "context_data": context_data,
                "tools_used": tools_used,
                "streaming_events": streaming_events,
                "workflow_status": "agent_complete"
            }
            
        except Exception as e:
            logger.error(f"Banking agent node failed: {str(e)}")
            return {
                "agent_response": f"Error: {str(e)}",
                "context_data": [],
                "tools_used": [],
                "streaming_events": [],
                "workflow_status": "agent_error"
            }
    
    async def _judge_evaluation_node(self, state: BankingWorkflowState) -> Dict[str, Any]:
        """Execute the LLM judge evaluation"""
        logger.info(f"Judge evaluating response for user {state['user_id']}")
        
        try:
            evaluation = await self.judge.evaluate_response(
                user_query=state["user_query"],
                agent_response=state["agent_response"],
                context_data=state["context_data"],
                tools_used=state["tools_used"]
            )
            
            return {
                "evaluation": evaluation,
                "workflow_status": "complete"
            }
            
        except Exception as e:
            logger.error(f"Judge evaluation node failed: {str(e)}")
            return {
                "evaluation": {
                    "overall_score": 3.0,
                    "error": True,
                    "explanation": f"Evaluation failed: {str(e)}"
                },
                "workflow_status": "judge_error"
            }
    
    async def stream_response_with_evaluation(
        self, 
        message: str, 
        thread_id: str, 
        user_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream banking agent response and then provide evaluation"""
        
        # Initialize state
        initial_state = BankingWorkflowState(
            user_query=message,
            user_id=user_id,
            thread_id=thread_id,
            agent_response="",
            context_data=[],
            tools_used=[],
            evaluation={},
            streaming_events=[],
            workflow_status="starting"
        )
        
        config = {"configurable": {"thread_id": f"{thread_id}_{user_id}"}}
        
        # Execute workflow
        final_state = await self.workflow.ainvoke(initial_state, config)
        
        # First, yield all the streaming events from the banking agent
        for event in final_state["streaming_events"]:
            yield event
        
        # Then yield the evaluation
        yield {
            "type": "evaluation",
            "evaluation": final_state["evaluation"],
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Final completion with evaluation
        yield {
            "type": "completion_with_evaluation",
            "chat_thread_id": thread_id,
            "tools_used": final_state["tools_used"],
            "response_length": len(final_state["agent_response"]),
            "evaluation_score": final_state["evaluation"].get("overall_score", 0),
            "timestamp": datetime.now().isoformat()
        }


class SimpleBankingAgentWithJudge:
    """Simplified version that evaluates after streaming without LangGraph complexity"""
    
    def __init__(self):
        self.banking_agent = BankingAgent()
        self.judge = get_banking_judge()
        
    async def stream_response_with_evaluation(
        self, 
        message: str, 
        thread_id: str, 
        user_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream banking agent response and then provide evaluation"""
        
        # Collect streaming events and extract data for evaluation
        streaming_events = []
        context_data = []
        tools_used = []
        final_response = ""
        
        # Stream the banking agent response
        async for event in self.banking_agent.stream_response(message, thread_id, user_id):
            # Forward the event to the client
            yield event
            
            # Collect data for evaluation
            streaming_events.append(event)
            
            # Extract tool information
            if event.get("type") == "react_step" and event.get("phase") == "OBSERVATION":
                tool_name = event.get("details", {}).get("tool_name", "unknown")
                if tool_name not in tools_used and tool_name != "unknown":
                    tools_used.append(tool_name)
                
                # Extract context data (simplified)
                result_preview = event.get("details", {}).get("result_preview", "")
                if result_preview and "Retrieved:" in result_preview:
                    context_data.append({"tool": tool_name, "preview": result_preview})
            
            # Extract final response
            if event.get("type") == "react_step" and event.get("phase") == "FINAL_ANSWER":
                final_response = event.get("details", {}).get("final_answer", "")
        
        # Now evaluate the response
        if final_response:
            try:
                evaluation = await self.judge.evaluate_response(
                    user_query=message,
                    agent_response=final_response,
                    context_data=context_data,
                    tools_used=tools_used
                )
                
                # Yield the evaluation
                yield {
                    "type": "evaluation",
                    "evaluation": evaluation,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"Response evaluated - Score: {evaluation.get('overall_score', 'N/A')} for user {user_id}")
                
            except Exception as e:
                logger.error(f"Evaluation failed: {str(e)}")
                yield {
                    "type": "evaluation",
                    "evaluation": {
                        "overall_score": 3.0,
                        "error": True,
                        "explanation": f"Evaluation failed: {str(e)}"
                    },
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }


# Global instances
_workflow_agent_instance = None
_simple_agent_instance = None

def get_banking_agent_with_judge(use_langgraph: bool = False):
    """Get the banking agent with judge evaluation"""
    global _workflow_agent_instance, _simple_agent_instance
    
    if use_langgraph:
        if _workflow_agent_instance is None:
            _workflow_agent_instance = BankingAgentWithJudge()
        return _workflow_agent_instance
    else:
        if _simple_agent_instance is None:
            _simple_agent_instance = SimpleBankingAgentWithJudge()
        return _simple_agent_instance
