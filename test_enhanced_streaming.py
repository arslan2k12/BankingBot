#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced streaming vs old streaming
Run this to see the differences in streaming output
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.app.agents.enhanced_banking_agent import get_enhanced_banking_agent

async def test_enhanced_streaming():
    """Test the enhanced streaming functionality"""
    print("🚀 Testing Enhanced LangGraph Message-Based Streaming")
    print("=" * 60)
    
    try:
        # Initialize enhanced agent
        agent = get_enhanced_banking_agent()
        print(f"✅ Agent initialized with {len(agent.tools)} tools")
        
        # Test streaming
        user_id = "mike_johnson"
        chat_thread_id = "test_thread_123"
        test_message = "What's my account balance and recent transactions?"
        
        print(f"\n📝 Test Query: '{test_message}'")
        print(f"👤 User ID: {user_id}")
        print(f"💬 Thread ID: {chat_thread_id}")
        print("\n📊 Streaming Output:")
        print("-" * 40)
        
        chunk_count = 0
        async for chunk in agent.stream_chat_enhanced(
            message=test_message,
            user_id=user_id,
            chat_thread_id=chat_thread_id
        ):
            chunk_count += 1
            chunk_type = chunk.get("type", "unknown")
            
            # Format output based on chunk type
            if chunk_type == "stream_start":
                print(f"🟢 STREAM START - User: {chunk.get('user_id')}")
                
            elif chunk_type == "agent_step":
                step = chunk.get("step", "?")
                phase = chunk.get("phase", "?")
                content = chunk.get("content", "")
                details = chunk.get("details", {})
                
                print(f"🔄 STEP {step} - {phase}")
                print(f"   Content: {content}")
                if details:
                    print(f"   Details: {details}")
                    
            elif chunk_type == "llm_token":
                content = chunk.get("content", "")
                print(f"💬 TOKEN: {repr(content)}")
                
            elif chunk_type == "debug_trace":
                trace_data = chunk.get("trace_data", {})
                print(f"🐛 DEBUG: {trace_data}")
                
            elif chunk_type == "stream_complete":
                print(f"🏁 STREAM COMPLETE")
                
            elif chunk_type == "error":
                message = chunk.get("message", "Unknown error")
                print(f"❌ ERROR: {message}")
            
            else:
                print(f"📦 {chunk_type.upper()}: {chunk}")
        
        print(f"\n📈 Summary: Processed {chunk_count} chunks")
        print("✅ Enhanced streaming test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during enhanced streaming test: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    print("Enhanced Banking Agent Streaming Test")
    print("=" * 50)
    
    # Check if we have the required environment
    try:
        from src.app.config.service_config import settings
        print(f"✅ Config loaded - Model: {settings.openai_model}")
    except Exception as e:
        print(f"❌ Config error: {e}")
        print("Make sure your .env file is properly configured")
        return
    
    await test_enhanced_streaming()

if __name__ == "__main__":
    asyncio.run(main())
