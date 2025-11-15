#!/usr/bin/env python3
"""
Tool Parameter Enhancement and Validation Script

This script provides comprehensive parameter validation, schema definitions,
and enhancement suggestions for all banking tools.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import re

# Import the tools
from src.app.tools.sql_retrieval_tool import (
    get_account_balance,
    get_transactions,
    get_credit_card_info
)

@dataclass
class ParameterValidation:
    """Parameter validation result"""
    is_valid: bool
    parameter_name: str
    value: Any
    error_message: Optional[str] = None
    suggestion: Optional[str] = None

@dataclass
class ToolTest:
    """Individual tool test case"""
    tool_name: str
    test_name: str
    parameters: Dict[str, Any]
    expected_result: str  # "success", "error", "validation_error"
    expected_error_type: Optional[str] = None

@dataclass
class ToolSchema:
    """Comprehensive tool schema with validation rules"""
    name: str
    description: str
    required_parameters: List[str]
    optional_parameters: Dict[str, Any]
    parameter_validation_rules: Dict[str, Any]
    return_format: str
    error_conditions: List[str]

# Define comprehensive tool schemas
BANKING_TOOL_SCHEMAS = {
    "get_account_balance": ToolSchema(
        name="get_account_balance",
        description="Retrieve account balance information for an authenticated user",
        required_parameters=["user_id"],
        optional_parameters={
            "account_number": "str | None - Filter by specific account number"
        },
        parameter_validation_rules={
            "user_id": {
                "type": str,
                "min_length": 1,
                "invalid_values": ['user_id', 'your_user_id', 'none', 'null', '', 'placeholder', 'example', 'test_user', 'userid'],
                "pattern": None,
                "description": "Valid authenticated user ID from database"
            },
            "account_number": {
                "type": [str, type(None)],
                "min_length": 1,
                "pattern": r"^[A-Z0-9]{1,20}$",  # Alphanumeric, 1-20 chars
                "description": "Optional account number to filter results"
            }
        },
        return_format="JSON with accounts array, total_balance, currency, as_of_date",
        error_conditions=[
            "Invalid user_id parameter (placeholder values)",
            "User not found in database",
            "Database connection failure",
            "No active accounts found"
        ]
    ),
    
    "get_transactions": ToolSchema(
        name="get_transactions", 
        description="Retrieve transaction history for an authenticated user",
        required_parameters=["user_id"],
        optional_parameters={
            "account_number": "str | None - Filter by specific account",
            "limit": "int (1-100) - Number of transactions to return (default: 10)",
            "start_date": "str - Start date in YYYY-MM-DD format",
            "end_date": "str - End date in YYYY-MM-DD format", 
            "transaction_type": "str - Filter by 'debit' or 'credit'"
        },
        parameter_validation_rules={
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
        },
        return_format="JSON with transactions array, total_count, limit, account_filter",
        error_conditions=[
            "Invalid user_id parameter",
            "User not found",
            "Invalid date format", 
            "Invalid limit range",
            "Invalid transaction_type",
            "Database connection failure"
        ]
    ),
    
    "get_credit_card_info": ToolSchema(
        name="get_credit_card_info",
        description="Retrieve credit card information for an authenticated user",
        required_parameters=["user_id"],
        optional_parameters={},
        parameter_validation_rules={
            "user_id": {
                "type": str,
                "min_length": 1,
                "invalid_values": ['user_id', 'your_user_id', 'none', 'null', '', 'placeholder', 'example', 'test_user', 'userid'],
                "description": "Valid authenticated user ID"
            }
        },
        return_format="JSON with credit_cards array, total_cards",
        error_conditions=[
            "Invalid user_id parameter",
            "User not found",
            "No active credit cards found",
            "Database connection failure"
        ]
    )
}

def validate_parameter(param_name: str, value: Any, validation_rules: Dict[str, Any]) -> ParameterValidation:
    """Validate a single parameter against its rules."""
    
    # Type validation
    expected_type = validation_rules.get("type")
    if expected_type:
        if isinstance(expected_type, list):
            # Multiple allowed types
            if not any(isinstance(value, t) for t in expected_type):
                return ParameterValidation(
                    False, param_name, value,
                    f"Expected type {expected_type}, got {type(value).__name__}",
                    f"Provide value of type {expected_type}"
                )
        else:
            # Single expected type
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

def validate_tool_parameters(tool_name: str, parameters: Dict[str, Any]) -> List[ParameterValidation]:
    """Validate all parameters for a tool."""
    if tool_name not in BANKING_TOOL_SCHEMAS:
        return [ParameterValidation(False, "tool_name", tool_name, f"Unknown tool: {tool_name}")]
    
    schema = BANKING_TOOL_SCHEMAS[tool_name]
    validations = []
    
    # Check required parameters
    for required_param in schema.required_parameters:
        if required_param not in parameters:
            validations.append(ParameterValidation(
                False, required_param, None,
                f"Required parameter '{required_param}' missing",
                f"Provide required parameter '{required_param}'"
            ))
        else:
            # Validate the parameter
            param_value = parameters[required_param]
            validation_rules = schema.parameter_validation_rules.get(required_param, {})
            validation = validate_parameter(required_param, param_value, validation_rules)
            validations.append(validation)
    
    # Check optional parameters
    for param_name, param_value in parameters.items():
        if param_name not in schema.required_parameters:
            # This is an optional parameter
            validation_rules = schema.parameter_validation_rules.get(param_name, {})
            if validation_rules:  # Only validate if we have rules for it
                validation = validate_parameter(param_name, param_value, validation_rules)
                validations.append(validation)
    
    return validations

def test_tool_parameter_validation():
    """Test parameter validation for all tools."""
    print("🧪 TESTING PARAMETER VALIDATION")
    print("="*60)
    
    test_cases = [
        # get_account_balance tests
        ToolTest("get_account_balance", "Valid parameters", 
                {"user_id": "jane_smith"}, "success"),
        ToolTest("get_account_balance", "Valid with account number", 
                {"user_id": "jane_smith", "account_number": "1001234569"}, "success"),
        ToolTest("get_account_balance", "Invalid user_id placeholder",
                {"user_id": "user_id"}, "validation_error", "invalid_user_id"),
        ToolTest("get_account_balance", "Empty user_id",
                {"user_id": ""}, "validation_error", "empty_user_id"),
        ToolTest("get_account_balance", "Missing user_id",
                {}, "validation_error", "missing_required"),
        
        # get_transactions tests
        ToolTest("get_transactions", "Valid basic parameters",
                {"user_id": "jane_smith"}, "success"),
        ToolTest("get_transactions", "Valid with all optional params",
                {"user_id": "jane_smith", "limit": 5, "start_date": "2024-01-01", "end_date": "2024-12-31"}, "success"),
        ToolTest("get_transactions", "Invalid date format",
                {"user_id": "jane_smith", "start_date": "2024/01/01"}, "validation_error", "invalid_date"),
        ToolTest("get_transactions", "Invalid limit too high",
                {"user_id": "jane_smith", "limit": 150}, "validation_error", "invalid_limit"),
        ToolTest("get_transactions", "Invalid transaction type",
                {"user_id": "jane_smith", "transaction_type": "invalid"}, "validation_error", "invalid_type"),
        
        # get_credit_card_info tests 
        ToolTest("get_credit_card_info", "Valid parameters",
                {"user_id": "jane_smith"}, "success"),
        ToolTest("get_credit_card_info", "Invalid placeholder user_id",
                {"user_id": "your_user_id"}, "validation_error", "invalid_user_id"),
    ]
    
    total_tests = len(test_cases)
    passed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}/{total_tests}: {test_case.test_name}")
        print(f"🛠️  Tool: {test_case.tool_name}")
        print(f"📥 Parameters: {test_case.parameters}")
        
        # Run parameter validation
        validations = validate_tool_parameters(test_case.tool_name, test_case.parameters)
        
        # Check results
        validation_errors = [v for v in validations if not v.is_valid]
        has_validation_errors = len(validation_errors) > 0
        
        if test_case.expected_result == "validation_error" and has_validation_errors:
            print("✅ PASS - Expected validation error occurred")
            for error in validation_errors:
                print(f"   ❌ {error.parameter_name}: {error.error_message}")
                if error.suggestion:
                    print(f"   💡 Suggestion: {error.suggestion}")
            passed_tests += 1
        elif test_case.expected_result == "success" and not has_validation_errors:
            print("✅ PASS - Validation successful")
            passed_tests += 1
        else:
            print("❌ FAIL - Unexpected validation result")
            if has_validation_errors:
                print("   Validation errors found:")
                for error in validation_errors:
                    print(f"   ❌ {error.parameter_name}: {error.error_message}")
            else:
                print("   No validation errors (but expected some)")
    
    print(f"\n📊 VALIDATION TEST SUMMARY")
    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")

def generate_tool_documentation():
    """Generate comprehensive documentation for all tools."""
    print(f"\n📚 BANKING TOOLS DOCUMENTATION")
    print("="*80)
    
    for tool_name, schema in BANKING_TOOL_SCHEMAS.items():
        print(f"\n🔧 {schema.name.upper()}")
        print(f"📝 Description: {schema.description}")
        print(f"🎯 Purpose: Banking tool for authenticated users")
        
        print(f"\n📥 REQUIRED PARAMETERS:")
        for param in schema.required_parameters:
            rules = schema.parameter_validation_rules.get(param, {})
            print(f"   • {param}: {rules.get('description', 'No description')}")
            if 'invalid_values' in rules:
                print(f"     ❌ Invalid values: {rules['invalid_values']}")
        
        print(f"\n📋 OPTIONAL PARAMETERS:")
        for param, description in schema.optional_parameters.items():
            print(f"   • {param}: {description}")
            rules = schema.parameter_validation_rules.get(param, {})
            if 'pattern' in rules:
                print(f"     🔍 Pattern: {rules['pattern']}")
            if 'allowed_values' in rules:
                print(f"     ✅ Allowed: {rules['allowed_values']}")
            if 'min_value' in rules or 'max_value' in rules:
                min_val = rules.get('min_value', 'N/A')
                max_val = rules.get('max_value', 'N/A')
                print(f"     📊 Range: {min_val} - {max_val}")
        
        print(f"\n📤 RETURN FORMAT:")
        print(f"   {schema.return_format}")
        
        print(f"\n⚠️  ERROR CONDITIONS:")
        for condition in schema.error_conditions:
            print(f"   • {condition}")
        
        print(f"\n💡 USAGE EXAMPLES:")
        if tool_name == "get_account_balance":
            print(f"   ✅ Correct: get_account_balance(user_id='jane_smith')")
            print(f"   ✅ Correct: get_account_balance(user_id='jane_smith', account_number='1001234569')")
            print(f"   ❌ Wrong: get_account_balance(user_id='user_id')  # placeholder")
        elif tool_name == "get_transactions":
            print(f"   ✅ Correct: get_transactions(user_id='jane_smith')")
            print(f"   ✅ Correct: get_transactions(user_id='jane_smith', limit=5, start_date='2024-01-01')")
            print(f"   ❌ Wrong: get_transactions(user_id='your_user_id')  # placeholder")
        elif tool_name == "get_credit_card_info":
            print(f"   ✅ Correct: get_credit_card_info(user_id='jane_smith')")
            print(f"   ❌ Wrong: get_credit_card_info(user_id='placeholder')  # placeholder")
        
        print("-" * 60)

def generate_agent_parameter_guidelines():
    """Generate guidelines for the agent on proper parameter usage."""
    print(f"\n🎯 AGENT PARAMETER USAGE GUIDELINES")
    print("="*80)
    
    print(f"""
