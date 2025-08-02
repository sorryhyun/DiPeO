"""
Pytest fixtures for input resolution tests.

Provides reusable test fixtures for creating mock diagrams, nodes, edges,
and other components needed for testing the input resolution mechanism.
"""

import pytest
from typing import List, Optional, Dict, Any
from unittest.mock import Mock, MagicMock

from dipeo.diagram_generated import (
    NodeType,
    NodeID,
    ExecutionState,
    NodeExecutionStatus,
    NodeState,
)
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableEdge, ExecutableNode
from dipeo.diagram_generated.generated_nodes import (
    PersonJobNode,
    ConditionNode,
    ApiJobNode,
    TemplateJobNode,
    StartNode,
)
from dipeo.core.execution.node_output import BaseNodeOutput, ConditionOutput
from dipeo.diagram_generated import NodeID


# ===== Node Fixtures =====

@pytest.fixture
def create_node():
    """Factory for creating mock ExecutableNode instances."""
    def _create_node(
        node_id: str,
        node_type: NodeType = NodeType.API_JOB,
        **kwargs
    ) -> ExecutableNode:
        node = Mock(spec=ExecutableNode)
        node.id = NodeID(node_id)
        node.type = node_type
        
        # Add any additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(node, key, value)
        
        return node
    return _create_node


