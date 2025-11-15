"""
Shared test configuration and fixtures for Banking Bot tests.

This module provides common setup, fixtures, and utilities used across all test modules.
"""

import pytest
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import asyncio
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.app.database.database import get_db
from src.app.models.database_models import User, Account, Transaction, CreditCard

# Test configuration
TEST_CONFIG = {
    "test_user_id": "jane_smith",
    "test_user_invalid": "user_id", 
    "test_thread_prefix": "test_thread_",
    "database_timeout": 5.0,
    "agent_timeout": 30.0,
    "expected_accounts": 2,
    "expected_transactions_min": 50,
    "expected_credit_cards": 1
}

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration across all tests."""
    return TEST_CONFIG

@pytest.fixture(scope="session")
def database_connection():
    """Provide database connection for tests."""
    try:
        db = next(get_db())
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def test_user_data(database_connection):
    """Get test user data from database."""
    db = database_connection
    user = db.query(User).filter(User.user_id == TEST_CONFIG["test_user_id"]).first()
    
    if not user:
        pytest.skip(f"Test user {TEST_CONFIG['test_user_id']} not found in database")
    
    accounts = db.query(Account).filter(Account.user_id == user.id, Account.is_active == True).all()
    transactions = db.query(Transaction).join(Account).filter(Account.user_id == user.id).all()
    credit_cards = db.query(CreditCard).filter(CreditCard.user_id == user.id, CreditCard.is_active == True).all()
    
    return {
        "user": user,
        "accounts": accounts,
        "transactions": transactions,
        "credit_cards": credit_cards,
        "account_numbers": [acc.account_number for acc in accounts],
        "total_balance": sum(acc.balance for acc in accounts)
    }

@pytest.fixture(scope="module")
def banking_agent():
    """Provide banking agent instance for tests."""
    # Lazy import to avoid warnings in non-agent tests
    from src.app.agents.banking_agent import BankingAgent
    return BankingAgent()

@pytest.fixture
def test_thread_id():
    """Generate unique test thread ID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{TEST_CONFIG['test_thread_prefix']}{timestamp}"

# Helper functions for tests
def validate_json_response(response_str: str) -> Dict[str, Any]:
    """Validate and parse JSON response from tools."""
    try:
        return eval(response_str) if isinstance(response_str, str) else response_str
    except:
        import json
        return json.loads(response_str)

def assert_tool_success(result: Dict[str, Any], expected_keys: List[str]):
    """Assert that tool result is successful and contains expected keys."""
    assert "error" not in result, f"Tool returned error: {result.get('error')}"
    for key in expected_keys:
        assert key in result, f"Missing expected key '{key}' in tool result"

def assert_tool_error(result: Dict[str, Any], expected_error_type: str = None):
    """Assert that tool result contains expected error."""
    assert "error" in result, "Expected tool to return error but it didn't"
    if expected_error_type:
        error_msg = result["error"].lower()
        assert expected_error_type.lower() in error_msg, f"Expected error type '{expected_error_type}' not found in '{error_msg}'"

def get_valid_test_parameters():
    """Get valid test parameters for tool testing."""
    return {
        "user_id": TEST_CONFIG["test_user_id"],
        "account_number": None,  # Will be filled with actual account number in tests
        "limit": 10,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "transaction_type": "debit"
    }

def get_invalid_test_parameters():
    """Get invalid test parameters for validation testing."""
    return [
        {"user_id": ""},  # Empty user_id
        {"user_id": "user_id"},  # Placeholder user_id
        {"user_id": "your_user_id"},  # Another placeholder
        {"user_id": "placeholder"},  # Generic placeholder
        {"user_id": None},  # None user_id
    ]

# Test categories for organization
class TestCategories:
    UNIT = "unit"
    INTEGRATION = "integration"
    VALIDATION = "validation"
    DATABASE = "database"
    AGENT = "agent"
    PERFORMANCE = "performance"

# Pytest markers for test categorization
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for system components")
    config.addinivalue_line("markers", "validation: Parameter and schema validation tests")
    config.addinivalue_line("markers", "database: Database connectivity and query tests")
    config.addinivalue_line("markers", "agent: End-to-end agent behavior tests")
    config.addinivalue_line("markers", "performance: Performance and load tests")
    config.addinivalue_line("markers", "slow: Tests that take more than 5 seconds")

# Test data for consistent testing
SAMPLE_TEST_MESSAGES = [
    "What's my account balance?",
    "Show me my recent transactions",
    "What's my credit card information?",
    "Give me my balance of all accounts, my user id, and my email?",
    "Show me transactions from last month",
    "What's my checking account balance?"
]

EXPECTED_TOOL_RESPONSES = {
    "get_account_balance": ["accounts", "total_balance", "currency", "as_of_date"],
    "get_transactions": ["transactions", "total_count", "limit"],
    "get_credit_card_info": ["credit_cards", "total_cards"]
}

# Export commonly used test utilities
__all__ = [
    "TEST_CONFIG",
    "validate_json_response", 
    "assert_tool_success",
    "assert_tool_error",
    "get_valid_test_parameters",
    "get_invalid_test_parameters",
    "TestCategories",
    "SAMPLE_TEST_MESSAGES",
    "EXPECTED_TOOL_RESPONSES"
]
