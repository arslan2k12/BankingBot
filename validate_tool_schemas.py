#!/usr/bin/env python3
"""
Tool Schema Validation Script

This script defines the expected input/output schemas for each banking tool
and validates that tools conform to these schemas.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import jsonschema

# Define expected schemas for each tool

# 1. Account Balance Tool Schema
ACCOUNT_BALANCE_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {
            "type": "string",
            "minLength": 1,
            "description": "Valid user ID from database, not a placeholder"
        },
        "account_number": {
            "type": ["string", "null"],
            "description": "Optional specific account number to filter"
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
                "user_id": {"type": "string"},
                "suggestion": {"type": "string"}
            },
            "required": ["error"]
        }
    ]
}

# 2. Transactions Tool Schema
TRANSACTIONS_INPUT_SCHEMA = {
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
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "default": 10
        },
        "start_date": {
            "type": ["string", "null"],
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
            "description": "Start date in YYYY-MM-DD format"
        },
        "end_date": {
            "type": ["string", "null"],
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
            "description": "End date in YYYY-MM-DD format"
        },
        "transaction_type": {
            "type": ["string", "null"],
            "enum": ["debit", "credit", null]
        }
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
                            "category": {"type": ["string", "null"]},
                            "merchant": {"type": ["string", "null"]},
                            "transaction_date": {"type": "string"},
                            "created_at": {"type": "string"}
                        },
                        "required": ["transaction_id", "account_number", "transaction_type", "amount", "transaction_date"]
                    }
                },
                "total_count": {"type": "integer"},
                "limit": {"type": "integer"},
                "account_filter": {"type": ["string", "null"]}
            },
            "required": ["transactions", "total_count", "limit"]
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

# 3. Credit Card Tool Schema
CREDIT_CARD_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {
            "type": "string",
            "minLength": 1,
            "description": "Valid user ID from database"
        }
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
                            "minimum_payment": {"type": "number"},
                            "due_date": {"type": ["string", "null"]},
                            "utilization_rate": {"type": "number"}
                        },
                        "required": ["card_number", "card_type", "credit_limit", "current_balance", "available_credit"]
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
                "message": {"type": "string"},
                "user_id": {"type": "string"}
            },
            "required": ["error"]
        }
    ]
}

@dataclass
class ToolSchema:
    """Tool schema definition."""
    name: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    description: str

# Define all tool schemas
TOOL_SCHEMAS = {
    "get_account_balance": ToolSchema(
        name="get_account_balance",
        input_schema=ACCOUNT_BALANCE_INPUT_SCHEMA,
        output_schema=ACCOUNT_BALANCE_OUTPUT_SCHEMA,
        description="Retrieves account balance information for a user"
    ),
    "get_transactions": ToolSchema(
        name="get_transactions", 
        input_schema=TRANSACTIONS_INPUT_SCHEMA,
        output_schema=TRANSACTIONS_OUTPUT_SCHEMA,
        description="Retrieves transaction history for a user"
    ),
    "get_credit_card_info": ToolSchema(
        name="get_credit_card_info",
        input_schema=CREDIT_CARD_INPUT_SCHEMA,
        output_schema=CREDIT_CARD_OUTPUT_SCHEMA,
        description="Retrieves credit card information for a user"
    )
}

def validate_input_schema(tool_name: str, input_data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate input against tool schema."""
    if tool_name not in TOOL_SCHEMAS:
        return False, f"Unknown tool: {tool_name}"
    
    try:
        jsonschema.validate(input_data, TOOL_SCHEMAS[tool_name].input_schema)
        return True, "Input schema validation passed"
    except jsonschema.ValidationError as e:
        return False, f"Input schema validation failed: {e.message}"

