#!/usr/bin/env python3
"""
Sample Data Creation Script for Banking Bot Workshop
Creates users, accounts, transactions, and sample documents for the workshop
"""

import os
import sys
import asyncio
import sqlite3
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import json

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.app.database.connection import get_database_manager
from src.app.models.user import User, UserCreate
from src.app.models.account import Account, AccountCreate, AccountType
from src.app.models.transaction import Transaction, TransactionCreate, TransactionType
from src.app.services.user_service import UserService
from src.app.services.account_service import AccountService
from src.app.services.transaction_service import TransactionService

# Sample workshop users
WORKSHOP_USERS = [
    {
        "user_id": "sarah_chen",
        "first_name": "Sarah",
        "last_name": "Chen",
        "email": "sarah.chen@example.com",
        "password": "password123",
        "profile": "Tech Professional"
    },
    {
        "user_id": "david_martinez",
        "first_name": "David",
        "last_name": "Martinez",
        "email": "david.martinez@example.com",
        "password": "password123",
        "profile": "Family Manager"
    },
    {
        "user_id": "emma_thompson",
        "first_name": "Emma",
        "last_name": "Thompson",
        "email": "emma.thompson@example.com",
        "password": "password123",
        "profile": "Retiree"
    },
    {
        "user_id": "ryan_patel",
        "first_name": "Ryan",
        "last_name": "Patel",
        "email": "ryan.patel@example.com",
        "password": "password123",
        "profile": "Student"
    },
    {
        "user_id": "lisa_wong",
        "first_name": "Lisa",
        "last_name": "Wong",
        "email": "lisa.wong@example.com",
        "password": "password123",
        "profile": "Business Owner"
    }
]

# Account configurations for each user
ACCOUNT_CONFIGS = {
    "sarah_chen": [
        {"type": AccountType.CHECKING, "name": "Primary Checking", "balance": 5420.50},
        {"type": AccountType.SAVINGS, "name": "Emergency Fund", "balance": 15000.00}
    ],
    "david_martinez": [
        {"type": AccountType.CHECKING, "name": "Family Checking", "balance": 3240.75},
        {"type": AccountType.SAVINGS, "name": "Kids College Fund", "balance": 22500.00}
    ],
    "emma_thompson": [
        {"type": AccountType.CHECKING, "name": "Retirement Checking", "balance": 2890.25},
        {"type": AccountType.SAVINGS, "name": "Travel Savings", "balance": 8750.00}
    ],
    "ryan_patel": [
        {"type": AccountType.CHECKING, "name": "Student Checking", "balance": 890.50}
    ],
    "lisa_wong": [
        {"type": AccountType.CHECKING, "name": "Business Checking", "balance": 12450.00},
        {"type": AccountType.SAVINGS, "name": "Business Savings", "balance": 35000.00}
    ]
}

# Transaction templates
TRANSACTION_TEMPLATES = {
    "sarah_chen": [
        {"description": "Salary Deposit", "amount": 5500.00, "type": TransactionType.DEPOSIT, "category": "Income"},
        {"description": "Netflix Subscription", "amount": -15.99, "type": TransactionType.PURCHASE, "category": "Entertainment"},
        {"description": "Groceries - Whole Foods", "amount": -127.43, "type": TransactionType.PURCHASE, "category": "Groceries"},
        {"description": "Coffee Shop", "amount": -4.75, "type": TransactionType.PURCHASE, "category": "Food & Dining"},
        {"description": "Gym Membership", "amount": -89.99, "type": TransactionType.PURCHASE, "category": "Health & Fitness"},
    ],
    "david_martinez": [
        {"description": "Paycheck", "amount": 4200.00, "type": TransactionType.DEPOSIT, "category": "Income"},
        {"description": "Mortgage Payment", "amount": -1850.00, "type": TransactionType.BILL_PAYMENT, "category": "Housing"},
        {"description": "Utilities", "amount": -245.67, "type": TransactionType.BILL_PAYMENT, "category": "Utilities"},
        {"description": "School Supplies", "amount": -67.89, "type": TransactionType.PURCHASE, "category": "Education"},
        {"description": "Family Dinner", "amount": -89.50, "type": TransactionType.PURCHASE, "category": "Food & Dining"},
    ],
    "emma_thompson": [
        {"description": "Social Security", "amount": 1890.00, "type": TransactionType.DEPOSIT, "category": "Income"},
        {"description": "Retirement Fund", "amount": 2150.00, "type": TransactionType.DEPOSIT, "category": "Income"},
        {"description": "Pharmacy", "amount": -45.67, "type": TransactionType.PURCHASE, "category": "Healthcare"},
        {"description": "Book Club", "amount": -23.99, "type": TransactionType.PURCHASE, "category": "Entertainment"},
        {"description": "Travel Insurance", "amount": -156.00, "type": TransactionType.PURCHASE, "category": "Travel"},
    ],
    "ryan_patel": [
        {"description": "Part-time Job", "amount": 750.00, "type": TransactionType.DEPOSIT, "category": "Income"},
        {"description": "Textbooks", "amount": -234.50, "type": TransactionType.PURCHASE, "category": "Education"},
        {"description": "Coffee & Study", "amount": -12.45, "type": TransactionType.PURCHASE, "category": "Food & Dining"},
        {"description": "Bus Pass", "amount": -85.00, "type": TransactionType.PURCHASE, "category": "Transportation"},
    ],
    "lisa_wong": [
        {"description": "Business Revenue", "amount": 8900.00, "type": TransactionType.DEPOSIT, "category": "Business Income"},
        {"description": "Office Supplies", "amount": -234.56, "type": TransactionType.PURCHASE, "category": "Business Expenses"},
        {"description": "Marketing Campaign", "amount": -1200.00, "type": TransactionType.PURCHASE, "category": "Business Expenses"},
        {"description": "Business Lunch", "amount": -67.89, "type": TransactionType.PURCHASE, "category": "Meals & Entertainment"},
    ]
}

