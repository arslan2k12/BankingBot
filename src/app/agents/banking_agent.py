from typing import List, Dict, Any, Optional, AsyncIterator
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
import json
import logging
from datetime import datetime

# Setup project path for consistent imports
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.app.config.service_config import settings
from src.app.tools.sql_retrieval_tool import get_account_balance, get_transactions, get_credit_card_info
from src.app.tools.doc_retrieval_tool import search_bank_documents
from src.app.utils.logger_utils import get_logger
from src.app.utils.prompts import get_banking_agent_prompt

logger = get_logger(__name__)


class BankingAgent:
    """Enterprise-grade banking agent with proper message-type based ReAct streaming"""
    
    def __init__(self):
        self.llm = init_chat_model(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=settings.openai_temperature,
            streaming=True
        )
        
        # Set up agent with tools
        self.tools = [get_account_balance, get_transactions, get_credit_card_info, search_bank_documents]
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=get_banking_agent_prompt(),
            checkpointer=InMemorySaver()
        )
        
        # State tracking for proper ReAct flow
        self.current_step = 0
        self.current_state = None

    async def stream_response(self, message: str, thread_id: str, user_id: str) -> AsyncIterator[Dict[str, Any]]:
        """Stream agent response with proper message-type based ReAct steps"""
        
        # Start stream
        yield {
            "type": "stream_start",
            "user_id": user_id,
            "chat_thread_id": thread_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Reset state for new conversation turn
        self.current_step = 0
        self._final_answer_emitted = False  # Reset final answer flag
        config = {"configurable": {"thread_id": f"{thread_id}_{user_id}"}}
        
        try:
            # Stream the agent execution - the agent will maintain conversation history automatically
            # We inject the authenticated user_id into the message for security
            async for event in self.agent.astream_events(
                {
                    "messages": [
                        HumanMessage(content=f"[AUTHENTICATED_USER_ID: {user_id}] {message}")
                    ]
                },
                config=config,
                version="v2"
            ):
                
                # Parse the event using message types instead of keyword matching
                parsed_event = await self._parse_langgraph_event(event, thread_id, user_id)
                if parsed_event:
                    yield parsed_event
                    
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            yield {
                "type": "error",
                "content": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Stream completion
        yield {
            "type": "stream_complete",
            "timestamp": datetime.now().isoformat()
        }
        
        yield {
            "type": "completion",
            "chat_thread_id": thread_id,
            "tools_used": len([t for t in self.tools]),
            "response_length": 0,  # Will be filled by frontend
            "timestamp": datetime.now().isoformat()
        }

    async def _parse_langgraph_event(self, event: Dict[str, Any], thread_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Parse LangGraph events using proper message types - Fixed for LangGraph 1.0.3"""
        
        event_type = event.get("event", "")
        event_data = event.get("data", {})
        
        # Debug logging to understand event structure
        if event_type in ["on_tool_start", "on_tool_end"]:
            logger.debug(f"Event type: {event_type}")
            logger.debug(f"Event data: {event_data}")
            logger.debug(f"Event metadata: {event.get('metadata', {})}")
            logger.debug(f"Event tags: {event.get('tags', [])}")
            logger.debug(f"Full event keys: {list(event.keys())}")
        
        # === 1. LLM START - Beginning of reasoning ===
        if event_type == "on_chat_model_start":
            self.current_step += 1
            return {
                "type": "react_step",
                "step": self.current_step,
                "phase": "THOUGHT",
                "content": "💭 Analyzing your request and planning the next steps...",
                "details": {
                    "thought_type": "planning",
                    "model": event_data.get("name", "unknown"),
                    "full_thought": "Starting analysis of user request"
                },
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # === 2. LLM STREAM - Reasoning tokens ===
        elif event_type == "on_chat_model_stream":
            chunk = event_data.get("chunk", {})
            
            # Handle AIMessageChunk objects
            if hasattr(chunk, 'content'):
                content = chunk.content
            else:
                content = chunk.get("content", "") if isinstance(chunk, dict) else ""
            
            if content:
                return {
                    "type": "reasoning_token",
                    "content": content,
                    "step": self.current_step,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
        
        # === 3. LLM END - Reasoning complete, check for tool calls ===
        elif event_type == "on_chat_model_end":
            output = event_data.get("output", {})
            
            # Check if AI decided to use tools
            if hasattr(output, 'tool_calls') and output.tool_calls:
                tool_call = output.tool_calls[0]  # Get first tool call
                
                # Handle both dict and object formats
                tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', 'unknown')
                tool_args = tool_call.get('args', {}) if isinstance(tool_call, dict) else getattr(tool_call, 'args', {})
                tool_id = tool_call.get('id') if isinstance(tool_call, dict) else getattr(tool_call, 'id', 'unknown')
                
                return {
                    "type": "react_step",
                    "step": self.current_step,
                    "phase": "ACTION",
                    "content": f"🔧 Using tool: {tool_name}",
                    "details": {
                        "tool_name": tool_name,
                        "arguments": tool_args,
                        "tool_call_id": tool_id
                    },
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # For final responses without tool calls, just show thinking phase
            # The actual content will be handled by on_chain_end
            elif hasattr(output, 'content') and output.content:
                return {
                    "type": "react_step",
                    "step": self.current_step,
                    "phase": "THOUGHT",
                    "content": "💭 Finalizing response based on the information gathered...",
                    "details": {
                        "thought_type": "finalizing",
                        "has_tool_calls": False
                    },
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
        
        # === 4. TOOL START - Tool execution begins ===
        elif event_type == "on_tool_start":
            # LangGraph 1.0.3 - extract tool name from different sources
            tool_name = event_data.get("name", "unknown")
            tool_input = event_data.get("input", {})
            
            # Try to get actual tool name from tool_input or metadata
            if tool_name == "unknown" and tool_input and 'user_id' in tool_input:
                # This is likely a banking tool - check the event metadata
                metadata = event.get("metadata", {})
                if "langgraph_node" in metadata and metadata["langgraph_node"] == "tools":
                    # This is a tool node, but we need the actual tool name
                    # For now, show generic tool execution message
                    tool_name = "banking_tool"
            
            # Increment step for new tool execution
            self.current_step += 1
            
            return {
                "type": "react_step",
                "step": self.current_step,
                "phase": "ACTION",
                "content": f"🔧 Executing {tool_name}",
                "details": {
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "execution_start": True
                },
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # === 5. TOOL END - Tool execution complete ===
        elif event_type == "on_tool_end":
            # LangGraph 1.0.3 - extract tool name from output
            tool_output = event_data.get("output", "")
            tool_input = event_data.get("input", {})
            
            # Extract the actual tool name from the ToolMessage
            tool_name = "unknown"
            if hasattr(tool_output, 'name'):
                tool_name = tool_output.name
            elif isinstance(tool_output, dict) and 'name' in tool_output:
                tool_name = tool_output['name']
            elif tool_input and 'user_id' in tool_input:
                # This is likely a banking tool
                tool_name = "banking_tool"
            
            # Ensure tool_output is JSON serializable
            if not isinstance(tool_output, (str, int, float, bool, dict, list, type(None))):
                tool_output = str(tool_output)
            
            # Create a clean preview of the tool result
            result_preview = self._create_result_preview(tool_name, tool_output)
            
            return {
                "type": "react_step",
                "step": self.current_step,
                "phase": "OBSERVATION",
                "content": f"👁️ {result_preview}",
                "details": {
                    "tool_name": tool_name,
                    "result_preview": result_preview,
                    "execution_complete": True
                },
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # === 6. CHAIN END - Final response ready (ONLY ONCE) ===
        elif event_type == "on_chain_end":
            output = event_data.get("output", {})
            
            # Debug: Check what's in the chain end
            logger.debug(f"Chain end output keys: {list(output.keys()) if isinstance(output, dict) else 'Not dict'}")
            
            # Only process the final chain end (not intermediate ones)
            # Check if this is the main agent chain by looking for messages
            if isinstance(output, dict) and "messages" in output:
                messages = output["messages"]
                logger.debug(f"Found {len(messages)} messages in chain end")
                
                # Find the last AI message that's not a tool call
                for msg in reversed(messages):
                    if (isinstance(msg, AIMessage) and 
                        hasattr(msg, 'content') and 
                        msg.content and 
                        not (hasattr(msg, 'tool_calls') and msg.tool_calls)):
                        
                        content = str(msg.content)
                        logger.debug(f"Found final AI message: {content[:100]}...")
                        
                        # Only emit FINAL_ANSWER once per conversation turn
                        if not self._final_answer_emitted:
                            self._final_answer_emitted = True
                            self.current_step += 1
                            
                            return {
                                "type": "react_step",
                                "step": self.current_step,
                                "phase": "FINAL_ANSWER",
                                "content": "✅ Here's your complete response:",
                                "details": {
                                    "final_answer": content,
                                    "answer_length": len(content)
                                },
                                "user_id": user_id,
                                "timestamp": datetime.now().isoformat()
                            }
                        break
        
        return None
    
    def _create_result_preview(self, tool_name: str, tool_output: str) -> str:
        """Create a human-readable preview of tool results"""
        try:
            # Try to parse as JSON for structured preview
            if isinstance(tool_output, str):
                data = json.loads(tool_output)
            else:
                data = tool_output
            
            # Banking-specific result summaries
            if tool_name == "get_account_balance" and isinstance(data, dict):
                if "accounts" in data:
                    account_count = len(data["accounts"])
                    total_balance = data.get("total_balance", 0)
                    return f"Found {account_count} accounts with total balance ${total_balance:,.2f}"
                    
            elif tool_name == "get_transactions" and isinstance(data, dict):
                if "transactions" in data:
                    tx_count = len(data["transactions"])
                    return f"Retrieved {tx_count} recent transactions"
                    
            elif tool_name == "search_bank_documents" and isinstance(data, dict):
                if "documents" in data:
                    doc_count = len(data["documents"])
                    return f"Found {doc_count} relevant documents"
            
            # Generic fallback
            return f"Tool {tool_name} completed successfully"
            
        except Exception:
            # Fallback for non-JSON responses
            preview = str(tool_output)[:100]
            return f"Retrieved: {preview}{'...' if len(str(tool_output)) > 100 else ''}"

    def get_conversation_history(self, user_id: str, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history from the agent's checkpointer"""
        try:
            config = {"configurable": {"thread_id": f"{thread_id}_{user_id}"}}
            
            # Get the current state from checkpointer
            state = self.agent.checkpointer.get(config)
            if state and "messages" in state.values:
                messages = state.values["messages"]
                
                # Convert to simple format for logging/debugging
                history = []
                for msg in messages[-limit:]:  # Get last N messages
                    if hasattr(msg, 'content') and msg.content:
                        msg_type = "human" if hasattr(msg, 'type') and msg.type == "human" else "ai"
                        history.append({
                            "type": msg_type,
                            "content": str(msg.content),
                            "timestamp": getattr(msg, 'timestamp', datetime.now().isoformat())
                        })
                
                logger.info(f"Retrieved {len(history)} messages for user {user_id}, thread {thread_id}")
                return history
                
        except Exception as e:
            logger.warning(f"Could not retrieve conversation history: {str(e)}")
        
        return []


# Global shared agent instance
_agent_instance = None

def get_banking_agent(user_id: str) -> BankingAgent:
    """Get the shared banking agent instance (user isolation handled by thread_id)"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = BankingAgent()
    return _agent_instance
