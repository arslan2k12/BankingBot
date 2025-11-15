#!/usr/bin/env python3
"""
Test the actual banking agent with proper parameters to verify everything works.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import asyncio
import json
from datetime import datetime

from src.app.agents.banking_agent import BankingAgent

async def test_banking_agent():
    """Test the banking agent with real scenarios."""
    print("🚀 Testing Banking Agent with Proper Parameters")
    print("="*60)
    
    # Initialize the agent
    agent = BankingAgent()
    
    # Test cases
    test_cases = [
        {
            "name": "Account Balance Request",
            "message": "What's my account balance?",
            "user_id": "jane_smith", 
            "thread_id": "test_thread_1"
        },
        {
            "name": "Transaction History Request", 
            "message": "Show me my recent transactions",
            "user_id": "jane_smith",
            "thread_id": "test_thread_2"
        },
        {
            "name": "Credit Card Info Request",
            "message": "What's my credit card information?", 
            "user_id": "jane_smith",
            "thread_id": "test_thread_3"
        },
        {
            "name": "Multiple Account Info",
            "message": "Give me my balance of all accounts, my user id, and my email?",
            "user_id": "jane_smith",
            "thread_id": "test_thread_4"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"👤 User: {test_case['user_id']}")
        print(f"💬 Message: {test_case['message']}")
        print(f"🧵 Thread: {test_case['thread_id']}")
        
        try:
            # Call the agent
            result = await agent.chat(
                message=test_case["message"],
                user_id=test_case["user_id"], 
                chat_thread_id=test_case["thread_id"]
            )
            
            print(f"✅ Response received")
            print(f"📝 Response: {result.get('response', 'No response')[:200]}...")
            print(f"🛠️  Tools used: {result.get('tools_used', [])}")
            print(f"⏱️  Response time: {result.get('response_time_ms', 0)}ms")
            
            if 'error' in str(result.get('response', '')).lower():
                print(f"⚠️  Possible error in response")
            else:
                print(f"🎯 Test appears successful")
                
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
        
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(test_banking_agent())
