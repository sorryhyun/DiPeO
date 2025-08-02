"""
Integration tests for input resolution within the execution context.

These tests validate the behavior of input resolution as part of the full execution flow,
including interactions with ExecutionRuntime, ExecutionTracker, and node handlers.
"""

import pytest
from typing import Any, Dict, List
from unittest.mock import Mock, MagicMock, AsyncMock

from dipeo.application.execution.execution_runtime import ExecutionRuntime
from dipeo.application.execution.resolution.input_resolution import TypedInputResolutionService
from dipeo.application.registry import ServiceRegistry
from dipeo.diagram_generated import (
    ExecutionState,
    NodeExecutionStatus,
    NodeID,
    NodeState,
    NodeType,
)
from dipeo.core.execution.node_output import BaseNodeOutput, ConditionOutput
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableEdge, ExecutableNode
from dipeo.diagram_generated.generated_nodes import PersonJobNode, ConditionNode, ApiJobNode


class TestInputResolutionIntegration:
    """Integration tests for input resolution within execution context."""
    
    @pytest.fixture
    def service_registry(self):
        """Create a service registry for testing."""
        return ServiceRegistry()
    
    @pytest.fixture
    def mock_execution_state(self):
        """Create a mock execution state."""
        state = Mock(spec=ExecutionState)
        state.id = "test_execution"
        state.diagram_id = "test_diagram"
        state.variables = {}
        state.node_states = {}
        state.node_outputs = {}  # Add required attribute
        state.exec_counts = {}  # Add required attribute
        return state
    
    @pytest.fixture
    def simple_diagram(self):
        """Create a simple diagram with two connected nodes."""
        # Create nodes
        node1 = Mock(spec=ExecutableNode)
        node1.id = NodeID("node1")
        node1.type = NodeType.API_JOB
        
        node2 = Mock(spec=ExecutableNode)
        node2.id = NodeID("node2")
        node2.type = NodeType.API_JOB
        
        # Create edge
        edge = Mock(spec=ExecutableEdge)
        edge.source_node_id = NodeID("node1")
        edge.target_node_id = NodeID("node2")
        edge.source_output = "default"
        edge.target_input = "default"
        edge.metadata = {}
        edge.data_transform = None
        
        # Create diagram
        diagram = Mock(spec=ExecutableDiagram)
        diagram.nodes = [node1, node2]
        diagram.edges = [edge]
        diagram.get_node = lambda node_id: next((n for n in diagram.nodes if n.id == node_id), None)
        diagram.get_outgoing_edges = lambda node_id: [e for e in diagram.edges if e.source_node_id == node_id]
        
        return diagram
    
    @pytest.fixture
    def person_job_diagram(self):
        """Create a diagram with PersonJob node and first/default inputs."""
        # Create nodes
        start_node = Mock(spec=ExecutableNode)
        start_node.id = NodeID("start")
        start_node.type = NodeType.START
        
        person_job = Mock(spec=PersonJobNode)
        person_job.id = NodeID("person_job")
        person_job.type = NodeType.PERSON_JOB
        person_job.max_iteration = 3
        person_job.memory_settings = None
        
        # Create edges
        first_edge = Mock(spec=ExecutableEdge)
        first_edge.source_node_id = NodeID("start")
        first_edge.target_node_id = NodeID("person_job")
        first_edge.source_output = "default"
        first_edge.target_input = "first"
        first_edge.metadata = {}
        first_edge.data_transform = None
        
        default_edge = Mock(spec=ExecutableEdge)
        default_edge.source_node_id = NodeID("start")
        default_edge.target_node_id = NodeID("person_job")
        default_edge.source_output = "default"
        default_edge.target_input = "default"
        default_edge.metadata = {}
        default_edge.data_transform = None
        
        # Create diagram
        diagram = Mock(spec=ExecutableDiagram)
        diagram.nodes = [start_node, person_job]
        diagram.edges = [first_edge, default_edge]
        diagram.get_node = lambda node_id: next((n for n in diagram.nodes if n.id == node_id), None)
        diagram.get_outgoing_edges = lambda node_id: [e for e in diagram.edges if e.source_node_id == node_id]
        
        return diagram
    
    def test_simple_execution_flow(self, simple_diagram, mock_execution_state, service_registry):
        """Test input resolution in a simple two-node execution flow."""
        # Create execution runtime
        runtime = ExecutionRuntime(
            diagram=simple_diagram,
            execution_state=mock_execution_state,
            service_registry=service_registry
        )
        
        # Simulate node1 execution
        node1_output = BaseNodeOutput(value={"result": "data"}, node_id=NodeID("node1"))
        runtime.transition_node_to_running(NodeID("node1"))
        runtime.transition_node_to_completed(NodeID("node1"), node1_output)
        
        # Resolve inputs for node2
        inputs = runtime.resolve_inputs(simple_diagram.nodes[1])
        
        # Verify inputs
        assert inputs == {"default": {"result": "data"}}
    
    def test_person_job_first_execution(self, person_job_diagram, mock_execution_state, service_registry):
        """Test PersonJob node receives only 'first' inputs on first execution."""
        # Create execution runtime
        runtime = ExecutionRuntime(
            diagram=person_job_diagram,
            execution_state=mock_execution_state,
            service_registry=service_registry
        )
        
        # Simulate start node execution
        start_output = BaseNodeOutput(value="initial_prompt", node_id=NodeID("start"))
        runtime.transition_node_to_running(NodeID("start"))
        runtime.transition_node_to_completed(NodeID("start"), start_output)
        
        # Mark PersonJob as running (first execution)
        runtime.transition_node_to_running(NodeID("person_job"))
        
        # Resolve inputs for person_job
        person_job_node = person_job_diagram.nodes[1]
        inputs = runtime.resolve_inputs(person_job_node)
        
        # Should only receive 'first' input on first execution
        assert inputs == {"first": "initial_prompt"}
        assert "default" not in inputs
    
    def test_person_job_subsequent_execution(self, person_job_diagram, mock_execution_state, service_registry):
        """Test PersonJob node receives only default inputs on subsequent executions."""
        # Create execution runtime
        runtime = ExecutionRuntime(
            diagram=person_job_diagram,
            execution_state=mock_execution_state,
            service_registry=service_registry
        )
        
        # Simulate start node execution
        start_output = BaseNodeOutput(value="follow_up_prompt", node_id=NodeID("start"))
        runtime.transition_node_to_running(NodeID("start"))
        runtime.transition_node_to_completed(NodeID("start"), start_output)
        
        # Simulate first execution completion
        person_job_output = BaseNodeOutput(value="first_response", node_id=NodeID("person_job"))
        runtime.transition_node_to_running(NodeID("person_job"))
        runtime.transition_node_to_completed(NodeID("person_job"), person_job_output)
        
        # Reset for second execution
        runtime.reset_node(NodeID("person_job"))
        runtime.transition_node_to_running(NodeID("person_job"))
        
        # Resolve inputs for second execution
        person_job_node = person_job_diagram.nodes[1]
        inputs = runtime.resolve_inputs(person_job_node)
        
        # Should only receive default input on subsequent executions
        assert inputs == {"default": "follow_up_prompt"}
        assert "first" not in inputs
    
    def test_condition_node_output_handling(self, service_registry, mock_execution_state):
        """Test handling of ConditionNode outputs in input resolution."""
        # Create nodes
        condition_node = Mock(spec=ConditionNode)
        condition_node.id = NodeID("condition")
        condition_node.type = NodeType.CONDITION
        
        api_node1 = Mock(spec=ApiJobNode)
        api_node1.id = NodeID("api1")
        api_node1.type = NodeType.API_JOB
        
        api_node2 = Mock(spec=ApiJobNode)
        api_node2.id = NodeID("api2")
        api_node2.type = NodeType.API_JOB
        
        # Create edges
        true_edge = Mock(spec=ExecutableEdge)
        true_edge.source_node_id = NodeID("condition")
        true_edge.target_node_id = NodeID("api1")
        true_edge.source_output = "condtrue"
        true_edge.target_input = "default"
        true_edge.metadata = {}
        true_edge.data_transform = None
        
        false_edge = Mock(spec=ExecutableEdge)
        false_edge.source_node_id = NodeID("condition")
        false_edge.target_node_id = NodeID("api2")
        false_edge.source_output = "condfalse"
        false_edge.target_input = "default"
        false_edge.metadata = {}
        false_edge.data_transform = None
        
        # Create diagram
        diagram = Mock(spec=ExecutableDiagram)
        diagram.nodes = [condition_node, api_node1, api_node2]
        diagram.edges = [true_edge, false_edge]
        
        # Create execution runtime
        runtime = ExecutionRuntime(
            diagram=diagram,
            execution_state=mock_execution_state,
            service_registry=service_registry
        )
        
        # Simulate condition node execution (true branch)
        condition_output = ConditionOutput(
            value=True,
            node_id=NodeID("condition"),
            true_output={"data": "true_data"},
            false_output={"data": "false_data"}
        )
        runtime.transition_node_to_running(NodeID("condition"))
        runtime.transition_node_to_completed(NodeID("condition"), condition_output)
        
        # Resolve inputs for both API nodes
        api1_inputs = runtime.resolve_inputs(api_node1)
        api2_inputs = runtime.resolve_inputs(api_node2)
        
        # api1 should receive true branch data (condition was true)
        assert api1_inputs == {"default": {"data": "true_data"}}
        # api2 should NOT receive data (condition was true, not false)
        assert api2_inputs == {}
    
    def test_data_transformation_integration(self, service_registry, mock_execution_state):
        """Test data transformation during input resolution."""
        # Create nodes
        node1 = Mock(spec=ExecutableNode)
        node1.id = NodeID("node1")
        node1.type = NodeType.API_JOB
        
        node2 = Mock(spec=ExecutableNode)
        node2.id = NodeID("node2")
        node2.type = NodeType.API_JOB
        
        # Create edge with data transformation
        edge = Mock(spec=ExecutableEdge)
        edge.source_node_id = NodeID("node1")
        edge.target_node_id = NodeID("node2")
        edge.source_output = "default"
        edge.target_input = "default"
        edge.metadata = {}
        edge.data_transform = {"content_type": "object"}
        
        # Create diagram
        diagram = Mock(spec=ExecutableDiagram)
        diagram.nodes = [node1, node2]
        diagram.edges = [edge]
        
        # Create execution runtime
        runtime = ExecutionRuntime(
            diagram=diagram,
            execution_state=mock_execution_state,
            service_registry=service_registry
        )
        
        # Simulate node1 execution with JSON string output
        node1_output = BaseNodeOutput(value='{"key": "value", "number": 42}', node_id=NodeID("node1"))
        runtime.transition_node_to_running(NodeID("node1"))
        runtime.transition_node_to_completed(NodeID("node1"), node1_output)
        
        # Resolve inputs for node2
        inputs = runtime.resolve_inputs(node2)
        
        # Should transform JSON string to object
        assert inputs == {"default": {"key": "value", "number": 42}}
    
    def test_multiple_inputs_resolution(self, service_registry, mock_execution_state):
        """Test resolution of multiple inputs from different sources."""
        # Create nodes
        source1 = Mock(spec=ExecutableNode)
        source1.id = NodeID("source1")
        source1.type = NodeType.API_JOB
        
        source2 = Mock(spec=ExecutableNode)
        source2.id = NodeID("source2")
        source2.type = NodeType.API_JOB
        
        target = Mock(spec=ExecutableNode)
        target.id = NodeID("target")
        target.type = NodeType.TEMPLATE_JOB
        
        # Create edges
        edge1 = Mock(spec=ExecutableEdge)
        edge1.source_node_id = NodeID("source1")
        edge1.target_node_id = NodeID("target")
        edge1.source_output = "default"
        edge1.target_input = "data1"
        edge1.metadata = {}
        edge1.data_transform = None
        
        edge2 = Mock(spec=ExecutableEdge)
        edge2.source_node_id = NodeID("source2")
        edge2.target_node_id = NodeID("target")
        edge2.source_output = "result"
        edge2.target_input = "data2"
        edge2.metadata = {}
        edge2.data_transform = None
        
        # Create diagram
        diagram = Mock(spec=ExecutableDiagram)
        diagram.nodes = [source1, source2, target]
        diagram.edges = [edge1, edge2]
        
        # Create execution runtime
        runtime = ExecutionRuntime(
            diagram=diagram,
            execution_state=mock_execution_state,
            service_registry=service_registry
        )
        
        # Simulate source node executions
        source1_output = BaseNodeOutput(value="value1", node_id=NodeID("source1"))
        source2_output = BaseNodeOutput(value={"result": "value2", "extra": "ignored"}, node_id=NodeID("source2"))
        
        runtime.transition_node_to_running(NodeID("source1"))
        runtime.transition_node_to_completed(NodeID("source1"), source1_output)
        runtime.transition_node_to_running(NodeID("source2"))
        runtime.transition_node_to_completed(NodeID("source2"), source2_output)
        
        # Resolve inputs for target
        inputs = runtime.resolve_inputs(target)
        
        # Should have both inputs
        assert inputs == {
            "data1": "value1",
            "data2": "value2"
        }
    
    def test_conversation_state_special_handling(self, service_registry, mock_execution_state):
        """Test that conversation_state content type is always processed for PersonJob."""
        # Create nodes
        condition_node = Mock(spec=ConditionNode)
        condition_node.id = NodeID("condition")
        condition_node.type = NodeType.CONDITION
        
        person_job = Mock(spec=PersonJobNode)
        person_job.id = NodeID("person_job")
        person_job.type = NodeType.PERSON_JOB
        person_job.max_iteration = 3
        person_job.memory_settings = None
        
        # Create edge with conversation_state content type
        edge = Mock(spec=ExecutableEdge)
        edge.source_node_id = NodeID("condition")
        edge.target_node_id = NodeID("person_job")
        edge.source_output = "default"
        edge.target_input = "conversation_state"
        edge.metadata = {}
        edge.data_transform = {"content_type": "conversation_state"}
        
        # Create diagram
        diagram = Mock(spec=ExecutableDiagram)
        diagram.nodes = [condition_node, person_job]
        diagram.edges = [edge]
        
        # Create execution runtime
        runtime = ExecutionRuntime(
            diagram=diagram,
            execution_state=mock_execution_state,
            service_registry=service_registry
        )
        
        # Simulate condition node execution
        condition_output = BaseNodeOutput(value={"conversation": "state_data"}, node_id=NodeID("condition"))
        runtime.transition_node_to_running(NodeID("condition"))
        runtime.transition_node_to_completed(NodeID("condition"), condition_output)
        
        # Mark PersonJob as running (first execution)
        runtime.transition_node_to_running(NodeID("person_job"))
        
        # Resolve inputs - conversation_state should always be included
        inputs = runtime.resolve_inputs(person_job)
        
        # Should receive conversation_state even on first execution
        assert inputs == {"conversation_state": {"conversation": "state_data"}}


