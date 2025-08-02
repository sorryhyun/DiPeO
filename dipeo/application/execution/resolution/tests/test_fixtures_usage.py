"""
Example tests demonstrating the usage of test fixtures.

This file shows how to use the fixtures defined in conftest.py to write
concise and maintainable tests for the input resolution mechanism.
"""

import pytest
from dipeo.application.execution.resolution.input_resolution import TypedInputResolutionService
from dipeo.diagram_generated import NodeType


class TestFixtureUsageExamples:
    """Examples of using the test fixtures."""
    
    @pytest.fixture
    def service(self):
        """Create input resolution service instance."""
        return TypedInputResolutionService()
    
    def test_using_node_factory(self, service, create_node, create_diagram):
        """Example of using create_node factory fixture."""
        # Create nodes with factory
        api_node = create_node("api1", NodeType.API_JOB)
        db_node = create_node("db1", NodeType.DB, custom_property="value")
        
        # Create diagram
        diagram = create_diagram([api_node, db_node], [])
        
        # Test properties
        assert api_node.id == "api1"
        assert api_node.type == NodeType.API_JOB
        assert db_node.custom_property == "value"
    
    def test_using_edge_factory(self, create_edge):
        """Example of using create_edge factory fixture."""
        # Create simple edge
        simple_edge = create_edge("source", "target")
        assert simple_edge.source_output == "default"
        assert simple_edge.target_input == "default"
        
        # Create edge with custom properties
        custom_edge = create_edge(
            "node1", 
            "node2",
            source_output="custom_out",
            target_input="custom_in",
            data_transform={"content_type": "object"},
            metadata={"label": "My Input"}
        )
        assert custom_edge.source_output == "custom_out"
        assert custom_edge.metadata["label"] == "My Input"
    
    def test_using_predefined_diagrams(self, service, linear_diagram, sample_node_outputs):
        """Example of using predefined diagram fixtures."""
        # Use the linear diagram (A -> B -> C)
        # Add some outputs
        node_outputs = {
            "A": sample_node_outputs["simple_value"],
            "B": sample_node_outputs["node_output"],
        }
        
        # Test resolution for node C
        result = service.resolve_inputs_for_node(
            node_id="C",
            node_type=NodeType.API_JOB,
            diagram=linear_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": "test_value"}
    
    def test_using_branching_diagram(self, service, branching_diagram, create_condition_output):
        """Example of using the branching diagram with condition node."""
        # Create condition output
        condition_output = create_condition_output(
            value=True,
            true_output={"result": "success"},
            false_output={"result": "failure"}
        )
        
        node_outputs = {
            "start": {"value": "initial"},
            "condition": condition_output
        }
        
        # Test true branch
        true_result = service.resolve_inputs_for_node(
            node_id="branch_a",
            node_type=NodeType.API_JOB,
            diagram=branching_diagram,
            node_outputs=node_outputs
        )
        
        assert true_result == {"default": {"result": "success"}}
    
    def test_using_person_job_diagram(self, service, person_job_diagram, node_exec_counts):
        """Example of using PersonJob diagram with first/default inputs."""
        node_outputs = {
            "start": {"value": "prompt_text"}
        }
        
        # First execution
        first_exec_result = service.resolve_inputs_for_node(
            node_id="person",
            node_type=NodeType.PERSON_JOB,
            diagram=person_job_diagram,
            node_outputs=node_outputs,
            node_exec_counts={"person": 1}
        )
        
        # Should only get "first" input
        assert first_exec_result == {"first": "prompt_text"}
        
        # Subsequent execution
        next_exec_result = service.resolve_inputs_for_node(
            node_id="person",
            node_type=NodeType.PERSON_JOB,
            diagram=person_job_diagram,
            node_outputs=node_outputs,
            node_exec_counts={"person": 2}
        )
        
        # Should only get "default" input
        assert next_exec_result == {"default": "prompt_text"}
    
    def test_using_sample_json_data(self, service, create_edge, create_diagram, create_node, sample_json_data):
        """Example of using sample JSON data for transformation tests."""
        # Create a simple diagram with JSON transformation
        source = create_node("source", NodeType.API_JOB)
        target = create_node("target", NodeType.API_JOB)
        edge = create_edge(
            "source", 
            "target",
            data_transform={"content_type": "object"}
        )
        diagram = create_diagram([source, target], [edge])
        
        # Test various JSON inputs
        for data_type, json_string in sample_json_data.items():
            node_outputs = {"source": {"value": json_string}}
            
            result = service.resolve_inputs_for_node(
                node_id="target",
                node_type=NodeType.API_JOB,
                diagram=diagram,
                node_outputs=node_outputs
            )
            
            # Verify transformation based on data type
            if data_type == "valid_object":
                assert result == {"default": {"name": "test", "value": 123}}
            elif data_type == "valid_array":
                assert result == {"default": [1, 2, 3, "four"]}
            elif data_type == "invalid_json":
                # Invalid JSON should pass through as string
                assert result == {"default": "{invalid: json}"}
    
    def test_using_complex_diagram(self, service, complex_diagram, create_node_output):
        """Example of using the complex diagram fixture."""
        # Create outputs for multiple nodes
        node_outputs = {
            "start": create_node_output("start_value"),
            "api1": create_node_output("api1_result"),
            "api2": create_node_output('{"json": "data"}'),
        }
        
        # Test PersonJob inputs (should get "first" on first execution)
        person_inputs = service.resolve_inputs_for_node(
            node_id="person",
            node_type=NodeType.PERSON_JOB,
            diagram=complex_diagram,
            node_outputs=node_outputs,
            node_exec_counts={"person": 1}
        )
        
        # On first execution with "first" inputs available,
        # PersonJob only processes "first" inputs
        assert person_inputs == {
            "first": "api1_result"
        }
    
    def test_using_assert_helper(self, assert_inputs_equal):
        """Example of using the assert_inputs_equal helper."""
        actual = {
            "input1": "value1",
            "input2": {"nested": "value2"},
            "input3": [1, 2, 3]
        }
        
        expected = {
            "input1": "value1",
            "input2": {"nested": "value2"},
            "input3": [1, 2, 3]
        }
        
        # This provides better error messages than simple assert
        assert_inputs_equal(actual, expected)
    
    def test_combining_fixtures(
        self, 
        service,
        create_node,
        create_person_job_node,
        create_edge,
        create_diagram,
        create_node_output,
        sample_json_data
    ):
        """Example of combining multiple fixtures in a single test."""
        # Build a custom diagram using factories
        api = create_node("api", NodeType.API_JOB)
        person = create_person_job_node("person", memory_settings={"key": "value"})
        template = create_node("template", NodeType.TEMPLATE_JOB)
        
        edges = [
            create_edge("api", "person", target_input="first"),
            create_edge(
                "api", 
                "template", 
                target_input="json_data",
                data_transform={"content_type": "object"}
            ),
            create_edge("person", "template", target_input="text")
        ]
        
        diagram = create_diagram([api, person, template], edges)
        
        # Use sample data and create outputs
        node_outputs = {
            "api": create_node_output(sample_json_data["valid_object"]),
            "person": create_node_output("Generated text")
        }
        
        # Test template inputs
        template_inputs = service.resolve_inputs_for_node(
            node_id="template",
            node_type=NodeType.TEMPLATE_JOB,
            diagram=diagram,
            node_outputs=node_outputs
        )
        
        assert template_inputs == {
            "json_data": {"name": "test", "value": 123},  # Transformed
            "text": "Generated text"
        }