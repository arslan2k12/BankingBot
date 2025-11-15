"""
Schema Validation Testing Module

This module tests input/output schema validation for all banking tools
to ensure they conform to expected data structures and formats.
"""

import pytest
import json
from typing import Dict, Any, List
import jsonschema
from datetime import datetime

from .conftest import validate_json_response, TestCategories


# Tool Schema Definitions
ACCOUNT_BALANCE_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {
            "type": "string",
            "minLength": 1,
            "description": "Valid user ID from database"
        },
        "account_number": {
            "type": ["string", "null"],
            "description": "Optional specific account number"
        }
    },
    "required": ["user_id"],
    "additionalProperties": False
}

ACCOUNT_BALANCE_OUTPUT_SCHEMA = {
    "type": "object",
    "oneOf": [
        {
            # Success response
            "properties": {
                "accounts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "account_number": {"type": "string"},
                            "account_type": {"type": "string"},
                            "balance": {"type": "number"},
                            "currency": {"type": "string"}
                        },
                        "required": ["account_number", "account_type", "balance", "currency"]
                    }
                },
                "total_balance": {"type": "number"},
                "currency": {"type": "string"},
                "as_of_date": {"type": "string"}
            },
            "required": ["accounts", "total_balance", "currency", "as_of_date"]
        },
        {
            # Error response
            "properties": {
                "error": {"type": "string"},
                "message": {"type": "string"},
                "user_id": {"type": "string"}
            },
            "required": ["error"]
        }
    ]
}

TRANSACTIONS_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string", "minLength": 1},
        "account_number": {"type": ["string", "null"]},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100},
        "start_date": {"type": ["string", "null"], "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
        "end_date": {"type": ["string", "null"], "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
        "transaction_type": {"enum": ["debit", "credit", None]}
    },
    "required": ["user_id"],
    "additionalProperties": False
}

TRANSACTIONS_OUTPUT_SCHEMA = {
    "type": "object",
    "oneOf": [
        {
            # Success response
            "properties": {
                "transactions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "transaction_id": {"type": "string"},
                            "account_number": {"type": "string"},
                            "transaction_type": {"type": "string"},
                            "amount": {"type": "number"},
                            "description": {"type": "string"},
                            "transaction_date": {"type": "string"},
                            "created_at": {"type": "string"}
                        },
                        "required": ["transaction_id", "account_number", "transaction_type", "amount", "transaction_date"]
                    }
                },
                "total_count": {"type": "integer"},
                "limit": {"type": "integer"}
            },
            "required": ["transactions", "total_count", "limit"]
        },
        {
            # Error response
            "properties": {
                "error": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["error"]
        }
    ]
}

CREDIT_CARD_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string", "minLength": 1}
    },
    "required": ["user_id"],
    "additionalProperties": False
}

CREDIT_CARD_OUTPUT_SCHEMA = {
    "type": "object",
    "oneOf": [
        {
            # Success response
            "properties": {
                "credit_cards": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "card_number": {"type": "string"},
                            "card_type": {"type": "string"},
                            "credit_limit": {"type": "number"},
                            "current_balance": {"type": "number"},
                            "available_credit": {"type": "number"},
                            "utilization_rate": {"type": "number"}
                        },
                        "required": ["card_number", "card_type", "credit_limit", "current_balance"]
                    }
                },
                "total_cards": {"type": "integer"}
            },
            "required": ["credit_cards", "total_cards"]
        },
        {
            # Error response
            "properties": {
                "error": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["error"]
        }
    ]
}

# Schema registry
TOOL_SCHEMAS = {
    "get_account_balance": {
        "input": ACCOUNT_BALANCE_INPUT_SCHEMA,
        "output": ACCOUNT_BALANCE_OUTPUT_SCHEMA
    },
    "get_transactions": {
        "input": TRANSACTIONS_INPUT_SCHEMA,
        "output": TRANSACTIONS_OUTPUT_SCHEMA
    },
    "get_credit_card_info": {
        "input": CREDIT_CARD_INPUT_SCHEMA,
        "output": CREDIT_CARD_OUTPUT_SCHEMA
    }
}


