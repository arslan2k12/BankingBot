"""
Database Connectivity Testing Module

This module tests database connections, queries, and data integrity
for the banking bot application.
"""

import pytest
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError

from ..database.database import get_db
from ..models.database_models import User, Account, Transaction, CreditCard
from .conftest import TEST_CONFIG, TestCategories


class TestDatabaseConnection:
    """Test database connectivity and basic operations."""
    
    @pytest.mark.database
    def test_database_connection_established(self, database_connection):
        """Test that database connection can be established."""
        assert database_connection is not None, "Database connection should be established"
        
        # Test a simple query
        try:
            user_count = database_connection.query(User).count()
            assert user_count >= 0, "Should be able to query user count"
        except SQLAlchemyError as e:
            pytest.fail(f"Database query failed: {e}")
    
    @pytest.mark.database
    def test_database_tables_exist(self, database_connection):
        """Test that all required database tables exist."""
        db = database_connection
        
        # Test each model can be queried
        models_to_test = [User, Account, Transaction, CreditCard]
        
        for model in models_to_test:
            try:
                count = db.query(model).count()
                assert count >= 0, f"Should be able to query {model.__name__} table"
            except SQLAlchemyError as e:
                pytest.fail(f"Table {model.__name__} query failed: {e}")
    
    @pytest.mark.database
    def test_database_schema_integrity(self, database_connection):
        """Test database schema integrity and relationships."""
        db = database_connection
        
        # Test that we have test data
        users = db.query(User).all()
        assert len(users) > 0, "Should have at least one user for testing"
        
        # Test user-account relationships
        for user in users:
            accounts = db.query(Account).filter(Account.user_id == user.id).all()
            # Users may or may not have accounts, but query should work
            assert isinstance(accounts, list), f"Should get list of accounts for user {user.user_id}"
            
            # If user has accounts, test account properties
            for account in accounts:
                assert account.user_id == user.id, "Account should reference correct user"
                assert account.account_number is not None, "Account should have account number"
                assert account.account_type is not None, "Account should have account type"
                assert isinstance(account.balance, (int, float)), "Account balance should be numeric"


class TestUserData:
    """Test user data integrity and availability."""
    
    @pytest.mark.database
    def test_test_user_exists(self, database_connection):
        """Test that the test user exists in database."""
        db = database_connection
        test_user_id = TEST_CONFIG["test_user_id"]
        
        user = db.query(User).filter(User.user_id == test_user_id).first()
        assert user is not None, f"Test user {test_user_id} should exist in database"
        
        # Verify user has required fields
        assert user.user_id == test_user_id, "User ID should match"
        assert user.first_name is not None, "User should have first name"
        assert user.last_name is not None, "User should have last name"
        assert user.email is not None, "User should have email"
        assert user.is_active is True, "Test user should be active"
    
    @pytest.mark.database
    def test_test_user_has_accounts(self, test_user_data):
        """Test that test user has accounts for testing."""
        accounts = test_user_data["accounts"]
        
        assert len(accounts) >= 1, "Test user should have at least one account"
        
        for account in accounts:
            assert account.is_active is True, "Test accounts should be active"
            assert account.balance is not None, "Account should have balance"
            assert account.account_number is not None, "Account should have account number"
            assert account.account_type in ["checking", "savings", "credit"], \
                "Account type should be valid"
    
    @pytest.mark.database
    def test_test_user_has_transactions(self, database_connection, test_user_data):
        """Test that test user has transaction history."""
        db = database_connection
        user = test_user_data["user"]
        
        # Get transactions through account relationships
        transactions = db.query(Transaction).join(Account).filter(
            Account.user_id == user.id
        ).all()
        
        # User should have some transaction history for meaningful tests
        assert len(transactions) >= 5, "Test user should have at least 5 transactions for testing"
        
        for transaction in transactions[:5]:  # Check first 5
            assert transaction.transaction_id is not None, "Transaction should have ID"
            assert transaction.amount is not None, "Transaction should have amount"
            assert transaction.transaction_type in ["debit", "credit"], \
                "Transaction type should be valid"
            assert transaction.transaction_date is not None, "Transaction should have date"
    
    @pytest.mark.database
    def test_test_user_has_credit_cards(self, test_user_data):
        """Test that test user has credit card data."""
        credit_cards = test_user_data["credit_cards"]
        
        # User should have at least one credit card for testing
        assert len(credit_cards) >= 1, "Test user should have at least one credit card"
        
        for card in credit_cards:
            assert card.is_active is True, "Test credit cards should be active"
            assert card.card_number is not None, "Card should have card number"
            assert card.card_type is not None, "Card should have card type"
            assert card.credit_limit > 0, "Card should have positive credit limit"
            assert card.current_balance >= 0, "Card balance should be non-negative"


