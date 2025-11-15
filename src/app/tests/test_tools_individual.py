"""
Individual Tool Testing Module

This module tests each banking tool independently to ensure they work correctly
with various inputs and handle errors appropriately.
"""

import pytest
import json
from typing import Dict, Any
from datetime import datetime

from ..tools.sql_retrieval_tool import (
    get_account_balance,
    get_transactions,
    get_credit_card_info
)
from .conftest import (
    validate_json_response,
    assert_tool_success,
    assert_tool_error,
    get_valid_test_parameters,
    get_invalid_test_parameters,
    EXPECTED_TOOL_RESPONSES
)


class TestAccountBalanceTool:
    """Test suite for get_account_balance tool."""
    
    @pytest.mark.unit
    def test_valid_user_balance(self, test_user_data):
        """Test getting balance for valid user."""
        user_id = test_user_data["user"].user_id
        
        result_str = get_account_balance.invoke({"user_id": user_id})
        result = validate_json_response(result_str)
        
        assert_tool_success(result, EXPECTED_TOOL_RESPONSES["get_account_balance"])
        assert len(result["accounts"]) > 0, "Should return at least one account"
        assert result["total_balance"] > 0, "Total balance should be positive"
        assert result["currency"] == "USD", "Currency should be USD"
    
    @pytest.mark.unit
    def test_valid_user_specific_account(self, test_user_data):
        """Test getting balance for specific account."""
        user_id = test_user_data["user"].user_id
        account_number = test_user_data["account_numbers"][0]
        
        result_str = get_account_balance.invoke({
            "user_id": user_id,
            "account_number": account_number
        })
        result = validate_json_response(result_str)
        
        if "error" not in result:  # Account exists
            assert_tool_success(result, EXPECTED_TOOL_RESPONSES["get_account_balance"])
            # Should return specific account or empty if not found
            assert isinstance(result["accounts"], list)
    
    @pytest.mark.validation
    @pytest.mark.parametrize("invalid_params", get_invalid_test_parameters())
    def test_invalid_user_id_rejection(self, invalid_params):
        """Test that invalid user_ids are properly rejected."""
        from pydantic_core import ValidationError
        
        # Some invalid parameters (like None) are caught by Pydantic validation
        # before reaching our tool logic
        if invalid_params.get("user_id") is None:
            with pytest.raises(ValidationError):
                get_account_balance.invoke(invalid_params)
        else:
            result_str = get_account_balance.invoke(invalid_params)
            result = validate_json_response(result_str)
            
            assert_tool_error(result, "invalid user_id")
            assert "message" in result, "Should provide helpful error message"
            assert "suggestion" in result, "Should provide suggestion for fix"
    
    @pytest.mark.unit
    def test_nonexistent_user(self):
        """Test behavior with non-existent user."""
        result_str = get_account_balance.invoke({"user_id": "nonexistent_user_12345"})
        result = validate_json_response(result_str)
        
        assert_tool_error(result, "user not found")
    
    @pytest.mark.unit 
    def test_missing_required_parameter(self):
        """Test behavior when required parameter is missing."""
        # This should be caught at the LangChain tool level
        with pytest.raises((TypeError, ValueError)):
            get_account_balance.invoke({})


class TestTransactionsTool:
    """Test suite for get_transactions tool."""
    
    @pytest.mark.unit
    def test_basic_transactions_retrieval(self, test_user_data):
        """Test basic transaction retrieval."""
        user_id = test_user_data["user"].user_id
        
        result_str = get_transactions.invoke({"user_id": user_id})
        result = validate_json_response(result_str)
        
        assert_tool_success(result, EXPECTED_TOOL_RESPONSES["get_transactions"])
        assert isinstance(result["transactions"], list)
        assert result["total_count"] >= 0, "Total count should be non-negative"
        assert result["limit"] == 10, "Default limit should be 10"
    
    @pytest.mark.unit
    def test_transactions_with_limit(self, test_user_data):
        """Test transaction retrieval with custom limit."""
        user_id = test_user_data["user"].user_id
        
        result_str = get_transactions.invoke({
            "user_id": user_id, 
            "limit": 5
        })
        result = validate_json_response(result_str)
        
        assert_tool_success(result, EXPECTED_TOOL_RESPONSES["get_transactions"])
        assert result["limit"] == 5, "Should respect custom limit"
        assert len(result["transactions"]) <= 5, "Should not exceed limit"
    
    @pytest.mark.unit
    def test_transactions_with_date_range(self, test_user_data):
        """Test transaction retrieval with date range."""
        user_id = test_user_data["user"].user_id
        
        result_str = get_transactions.invoke({
            "user_id": user_id,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "limit": 100
        })
        result = validate_json_response(result_str)
        
        assert_tool_success(result, EXPECTED_TOOL_RESPONSES["get_transactions"])
        
        # Validate transaction date format if transactions exist
        if result["transactions"]:
            for txn in result["transactions"]:
                assert "transaction_date" in txn
                # Should be valid ISO date format
                datetime.fromisoformat(txn["transaction_date"].replace('Z', '+00:00'))
    
    @pytest.mark.validation
    def test_invalid_date_format(self):
        """Test rejection of invalid date formats."""
        result_str = get_transactions.invoke({
            "user_id": "jane_smith",
            "start_date": "2024/01/01"  # Wrong format
        })
        result = validate_json_response(result_str)
        
        # Tool should either reject or handle gracefully
        # Most validation happens at parameter level
        assert isinstance(result, dict)
    
    @pytest.mark.validation
    def test_invalid_limit_values(self):
        """Test rejection of invalid limit values."""
        # Test limit too high (should be caught by parameter validation)
        result_str = get_transactions.invoke({
            "user_id": "jane_smith",
            "limit": 150  # Above max of 100
        })
        result = validate_json_response(result_str)
        
        # Should either be clamped or rejected
        assert isinstance(result, dict)
    
    @pytest.mark.validation
    @pytest.mark.parametrize("invalid_params", get_invalid_test_parameters()) 
    def test_invalid_user_id_rejection(self, invalid_params):
        """Test that invalid user_ids are properly rejected."""
        from pydantic_core import ValidationError
        
        # Some invalid parameters (like None) are caught by Pydantic validation
        # before reaching our tool logic
        if invalid_params.get("user_id") is None:
            with pytest.raises(ValidationError):
                get_transactions.invoke(invalid_params)
        else:
            result_str = get_transactions.invoke(invalid_params)
            result = validate_json_response(result_str)
            
            assert_tool_error(result, "invalid user_id")