def validate_output_schema(tool_name: str, output_data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate output against tool schema."""
    if tool_name not in TOOL_SCHEMAS:
        return False, f"Unknown tool: {tool_name}"
    
    try:
        jsonschema.validate(output_data, TOOL_SCHEMAS[tool_name].output_schema)
        return True, "Output schema validation passed"
    except jsonschema.ValidationError as e:
        return False, f"Output schema validation failed: {e.message}"

def test_tool_with_schema_validation(tool_name: str, tool_function, input_data: Dict[str, Any]):
    """Test a tool with full schema validation."""
    print(f"\n🧪 Testing {tool_name} with schema validation")
    print(f"📥 Input: {input_data}")
    
    # Validate input
    input_valid, input_msg = validate_input_schema(tool_name, input_data)
    print(f"📋 Input validation: {'✅' if input_valid else '❌'} {input_msg}")
    
    if not input_valid:
        return False
    
    try:
        # Call the tool
        result = tool_function(**input_data)
        output_data = json.loads(result)
        
        # Validate output
        output_valid, output_msg = validate_output_schema(tool_name, output_data)
        print(f"📤 Output validation: {'✅' if output_valid else '❌'} {output_msg}")
        
        if output_valid:
            print(f"🎯 Tool execution successful")
            if "error" in output_data:
                print(f"⚠️  Tool returned error: {output_data['error']}")
            else:
                print(f"✅ Tool returned success response")
        
        return output_valid
        
    except Exception as e:
        print(f"💥 Tool execution failed: {str(e)}")
        return False

def run_comprehensive_schema_tests():
    """Run comprehensive schema validation tests."""
    from src.app.tools.sql_retrieval_tool import (
        get_account_balance,
        get_transactions,
        get_credit_card_info
    )
    
    print("🚀 Starting Comprehensive Schema Validation Tests")
    print("="*70)
    
    test_results = []
    
    # Test Account Balance Tool
    print(f"\n📊 TESTING: get_account_balance")
    print("-" * 50)
    
    balance_tests = [
        {
            "name": "Valid user input",
            "input": {"user_id": "jane_smith"},
            "expected": "pass"
        },
        {
            "name": "Valid user with account",
            "input": {"user_id": "jane_smith", "account_number": "ACC001"},
            "expected": "pass"
        },
        {
            "name": "Invalid empty user_id",
            "input": {"user_id": ""},
            "expected": "fail_input"
        }
    ]
    
    for test in balance_tests:
        print(f"\n🔍 Test: {test['name']}")
        result = test_tool_with_schema_validation("get_account_balance", get_account_balance, test["input"])
        test_results.append({"tool": "get_account_balance", "test": test["name"], "passed": result})
    
    # Test Transactions Tool
    print(f"\n📊 TESTING: get_transactions")
    print("-" * 50)
    
    transaction_tests = [
        {
            "name": "Basic valid input",
            "input": {"user_id": "jane_smith"},
            "expected": "pass"
        },
        {
            "name": "Valid input with filters",
            "input": {
                "user_id": "jane_smith",
                "limit": 5,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            "expected": "pass"
        },
        {
            "name": "Invalid date format",
            "input": {
                "user_id": "jane_smith",
                "start_date": "2024/01/01"  # Wrong format
            },
            "expected": "fail_input"
        }
    ]
    
    for test in transaction_tests:
        print(f"\n🔍 Test: {test['name']}")
        result = test_tool_with_schema_validation("get_transactions", get_transactions, test["input"])
        test_results.append({"tool": "get_transactions", "test": test["name"], "passed": result})
    
    # Test Credit Card Tool
    print(f"\n📊 TESTING: get_credit_card_info")
    print("-" * 50)
    
    credit_tests = [
        {
            "name": "Valid user input",
            "input": {"user_id": "jane_smith"},
            "expected": "pass"
        },
        {
            "name": "Invalid placeholder user_id",
            "input": {"user_id": "user_id"},
            "expected": "pass"  # Tool should handle this gracefully with error response
        }
    ]
    
    for test in credit_tests:
        print(f"\n🔍 Test: {test['name']}")
        result = test_tool_with_schema_validation("get_credit_card_info", get_credit_card_info, test["input"])
        test_results.append({"tool": "get_credit_card_info", "test": test["name"], "passed": result})
    
    # Summary
    print(f"\n🏁 SCHEMA VALIDATION SUMMARY")
    print("="*70)
    
    passed_tests = sum(1 for r in test_results if r["passed"])
    total_tests = len(test_results)
    
    print(f"✅ Passed: {passed_tests}/{total_tests} tests")
    
    for result in test_results:
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['tool']} - {result['test']}")
    
    return test_results

def print_tool_schemas():
    """Print all defined tool schemas for reference."""
    print("📋 TOOL SCHEMAS REFERENCE")
    print("="*70)
    
    for tool_name, schema in TOOL_SCHEMAS.items():
        print(f"\n🔧 {schema.name.upper()}")
        print(f"📝 Description: {schema.description}")
        print(f"📥 Input Schema: {json.dumps(schema.input_schema, indent=2)}")
        print(f"📤 Output Schema: {json.dumps(schema.output_schema, indent=2)}")
        print("-" * 50)

if __name__ == "__main__":
    print("🎯 Banking Tools Schema Validation")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Print schemas for reference
    print_tool_schemas()
    
    # Run comprehensive tests
    results = run_comprehensive_schema_tests()
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
