"""
Tests for the new interface implementations and adapters.

This test suite verifies that:
1. The new interfaces work correctly
2. The adapters maintain backward compatibility
3. The behavior matches the original implementation
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Any

from dipeo.diagram_generated import NodeType
from dipeo.core.static.executable_diagram import ExecutableEdge, ExecutableNode
from dipeo.core.execution.node_output import BaseNodeOutput, ConditionOutput

# Import original implementation
from dipeo.application.execution.resolution.input_resolution import TypedInputResolutionService

# Import new implementations
from dipeo.application.execution.resolution.interfaces import (
    StandardNodeOutput,
    NodeStrategyFactory,
    PersonJobStrategy,
    StandardTransformationEngine,
    ExecutionContextProtocol,
)
from dipeo.application.execution.resolution.adapters import (
    TypedInputResolutionServiceAdapter,
    ExecutionContextAdapter,
    RuntimeInputResolverAdapter,
)
from dipeo.application.execution.resolution.refactored_input_resolution import (
    RefactoredInputResolutionService,
)


class TestInterfaceImplementations:
    """Test the new interface implementations."""
    
    def test_standard_node_output_from_value(self):
        """Test StandardNodeOutput creation from simple value."""
        value = "test_value"
        output = StandardNodeOutput.from_value(value)
        
        assert output.value == value
        assert output.get_output() == value
        assert output.get_output("default") == value
        assert output.has_output("default")
    
    def test_standard_node_output_from_dict(self):
        """Test StandardNodeOutput creation from dict."""
        data = {
            "value": "main_value",
            "outputs": {"custom": "custom_value"},
            "metadata": {"key": "value"}
        }
        output = StandardNodeOutput.from_dict(data)
        
        assert output.value == "main_value"
        assert output.get_output("custom") == "custom_value"
        assert output.metadata == {"key": "value"}
    
    def test_node_strategy_factory(self):
        """Test NodeStrategyFactory returns correct strategies."""
        factory = NodeStrategyFactory()
        
        # Test built-in strategies
        person_strategy = factory.get_strategy(NodeType.PERSON_JOB)
        assert isinstance(person_strategy, PersonJobStrategy)
        assert person_strategy.node_type == NodeType.PERSON_JOB
        
        # Test default strategy for unknown types
        default_strategy = factory.get_strategy(NodeType.API_JOB)
        assert default_strategy.node_type == NodeType.API_JOB
    
    def test_person_job_strategy_first_input_detection(self):
        """Test PersonJob strategy detects first inputs correctly."""
        strategy = PersonJobStrategy()
        
        # Create edges with first inputs
        first_edge = Mock(target_input="first")
        default_edge = Mock(target_input="default")
        custom_first_edge = Mock(target_input="custom_first")
        
        assert strategy.has_first_inputs([first_edge, default_edge])
        assert strategy.has_first_inputs([custom_first_edge])
        assert not strategy.has_first_inputs([default_edge])
    
    def test_transformation_engine(self):
        """Test transformation engine applies rules correctly."""
        engine = StandardTransformationEngine()
        
        # Test content type conversion
        rules = {"content_type": "object"}
        json_string = '{"key": "value"}'
        result = engine.transform(json_string, rules)
        assert result == {"key": "value"}
        
        # Test variable extraction
        rules = {"extract_variable": "field"}
        data = {"field": "extracted_value", "other": "ignored"}
        result = engine.transform(data, rules)
        assert result == "extracted_value"
        
        # Test format transformation
        rules = {"format": "Hello {value}!"}
        result = engine.transform("World", rules)
        assert result == "Hello World!"


class TestAdapterCompatibility:
    """Test that adapters maintain backward compatibility."""
    
    @pytest.fixture
    def mock_diagram(self):
        """Create a mock diagram with edges."""
        diagram = Mock()
        diagram.edges = []
        diagram.get_incoming_edges = Mock(return_value=[])
        diagram.get_node = Mock(return_value=None)
        return diagram
    
    @pytest.fixture
    def mock_edge(self):
        """Create a mock edge."""
        edge = Mock()
        edge.source_node_id = "source"
        edge.target_node_id = "target"
        edge.source_output = None
        edge.target_input = None
        edge.data_transform = None
        edge.metadata = {}
        return edge
    
    def test_execution_context_adapter(self):
        """Test ExecutionContextAdapter provides correct interface."""
        node_outputs = {"node1": "output1"}
        node_exec_counts = {"node1": 1, "node2": 2}
        
        context = ExecutionContextAdapter(
            node_outputs=node_outputs,
            node_exec_counts=node_exec_counts,
            current_node_id="node2"
        )
        
        assert context.get_node_exec_count("node1") == 1
        assert context.get_node_exec_count("node2") == 2
        assert context.get_node_exec_count("node3") == 0  # Missing node
        assert context.has_node_output("node1")
        assert not context.has_node_output("node3")
        assert context.get_node_output("node1") == "output1"
    
    def test_adapter_produces_same_results_as_original(self, mock_diagram, mock_edge):
        """Test that adapter produces same results as original service."""
        # Setup
        node_outputs = {
            "source": {"value": "test_value"}
        }
        mock_edge.source_node_id = "source"
        mock_edge.target_node_id = "target"
        mock_diagram.edges = [mock_edge]
        
        # Original service
        original_service = TypedInputResolutionService()
        
        # Adapted service
        adapted_service = TypedInputResolutionServiceAdapter()
        
        # Both should produce same results
        original_result = original_service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        adapted_result = adapted_service.resolve_inputs_for_node(
            node_id="target", 
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert original_result == adapted_result


class TestRefactoredImplementation:
    """Test the refactored implementation using new interfaces."""
    
    @pytest.fixture
    def mock_node(self):
        """Create a mock executable node."""
        node = Mock(spec=ExecutableNode)
        node.id = "test_node"
        node.type = NodeType.PERSON_JOB
        return node
    
    @pytest.fixture
    def mock_diagram_with_node(self, mock_node):
        """Create a mock diagram with a node."""
        diagram = Mock()
        diagram.get_node = Mock(return_value=mock_node)
        diagram.get_incoming_edges = Mock(return_value=[])
        return diagram
    
    def test_refactored_service_basic_resolution(self, mock_diagram_with_node):
        """Test basic input resolution with refactored service."""
        service = RefactoredInputResolutionService()
        
        node_outputs = {"source": "value"}
        
        result = service.resolve_inputs_for_node(
            node_id="test_node",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram_with_node,
            node_outputs=node_outputs
        )
        
        # Should return empty dict for no incoming edges
        assert result == {}
    
    def test_runtime_resolver_normalization(self):
        """Test that runtime resolver normalizes outputs correctly."""
        resolver = RuntimeInputResolverAdapter()
        
        # Test with NodeOutputProtocol
        mock_output = Mock(spec=BaseNodeOutput)
        mock_output.value = "test_value"
        
        context = Mock()
        context.get_node_output = Mock(return_value=mock_output)
        
        edge = Mock()
        edge.source_node_id = "source"
        edge.source_output = None
        
        value = resolver.get_edge_value(edge, context)
        assert isinstance(value, StandardNodeOutput)
        assert value.value == "test_value"
        
        # Test with dict format
        dict_output = {"value": "dict_value"}
        context.get_node_output = Mock(return_value=dict_output)
        
        value = resolver.get_edge_value(edge, context)
        assert isinstance(value, StandardNodeOutput)
        assert value.value == "dict_value"
        
        # Test with raw value
        raw_output = "raw_value"
        context.get_node_output = Mock(return_value=raw_output)
        
        value = resolver.get_edge_value(edge, context)
        assert isinstance(value, StandardNodeOutput)
        assert value.value == "raw_value"


class TestPersonJobFirstInputBehavior:
    """Test PersonJob first input behavior with new implementation."""
    
    def test_person_job_strategy_should_process_edge(self):
        """Test PersonJob strategy edge processing logic."""
        strategy = PersonJobStrategy()
        
        # Mock objects
        node = Mock()
        node.id = "person_node"
        node.type = NodeType.PERSON_JOB
        
        context = Mock(spec=ExecutionContextProtocol)
        
        # First execution with first input
        context.get_node_exec_count = Mock(return_value=1)
        edge_first = Mock()
        edge_first.target_input = "first"
        edge_first.data_transform = None
        
        assert strategy.should_process_edge(
            edge_first, node, context, has_special_inputs=True
        )
        
        # First execution with default input (no first inputs exist)
        edge_default = Mock()
        edge_default.target_input = "default"
        edge_default.data_transform = None
        
        assert strategy.should_process_edge(
            edge_default, node, context, has_special_inputs=False
        )
        
        # Second execution should skip first inputs
        context.get_node_exec_count = Mock(return_value=2)
        
        assert not strategy.should_process_edge(
            edge_first, node, context, has_special_inputs=True
        )
        assert strategy.should_process_edge(
            edge_default, node, context, has_special_inputs=True
        )
    
    def test_conversation_state_always_processed(self):
        """Test that conversation_state inputs are always processed."""
        strategy = PersonJobStrategy()
        
        node = Mock()
        node.type = NodeType.PERSON_JOB
        
        context = Mock(spec=ExecutionContextProtocol)
        context.get_node_exec_count = Mock(return_value=1)
        
        # Edge with conversation_state content type
        edge = Mock()
        edge.target_input = "default"
        edge.data_transform = {"content_type": "conversation_state"}
        
        # Should be processed even on first execution with first inputs
        assert strategy.should_process_edge(
            edge, node, context, has_special_inputs=True
        )