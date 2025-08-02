# Input Resolution Test Suite

This directory contains comprehensive tests for the input resolution mechanism in DiPeO.

## Test Structure

### Core Test Files

1. **`test_input_resolution.py`**
   - Unit tests for `TypedInputResolutionService`
   - Tests basic input resolution functionality
   - Tests PersonJob special handling
   - Tests edge processing logic

2. **`test_input_resolution_integration.py`**
   - Integration tests with `ExecutionRuntime`
   - Tests full execution flow scenarios
   - Tests complex diagram interactions
   - Tests error handling and edge cases

3. **`test_data_transformation.py`**
   - Tests for content type transformations
   - JSON parsing and validation
   - Special content type handling
   - Edge metadata processing

4. **`test_fixtures_usage.py`**
   - Examples of using test fixtures
   - Demonstrates test patterns
   - Reference for writing new tests

### Supporting Files

- **`conftest.py`** - Pytest fixtures and utilities
- **`INPUT_RESOLUTION_BEHAVIOR.md`** - Expected behavior documentation
- **`__init__.py`** - Package marker

## Running Tests

```bash
# Run all input resolution tests
pytest dipeo/application/execution/resolution/tests/

# Run specific test file
pytest dipeo/application/execution/resolution/tests/test_input_resolution.py

# Run with coverage
pytest --cov=dipeo.application.execution.resolution dipeo/application/execution/resolution/tests/

# Run specific test
pytest dipeo/application/execution/resolution/tests/test_input_resolution.py::TestTypedInputResolutionService::test_resolve_inputs_basic
```

## Test Coverage Areas

### 1. Basic Input Resolution
- Simple edge connections
- Named inputs and outputs
- Multiple input sources
- Missing outputs handling

### 2. Node Type Special Cases
- PersonJob first/default input logic
- Condition node branching
- Conversation state handling

### 3. Data Transformation
- JSON string to object conversion
- Content type handling
- Invalid data graceful handling
- Unicode and special characters

### 4. Integration Scenarios
- Full execution flow
- State management
- Error propagation
- Complex diagram patterns

## Writing New Tests

### Using Fixtures

The test suite provides rich fixtures for creating test scenarios:

```python
def test_new_scenario(
    service,              # Input resolution service
    create_node,          # Node factory
    create_edge,          # Edge factory  
    create_diagram,       # Diagram factory
    sample_node_outputs   # Sample outputs
):
    # Build test scenario
    node1 = create_node("node1", NodeType.API_JOB)
    node2 = create_node("node2", NodeType.TEMPLATE_JOB)
    edge = create_edge("node1", "node2")
    diagram = create_diagram([node1, node2], [edge])
    
    # Test resolution
    result = service.resolve_inputs_for_node(...)
```

### Test Patterns

1. **Unit Tests**: Test single methods in isolation
2. **Integration Tests**: Test interaction between components
3. **Edge Case Tests**: Test error conditions and boundaries
4. **Fixture Usage Examples**: Reference implementations

## Key Test Scenarios

### PersonJob First Input Handling
- First execution with "first" inputs available
- First execution without "first" inputs
- Subsequent executions
- Conversation state special handling

### Data Transformation
- Valid JSON parsing
- Invalid JSON handling
- Content type conversions
- Metadata processing

### Error Conditions
- Missing source nodes
- Circular dependencies
- Invalid transformations
- Missing outputs

## Maintenance

When modifying the input resolution mechanism:

1. Run existing tests to ensure compatibility
2. Add tests for new functionality
3. Update behavior documentation
4. Consider edge cases and error scenarios
5. Maintain high test coverage (aim for >90%)

## Future Enhancements

Areas for additional testing:
- Performance tests for large diagrams
- Concurrent execution scenarios
- Memory optimization validation
- Additional content type transformations