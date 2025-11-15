"""
Parameter Enhancement and Validation Testing Module

This module tests comprehensive parameter validation, enhancement rules,
and error handling for all banking tools.
"""

import pytest
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .conftest import validate_json_response, TestCategories


@dataclass
class ParameterValidation:
    """Parameter validation result."""
    is_valid: bool
    parameter_name: str
    value: Any
    error_message: Optional[str] = None
    suggestion: Optional[str] = None


class ParameterValidator:
    """Comprehensive parameter validation for banking tools."""
    
    # Validation rules for all tools
    VALIDATION_RULES = {
        "get_account_balance": {
            "required": ["user_id"],
            "optional": ["account_number"],
            "rules": {
                "user_id": {
                    "type": str,
                    "min_length": 1,
                    "invalid_values": ['user_id', 'your_user_id', 'none', 'null', '', 'placeholder', 'example', 'test_user', 'userid'],
                    "description": "Valid authenticated user ID from database"
                },
                "account_number": {
                    "type": [str, type(None)],
                    "pattern": r"^[A-Z0-9]{1,20}$",
                    "description": "Optional account number filter"
                }
            }
        },
        "get_transactions": {
            "required": ["user_id"],
            "optional": ["account_number", "limit", "start_date", "end_date", "transaction_type"],
            "rules": {
                "user_id": {
                    "type": str,
                    "min_length": 1,
                    "invalid_values": ['user_id', 'your_user_id', 'none', 'null', '', 'placeholder', 'example', 'test_user', 'userid'],
                    "description": "Valid authenticated user ID"
                },
                "account_number": {
                    "type": [str, type(None)],
                    "pattern": r"^[A-Z0-9]{1,20}$",
                    "description": "Optional account number filter"
                },
                "limit": {
                    "type": int,
                    "min_value": 1,
                    "max_value": 100,
                    "default": 10,
                    "description": "Number of transactions to return"
                },
                "start_date": {
                    "type": [str, type(None)],
                    "pattern": r"^\d{4}-\d{2}-\d{2}$",
                    "description": "Start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": [str, type(None)],
                    "pattern": r"^\d{4}-\d{2}-\d{2}$",
                    "description": "End date in YYYY-MM-DD format"
                },
                "transaction_type": {
                    "type": [str, type(None)],
                    "allowed_values": ["debit", "credit", None],
                    "description": "Transaction type filter"
                }
            }
        },
        "get_credit_card_info": {
            "required": ["user_id"],
            "optional": [],
            "rules": {
                "user_id": {
                    "type": str,
                    "min_length": 1,
                    "invalid_values": ['user_id', 'your_user_id', 'none', 'null', '', 'placeholder', 'example', 'test_user', 'userid'],
                    "description": "Valid authenticated user ID"
                }
            }
        }
    }
    
    def validate_parameter(self, param_name: str, value: Any, validation_rules: Dict[str, Any]) -> ParameterValidation:
        """Validate a single parameter against its rules."""
        
        # Type validation
        expected_type = validation_rules.get("type")
        if expected_type:
            if isinstance(expected_type, list):
                if not any(isinstance(value, t) for t in expected_type):
                    return ParameterValidation(
                        False, param_name, value,
                        f"Expected type {expected_type}, got {type(value).__name__}",
                        f"Provide value of type {expected_type}"
                    )
            else:
                if not isinstance(value, expected_type):
                    return ParameterValidation(
                        False, param_name, value,
                        f"Expected type {expected_type.__name__}, got {type(value).__name__}",
                        f"Provide value of type {expected_type.__name__}"
                    )
        
        # Skip further validation if value is None and that's allowed
        if value is None and (isinstance(expected_type, list) and type(None) in expected_type):
            return ParameterValidation(True, param_name, value)
        
        # String-specific validations
        if isinstance(value, str):
            # Min length validation
            min_length = validation_rules.get("min_length")
            if min_length and len(value) < min_length:
                return ParameterValidation(
                    False, param_name, value,
                    f"Minimum length {min_length}, got {len(value)}",
                    f"Provide string with at least {min_length} characters"
                )
            
            # Invalid values validation
            invalid_values = validation_rules.get("invalid_values", [])
            if value.lower() in [iv.lower() for iv in invalid_values]:
                return ParameterValidation(
                    False, param_name, value,
                    f"Value '{value}' is a placeholder or invalid",
                    "Provide the actual authenticated user ID, not a placeholder"
                )
            
            # Pattern validation
            pattern = validation_rules.get("pattern")
            if pattern and not re.match(pattern, value):
                return ParameterValidation(
                    False, param_name, value,
                    f"Value '{value}' doesn't match required pattern {pattern}",
                    f"Provide value matching pattern {pattern}"
                )
            
            # Allowed values validation
            allowed_values = validation_rules.get("allowed_values")
            if allowed_values and value not in allowed_values:
                return ParameterValidation(
                    False, param_name, value,
                    f"Value '{value}' not in allowed values {allowed_values}",
                    f"Use one of: {allowed_values}"
                )
        
        # Integer-specific validations
        if isinstance(value, int):
            min_value = validation_rules.get("min_value")
            max_value = validation_rules.get("max_value")
            
            if min_value and value < min_value:
                return ParameterValidation(
                    False, param_name, value,
                    f"Value {value} below minimum {min_value}",
                    f"Provide value >= {min_value}"
                )
            
            if max_value and value > max_value:
                return ParameterValidation(
                    False, param_name, value,
                    f"Value {value} above maximum {max_value}",
                    f"Provide value <= {max_value}"
                )
        
        return ParameterValidation(True, param_name, value)
    
    def validate_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> List[ParameterValidation]:
        """Validate all parameters for a tool."""
        if tool_name not in self.VALIDATION_RULES:
            return [ParameterValidation(False, "tool_name", tool_name, f"Unknown tool: {tool_name}")]
        
        tool_rules = self.VALIDATION_RULES[tool_name]
        validations = []
        
        # Check required parameters
        for required_param in tool_rules["required"]:
            if required_param not in parameters:
                validations.append(ParameterValidation(
                    False, required_param, None,
                    f"Required parameter '{required_param}' missing",
                    f"Provide required parameter '{required_param}'"
                ))
            else:
                param_value = parameters[required_param]
                param_rules = tool_rules["rules"].get(required_param, {})
                validation = self.validate_parameter(required_param, param_value, param_rules)
                validations.append(validation)
        
        # Check optional parameters
        for param_name, param_value in parameters.items():
            if param_name not in tool_rules["required"]:
                param_rules = tool_rules["rules"].get(param_name, {})
                if param_rules:  # Only validate if we have rules for it
                    validation = self.validate_parameter(param_name, param_value, param_rules)
                    validations.append(validation)
        
        return validations


