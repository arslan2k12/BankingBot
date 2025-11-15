from langchain.tools import tool
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta
import json

from ..database.database import get_db
from ..models.database_models import User, Account, Transaction, CreditCard
from ..utils.logger_utils import get_logger

logger = get_logger(__name__)

@tool
def get_account_balance(user_id: str, account_number: Optional[str] = None) -> str:
    """Get account balance information for a user.
    
    Args:
        user_id: The user ID to get balance for (must be an actual user ID from the database, not a placeholder)
        account_number: Optional specific account number to check
    
    Returns:
        JSON string with account balances
    """
    logger.info(f"💰 TOOL CALLED: get_account_balance for user_id='{user_id}', account_number='{account_number}'")
    
    # Validate user_id parameter - reject common placeholder values
    invalid_user_ids = ['user_id', 'your_user_id', 'none', 'null', '', 'placeholder', 'example', 'test_user', 'userid', 'authenticated_user']
    if not user_id or user_id.lower() in invalid_user_ids:
        logger.error(f"❌ Invalid user_id parameter: '{user_id}'. Cannot proceed with tool call.")
        return json.dumps({
            "error": "Invalid user_id parameter",
            "message": f"The user_id '{user_id}' appears to be a placeholder or invalid. I need the actual authenticated user's ID to check their account balance.",
            "user_id": user_id,
            "suggestion": "The user is already authenticated - please use their actual user_id from the authentication context, not a placeholder."
        })
    
    try:
        db = next(get_db())
        logger.info("🔗 Database connection established")
        
        # First, get the user
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            logger.warning(f"❌ User not found: {user_id}")
            return json.dumps({
                "error": "User not found", 
                "user_id": user_id,
                "message": f"No user found with ID '{user_id}'. Please verify the user ID is correct.",
                "suggestion": "Ask user to verify their user ID or provide account number instead."
            })
        
        logger.info(f"👤 User found: {user.first_name} {user.last_name} (ID: {user.id})")
        
        query = db.query(Account).filter(Account.user_id == user.id, Account.is_active == True)
        
        if account_number:
            query = query.filter(Account.account_number == account_number)
            logger.info(f"🔍 Filtering by specific account number: {account_number}")
        
        accounts = query.all()
        logger.info(f"🏦 Found {len(accounts)} active accounts")
        
        balances = []
        total_balance = 0
        
        for i, account in enumerate(accounts):
            logger.info(f"   💳 Account {i+1}: {account.account_number} ({account.account_type}) - ${account.balance}")
            balance_info = {
                "account_number": account.account_number,
                "account_type": account.account_type,
                "balance": account.balance,
                "currency": account.currency
            }
            balances.append(balance_info)
            total_balance += account.balance
        
        result = {
            "accounts": balances,
            "total_balance": total_balance,
            "currency": "USD",
            "as_of_date": datetime.now().isoformat()
        }
        
        logger.info(f"Balance retrieval successful for user {user_id}")
        return json.dumps(result, default=str)
        
    except Exception as e:
        logger.error(f"Balance retrieval error: {str(e)}")
        return json.dumps({"error": f"Database query failed: {str(e)}"})
    finally:
        db.close()

