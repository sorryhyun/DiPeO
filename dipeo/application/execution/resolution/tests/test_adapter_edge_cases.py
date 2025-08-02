"""
Test edge cases and complex scenarios with the adapters.

This ensures the adapters handle all the subtle behaviors correctly.
"""

import pytest
from unittest.mock import Mock

from dipeo.diagram_generated import NodeType
from dipeo.core.static.executable_diagram import ExecutableEdge

from dipeo.application.execution.resolution.input_resolution import TypedInputResolutionService
from dipeo.application.execution.resolution.adapters import TypedInputResolutionServiceAdapter


class TestAdapterEdgeCases:
    """Test edge cases to ensure adapters handle complex scenarios."""
    
    @pytest.fixture
    def create_edge(self):
        """Factory for creating test edges."""
        def _create(source="source", target="target", source_output=None, 
                   target_input=None, data_transform=None):
            edge = Mock(spec=ExecutableEdge)
            edge.id = f"{source}->{target}"
            edge.source_node_id = source
            edge.target_node_id = target
            edge.source_output = source_output
            edge.target_input = target_input
            edge.data_transform = data_transform
            edge.metadata = {}
            return edge
        return _create
    
    @pytest.fixture
    def mock_diagram(self):
        """Create a mock diagram."""
        diagram = Mock()
        diagram.edges = []
        diagram.get_incoming_edges = lambda node_id: [
            e for e in diagram.edges if str(e.target_node_id) == node_id
        ]
        node = Mock()
        node.id = "person_node"
        node.type = NodeType.PERSON_JOB
        diagram.get_node = Mock(return_value=node)
        return diagram
    
    def test_person_job_complex_first_input_scenario(self, create_edge, mock_diagram):
        """Test complex PersonJob scenario with mixed first/default inputs."""
        # Setup: PersonJob with both first and default inputs
        edges = [
            create_edge("init", "person_node", target_input="first"),
            create_edge("config", "person_node", target_input="config_first"),
            create_edge("data", "person_node", target_input="default"),
            create_edge("context", "person_node"),  # implicit default
        ]
        mock_diagram.edges = edges
        
        node_outputs = {
            "init": {"value": "initial_prompt"},
            "config": {"value": {"model": "gpt-4"}},
            "data": {"value": "data_value"},
            "context": {"value": "context_value"}
        }
        
        # Test with original service
        original = TypedInputResolutionService()
        original_result = original.resolve_inputs_for_node(
            node_id="person_node",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs,
            node_exec_counts={"person_node": 1}  # First execution
        )
        
        # Test with adapter
        adapter = TypedInputResolutionServiceAdapter()
        adapter_result = adapter.resolve_inputs_for_node(
            node_id="person_node",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs,
            node_exec_counts={"person_node": 1}  # First execution
        )
        
        # Both should process only "first" inputs on first execution
        assert original_result == adapter_result
        assert "first" in original_result
        assert "config_first" in original_result
        assert "default" not in original_result
        assert len(original_result) == 2
        
        # Second execution - should process only default inputs
        original_result2 = original.resolve_inputs_for_node(
            node_id="person_node",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs,
            node_exec_counts={"person_node": 2}  # Second execution
        )
        
        adapter_result2 = adapter.resolve_inputs_for_node(
            node_id="person_node",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs,
            node_exec_counts={"person_node": 2}  # Second execution
        )
        
        # Debug: print results to understand behavior
        print(f"Original result2: {original_result2}")
        print(f"Adapter result2: {adapter_result2}")
        
        assert original_result2 == adapter_result2
        assert "first" not in original_result2
        assert "config_first" not in original_result2
        assert "default" in original_result2
        # The original might merge multiple defaults into one
    
    def test_conversation_state_special_handling(self, create_edge, mock_diagram):
        """Test that conversation_state is always processed."""
        # Put conversation_state edge last to ensure it wins
        edges = [
            create_edge("other", "person_node", target_input="first"),
            create_edge("condition", "person_node", target_input="first",
                       data_transform={"content_type": "conversation_state"}),
        ]
        mock_diagram.edges = edges
        
        node_outputs = {
            "condition": {"value": {"messages": []}},
            "other": {"value": "other_value"}
        }
        
        # First execution with first inputs
        original = TypedInputResolutionService()
        original_result = original.resolve_inputs_for_node(
            node_id="person_node",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs,
            node_exec_counts={"person_node": 1}
        )
        
        adapter = TypedInputResolutionServiceAdapter()
        adapter_result = adapter.resolve_inputs_for_node(
            node_id="person_node",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs,
            node_exec_counts={"person_node": 1}
        )
        
        # Both should have same behavior
        assert original_result == adapter_result
        assert "first" in original_result
        # The conversation_state edge should win since it's processed last
        assert original_result["first"] == {"messages": []}
    
    def test_smart_output_extraction(self, create_edge, mock_diagram):
        """Test that the new system extracts outputs more intelligently."""
        edge = create_edge("source", "target", source_output="specific")
        mock_diagram.edges = [edge]
        
        # Test the smarter approach
        test_cases = [
            # NodeOutputProtocol mock
            {
                "output": Mock(value={"specific": "extracted"}),
                "expected": "extracted"
            },
            # Dict with outputs - NEW system should find it in outputs
            {
                "output": {
                    "value": "main",
                    "outputs": {"specific": "from_outputs", "default": "fallback"}
                },
                "expected": "from_outputs"  # Smart: looks in outputs dict
            },
            # Raw dict treated as outputs
            {
                "output": {"specific": "direct_access", "other": "ignored"},
                "expected": "direct_access"
            }
        ]
        
        # Test with refactored service
        from dipeo.application.execution.resolution.refactored_input_resolution import (
            RefactoredInputResolutionService
        )
        service = RefactoredInputResolutionService()
        
        for i, test_case in enumerate(test_cases):
            node_outputs = {"source": test_case["output"]}
            
            # Make output mock behave like NodeOutputProtocol if needed
            if hasattr(test_case["output"], "value"):
                test_case["output"].__class__.__name__ = "NodeOutput"
            
            # Need to mock the diagram properly for refactored service
            mock_node = Mock()
            mock_node.id = "target"
            mock_node.type = NodeType.API_JOB
            mock_diagram.get_node = Mock(return_value=mock_node)
            mock_diagram.get_incoming_edges = Mock(return_value=[edge])
            
            result = service.resolve_inputs_for_node(
                node_id="target",
                node_type=NodeType.API_JOB,
                diagram=mock_diagram,
                node_outputs=node_outputs
            )
            
            assert "default" in result
            assert result["default"] == test_case["expected"], f"Test case {i} failed"
    
    def test_data_transformation_compatibility(self, create_edge, mock_diagram):
        """Test that data transformations work identically."""
        edges = [
            create_edge("json_source", "target", 
                       data_transform={"content_type": "object"}),
            create_edge("format_source", "target2",
                       data_transform={"format": "Processed: {value}"})
        ]
        mock_diagram.edges = edges
        
        node_outputs = {
            "json_source": {"value": '{"key": "value"}'},
            "format_source": {"value": "input"}
        }
        
        original = TypedInputResolutionService()
        adapter = TypedInputResolutionServiceAdapter()
        
        # Test JSON transformation
        mock_diagram.edges = [edges[0]]
        original_json = original.resolve_inputs_for_node(
            "target", NodeType.API_JOB, mock_diagram, node_outputs
        )
        adapter_json = adapter.resolve_inputs_for_node(
            "target", NodeType.API_JOB, mock_diagram, node_outputs
        )
        
        assert original_json == adapter_json
        assert isinstance(original_json.get("default"), dict)
        assert original_json["default"]["key"] == "value"
        
        # Test format transformation - new system is smarter
        mock_diagram.edges = [edges[1]]
        
        # Test with refactored service to show it supports format transformation
        from dipeo.application.execution.resolution.refactored_input_resolution import (
            RefactoredInputResolutionService
        )
        smart_service = RefactoredInputResolutionService()
        
        # Mock the diagram properly
        mock_node = Mock()
        mock_node.id = "target2"
        mock_node.type = NodeType.API_JOB
        mock_diagram.get_node = Mock(return_value=mock_node)
        mock_diagram.get_incoming_edges = Mock(return_value=[edges[1]])
        
        smart_result = smart_service.resolve_inputs_for_node(
            "target2", NodeType.API_JOB, mock_diagram, node_outputs
        )
        
        # Smart system applies the format transformation
        assert smart_result["default"] == "Processed: input"