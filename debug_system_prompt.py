#!/usr/bin/env python3
"""
System Prompt Debug Script - Check the actual system prompt being used
"""

import sys
from pathlib import Path

# Setup project path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.app.agents.banking_agent import BankingAgent

def debug_system_prompt():
    """Debug the system prompt to see what's actually being sent to the LLM"""
    
    print("🔍 System Prompt Debug")
    print("=" * 50)
    
    # Initialize the banking agent
    agent = BankingAgent()
    
    # Test with the user_id from the log
    user_id = "jane_smith"
    
    print(f"\n1. 📝 System Prompt for user_id: '{user_id}'")
    print("-" * 30)
    
    system_prompt = agent._get_system_prompt(user_id)
    
    print(system_prompt)
    
    print(f"\n2. 🔍 Key Security Elements Check:")
    print(f"   Contains user_id '{user_id}': {'✅' if user_id in system_prompt else '❌'}")
    print(f"   Contains security constraints: {'✅' if 'MANDATORY' in system_prompt else '❌'}")
    print(f"   Contains forbidden actions: {'✅' if 'FORBIDDEN' in system_prompt else '❌'}")
    print(f"   Contains explicit examples: {'✅' if 'get_account_balance(user_id=' in system_prompt else '❌'}")
    
    # Count occurrences of the user_id
    user_id_count = system_prompt.count(user_id)
    print(f"   User_id mentioned {user_id_count} times")
    
    return system_prompt

if __name__ == "__main__":
    debug_system_prompt()