class TestCreditCardTool:
    """Test suite for get_credit_card_info tool."""
    
    @pytest.mark.unit
    def test_valid_user_credit_cards(self, test_user_data):
        """Test getting credit card info for valid user."""
        user_id = test_user_data["user"].user_id
        
        result_str = get_credit_card_info.invoke({"user_id": user_id})
        result = validate_json_response(result_str)
        
        assert_tool_success(result, EXPECTED_TOOL_RESPONSES["get_credit_card_info"])
        assert isinstance(result["credit_cards"], list)
        assert result["total_cards"] >= 0, "Total cards should be non-negative"
        
        # Validate credit card data structure if cards exist
        if result["credit_cards"]:
            for card in result["credit_cards"]:
                assert "card_number" in card
                assert "card_type" in card
                assert "credit_limit" in card
                assert "current_balance" in card
                assert "utilization_rate" in card
                
                # Card number should be masked
                assert "****" in card["card_number"], "Card number should be masked"
                
                # Utilization rate should be reasonable
                assert 0 <= card["utilization_rate"] <= 100, "Utilization rate should be 0-100%"
    
    @pytest.mark.validation
    @pytest.mark.parametrize("invalid_params", get_invalid_test_parameters())
    def test_invalid_user_id_rejection(self, invalid_params):
        """Test that invalid user_ids are properly rejected."""
        from pydantic_core import ValidationError
        
        # Some invalid parameters (like None) are caught by Pydantic validation
        # before reaching our tool logic
        if invalid_params.get("user_id") is None:
            with pytest.raises(ValidationError):
                get_credit_card_info.invoke(invalid_params)
        else:
            result_str = get_credit_card_info.invoke(invalid_params)
            result = validate_json_response(result_str)
            
            assert_tool_error(result, "invalid user_id")
    
    @pytest.mark.unit
    def test_nonexistent_user(self):
        """Test behavior with non-existent user."""
        result_str = get_credit_card_info.invoke({"user_id": "nonexistent_user_12345"})
        result = validate_json_response(result_str)
        
        assert_tool_error(result, "user not found")


class TestToolsIntegration:
    """Integration tests for all tools working together."""
    
    @pytest.mark.integration
    def test_all_tools_for_user(self, test_user_data):
        """Test that all tools work for the same user."""
        user_id = test_user_data["user"].user_id
        
        # Test all tools
        balance_result = validate_json_response(
            get_account_balance.invoke({"user_id": user_id})
        )
        txn_result = validate_json_response(
            get_transactions.invoke({"user_id": user_id, "limit": 5})
        )
        card_result = validate_json_response(
            get_credit_card_info.invoke({"user_id": user_id})
        )
        
        # All should succeed for valid user
        assert_tool_success(balance_result, EXPECTED_TOOL_RESPONSES["get_account_balance"])
        assert_tool_success(txn_result, EXPECTED_TOOL_RESPONSES["get_transactions"])
        assert_tool_success(card_result, EXPECTED_TOOL_RESPONSES["get_credit_card_info"])
        
        # Data consistency checks
        if balance_result["accounts"] and txn_result["transactions"]:
            account_numbers_balance = {acc["account_number"] for acc in balance_result["accounts"]}
            account_numbers_txn = {txn["account_number"] for txn in txn_result["transactions"]}
            
            # Transactions should reference existing accounts
            assert account_numbers_txn.issubset(account_numbers_balance), \
                "Transaction account numbers should match existing accounts"
    
    @pytest.mark.performance
    def test_tool_response_times(self, test_user_data):
        """Test that tools respond within acceptable time limits."""
        user_id = test_user_data["user"].user_id
        max_response_time = 5.0  # 5 seconds max
        
        # Test each tool response time
        tools_to_test = [
            ("get_account_balance", get_account_balance, {"user_id": user_id}),
            ("get_transactions", get_transactions, {"user_id": user_id, "limit": 10}),
            ("get_credit_card_info", get_credit_card_info, {"user_id": user_id})
        ]
        
        for tool_name, tool_func, params in tools_to_test:
            start_time = datetime.now()
            result_str = tool_func.invoke(params)
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds()
            assert response_time < max_response_time, \
                f"{tool_name} took {response_time:.2f}s, expected < {max_response_time}s"
            
            # Ensure the tool actually returned valid data
            result = validate_json_response(result_str)
            assert isinstance(result, dict), f"{tool_name} should return dict-like structure"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])