class TestParameterValidation:
    """Test suite for parameter validation."""
    
    def setup_method(self):
        """Setup parameter validator for each test."""
        self.validator = ParameterValidator()
    
    @pytest.mark.validation
    @pytest.mark.parametrize("tool_name,parameters,expected_valid", [
        # Valid parameter sets
        ("get_account_balance", {"user_id": "jane_smith"}, True),
        ("get_account_balance", {"user_id": "jane_smith", "account_number": "ACC001"}, True),
        ("get_transactions", {"user_id": "jane_smith"}, True),
        ("get_transactions", {"user_id": "jane_smith", "limit": 5, "start_date": "2024-01-01"}, True),
        ("get_credit_card_info", {"user_id": "jane_smith"}, True),
        
        # Invalid parameter sets
        ("get_account_balance", {"user_id": ""}, False),  # Empty user_id
        ("get_account_balance", {"user_id": "user_id"}, False),  # Placeholder user_id
        ("get_account_balance", {}, False),  # Missing user_id
        ("get_transactions", {"user_id": "jane_smith", "limit": 150}, False),  # Limit too high
        ("get_transactions", {"user_id": "jane_smith", "start_date": "2024/01/01"}, False),  # Wrong date format
        ("get_transactions", {"user_id": "your_user_id"}, False),  # Placeholder user_id
        ("get_credit_card_info", {"user_id": "placeholder"}, False),  # Placeholder user_id
    ])
    def test_parameter_validation(self, tool_name, parameters, expected_valid):
        """Test parameter validation for various input combinations."""
        validations = self.validator.validate_tool_parameters(tool_name, parameters)
        
        # Check if any validation failed
        has_errors = any(not v.is_valid for v in validations)
        
        if expected_valid:
            assert not has_errors, f"Expected valid parameters but got errors: {[v.error_message for v in validations if not v.is_valid]}"
        else:
            assert has_errors, f"Expected invalid parameters but validation passed"
    
    @pytest.mark.validation
    def test_placeholder_user_id_detection(self):
        """Test detection of placeholder user_id values."""
        placeholder_values = [
            'user_id', 'your_user_id', 'none', 'null',
            'placeholder', 'example', 'test_user', 'userid'
        ]
        
        for placeholder in placeholder_values:
            validations = self.validator.validate_tool_parameters(
                "get_account_balance",
                {"user_id": placeholder}
            )
            
            user_id_validation = next(v for v in validations if v.parameter_name == "user_id")
            assert not user_id_validation.is_valid, f"Placeholder '{placeholder}' should be rejected"
            assert "placeholder" in user_id_validation.error_message.lower(), \
                f"Error message should mention placeholder for '{placeholder}'"
        
        # Test empty string separately (different error message)
        validations = self.validator.validate_tool_parameters(
            "get_account_balance",
            {"user_id": ""}
        )
        user_id_validation = next(v for v in validations if v.parameter_name == "user_id")
        assert not user_id_validation.is_valid, "Empty string should be rejected"
        assert "minimum length" in user_id_validation.error_message.lower(), \
            "Error message should mention minimum length for empty string"    @pytest.mark.validation
    def test_date_format_validation(self):
        """Test date format validation."""
        valid_dates = ["2024-01-01", "2024-12-31", "2023-06-15"]
        invalid_dates = ["2024/01/01", "01-01-2024", "Jan 1, 2024", "2024-1-1", ""]
        
        for date in valid_dates:
            validations = self.validator.validate_tool_parameters(
                "get_transactions",
                {"user_id": "jane_smith", "start_date": date}
            )
            date_validation = next(v for v in validations if v.parameter_name == "start_date")
            assert date_validation.is_valid, f"Valid date '{date}' should pass validation"
        
        for date in invalid_dates:
            validations = self.validator.validate_tool_parameters(
                "get_transactions",
                {"user_id": "jane_smith", "start_date": date}
            )
            date_validation = next(v for v in validations if v.parameter_name == "start_date")
            assert not date_validation.is_valid, f"Invalid date '{date}' should fail validation"
    
    @pytest.mark.validation
    def test_limit_range_validation(self):
        """Test limit parameter range validation."""
        valid_limits = [1, 10, 50, 100]
        invalid_limits = [0, -1, 101, 150, 1000]
        
        for limit in valid_limits:
            validations = self.validator.validate_tool_parameters(
                "get_transactions",
                {"user_id": "jane_smith", "limit": limit}
            )
            limit_validation = next(v for v in validations if v.parameter_name == "limit")
            assert limit_validation.is_valid, f"Valid limit {limit} should pass validation"
        
        for limit in invalid_limits:
            validations = self.validator.validate_tool_parameters(
                "get_transactions",
                {"user_id": "jane_smith", "limit": limit}
            )
            limit_validation = next(v for v in validations if v.parameter_name == "limit")
            assert not limit_validation.is_valid, f"Invalid limit {limit} should fail validation"
    
    @pytest.mark.validation
    def test_transaction_type_validation(self):
        """Test transaction type validation."""
        valid_types = ["debit", "credit", None]
        invalid_types = ["withdrawal", "deposit", "payment", "", "DEBIT", "Credit"]
        
        for tx_type in valid_types:
            validations = self.validator.validate_tool_parameters(
                "get_transactions",
                {"user_id": "jane_smith", "transaction_type": tx_type}
            )
            type_validation = next((v for v in validations if v.parameter_name == "transaction_type"), None)
            if type_validation:  # Only check if validation was performed
                assert type_validation.is_valid, f"Valid transaction type '{tx_type}' should pass validation"
        
        for tx_type in invalid_types:
            validations = self.validator.validate_tool_parameters(
                "get_transactions",
                {"user_id": "jane_smith", "transaction_type": tx_type}
            )
            type_validation = next((v for v in validations if v.parameter_name == "transaction_type"), None)
            if type_validation:  # Only check if validation was performed
                assert not type_validation.is_valid, f"Invalid transaction type '{tx_type}' should fail validation"