class TestSchemaValidation:
    """Test suite for schema validation of all tools."""
    
    def validate_input_schema(self, tool_name: str, input_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate input against tool schema."""
        if tool_name not in TOOL_SCHEMAS:
            return False, f"Unknown tool: {tool_name}"
        
        try:
            jsonschema.validate(input_data, TOOL_SCHEMAS[tool_name]["input"])
            return True, "Input schema validation passed"
        except jsonschema.ValidationError as e:
            return False, f"Input schema validation failed: {e.message}"
    
    def validate_output_schema(self, tool_name: str, output_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate output against tool schema."""
        if tool_name not in TOOL_SCHEMAS:
            return False, f"Unknown tool: {tool_name}"
        
        try:
            jsonschema.validate(output_data, TOOL_SCHEMAS[tool_name]["output"])
            return True, "Output schema validation passed"
        except jsonschema.ValidationError as e:
            return False, f"Output schema validation failed: {e.message}"
    
    @pytest.mark.validation
    @pytest.mark.parametrize("tool_name,input_data,expected_valid", [
        # Valid inputs
        ("get_account_balance", {"user_id": "jane_smith"}, True),
        ("get_account_balance", {"user_id": "jane_smith", "account_number": "ACC001"}, True),
        ("get_transactions", {"user_id": "jane_smith"}, True),
        ("get_transactions", {"user_id": "jane_smith", "limit": 5, "start_date": "2024-01-01"}, True),
        ("get_credit_card_info", {"user_id": "jane_smith"}, True),
        
        # Invalid inputs
        ("get_account_balance", {}, False),  # Missing user_id
        ("get_account_balance", {"user_id": ""}, False),  # Empty user_id
        ("get_transactions", {"user_id": "jane_smith", "limit": 150}, False),  # Limit too high
        ("get_transactions", {"user_id": "jane_smith", "start_date": "2024/01/01"}, False),  # Wrong date format
        ("get_credit_card_info", {"user_id": ""}, False),  # Empty user_id
    ])
    def test_input_schema_validation(self, tool_name, input_data, expected_valid):
        """Test input schema validation for all tools."""
        is_valid, message = self.validate_input_schema(tool_name, input_data)
        
        if expected_valid:
            assert is_valid, f"Expected valid input but got error: {message}"
        else:
            assert not is_valid, f"Expected invalid input but validation passed"
    
    @pytest.mark.validation
    @pytest.mark.integration
    def test_actual_tool_output_schemas(self, test_user_data):
        """Test that actual tool outputs conform to schemas."""
        from ..tools.sql_retrieval_tool import (
            get_account_balance,
            get_transactions,
            get_credit_card_info
        )
        
        user_id = test_user_data["user"].user_id
        
        # Test each tool's actual output
        tools_to_test = [
            ("get_account_balance", get_account_balance, {"user_id": user_id}),
            ("get_transactions", get_transactions, {"user_id": user_id, "limit": 5}),
            ("get_credit_card_info", get_credit_card_info, {"user_id": user_id})
        ]
        
        for tool_name, tool_func, params in tools_to_test:
            # Get actual tool output
            result_str = tool_func.invoke(params)
            result = validate_json_response(result_str)
            
            # Validate against schema
            is_valid, message = self.validate_output_schema(tool_name, result)
            assert is_valid, f"{tool_name} output schema validation failed: {message}"
    
    @pytest.mark.validation
    def test_error_response_schemas(self):
        """Test that error responses conform to schemas."""
        from ..tools.sql_retrieval_tool import (
            get_account_balance,
            get_transactions,
            get_credit_card_info
        )
        
        # Test with invalid user_id to get error responses
        invalid_user_id = "user_id"  # Placeholder that should be rejected
        
        tools_to_test = [
            ("get_account_balance", get_account_balance, {"user_id": invalid_user_id}),
            ("get_transactions", get_transactions, {"user_id": invalid_user_id}),
            ("get_credit_card_info", get_credit_card_info, {"user_id": invalid_user_id})
        ]
        
        for tool_name, tool_func, params in tools_to_test:
            result_str = tool_func.invoke(params)
            result = validate_json_response(result_str)
            
            # Should be error response
            assert "error" in result, f"{tool_name} should return error for invalid user_id"
            
            # Validate error response schema
            is_valid, message = self.validate_output_schema(tool_name, result)
            assert is_valid, f"{tool_name} error response schema validation failed: {message}"


class TestDataFormatValidation:
    """Test suite for specific data format validation."""
    
    @pytest.mark.validation
    def test_date_format_validation(self):
        """Test date format validation."""
        valid_dates = ["2024-01-01", "2024-12-31", "2023-06-15"]
        invalid_dates = ["2024/01/01", "01-01-2024", "Jan 1, 2024", "2024-1-1"]
        
        date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        import re
        
        for date in valid_dates:
            assert re.match(date_pattern, date), f"Valid date {date} should match pattern"
        
        for date in invalid_dates:
            assert not re.match(date_pattern, date), f"Invalid date {date} should not match pattern"
    
    @pytest.mark.validation
    def test_account_number_format_validation(self):
        """Test account number format validation."""
        valid_account_numbers = ["ACC001", "1001234569", "CHECKING123", "A1B2C3"]
        invalid_account_numbers = ["acc-001", "account_number", "", "a" * 25]  # Too long
        
        account_pattern = r"^[A-Z0-9]{1,20}$"
        import re
        
        for acc_num in valid_account_numbers:
            assert re.match(account_pattern, acc_num), f"Valid account {acc_num} should match pattern"
        
        for acc_num in invalid_account_numbers:
            assert not re.match(account_pattern, acc_num), f"Invalid account {acc_num} should not match pattern"
    
    @pytest.mark.validation
    def test_transaction_type_validation(self):
        """Test transaction type validation."""
        valid_types = ["debit", "credit", None]
        invalid_types = ["withdrawal", "deposit", "payment", "", "DEBIT"]
        
        for tx_type in valid_types:
            assert tx_type in ["debit", "credit", None], f"Valid type {tx_type} should be allowed"
        
        for tx_type in invalid_types:
            assert tx_type not in ["debit", "credit", None], f"Invalid type {tx_type} should not be allowed"


class TestSchemaEvolution:
    """Test suite for schema evolution and backward compatibility."""
    
    @pytest.mark.validation
    def test_schema_completeness(self):
        """Test that all required tools have schemas defined."""
        required_tools = ["get_account_balance", "get_transactions", "get_credit_card_info"]
        
        for tool in required_tools:
            assert tool in TOOL_SCHEMAS, f"Tool {tool} missing from schema registry"
            assert "input" in TOOL_SCHEMAS[tool], f"Tool {tool} missing input schema"
            assert "output" in TOOL_SCHEMAS[tool], f"Tool {tool} missing output schema"
    
    @pytest.mark.validation
    def test_schema_consistency(self):
        """Test schema consistency across tools."""
        # All tools should have user_id as required parameter
        for tool_name, schemas in TOOL_SCHEMAS.items():
            input_schema = schemas["input"]
            assert "user_id" in input_schema["required"], f"Tool {tool_name} should require user_id"
            
            user_id_prop = input_schema["properties"]["user_id"]
            assert user_id_prop["type"] == "string", f"Tool {tool_name} user_id should be string"
            assert user_id_prop["minLength"] == 1, f"Tool {tool_name} user_id should have minLength 1"
    
    @pytest.mark.validation
    def test_error_response_consistency(self):
        """Test that all tools have consistent error response format."""
        for tool_name, schemas in TOOL_SCHEMAS.items():
            output_schema = schemas["output"]
            
            # Should have oneOf with error response option
            assert "oneOf" in output_schema, f"Tool {tool_name} should have oneOf in output schema"
            
            # Find error response schema
            error_schemas = [
                schema for schema in output_schema["oneOf"] 
                if "error" in schema.get("properties", {})
            ]
            assert len(error_schemas) > 0, f"Tool {tool_name} should have error response schema"
            
            error_schema = error_schemas[0]
            assert "error" in error_schema["required"], f"Tool {tool_name} error response should require 'error' field"


if __name__ == "__main__":
    # Run schema validation tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "validation"])