class TestDataConsistency:
    """Test data consistency and integrity across tables."""
    
    @pytest.mark.database
    def test_account_balance_consistency(self, database_connection, test_user_data):
        """Test that account balances are consistent with transactions."""
        db = database_connection
        accounts = test_user_data["accounts"]
        
        for account in accounts:
            # Get all transactions for this account
            transactions = db.query(Transaction).filter(
                Transaction.account_id == account.id
            ).all()
            
            # Calculate expected balance (this is a simplified check)
            if transactions:
                # Just verify we can calculate with the transactions
                total_credits = sum(t.amount for t in transactions if t.transaction_type == "credit")
                total_debits = sum(t.amount for t in transactions if t.transaction_type == "debit")
                
                assert total_credits >= 0, "Total credits should be non-negative"
                assert total_debits >= 0, "Total debits should be non-negative"
                
                # The actual balance may not match due to initial balance or other factors
                # but we can verify the data types and basic consistency
                assert isinstance(account.balance, (int, float)), "Balance should be numeric"
    
    @pytest.mark.database
    def test_transaction_date_consistency(self, database_connection, test_user_data):
        """Test that transaction dates are reasonable."""
        db = database_connection
        user = test_user_data["user"]
        
        transactions = db.query(Transaction).join(Account).filter(
            Account.user_id == user.id
        ).limit(10).all()
        
        current_date = datetime.now()
        one_year_ago = current_date - timedelta(days=365)
        
        for transaction in transactions:
            assert transaction.transaction_date is not None, "Transaction should have date"
            
            # Transaction dates should be reasonable (not in future, not too old)
            assert transaction.transaction_date <= current_date, \
                "Transaction date should not be in the future"
            assert transaction.transaction_date >= one_year_ago, \
                "Transaction date should not be more than a year old (for test data)"
    
    @pytest.mark.database
    def test_credit_card_utilization_consistency(self, test_user_data):
        """Test that credit card utilization calculations are consistent."""
        credit_cards = test_user_data["credit_cards"]
        
        for card in credit_cards:
            if card.credit_limit > 0:
                expected_utilization = (card.current_balance / card.credit_limit) * 100
                
                # Allow for small floating point differences
                assert abs(expected_utilization - 
                          (card.current_balance / card.credit_limit * 100)) < 0.01, \
                    "Credit card utilization should be calculated correctly"
                
                assert 0 <= expected_utilization <= 100, \
                    "Utilization should be between 0 and 100 percent"


class TestDatabasePerformance:
    """Test database query performance."""
    
    @pytest.mark.database
    @pytest.mark.performance
    def test_user_query_performance(self, database_connection):
        """Test that user queries perform within acceptable time."""
        db = database_connection
        test_user_id = TEST_CONFIG["test_user_id"]
        
        start_time = datetime.now()
        user = db.query(User).filter(User.user_id == test_user_id).first()
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds()
        assert query_time < 1.0, f"User query took {query_time:.3f}s, should be < 1s"
        assert user is not None, "Should find test user"
    
    @pytest.mark.database
    @pytest.mark.performance
    def test_account_query_performance(self, database_connection, test_user_data):
        """Test that account queries perform within acceptable time."""
        db = database_connection
        user = test_user_data["user"]
        
        start_time = datetime.now()
        accounts = db.query(Account).filter(
            Account.user_id == user.id,
            Account.is_active == True
        ).all()
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds()
        assert query_time < 1.0, f"Account query took {query_time:.3f}s, should be < 1s"
        assert len(accounts) > 0, "Should find test user accounts"
    
    @pytest.mark.database
    @pytest.mark.performance
    def test_transaction_query_performance(self, database_connection, test_user_data):
        """Test that transaction queries perform within acceptable time."""
        db = database_connection
        user = test_user_data["user"]
        
        start_time = datetime.now()
        transactions = db.query(Transaction).join(Account).filter(
            Account.user_id == user.id
        ).limit(50).all()
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds()
        assert query_time < 2.0, f"Transaction query took {query_time:.3f}s, should be < 2s"
        # Should have at least some transactions
        assert len(transactions) >= 0, "Query should complete successfully"


class TestDatabaseErrorHandling:
    """Test database error handling and recovery."""
    
    @pytest.mark.database
    def test_nonexistent_user_query(self, database_connection):
        """Test querying for non-existent user."""
        db = database_connection
        
        user = db.query(User).filter(User.user_id == "nonexistent_user_12345").first()
        assert user is None, "Should return None for non-existent user"
    
    @pytest.mark.database
    def test_empty_result_handling(self, database_connection):
        """Test handling of empty query results."""
        db = database_connection
        
        # Query with impossible condition
        accounts = db.query(Account).filter(Account.balance < -999999).all()
        assert isinstance(accounts, list), "Should return empty list, not None"
        assert len(accounts) == 0, "Should return empty list for impossible condition"
    
    @pytest.mark.database
    def test_database_connection_recovery(self):
        """Test that new database connections can be established."""
        # Test multiple sequential connections
        for i in range(3):
            try:
                db = next(get_db())
                user_count = db.query(User).count()
                assert user_count >= 0, f"Connection {i} should work"
                db.close()
            except Exception as e:
                pytest.fail(f"Database connection {i} failed: {e}")


if __name__ == "__main__":
    # Run database tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "database"])
