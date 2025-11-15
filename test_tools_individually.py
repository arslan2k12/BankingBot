#!/usr/bin/env python3
"""
Individual tool testing script to validate each banking tool independently.
This script will test each tool with various inputs to ensure proper functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import json
from datetime import datetime
from typing import Dict, Any

# Import the tools
from src.app.tools.sql_retrieval_tool import (
    get_account_balance,
    get_transactions,
    get_credit_card_info
)

def print_test_header(test_name: str):
    """Print a formatted test header."""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {test_name}")
    print(f"{'='*60}")

def print_test_result(test_name: str, result: str, expected: str = None):
    """Print formatted test result."""
    print(f"\n📊 TEST: {test_name}")
    print(f"📤 RESULT: {result}")
    if expected:
        print(f"✅ EXPECTED: {expected}")
    print("-" * 40)

def test_account_balance_tool():
    """Test the get_account_balance tool with various inputs."""
    print_test_header("get_account_balance Tool")
    
    # Test cases
    test_cases = [
        {
            "name": "Valid user - jane_smith",
            "user_id": "jane_smith",
            "account_number": None,
            "expected": "success"
        },
        {
            "name": "Valid user with specific account",
            "user_id": "jane_smith", 
            "account_number": "ACC001",
            "expected": "success"
        },
        {
            "name": "Invalid user - placeholder",
            "user_id": "user_id",
            "account_number": None,
            "expected": "error - invalid user_id"
        },
        {
            "name": "Non-existent user",
            "user_id": "non_existent_user",
            "account_number": None,
            "expected": "error - user not found"
        },
        {
            "name": "Empty user_id",
            "user_id": "",
            "account_number": None,
            "expected": "error - invalid user_id"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        try:
            result = get_account_balance.invoke({
                "user_id": test_case["user_id"],
                "account_number": test_case["account_number"]
            })
            result_data = json.loads(result)
            
            if "error" in result_data:
                print(f"❌ ERROR: {result_data['error']}")
                print(f"💬 MESSAGE: {result_data.get('message', 'No message')}")
            else:
                print(f"✅ SUCCESS: Found {len(result_data.get('accounts', []))} accounts")
                print(f"💰 Total Balance: ${result_data.get('total_balance', 0)}")
                for acc in result_data.get('accounts', []):
                    print(f"   🏦 {acc['account_number']} ({acc['account_type']}): ${acc['balance']}")
                    
        except Exception as e:
            print(f"💥 EXCEPTION: {str(e)}")

def test_transactions_tool():
    """Test the get_transactions tool with various inputs."""
    print_test_header("get_transactions Tool")
    
    test_cases = [
        {
            "name": "Valid user - recent transactions",
            "user_id": "jane_smith",
            "account_number": None,
            "limit": 5,
            "expected": "success"
        },
        {
            "name": "Valid user - specific account",
            "user_id": "jane_smith",
            "account_number": "ACC001",
            "limit": 10,
            "expected": "success"
        },
        {
            "name": "Invalid user - placeholder",
            "user_id": "your_user_id",
            "account_number": None,
            "limit": 10,
            "expected": "error - invalid user_id"
        },
        {
            "name": "Valid user - with date range",
            "user_id": "jane_smith",
            "account_number": None,
            "limit": 10,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "expected": "success"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        try:
            kwargs = {
                "user_id": test_case["user_id"],
                "account_number": test_case["account_number"],
                "limit": test_case["limit"]
            }
            
            # Add optional parameters if they exist
            if "start_date" in test_case:
                kwargs["start_date"] = test_case["start_date"]
            if "end_date" in test_case:
                kwargs["end_date"] = test_case["end_date"]
                
            result = get_transactions.invoke(kwargs)
            result_data = json.loads(result)
            
            if "error" in result_data:
                print(f"❌ ERROR: {result_data['error']}")
                print(f"💬 MESSAGE: {result_data.get('message', 'No message')}")
            else:
                print(f"✅ SUCCESS: Found {result_data.get('total_count', 0)} total transactions")
                print(f"📋 Returned: {len(result_data.get('transactions', []))} transactions")
                for txn in result_data.get('transactions', [])[:3]:  # Show first 3
                    print(f"   💸 {txn['transaction_date'][:10]} - {txn['description']} - ${txn['amount']}")
                    
        except Exception as e:
            print(f"💥 EXCEPTION: {str(e)}")

def test_credit_card_tool():
    """Test the get_credit_card_info tool with various inputs."""
    print_test_header("get_credit_card_info Tool")
    
    test_cases = [
        {
            "name": "Valid user - jane_smith",
            "user_id": "jane_smith",
            "expected": "success"
        },
        {
            "name": "Invalid user - placeholder",
            "user_id": "user_id",
            "expected": "error - invalid user_id"
        },
        {
            "name": "Non-existent user",
            "user_id": "non_existent_user",
            "expected": "error - user not found"
        },
        {
            "name": "Empty user_id",
            "user_id": "",
            "expected": "error - invalid user_id"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        try:
            result = get_credit_card_info.invoke({"user_id": test_case["user_id"]})
            result_data = json.loads(result)
            
            if "error" in result_data:
                print(f"❌ ERROR: {result_data['error']}")
                print(f"💬 MESSAGE: {result_data.get('message', 'No message')}")
            else:
                print(f"✅ SUCCESS: Found {result_data.get('total_cards', 0)} credit cards")
                for card in result_data.get('credit_cards', []):
                    print(f"   💳 {card['card_number']} ({card['card_type']})")
                    print(f"      💰 Balance: ${card['current_balance']} / ${card['credit_limit']}")
                    print(f"      📊 Utilization: {card['utilization_rate']}%")
                    
        except Exception as e:
            print(f"💥 EXCEPTION: {str(e)}")

def test_database_connection():
    """Test basic database connectivity."""
    print_test_header("Database Connection Test")
    
    try:
        from src.app.database.database import get_db
        from src.app.models.database_models import User
        
        db = next(get_db())
        print("✅ Database connection established")
        
        # Test basic query
        user_count = db.query(User).count()
        print(f"📊 Total users in database: {user_count}")
        
        # Get sample user
        sample_user = db.query(User).first()
        if sample_user:
            print(f"👤 Sample user: {sample_user.user_id} ({sample_user.first_name} {sample_user.last_name})")
        else:
            print("❌ No users found in database")
            
        db.close()
        
    except Exception as e:
        print(f"💥 Database connection failed: {str(e)}")

def main():
    """Run all tool tests."""
    print("🚀 Starting Individual Tool Testing")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test database connectivity first
    test_database_connection()
    
    # Test each tool
    test_account_balance_tool()
    test_transactions_tool()
    test_credit_card_tool()
    
    print(f"\n🏁 All tests completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    main()
