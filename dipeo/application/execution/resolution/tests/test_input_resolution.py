"""
Comprehensive tests for TypedInputResolutionService.

This test suite documents and validates the expected behavior of the input resolution mechanism,
including edge cases and special handling for different node types.
"""

import pytest
from typing import Any, Optional
from unittest.mock import Mock, MagicMock

from dipeo.application.execution.resolution.input_resolution import TypedInputResolutionService
from dipeo.diagram_generated import NodeType
from dipeo.core.execution.node_output import BaseNodeOutput, ConditionOutput
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableEdge, ExecutableNode


class TestTypedInputResolutionService:
    """Test suite for TypedInputResolutionService."""
    
    @pytest.fixture
    def service(self):
        """Create input resolution service instance."""
        return TypedInputResolutionService()
    
    @pytest.fixture
    def mock_edge(self):
        """Create a mock edge for testing."""
        edge = Mock(spec=ExecutableEdge)
        edge.source_node_id = "source_node"
        edge.target_node_id = "target_node"
        edge.source_output = "default"
        edge.target_input = "default"
        edge.metadata = {}
        edge.data_transform = None
        return edge
    
    @pytest.fixture
    def mock_diagram(self):
        """Create a mock executable diagram."""
        diagram = Mock(spec=ExecutableDiagram)
        diagram.edges = []
        return diagram
    
    def test_resolve_inputs_empty_edges(self, service, mock_diagram):
        """Test input resolution with no incoming edges."""
        node_outputs = {}
        
        result = service.resolve_inputs_for_node(
            node_id="test_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {}
    
    def test_resolve_inputs_basic(self, service, mock_diagram, mock_edge):
        """Test basic input resolution with single edge."""
        mock_edge.target_node_id = "target_node"
        mock_diagram.edges = [mock_edge]
        
        node_outputs = {
            "source_node": {"value": "test_value"}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": "test_value"}
    
    def test_resolve_inputs_with_node_output_protocol(self, service, mock_diagram, mock_edge):
        """Test input resolution with NodeOutputProtocol objects."""
        mock_edge.target_node_id = "target_node"
        mock_diagram.edges = [mock_edge]
        
        # Create NodeOutput with required node_id
        from dipeo.diagram_generated import NodeID
        node_output = BaseNodeOutput(value="test_value", node_id=NodeID("source_node"))
        node_outputs = {
            "source_node": node_output
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": "test_value"}
    
    def test_resolve_inputs_condition_output_true(self, service, mock_diagram, mock_edge):
        """Test input resolution with ConditionOutput (true branch)."""
        mock_edge.target_node_id = "target_node"
        mock_diagram.edges = [mock_edge]
        
        from dipeo.diagram_generated import NodeID
        condition_output = ConditionOutput(
            value=True,
            node_id=NodeID("source_node"),
            true_output={"result": "true_path"},
            false_output={"result": "false_path"}
        )
        node_outputs = {
            "source_node": condition_output
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": {"condtrue": {"result": "true_path"}}}
    
    def test_resolve_inputs_condition_output_false(self, service, mock_diagram, mock_edge):
        """Test input resolution with ConditionOutput (false branch)."""
        mock_edge.target_node_id = "target_node"
        mock_diagram.edges = [mock_edge]
        
        from dipeo.diagram_generated import NodeID
        condition_output = ConditionOutput(
            value=False,
            node_id=NodeID("source_node"),
            true_output={"result": "true_path"},
            false_output={"result": "false_path"}
        )
        node_outputs = {
            "source_node": condition_output
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": {"condfalse": {"result": "false_path"}}}
    
    def test_resolve_inputs_with_named_outputs(self, service, mock_diagram, mock_edge):
        """Test input resolution with named source outputs."""
        mock_edge.target_node_id = "target_node"
        mock_edge.source_output = "custom_output"
        mock_diagram.edges = [mock_edge]
        
        node_outputs = {
            "source_node": {"value": {"custom_output": "custom_value", "default": "default_value"}}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": "custom_value"}
    
    def test_resolve_inputs_with_labeled_edge(self, service, mock_diagram, mock_edge):
        """Test input resolution with edge labels."""
        mock_edge.target_node_id = "target_node"
        mock_edge.metadata = {"label": "custom_input"}
        mock_diagram.edges = [mock_edge]
        
        node_outputs = {
            "source_node": {"value": "test_value"}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"custom_input": "test_value"}
    
    def test_resolve_inputs_data_transform_object(self, service, mock_diagram, mock_edge):
        """Test input resolution with data transformation (JSON string to object)."""
        mock_edge.target_node_id = "target_node"
        mock_edge.data_transform = {"content_type": "object"}
        mock_diagram.edges = [mock_edge]
        
        node_outputs = {
            "source_node": {"value": '{"key": "value"}'}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": {"key": "value"}}
    
    def test_resolve_inputs_data_transform_invalid_json(self, service, mock_diagram, mock_edge):
        """Test input resolution with invalid JSON for object content type."""
        mock_edge.target_node_id = "target_node"
        mock_edge.data_transform = {"content_type": "object"}
        mock_diagram.edges = [mock_edge]
        
        node_outputs = {
            "source_node": {"value": "not valid json"}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        # Should keep original value if JSON parsing fails
        assert result == {"default": "not valid json"}
    
    def test_person_job_first_execution_with_first_inputs(self, service, mock_diagram):
        """Test PersonJob node on first execution with 'first' inputs."""
        edge1 = Mock(spec=ExecutableEdge)
        edge1.source_node_id = "source1"
        edge1.target_node_id = "person_job"
        edge1.source_output = "default"
        edge1.target_input = "first"
        edge1.metadata = {}
        edge1.data_transform = None
        
        edge2 = Mock(spec=ExecutableEdge)
        edge2.source_node_id = "source2"
        edge2.target_node_id = "person_job"
        edge2.source_output = "default"
        edge2.target_input = "default"
        edge2.metadata = {}
        edge2.data_transform = None
        
        mock_diagram.edges = [edge1, edge2]
        
        node_outputs = {
            "source1": {"value": "first_value"},
            "source2": {"value": "default_value"}
        }
        
        node_exec_counts = {"person_job": 1}
        
        result = service.resolve_inputs_for_node(
            node_id="person_job",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs,
            node_exec_counts=node_exec_counts
        )
        
        # On first execution with first inputs, only process "first" inputs
        assert result == {"first": "first_value"}
    
    def test_person_job_first_execution_without_first_inputs(self, service, mock_diagram, mock_edge):
        """Test PersonJob node on first execution without 'first' inputs."""
        mock_edge.target_node_id = "person_job"
        mock_edge.target_input = "default"
        mock_diagram.edges = [mock_edge]
        
        node_outputs = {
            "source_node": {"value": "default_value"}
        }
        
        node_exec_counts = {"person_job": 1}
        
        result = service.resolve_inputs_for_node(
            node_id="person_job",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs,
            node_exec_counts=node_exec_counts
        )
        
        # On first execution without first inputs, process default inputs
        assert result == {"default": "default_value"}
    
    def test_person_job_subsequent_execution(self, service, mock_diagram):
        """Test PersonJob node on subsequent executions."""
        edge1 = Mock(spec=ExecutableEdge)
        edge1.source_node_id = "source1"
        edge1.target_node_id = "person_job"
        edge1.source_output = "default"
        edge1.target_input = "first"
        edge1.metadata = {}
        edge1.data_transform = None
        
        edge2 = Mock(spec=ExecutableEdge)
        edge2.source_node_id = "source2"
        edge2.target_node_id = "person_job"
        edge2.source_output = "default"
        edge2.target_input = "default"
        edge2.metadata = {}
        edge2.data_transform = None
        
        mock_diagram.edges = [edge1, edge2]
        
        node_outputs = {
            "source1": {"value": "first_value"},
            "source2": {"value": "default_value"}
        }
        
        node_exec_counts = {"person_job": 2}  # Second execution
        
        result = service.resolve_inputs_for_node(
            node_id="person_job",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs,
            node_exec_counts=node_exec_counts
        )
        
        # On subsequent executions, ignore "first" inputs
        assert result == {"default": "default_value"}
    
    def test_person_job_conversation_state_always_processed(self, service, mock_diagram, mock_edge):
        """Test PersonJob node always processes conversation_state inputs."""
        mock_edge.target_node_id = "person_job"
        mock_edge.data_transform = {"content_type": "conversation_state"}
        mock_diagram.edges = [mock_edge]
        
        node_outputs = {
            "source_node": {"value": {"state": "conversation_data"}}
        }
        
        node_exec_counts = {"person_job": 1}
        
        result = service.resolve_inputs_for_node(
            node_id="person_job",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs,
            node_exec_counts=node_exec_counts
        )
        
        # conversation_state should always be processed
        assert result == {"default": {"state": "conversation_data"}}
    
    def test_multiple_incoming_edges(self, service, mock_diagram):
        """Test node with multiple incoming edges."""
        edge1 = Mock(spec=ExecutableEdge)
        edge1.source_node_id = "source1"
        edge1.target_node_id = "target"
        edge1.source_output = "default"
        edge1.target_input = "input1"
        edge1.metadata = {}
        edge1.data_transform = None
        
        edge2 = Mock(spec=ExecutableEdge)
        edge2.source_node_id = "source2"
        edge2.target_node_id = "target"
        edge2.source_output = "default"
        edge2.target_input = "input2"
        edge2.metadata = {}
        edge2.data_transform = None
        
        mock_diagram.edges = [edge1, edge2]
        
        node_outputs = {
            "source1": {"value": "value1"},
            "source2": {"value": "value2"}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"input1": "value1", "input2": "value2"}
    
    def test_missing_source_output(self, service, mock_diagram, mock_edge):
        """Test edge with missing source output."""
        mock_edge.target_node_id = "target_node"
        mock_diagram.edges = [mock_edge]
        
        node_outputs = {}  # No output from source node
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {}
    
    def test_raw_value_output(self, service, mock_diagram, mock_edge):
        """Test with raw value output (not dict or NodeOutputProtocol)."""
        mock_edge.target_node_id = "target_node"
        mock_diagram.edges = [mock_edge]
        
        node_outputs = {
            "source_node": "raw_string_value"  # Raw value, not wrapped
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": "raw_string_value"}
    
    def test_complex_output_key_matching(self, service, mock_diagram, mock_edge):
        """Test complex scenarios for output key matching."""
        mock_edge.target_node_id = "target_node"
        mock_edge.source_output = "missing_key"
        mock_diagram.edges = [mock_edge]
        
        # Output doesn't have requested key, but has default
        node_outputs = {
            "source_node": {"value": {"default": "default_value", "other": "other_value"}}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        # Should fall back to default when requested key is missing
        assert result == {"default": "default_value"}
    
    def test_edge_with_no_matching_output(self, service, mock_diagram, mock_edge):
        """Test edge when no matching output key exists."""
        mock_edge.target_node_id = "target_node"
        mock_edge.source_output = "missing_key"
        mock_diagram.edges = [mock_edge]
        
        # Output has neither requested key nor default
        node_outputs = {
            "source_node": {"value": {"other": "other_value"}}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target_node",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        # Should skip this edge
        assert result == {}


class TestShouldProcessEdge:
    """Test the _should_process_edge method specifically."""
    
    @pytest.fixture
    def service(self):
        """Create input resolution service instance."""
        return TypedInputResolutionService()
    
    @pytest.fixture
    def mock_edge(self):
        """Create a mock edge for testing."""
        edge = Mock()
        edge.target_node_id = "test_node"
        edge.target_input = "default"
        edge.data_transform = None
        return edge
    
    def test_non_person_job_always_processed(self, service, mock_edge):
        """Test that non-PersonJob nodes always process edges."""
        result = service._should_process_edge(
            mock_edge, 
            NodeType.API_JOB,
            node_exec_counts=None,
            has_first_inputs=False
        )
        assert result is True
    
    def test_person_job_first_execution_conversation_state(self, service, mock_edge):
        """Test PersonJob always processes conversation_state on first execution."""
        mock_edge.data_transform = {"content_type": "conversation_state"}
        
        result = service._should_process_edge(
            mock_edge,
            NodeType.PERSON_JOB,
            node_exec_counts={"test_node": 1},
            has_first_inputs=True
        )
        assert result is True
    
    def test_person_job_first_execution_with_first_input(self, service, mock_edge):
        """Test PersonJob processes 'first' input on first execution when first inputs exist."""
        mock_edge.target_input = "first"
        
        result = service._should_process_edge(
            mock_edge,
            NodeType.PERSON_JOB,
            node_exec_counts={"test_node": 1},
            has_first_inputs=True
        )
        assert result is True
    
    def test_person_job_first_execution_without_first_input(self, service, mock_edge):
        """Test PersonJob doesn't process default input on first execution when first inputs exist."""
        mock_edge.target_input = "default"
        
        result = service._should_process_edge(
            mock_edge,
            NodeType.PERSON_JOB,
            node_exec_counts={"test_node": 1},
            has_first_inputs=True
        )
        assert result is False
    
    def test_person_job_subsequent_execution_filters_first(self, service, mock_edge):
        """Test PersonJob filters out 'first' inputs on subsequent executions."""
        mock_edge.target_input = "first"
        
        result = service._should_process_edge(
            mock_edge,
            NodeType.PERSON_JOB,
            node_exec_counts={"test_node": 2},
            has_first_inputs=False
        )
        assert result is False
    
    def test_person_job_subsequent_execution_allows_default(self, service, mock_edge):
        """Test PersonJob allows default inputs on subsequent executions."""
        mock_edge.target_input = "default"
        
        result = service._should_process_edge(
            mock_edge,
            NodeType.PERSON_JOB,
            node_exec_counts={"test_node": 2},
            has_first_inputs=False
        )
        assert result is True