class TestParameterEnhancement:
    """Test suite for parameter enhancement features."""
    
    def setup_method(self):
        """Setup parameter validator for each test."""
        self.validator = ParameterValidator()
    
    @pytest.mark.validation
    def test_error_message_quality(self):
        """Test that error messages are helpful and specific."""
        # Test various error conditions
        test_cases = [
            ({"user_id": ""}, "minimum length", "empty user_id"),
            ({"user_id": "user_id"}, "placeholder", "placeholder user_id"),
            ({}, "missing", "missing required parameter"),
            ({"user_id": "jane_smith", "limit": 150}, "maximum", "limit too high"),
            ({"user_id": "jane_smith", "start_date": "2024/01/01"}, "pattern", "wrong date format")
        ]
        
        for params, expected_error_keyword, description in test_cases:
            validations = self.validator.validate_tool_parameters("get_transactions", params)
            error_validations = [v for v in validations if not v.is_valid]
            
            assert len(error_validations) > 0, f"Should have validation errors for {description}"
            
            for error_validation in error_validations:
                assert error_validation.error_message, f"Should have error message for {description}"
                assert expected_error_keyword.lower() in error_validation.error_message.lower(), \
                    f"Error message should contain '{expected_error_keyword}' for {description}"
                
                if error_validation.suggestion:
                    assert len(error_validation.suggestion) > 10, \
                        f"Suggestion should be meaningful for {description}"
    
    @pytest.mark.validation
    def test_validation_completeness(self):
        """Test that all tools have complete validation rules."""
        for tool_name, tool_rules in self.validator.VALIDATION_RULES.items():
            assert "required" in tool_rules, f"Tool {tool_name} should define required parameters"
            assert "optional" in tool_rules, f"Tool {tool_name} should define optional parameters"
            assert "rules" in tool_rules, f"Tool {tool_name} should define validation rules"
            
            # All required parameters should have validation rules
            for required_param in tool_rules["required"]:
                assert required_param in tool_rules["rules"], \
                    f"Tool {tool_name} missing validation rules for required parameter '{required_param}'"
            
            # All parameters with rules should have proper structure
            for param_name, param_rules in tool_rules["rules"].items():
                assert "type" in param_rules, f"Parameter {param_name} in {tool_name} should define type"
                assert "description" in param_rules, f"Parameter {param_name} in {tool_name} should have description"
    
    @pytest.mark.validation
    def test_parameter_suggestions(self):
        """Test that validation errors provide helpful suggestions."""
        error_cases = [
            ({"user_id": "user_id"}, "actual authenticated user ID"),
            ({"user_id": "jane_smith", "limit": 150}, "value <= 100"),
            ({"user_id": "jane_smith", "start_date": "2024/01/01"}, "pattern"),
            ({}, "required parameter")
        ]
        
        for params, expected_suggestion_keyword in error_cases:
            validations = self.validator.validate_tool_parameters("get_transactions", params)
            error_validations = [v for v in validations if not v.is_valid]
            
            for error_validation in error_validations:
                if error_validation.suggestion:
                    assert expected_suggestion_keyword.lower() in error_validation.suggestion.lower(), \
                        f"Suggestion should contain '{expected_suggestion_keyword}' for parameters {params}"


