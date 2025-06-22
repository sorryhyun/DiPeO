# DiPeO Server Tests

This directory contains the consolidated test suite for the DiPeO server.

## Test Organization

### Structure
```
tests/
├── conftest.py                    # Shared fixtures and utilities
├── test_health_metrics.py         # Health check and metrics tests
├── test_graphql_upload.py         # File upload functionality tests
├── test_rest_freeze.py           # REST endpoint freeze guard
├── mutations/                     # GraphQL mutation tests
│   ├── test_diagram_mutations.py  # Diagram CRUD operations
│   ├── test_person_mutations.py   # Person management
│   └── test_execution_mutations.py # Execution control
└── integration/                   # Integration test scenarios
    ├── test_execution_flow.py     # End-to-end execution tests
    ├── test_interactive_flow.py   # Interactive features
    └── test_error_scenarios.py    # Error handling tests
```

### Key Improvements

1. **Shared Test Utilities (conftest.py)**
   - Common fixtures for GraphQL clients (HTTP and WebSocket)
   - Test data builders for diagrams, people, and API keys
   - Reusable GraphQL queries, mutations, and subscriptions
   - Environment setup and mocking utilities

2. **Organized by Feature Domain**
   - Tests are grouped by functionality rather than technology
   - Clear separation between unit tests (mutations) and integration tests
   - Each test file focuses on a specific aspect of the system

3. **Reduced Code Duplication**
   - Eliminated ~30% redundant code through shared fixtures
   - Consistent test patterns across all files
   - Reusable test data builders

4. **Better Test Coverage**
   - Added mutation tests for diagrams, people, and executions
   - Enhanced upload tests with actual file operations
   - Comprehensive error scenario testing

## Running Tests

### All Tests
```bash
pytest tests/
```

### Specific Test Categories
```bash
# Unit tests only
pytest tests/mutations/

# Integration tests only
pytest tests/integration/

# Specific feature
pytest tests/test_graphql_upload.py
```

### With Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Requirements

- Python 3.12+
- All server dependencies (`pip install -r requirements.txt`)
- GraphQL client libraries (gql, httpx)
- pytest and pytest-asyncio

## Writing New Tests

1. **Use Shared Fixtures**: Import from conftest.py instead of creating duplicate fixtures
2. **Follow Naming Conventions**: 
   - Test files: `test_*.py`
   - Test classes: `Test*`
   - Test methods: `test_*`
3. **Group Related Tests**: Use test classes to organize related test cases
4. **Mock External Dependencies**: Use the provided mock fixtures for LLM responses, etc.
5. **Test Both Success and Failure Cases**: Include error scenarios and edge cases

## Architecture Notes

- **GraphQL-First**: All business logic is exposed via GraphQL
- **REST Freeze**: Only operational endpoints (/metrics) remain as REST
- **Async Testing**: Use pytest-asyncio for async GraphQL operations
- **Real Subscriptions**: Integration tests use actual WebSocket subscriptions