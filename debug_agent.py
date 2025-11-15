#!/usr/bin/env python3
"""
Debug script for testing the Banking Agent directly
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.app.agents.banking_agent import get_banking_agent

async def test_agent():
    """Test the banking agent with a sample query"""
    
    # Test parameters
    user_id = "john_doe"
    thread_id = "debug_thread_001"
    test_message = "What is my account balance?"
    
    print(f"🚀 Testing Banking Agent")
    print(f"User ID: {user_id}")
    print(f"Thread ID: {thread_id}")
    print(f"Message: {test_message}")
    print("-" * 50)
    
    try:
        # Get the agent
        agent = get_banking_agent(user_id)
        
        # Stream the response
        print("📡 Streaming response:")
        async for chunk in agent.stream_response(test_message, thread_id, user_id):
            chunk_type = chunk.get("type", "unknown")
            
            if chunk_type == "stream_start":
                print(f"✅ Stream started for user {chunk.get('user_id')}")
                
            elif chunk_type == "react_step":
                phase = chunk.get("phase", "")
                content = chunk.get("content", "")
                step = chunk.get("step", 0)
                details = chunk.get("details", {})
                
                print(f"🔄 Step {step} - {phase}: {content}")
                
                # Show additional details for debugging
                if phase == "ACTION" and details.get("tool_name"):
                    print(f"   🔧 Tool: {details['tool_name']}")
                    print(f"   📝 Args: {details.get('arguments', {})}")
                    
                elif phase == "OBSERVATION" and details.get("result_preview"):
                    print(f"   👁️ Result: {details['result_preview']}")
                    
                elif phase == "FINAL_ANSWER" and details.get("final_answer"):
                    print(f"   ✅ Final Answer Length: {len(details['final_answer'])} chars")
                    print(f"   📄 Content Preview: {details['final_answer'][:100]}...")
                    
            elif chunk_type == "reasoning_token":
                content = chunk.get("content", "")
                if content.strip():
                    print(f"💭 Reasoning: {content.strip()}")
                    
            elif chunk_type == "llm_token":
                content = chunk.get("content", "")
                is_final = chunk.get("final", False)
                if is_final:
                    print(f"🎯 Final LLM Token ({len(content)} chars): {content[:100]}...")
                    
            elif chunk_type == "error":
                print(f"❌ Error: {chunk.get('content', 'Unknown error')}")
                
            elif chunk_type == "stream_complete":
                print("✅ Stream completed")
                
            elif chunk_type == "completion":
                print(f"🏁 Final completion: {chunk}")
                
        print("-" * 50)
        print("✅ Agent test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing agent: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Banking Agent Debug Script")
    print("=" * 50)
    
    # Run the test
    asyncio.run(test_agent())