🔑 CRITICAL PARAMETER RULES FOR BANKING AGENT:

1. USER_ID PARAMETER - MOST IMPORTANT:
   ✅ ALWAYS use the authenticated user_id from conversation context
   ✅ Examples of VALID user_ids: 'jane_smith', 'john_doe', 'mike_johnson'
   ❌ NEVER use these placeholder values:
      - 'user_id' (generic placeholder)
      - 'your_user_id' (instruction placeholder)
      - 'placeholder', 'example', 'test_user'
      - Empty string '', 'null', 'none'

2. ACCOUNT_NUMBER PARAMETER (Optional):
   ✅ Use actual account numbers: '1001234569', '1001234570'
   ✅ Can be None/null for all accounts  
   ❌ Don't use placeholders like 'account_number', 'ACC123'

3. DATE PARAMETERS (Optional):
   ✅ Use YYYY-MM-DD format: '2024-01-01', '2024-12-31'
   ❌ Don't use: '2024/01/01', 'Jan 1, 2024', '01-01-2024'

4. LIMIT PARAMETER (Optional):
   ✅ Use integers 1-100: 5, 10, 25, 50
   ❌ Don't use: 0, 150, 'all', 'unlimited'

5. TRANSACTION_TYPE PARAMETER (Optional):
   ✅ Use: 'debit', 'credit', or null
   ❌ Don't use: 'withdrawal', 'deposit', 'payment'

