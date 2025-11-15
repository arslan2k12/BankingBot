#!/usr/bin/env python3
"""
Security Debug Script - Check if user-specific agents are working
"""

import asyncio
import sys
from pathlib import Path

# Setup project path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.app.agents.banking_agent import BankingAgent
from src.app.utils.logger_utils import get_logger

logger = get_logger(__name__)

async def debug_security_implementation():
    """Debug the security implementation to see why user123 is being used"""
    
    print("🔍 Security Debug: Checking User-Specific Agent Creation")
    print("=" * 60)
    
    # Initialize the banking agent
    agent = BankingAgent()
    
    print(f"\n1. 📋 Initial State:")
    print(f"   User agents cache: {len(agent.user_agents)} entries")
    print(f"   Available tools: {[tool.name for tool in agent.tools]}")
    
    print(f"\n2. 🔒 Creating User-Specific Agent for 'jane_smith':")
    user_agent = agent._get_user_agent("jane_smith")
    
    print(f"   User agents cache after creation: {len(agent.user_agents)} entries")
    print(f"   Agent created: {user_agent is not None}")
    print(f"   Agent tools: {[tool.name for tool in user_agent.graph.nodes['agent'].tools] if hasattr(user_agent, 'graph') else 'Unknown'}")
    
    print(f"\n3. 🧪 Testing Direct Tool Call:")
    # Let's test if we can call the secure tool directly
    try:
        result = await agent.chat(
            message="What's my balance?",
            user_id="jane_smith",
            chat_thread_id="debug_thread"
        )
        
        print(f"   Chat result received: {result is not None}")
        print(f"   Tools used: {result.get('tools_used', 'Unknown')}")
        print(f"   Response preview: {result.get('response', 'No response')[:100]}...")
        
    except Exception as e:
        print(f"   Error during chat: {e}")
    
    print(f"\n4. 🔍 Checking Tool Arguments in Recent Execution:")
    print("   Looking for user_id arguments in tool calls...")
    
    return True

if __name__ == "__main__":
    asyncio.run(debug_security_implementation())