class TestValidationIntegration:
    """Test integration of validation with actual tools."""
    
    @pytest.mark.integration
    @pytest.mark.validation
    def test_tool_validation_integration(self, test_user_data):
        """Test that actual tools implement the validation correctly."""
        from ..tools.sql_retrieval_tool import (
            get_account_balance,
            get_transactions,
            get_credit_card_info
        )
        
        # Test that tools reject placeholder user_ids
        placeholder_user_id = "user_id"
        
        tools_to_test = [
            ("get_account_balance", get_account_balance),
            ("get_transactions", get_transactions),
            ("get_credit_card_info", get_credit_card_info)
        ]
        
        for tool_name, tool_func in tools_to_test:
            result_str = tool_func.invoke({"user_id": placeholder_user_id})
            result = validate_json_response(result_str)
            
            assert "error" in result, f"{tool_name} should reject placeholder user_id"
            assert "invalid" in result["error"].lower() or "placeholder" in result["error"].lower(), \
                f"{tool_name} should specifically mention invalid/placeholder user_id"
    
    @pytest.mark.integration
    @pytest.mark.validation
    def test_validation_consistency_across_tools(self):
        """Test that all tools consistently validate user_id."""
        from ..tools.sql_retrieval_tool import (
            get_account_balance,
            get_transactions,
            get_credit_card_info
        )
        
        # Test various invalid user_ids
        invalid_user_ids = ["", "user_id", "your_user_id", "placeholder"]
        tools = [get_account_balance, get_transactions, get_credit_card_info]
        
        for user_id in invalid_user_ids:
            for tool in tools:
                result_str = tool.invoke({"user_id": user_id})
                result = validate_json_response(result_str)
                
                assert "error" in result, f"{tool.name} should reject invalid user_id '{user_id}'"


if __name__ == "__main__":
    # Run parameter validation tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "validation"])
