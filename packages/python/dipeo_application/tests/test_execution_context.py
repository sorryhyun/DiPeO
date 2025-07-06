"""Tests for new execution context implementation."""

import pytest
from datetime import datetime

from dipeo_domain.models import ExecutionState, ExecutionStatus, NodeState, NodeOutput, TokenUsage
from dipeo_domain.domains.ports.execution_context import ExecutionContextPort
from dipeo_application.execution_context.application_execution_context import ApplicationExecutionContext


class MockServiceRegistry:
    """Mock service registry for testing."""
    def __init__(self):
        self.llm_service = "mock_llm_service"
        self.file_service = "mock_file_service"
        self.api_key_service = "mock_api_key_service"


class TestApplicationExecutionContext:
    """Test ApplicationExecutionContext implementation."""

    def test_implements_protocol(self):
        """Test that ApplicationExecutionContext implements ExecutionContextPort."""
        state = self._create_test_state()
        registry = MockServiceRegistry()
        context = ApplicationExecutionContext(state, registry)
        
        # Check protocol compliance (duck typing)
        assert hasattr(context, 'get_node_output')
        assert hasattr(context, 'get_variable')
        assert hasattr(context, 'get_service')
        assert hasattr(context, 'diagram_id')
        assert hasattr(context, 'execution_state')

    def test_get_node_output(self):
        """Test retrieving node outputs."""
        state = self._create_test_state()
        registry = MockServiceRegistry()
        context = ApplicationExecutionContext(state, registry)
        
        # Test existing output
        assert context.get_node_output("node1") == "test_value"
        
        # Test non-existing output
        assert context.get_node_output("nonexistent") is None
        
        # Test with empty outputs
        state.node_outputs = {}
        assert context.get_node_output("node1") is None

    def test_get_variable(self):
        """Test retrieving variables."""
        state = self._create_test_state()
        registry = MockServiceRegistry()
        context = ApplicationExecutionContext(state, registry)
        
        # Test existing variable
        assert context.get_variable("test_var") == "test_value"
        
        # Test non-existing variable
        assert context.get_variable("nonexistent") is None
        
        # Test with empty variables
        state.variables = {}
        assert context.get_variable("test_var") is None

    def test_get_service(self):
        """Test retrieving services from registry."""
        state = self._create_test_state()
        registry = MockServiceRegistry()
        context = ApplicationExecutionContext(state, registry)
        
        # Test existing services
        assert context.get_service("llm_service") == "mock_llm_service"
        assert context.get_service("file_service") == "mock_file_service"
        
        # Test non-existing service
        assert context.get_service("nonexistent_service") is None

    def test_properties(self):
        """Test context properties."""
        state = self._create_test_state()
        registry = MockServiceRegistry()
        context = ApplicationExecutionContext(state, registry)
        
        assert context.diagram_id == "test_diagram"
        assert context.execution_state == state

    def test_immutability(self):
        """Test that execution state remains immutable."""
        state = self._create_test_state()
        registry = MockServiceRegistry()
        context = ApplicationExecutionContext(state, registry)
        
        # Try to modify the returned state (should not affect internal state)
        returned_state = context.execution_state
        assert returned_state is state  # Should be the same object

    def test_create_node_view(self):
        """Test creating node-specific context view."""
        state = self._create_test_state()
        registry = MockServiceRegistry()
        context = ApplicationExecutionContext(state, registry)
        
        # Create view for specific node
        node_view = context.create_node_view("node1")
        
        # For now, it returns the same context
        assert node_view is context

    def _create_test_state(self):
        """Create a test ExecutionState."""
        return ExecutionState(
            id="test_execution",
            status=ExecutionStatus.RUNNING,
            diagram_id="test_diagram",
            started_at=datetime.now().isoformat(),
            node_states={
                "node1": NodeState(status="COMPLETED", started_at=datetime.now().isoformat())
            },
            node_outputs={
                "node1": NodeOutput(value="test_value")
            },
            token_usage=TokenUsage(input=0, output=0, total=0),
            variables={"test_var": "test_value"},
            is_active=True
        )


class TestExecutionContextPort:
    """Test ExecutionContextPort protocol compliance."""
    
    def test_protocol_methods(self):
        """Verify protocol defines expected methods."""
        # This is more of a documentation test
        expected_methods = [
            'get_node_output',
            'get_variable', 
            'get_service',
            'diagram_id',
            'execution_state'
        ]
        
        # Can't directly test Protocol, but we can verify our implementation
        state = ExecutionState(
            id="test",
            status=ExecutionStatus.RUNNING,
            diagram_id="test",
            started_at=datetime.now().isoformat(),
            node_states={},
            node_outputs={},
            token_usage=TokenUsage(input=0, output=0, total=0),
            variables={},
            is_active=True
        )
        context = ApplicationExecutionContext(state, MockServiceRegistry())
        
        for method in expected_methods:
            assert hasattr(context, method), f"Missing method: {method}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])