def create_sample_documents():
    """Create sample documents for the workshop"""
    docs_dir = os.path.join(project_root, 'data', 'sample_documents')
    os.makedirs(docs_dir, exist_ok=True)
    
    # Sample Scotiabank statement content
    scotia_content = """
SCOTIABANK STATEMENT
Account: *****1234
Statement Period: October 1-31, 2024

TRANSACTIONS:
Date        Description                 Amount      Balance
2024-10-01  Opening Balance                        $2,450.75
2024-10-02  Direct Deposit - Salary    +$3,200.00  $5,650.75
2024-10-03  Grocery Store              -$127.43    $5,523.32
2024-10-05  Coffee Shop                -$4.75      $5,518.57
2024-10-07  Gas Station                -$65.89     $5,452.68
2024-10-10  Restaurant                 -$89.50     $5,363.18
2024-10-15  Direct Deposit - Salary    +$3,200.00  $8,563.18
2024-10-18  Utility Bill               -$245.67    $8,317.51
2024-10-20  Online Purchase            -$156.99    $8,160.52
2024-10-25  ATM Withdrawal             -$100.00    $8,060.52
2024-10-30  Monthly Service Fee        -$12.95     $8,047.57

ACCOUNT SUMMARY:
Beginning Balance: $2,450.75
Total Credits: $6,400.00
Total Debits: $-803.18
Ending Balance: $8,047.57

For customer service, call 1-800-SCOTIA1
"""
    
    # Write sample document
    with open(os.path.join(docs_dir, 'scotiabank_statement_sample.txt'), 'w') as f:
        f.write(scotia_content)
    
    print(f"✅ Created sample documents in {docs_dir}")

async def create_sample_data():
    """Create all sample data for the workshop"""
    print("🏦 Creating Banking Bot Workshop Sample Data")
    print("=" * 50)
    
    # Initialize database manager
    db_manager = get_database_manager()
    await db_manager.initialize()
    
    # Initialize services
    user_service = UserService(db_manager)
    account_service = AccountService(db_manager)
    transaction_service = TransactionService(db_manager)
    
    try:
        # Create users
        print("👥 Creating workshop users...")
        created_users = {}
        
        for user_data in WORKSHOP_USERS:
            try:
                user_create = UserCreate(
                    user_id=user_data["user_id"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    email=user_data["email"],
                    password=user_data["password"]
                )
                user = await user_service.create_user(user_create)
                created_users[user_data["user_id"]] = user
                print(f"  ✅ Created user: {user_data['user_id']} ({user_data['profile']})")
            except Exception as e:
                print(f"  ⚠️  User {user_data['user_id']} might already exist: {str(e)}")
                # Try to get existing user
                try:
                    user = await user_service.get_user_by_user_id(user_data["user_id"])
                    created_users[user_data["user_id"]] = user
                    print(f"  ✅ Using existing user: {user_data['user_id']}")
                except:
                    print(f"  ❌ Failed to get user: {user_data['user_id']}")
                    continue
        
        # Create accounts
        print("\n💳 Creating accounts...")
        created_accounts = {}
        
        for user_id, account_configs in ACCOUNT_CONFIGS.items():
            if user_id not in created_users:
                continue
                
            created_accounts[user_id] = []
            for config in account_configs:
                try:
                    account_create = AccountCreate(
                        user_id=created_users[user_id].id,
                        account_type=config["type"],
                        account_name=config["name"],
                        balance=config["balance"]
                    )
                    account = await account_service.create_account(account_create)
                    created_accounts[user_id].append(account)
                    print(f"  ✅ Created {config['type'].value} account for {user_id}: ${config['balance']:,.2f}")
                except Exception as e:
                    print(f"  ❌ Failed to create account for {user_id}: {str(e)}")
        
        # Create transactions
        print("\n📊 Creating sample transactions...")
        total_transactions = 0
        
        for user_id, templates in TRANSACTION_TEMPLATES.items():
            if user_id not in created_accounts or not created_accounts[user_id]:
                continue
            
            # Use the first account for transactions
            account = created_accounts[user_id][0]
            
            for i, template in enumerate(templates):
                # Create transactions over the last 30 days
                transaction_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
                try:
                    transaction_create = TransactionCreate(
                        account_id=account.id,
                        amount=template["amount"],
                        transaction_type=template["type"],
                        description=template["description"],
                        category=template["category"],
                        transaction_date=transaction_date
                    )
                    
                    transaction = await transaction_service.create_transaction(transaction_create)
                    total_transactions += 1
                    
                    if i == 0:  # Only print first transaction per user to avoid spam
                        print(f"  ✅ Created transactions for {user_id} (${template['amount']:+.2f})")
                
                except Exception as e:
                    print(f"  ❌ Failed to create transaction for {user_id}: {str(e)}")
        
        # Create sample documents
        create_sample_documents()
        
        print(f"\n🎉 Sample data creation completed!")
        print(f"📊 Summary:")
        print(f"  • Users created: {len(created_users)}")
        print(f"  • Accounts created: {sum(len(accounts) for accounts in created_accounts.values())}")
        print(f"  • Transactions created: {total_transactions}")
        print(f"  • Sample documents: 1")
        
        print(f"\n🧪 Workshop Test Users (all with password 'password123'):")
        for user_data in WORKSHOP_USERS:
            if user_data["user_id"] in created_users:
                print(f"  • {user_data['user_id']} - {user_data['profile']}")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {str(e)}")
        raise
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(create_sample_data())