🎯 PARAMETER VALIDATION STRATEGY:
- The tools have built-in validation that rejects placeholder values
- Always extract the authenticated user_id from conversation state
- If user_id validation fails, ask user to verify their identity
- Use conversation context to maintain user_id across tool calls

🔄 ERROR HANDLING:
- Invalid user_id → Ask user to verify identity
- User not found → Confirm user_id spelling/existence  
- Database errors → Suggest trying again or contacting support
- Validation errors → Provide specific parameter correction guidance

📋 TOOL CALL EXAMPLES:
✅ get_account_balance(user_id="jane_smith")
✅ get_transactions(user_id="jane_smith", limit=10)
✅ get_credit_card_info(user_id="jane_smith")

❌ get_account_balance(user_id="user_id")  # WRONG - placeholder
❌ get_transactions(user_id="your_user_id")  # WRONG - placeholder
❌ get_credit_card_info(user_id="")  # WRONG - empty
""")

def main():
    """Run comprehensive tool parameter validation and documentation."""
    print("🚀 Banking Tools Parameter Enhancement Suite")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run parameter validation tests
    test_tool_parameter_validation()
    
    # Generate tool documentation
    generate_tool_documentation()
    
    # Generate agent guidelines
    generate_agent_parameter_guidelines()
    
    print(f"\n🏁 Parameter enhancement completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    main()