@pytest.fixture
def create_person_job_node():
    """Factory for creating mock PersonJobNode instances."""
    def _create_person_job_node(
        node_id: str,
        max_iteration: int = 3,
        memory_settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> PersonJobNode:
        node = Mock(spec=PersonJobNode)
        node.id = NodeID(node_id)
        node.type = NodeType.PERSON_JOB
        node.max_iteration = max_iteration
        node.memory_settings = memory_settings
        
        for key, value in kwargs.items():
            setattr(node, key, value)
        
        return node
    return _create_person_job_node


@pytest.fixture
def create_condition_node():
    """Factory for creating mock ConditionNode instances."""
    def _create_condition_node(
        node_id: str,
        **kwargs
    ) -> ConditionNode:
        node = Mock(spec=ConditionNode)
        node.id = NodeID(node_id)
        node.type = NodeType.CONDITION
        
        for key, value in kwargs.items():
            setattr(node, key, value)
        
        return node
    return _create_condition_node


# ===== Edge Fixtures =====

@pytest.fixture
def create_edge():
    """Factory for creating mock ExecutableEdge instances."""
    def _create_edge(
        source_node_id: str,
        target_node_id: str,
        source_output: str = "default",
        target_input: str = "default",
        data_transform: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ExecutableEdge:
        edge = Mock(spec=ExecutableEdge)
        edge.source_node_id = NodeID(source_node_id)
        edge.target_node_id = NodeID(target_node_id)
        edge.source_output = source_output
        edge.target_input = target_input
        edge.data_transform = data_transform
        edge.metadata = metadata or {}
        
        for key, value in kwargs.items():
            setattr(edge, key, value)
        
        return edge
    return _create_edge


# ===== Diagram Fixtures =====

@pytest.fixture
def create_diagram():
    """Factory for creating mock ExecutableDiagram instances."""
    def _create_diagram(
        nodes: List[ExecutableNode],
        edges: List[ExecutableEdge],
        **kwargs
    ) -> ExecutableDiagram:
        diagram = Mock(spec=ExecutableDiagram)
        diagram.nodes = nodes
        diagram.edges = edges
        
        # Helper methods
        diagram.get_node = lambda node_id: next(
            (n for n in diagram.nodes if n.id == node_id), 
            None
        )
        diagram.get_outgoing_edges = lambda node_id: [
            e for e in diagram.edges if e.source_node_id == node_id
        ]
        diagram.get_incoming_edges = lambda node_id: [
            e for e in diagram.edges if e.target_node_id == node_id
        ]
        
        for key, value in kwargs.items():
            setattr(diagram, key, value)
        
        return diagram
    return _create_diagram


# ===== Output Fixtures =====

@pytest.fixture
def create_node_output():
    """Factory for creating NodeOutput instances."""
    def _create_node_output(
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BaseNodeOutput:
        # Create a mock node_id for the output
        from dipeo.diagram_generated import NodeID
        return BaseNodeOutput(value=value, node_id=NodeID("test_node"), metadata=metadata or {})
    return _create_node_output


@pytest.fixture
def create_condition_output():
    """Factory for creating ConditionOutput instances."""
    def _create_condition_output(
        value: bool,
        true_output: Optional[Dict[str, Any]] = None,
        false_output: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        node_id: str = "test_condition"
    ) -> ConditionOutput:
        return ConditionOutput(
            value=value,
            node_id=NodeID(node_id),
            true_output=true_output or {},
            false_output=false_output or {},
            metadata=metadata or {}
        )
    return _create_condition_output


# ===== Execution State Fixtures =====

@pytest.fixture
def create_execution_state():
    """Factory for creating mock ExecutionState instances."""
    def _create_execution_state(
        execution_id: str = "test_execution",
        diagram_id: str = "test_diagram",
        variables: Optional[Dict[str, Any]] = None,
        node_states: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ExecutionState:
        state = Mock(spec=ExecutionState)
        state.id = execution_id
        state.diagram_id = diagram_id
        state.variables = variables or {}
        state.node_states = node_states or {}
        
        for key, value in kwargs.items():
            setattr(state, key, value)
        
        return state
    return _create_execution_state


# ===== Sample Diagram Fixtures =====

@pytest.fixture
def linear_diagram(create_node, create_edge, create_diagram):
    """Create a simple linear diagram: A -> B -> C."""
    node_a = create_node("A", NodeType.START)
    node_b = create_node("B", NodeType.API_JOB)
    node_c = create_node("C", NodeType.API_JOB)
    
    edge_ab = create_edge("A", "B")
    edge_bc = create_edge("B", "C")
    
    return create_diagram([node_a, node_b, node_c], [edge_ab, edge_bc])


@pytest.fixture
def branching_diagram(create_node, create_condition_node, create_edge, create_diagram):
    """Create a branching diagram with condition node."""
    start = create_node("start", NodeType.START)
    condition = create_condition_node("condition")
    branch_a = create_node("branch_a", NodeType.API_JOB)
    branch_b = create_node("branch_b", NodeType.API_JOB)
    
    edge_start = create_edge("start", "condition")
    edge_true = create_edge("condition", "branch_a", source_output="condtrue")
    edge_false = create_edge("condition", "branch_b", source_output="condfalse")
    
    return create_diagram(
        [start, condition, branch_a, branch_b],
        [edge_start, edge_true, edge_false]
    )


@pytest.fixture
def person_job_diagram(create_node, create_person_job_node, create_edge, create_diagram):
    """Create a diagram with PersonJob node and first/default inputs."""
    start = create_node("start", NodeType.START)
    person_job = create_person_job_node("person", max_iteration=3)
    end = create_node("end", NodeType.API_JOB)
    
    # Two inputs to PersonJob: first and default
    edge_first = create_edge("start", "person", target_input="first")
    edge_default = create_edge("start", "person", target_input="default")
    edge_output = create_edge("person", "end")
    
    return create_diagram(
        [start, person_job, end],
        [edge_first, edge_default, edge_output]
    )


@pytest.fixture
def complex_diagram(
    create_node, 
    create_person_job_node, 
    create_condition_node, 
    create_edge, 
    create_diagram
):
    """Create a complex diagram with multiple node types and connections."""
    # Nodes
    start = create_node("start", NodeType.START)
    api1 = create_node("api1", NodeType.API_JOB)
    api2 = create_node("api2", NodeType.API_JOB)
    person = create_person_job_node("person", max_iteration=5)
    condition = create_condition_node("condition")
    template = create_node("template", NodeType.TEMPLATE_JOB)
    
    # Edges with various configurations
    edges = [
        create_edge("start", "api1"),
        create_edge("start", "api2"),
        create_edge("api1", "person", target_input="first"),
        create_edge("api2", "person", target_input="context"),
        create_edge("person", "condition"),
        create_edge("condition", "template", source_output="condtrue"),
        create_edge(
            "api2", 
            "template", 
            target_input="data",
            data_transform={"content_type": "object"}
        ),
    ]
    
    return create_diagram(
        [start, api1, api2, person, condition, template],
        edges
    )


# ===== Test Data Fixtures =====

@pytest.fixture
def sample_json_data():
    """Sample JSON data for transformation tests."""
    return {
        "valid_object": '{"name": "test", "value": 123}',
        "valid_array": '[1, 2, 3, "four"]',
        "nested_object": '{"level1": {"level2": {"data": "nested"}}}',
        "invalid_json": "{invalid: json}",
        "empty_string": "",
        "null_value": "null",
        "boolean_true": "true",
        "boolean_false": "false",
        "number": "42.5",
        "quoted_string": '"hello world"',
    }


@pytest.fixture
def sample_node_outputs():
    """Sample node outputs for testing."""
    return {
        "simple_value": {"value": "test_data"},
        "node_output": BaseNodeOutput(value="test_value", node_id=NodeID("test_node")),
        "condition_true": ConditionOutput(
            value=True,
            node_id=NodeID("test_condition"),
            true_output={"data": "true_branch"},
            false_output={"data": "false_branch"}
        ),
        "condition_false": ConditionOutput(
            value=False,
            node_id=NodeID("test_condition"),
            true_output={"data": "true_branch"},
            false_output={"data": "false_branch"}
        ),
        "raw_value": "raw_string",
        "complex_output": {
            "value": {
                "default": "default_value",
                "custom": "custom_value",
                "nested": {
                    "deep": "deep_value"
                }
            }
        }
    }


# ===== Execution Context Fixtures =====

@pytest.fixture
def node_exec_counts():
    """Sample node execution counts."""
    return {
        "node1": 1,
        "node2": 2,
        "person_job": 1,
        "condition": 3,
    }


@pytest.fixture
def empty_node_outputs():
    """Empty node outputs dictionary."""
    return {}


# ===== Service Registry Fixtures =====

@pytest.fixture
def mock_service_registry():
    """Create a mock service registry."""
    from dipeo.application.registry import ServiceRegistry
    return ServiceRegistry()


# ===== Utility Fixtures =====

@pytest.fixture
def assert_inputs_equal():
    """Helper to assert input dictionaries are equal with better error messages."""
    def _assert_inputs_equal(actual: Dict[str, Any], expected: Dict[str, Any]):
        assert set(actual.keys()) == set(expected.keys()), \
            f"Input keys mismatch. Actual: {set(actual.keys())}, Expected: {set(expected.keys())}"
        
        for key in expected:
            assert actual[key] == expected[key], \
                f"Value mismatch for key '{key}'. Actual: {actual[key]}, Expected: {expected[key]}"
    
    return _assert_inputs_equal