@tool
def get_transactions(user_id: str, account_number: Optional[str] = None, 
                    limit: int = 10, start_date: Optional[str] = None,
                    end_date: Optional[str] = None, transaction_type: Optional[str] = None) -> str:
    """Get transaction history for a user.
    
    Args:
        user_id: The user ID to get transactions for (must be an actual user ID from the database)
        account_number: Optional specific account number
        limit: Number of transactions to return (default 10)
        start_date: Optional start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
        transaction_type: Optional transaction type filter
    
    Returns:
        JSON string with transaction history
    """
    logger.info(f"📊 TOOL CALLED: get_transactions for user_id='{user_id}', account_number='{account_number}'")
    
    # Validate user_id parameter - reject common placeholder values
    invalid_user_ids = ['user_id', 'your_user_id', 'none', 'null', '', 'placeholder', 'example', 'test_user', 'userid', 'authenticated_user']
    if not user_id or user_id.lower() in invalid_user_ids:
        logger.error(f"❌ Invalid user_id parameter: '{user_id}'. Cannot proceed with tool call.")
        return json.dumps({
            "error": "Invalid user_id parameter",
            "message": f"The user_id '{user_id}' appears to be a placeholder or invalid. I need the actual authenticated user's ID to check their transactions.",
            "user_id": user_id,
            "suggestion": "The user is already authenticated - please use their actual user_id from the authentication context, not a placeholder."
        })
    
    try:
        db = next(get_db())
        
        # First, get the user
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return json.dumps({"error": "User not found", "user_id": user_id})
        
        # Get user's accounts first
        accounts_query = db.query(Account).filter(Account.user_id == user.id, Account.is_active == True)
        
        if account_number:
            accounts_query = accounts_query.filter(Account.account_number == account_number)
        
        accounts = accounts_query.all()
        account_ids = [acc.id for acc in accounts]
        
        if not account_ids:
            return json.dumps({"transactions": [], "total_count": 0})
        
        # Build transaction query
        query = db.query(Transaction).filter(Transaction.account_id.in_(account_ids))
        
        # Apply filters
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
        
        # Get total count
        total_count = query.count()
        
        # Get transactions with limit
        transactions = query.order_by(desc(Transaction.transaction_date)).limit(limit).all()
        
        transaction_list = []
        for txn in transactions:
            # Get account info for this transaction
            account = next((acc for acc in accounts if acc.id == txn.account_id), None)
            
            transaction_info = {
                "transaction_id": txn.transaction_id,
                "account_number": account.account_number if account else "Unknown",
                "transaction_type": txn.transaction_type,
                "amount": txn.amount,
                "description": txn.description,
                "category": txn.category,
                "merchant": txn.merchant,
                "transaction_date": txn.transaction_date.isoformat(),
                "created_at": txn.created_at.isoformat()
            }
            transaction_list.append(transaction_info)
        
        result = {
            "transactions": transaction_list,
            "total_count": total_count,
            "limit": limit,
            "account_filter": account_number
        }
        
        logger.info(f"Transaction retrieval successful for user {user_id}")
        return json.dumps(result, default=str)
        
    except Exception as e:
        logger.error(f"Transaction retrieval error: {str(e)}")
        return json.dumps({"error": f"Database query failed: {str(e)}"})
    finally:
        db.close()

@tool
def get_credit_card_info(user_id: str) -> str:
    """Get credit card information for a user.
    
    Args:
        user_id: The user ID to get credit card info for (must be an actual user ID from the database)
    
    Returns:
        JSON string with credit card information
    """
    logger.info(f"💳 TOOL CALLED: get_credit_card_info for user_id='{user_id}'")
    
    # Validate user_id parameter - reject common placeholder values
    invalid_user_ids = ['user_id', 'your_user_id', 'none', 'null', '', 'placeholder', 'example', 'test_user', 'userid', 'authenticated_user']
    if not user_id or user_id.lower() in invalid_user_ids:
        logger.error(f"❌ Invalid user_id parameter: '{user_id}'. Cannot proceed with tool call.")
        return json.dumps({
            "error": "Invalid user_id parameter",
            "message": f"The user_id '{user_id}' appears to be a placeholder or invalid. I need the actual authenticated user's ID to check their credit card information.",
            "user_id": user_id,
            "suggestion": "The user is already authenticated - please use their actual user_id from the authentication context, not a placeholder."
        })
    
    try:
        db = next(get_db())
        logger.info("🔗 Database connection established")
        
        # First, get the user
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            logger.warning(f"❌ User not found: {user_id}")
            return json.dumps({
                "error": "User not found", 
                "user_id": user_id,
                "message": f"No user found with ID '{user_id}'. Please verify the user ID is correct.",
                "suggestion": "Ask user to verify their user ID."
            })
        
        credit_cards = db.query(CreditCard).filter(
            CreditCard.user_id == user.id, 
            CreditCard.is_active == True
        ).all()
        
        cards = []
        for card in credit_cards:
            card_info = {
                "card_number": f"****-****-****-{card.card_number[-4:]}" if len(card.card_number) >= 4 else card.card_number,
                "card_type": card.card_type,
                "credit_limit": card.credit_limit,
                "current_balance": card.current_balance,
                "available_credit": card.available_credit or (card.credit_limit - card.current_balance),
                "minimum_payment": card.minimum_payment,
                "due_date": card.due_date.isoformat() if card.due_date else None,
                "utilization_rate": round((card.current_balance / card.credit_limit) * 100, 2) if card.credit_limit > 0 else 0
            }
            cards.append(card_info)
        
        result = {
            "credit_cards": cards,
            "total_cards": len(cards)
        }
        
        logger.info(f"Credit card retrieval successful for user {user_id}")
        return json.dumps(result, default=str)
        
    except Exception as e:
        logger.error(f"Credit card retrieval error: {str(e)}")
        return json.dumps({"error": f"Database query failed: {str(e)}"})
    finally:
        db.close()
