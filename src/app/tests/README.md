# Banking Bot Testing Documentation

## Overview
This directory contains comprehensive tests for the Banking Bot application. The testing suite is organized into multiple modules, each focusing on different aspects of the system.

## Test Structure

```
src/app/tests/
├── __init__.py                     # Package initialization
├── conftest.py                     # Shared fixtures and configuration
├── run_tests.py                    # Comprehensive test runner
├── test_tools_individual.py        # Individual tool testing
├── test_schemas_validation.py      # Schema validation tests
├── test_parameters_enhancement.py  # Parameter validation tests
├── test_agent_integration.py       # End-to-end agent tests
└── test_database_connectivity.py   # Database connection tests
```

## Test Categories

### 🧪 Unit Tests (`-m unit`)
- Individual tool functionality
- Parameter validation
- Database model tests
- Utility function tests

### 🔗 Integration Tests (`-m integration`)
- Tool integration with database
- Agent-tool interactions
- Cross-component functionality
- Data flow validation

### ✅ Validation Tests (`-m validation`)
- Input parameter validation
- Output schema validation
- Data format validation
- Error handling validation

### 🗄️ Database Tests (`-m database`)
- Database connectivity
- Data integrity
- Query performance
- Relationship consistency

### 🤖 Agent Tests (`-m agent`)
- End-to-end conversation flow
- Multi-turn conversations
- Error handling and recovery
- User experience validation

### ⚡ Performance Tests (`-m performance`)
- Response time testing
- Concurrent request handling
- Database query performance
- Resource utilization

## Running Tests

### Quick Start
```bash
# Run all tests (excluding slow ones)
python src/app/tests/run_tests.py

# Run specific test category
python src/app/tests/run_tests.py --type unit
python src/app/tests/run_tests.py --type validation
python src/app/tests/run_tests.py --type agent

# Run specific test file
python src/app/tests/run_tests.py --file test_tools_individual.py

# Include slow/performance tests
python src/app/tests/run_tests.py --type all --slow

# Quick CI/CD tests
python src/app/tests/run_tests.py --type quick
```

### Using pytest directly
```bash
# Run all tests
pytest src/app/tests/

# Run specific markers
pytest src/app/tests/ -m unit
pytest src/app/tests/ -m "validation and not slow"
pytest src/app/tests/ -m database

# Run with coverage
pytest src/app/tests/ --cov=src --cov-report=html

# Run specific file
pytest src/app/tests/test_tools_individual.py -v
```

## Test Configuration

### Prerequisites
1. **Database Setup**: Ensure test database is populated with sample data
2. **Environment**: Set up environment variables for testing  
3. **Dependencies**: Install test requirements
   ```bash
   pip install -r requirements-test.txt
   ```

### Test Data Requirements
- Test user: `jane_smith` with complete data set
- Multiple accounts (checking, savings)
- Transaction history (50+ transactions)
- Credit card information
- Proper user relationships

### Configuration Files
- `pytest.ini`: Pytest configuration and markers
- `conftest.py`: Shared fixtures and test utilities
- `requirements-test.txt`: Testing dependencies

## Test Writing Guidelines

### Test Naming
- Files: `test_*.py`
- Classes: `Test*`
- Functions: `test_*`
- Descriptive names that explain what is being tested

### Test Structure
```python
@pytest.mark.category
def test_specific_functionality(fixtures):
    """Test description explaining what this validates."""
    # Arrange
    setup_test_data()
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result is expected, "Clear error message"
```

### Fixture Usage
- Use provided fixtures from `conftest.py`
- `test_user_data`: Complete test user with accounts/transactions
- `banking_agent`: Banking agent instance
- `database_connection`: Database connection
- `test_thread_id`: Unique thread ID for each test

### Assertion Patterns
```python
# Tool success validation
assert_tool_success(result, expected_keys)

# Tool error validation  
assert_tool_error(result, expected_error_type)

# JSON response validation
result = validate_json_response(response_string)
```

## Continuous Integration

### Quick Tests (CI/CD)
```bash
# Fast tests for continuous integration
python src/app/tests/run_tests.py --type quick
```
- Excludes slow and performance tests
- Stops on first failure
- Optimized for CI/CD pipelines

### Full Test Suite
```bash
# Complete test suite with all tests
python src/app/tests/run_tests.py --type all --slow
```
- Includes all test categories
- Performance and load tests
- Comprehensive validation

## Test Maintenance

### Adding New Tests
1. Choose appropriate test file based on functionality
2. Use existing fixtures and utilities
3. Follow naming conventions
4. Add appropriate markers
5. Update documentation if needed

### Updating Tests After Tool Changes
1. Run relevant test category to identify failures
2. Update test expectations based on new behavior
3. Verify parameter validation still works
4. Check schema validation for output changes
5. Run full test suite to ensure no regressions

### Performance Baselines
- Individual tool calls: < 1 second
- Agent responses: < 10 seconds  
- Database queries: < 2 seconds
- Full conversation: < 30 seconds (with timeout)

## Troubleshooting

### Common Issues

**Database Connection Errors**
- Verify database is running and accessible
- Check that test user `jane_smith` exists with data
- Ensure database schema is up to date

**Test Failures After Tool Updates**
- Run parameter validation tests first
- Check schema validation for output format changes
- Verify tool behavior matches test expectations
- Update test data if needed

**Slow Test Performance**
- Check database query efficiency
- Verify test isolation (tests affecting each other)
- Consider using test data fixtures instead of real queries

**Import Errors**
- Ensure Python path includes project root
- Check that all dependencies are installed
- Verify relative imports are correct

### Debugging Tests
```bash
# Run with verbose output
pytest src/app/tests/ -v -s

# Run single test with debugging
pytest src/app/tests/test_tools_individual.py::TestAccountBalanceTool::test_valid_user_balance -v -s

# Show test durations
pytest src/app/tests/ --durations=10

# Show detailed failure information
pytest src/app/tests/ --tb=long
```

## Coverage Reporting

```bash
# Generate HTML coverage report
python src/app/tests/run_tests.py --coverage

# View coverage report
open htmlcov/index.html
```

## Best Practices

1. **Test Independence**: Each test should be independent and not rely on other tests
2. **Clear Assertions**: Use descriptive error messages in assertions
3. **Proper Cleanup**: Use fixtures for setup/teardown
4. **Performance Awareness**: Mark slow tests appropriately
5. **Documentation**: Comment complex test logic
6. **Data Isolation**: Use test-specific data when possible
7. **Error Testing**: Test both success and failure cases
8. **Realistic Data**: Use realistic test data that matches production patterns

## Maintenance Schedule

- **Before Each Release**: Run full test suite
- **Weekly**: Run performance tests to check for regressions  
- **After Tool Updates**: Run validation and integration tests
- **Monthly**: Review and update test data
- **Quarterly**: Review test coverage and add missing tests