class TestEdgeCasesAndErrors:
    """Test edge cases and error handling in input resolution."""
    
    @pytest.fixture
    def service_registry(self):
        """Create a service registry for testing."""
        return ServiceRegistry()
    
    @pytest.fixture
    def mock_execution_state(self):
        """Create a mock execution state."""
        state = Mock(spec=ExecutionState)
        state.id = "test_execution"
        state.diagram_id = "test_diagram"
        state.variables = {}
        state.node_states = {}
        state.node_outputs = {}  # Add required attribute
        state.exec_counts = {}  # Add required attribute
        return state
    
    def test_circular_dependencies(self, service_registry, mock_execution_state):
        """Test handling of circular dependencies in the diagram."""
        # Create nodes
        node1 = Mock(spec=ExecutableNode)
        node1.id = NodeID("node1")
        node1.type = NodeType.API_JOB
        
        node2 = Mock(spec=ExecutableNode)
        node2.id = NodeID("node2")
        node2.type = NodeType.API_JOB
        
        # Create circular edges
        edge1 = Mock(spec=ExecutableEdge)
        edge1.source_node_id = NodeID("node1")
        edge1.target_node_id = NodeID("node2")
        edge1.source_output = "default"
        edge1.target_input = "default"
        edge1.metadata = {}
        edge1.data_transform = None
        
        edge2 = Mock(spec=ExecutableEdge)
        edge2.source_node_id = NodeID("node2")
        edge2.target_node_id = NodeID("node1")
        edge2.source_output = "default"
        edge2.target_input = "default"
        edge2.metadata = {}
        edge2.data_transform = None
        
        # Create diagram
        diagram = Mock(spec=ExecutableDiagram)
        diagram.nodes = [node1, node2]
        diagram.edges = [edge1, edge2]
        
        # Create execution runtime
        runtime = ExecutionRuntime(
            diagram=diagram,
            execution_state=mock_execution_state,
            service_registry=service_registry
        )
        
        # Neither node has output yet
        inputs1 = runtime.resolve_inputs(node1)
        inputs2 = runtime.resolve_inputs(node2)
        
        # Both should have empty inputs
        assert inputs1 == {}
        assert inputs2 == {}
    
    def test_missing_source_node(self, service_registry, mock_execution_state):
        """Test handling when source node doesn't exist."""
        # Create node
        target = Mock(spec=ExecutableNode)
        target.id = NodeID("target")
        target.type = NodeType.API_JOB
        
        # Create edge with non-existent source
        edge = Mock(spec=ExecutableEdge)
        edge.source_node_id = NodeID("missing_node")
        edge.target_node_id = NodeID("target")
        edge.source_output = "default"
        edge.target_input = "default"
        edge.metadata = {}
        edge.data_transform = None
        
        # Create diagram
        diagram = Mock(spec=ExecutableDiagram)
        diagram.nodes = [target]
        diagram.edges = [edge]
        
        # Create execution runtime
        runtime = ExecutionRuntime(
            diagram=diagram,
            execution_state=mock_execution_state,
            service_registry=service_registry
        )
        
        # Should handle gracefully
        inputs = runtime.resolve_inputs(target)
        assert inputs == {}
    
    def test_complex_node_output_formats(self, service_registry, mock_execution_state):
        """Test handling of various node output formats."""
        # Create nodes
        source = Mock(spec=ExecutableNode)
        source.id = NodeID("source")
        source.type = NodeType.API_JOB
        
        target = Mock(spec=ExecutableNode)
        target.id = NodeID("target")
        target.type = NodeType.API_JOB
        
        # Create edge
        edge = Mock(spec=ExecutableEdge)
        edge.source_node_id = NodeID("source")
        edge.target_node_id = NodeID("target")
        edge.source_output = "nested.path"
        edge.target_input = "default"
        edge.metadata = {}
        edge.data_transform = None
        
        # Create diagram
        diagram = Mock(spec=ExecutableDiagram)
        diagram.nodes = [source, target]
        diagram.edges = [edge]
        
        # Create execution runtime
        runtime = ExecutionRuntime(
            diagram=diagram,
            execution_state=mock_execution_state,
            service_registry=service_registry
        )
        
        # Test with nested output structure
        complex_output = BaseNodeOutput(
            value={
                "nested.path": "direct_value",
                "nested": {
                    "path": "nested_value"
                }
            },
            node_id=NodeID("source")
        )
        runtime.transition_node_to_running(NodeID("source"))
        runtime.transition_node_to_completed(NodeID("source"), complex_output)
        
        # Should use the direct key match
        inputs = runtime.resolve_inputs(target)
        assert inputs == {"default": "direct_value"}