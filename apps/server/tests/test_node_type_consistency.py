"""
Comprehensive tests for node type consistency across frontend and backend.
"""

import pytest
from src.utils.node_type_utils import (
    normalize_node_type_to_backend,
    normalize_node_type_to_frontend,
    extract_node_type,
    FRONTEND_TO_BACKEND_TYPE_MAP,
    TYPE_ALIASES
)
from src.constants import NodeType


class TestNodeTypeFormats:
    """Test all node type format conversions."""
    
    def test_frontend_to_backend_conversion(self):
        """Test conversion from frontend format to backend format."""
        test_cases = [
            ("startNode", "start"),
            ("personJobNode", "person_job"),
            ("personBatchJobNode", "person_batch_job"),
            ("conditionNode", "condition"),
            ("dbNode", "db"),
            ("jobNode", "job"),
            ("endpointNode", "endpoint"),
        ]
        
        for frontend_type, expected_backend in test_cases:
            assert normalize_node_type_to_backend(frontend_type) == expected_backend
    
    def test_backend_to_frontend_conversion(self):
        """Test conversion from backend format to frontend format."""
        test_cases = [
            ("start", "startNode"),
            ("person_job", "personJobNode"),
            ("person_batch_job", "personBatchJobNode"),
            ("condition", "conditionNode"),
            ("db", "dbNode"),
            ("job", "jobNode"),
            ("endpoint", "endpointNode"),
        ]
        
        for backend_type, expected_frontend in test_cases:
            assert normalize_node_type_to_frontend(backend_type) == expected_frontend
    
    def test_type_aliases(self):
        """Test that type aliases are properly normalized."""
        test_cases = [
            ("personjob", "person_job"),
            ("personbatchjob", "person_batch_job"),
            ("personJob", "person_job"),
            ("personBatchJob", "person_batch_job"),
        ]
        
        for alias, expected_backend in test_cases:
            assert normalize_node_type_to_backend(alias) == expected_backend
    
    def test_already_normalized_types(self):
        """Test that already normalized types remain unchanged."""
        # Backend types should remain backend
        backend_types = ["start", "person_job", "condition", "db", "job", "endpoint"]
        for backend_type in backend_types:
            assert normalize_node_type_to_backend(backend_type) == backend_type
        
        # Frontend types should remain frontend
        frontend_types = ["startNode", "personJobNode", "conditionNode", "dbNode"]
        for frontend_type in frontend_types:
            assert normalize_node_type_to_frontend(frontend_type) == frontend_type
    
    def test_unknown_types_passthrough(self):
        """Test that unknown types pass through unchanged."""
        unknown_types = ["customNode", "unknownType", "special_node"]
        
        for unknown_type in unknown_types:
            assert normalize_node_type_to_backend(unknown_type) == unknown_type
            assert normalize_node_type_to_frontend(unknown_type) == unknown_type


class TestNodeTypeExtraction:
    """Test the unified node type extraction function."""
    
    def test_extract_from_data_type(self):
        """Test extraction from data.type field (highest priority)."""
        test_nodes = [
            {
                "id": "node1",
                "type": "startNode",
                "data": {"type": "start"},
                "properties": {"type": "something_else"}
            },
            {
                "id": "node2",
                "type": "personJobNode",
                "data": {"type": "person_job"}
            }
        ]
        
        assert extract_node_type(test_nodes[0]) == "start"
        assert extract_node_type(test_nodes[1]) == "person_job"
    
    def test_extract_from_properties_type(self):
        """Test extraction from properties.type field (second priority)."""
        test_nodes = [
            {
                "id": "node1",
                "type": "startNode",
                "properties": {"type": "start"}
            },
            {
                "id": "node2",
                "properties": {"type": "personJobNode"}
            }
        ]
        
        assert extract_node_type(test_nodes[0]) == "start"
        assert extract_node_type(test_nodes[1]) == "person_job"
    
    def test_extract_from_top_level_type(self):
        """Test extraction from top-level type field (fallback)."""
        test_nodes = [
            {"id": "node1", "type": "startNode"},
            {"id": "node2", "type": "person_job"},
            {"id": "node3", "type": "conditionNode"}
        ]
        
        assert extract_node_type(test_nodes[0]) == "start"
        assert extract_node_type(test_nodes[1]) == "person_job"
        assert extract_node_type(test_nodes[2]) == "condition"
    
    def test_extract_with_priority_order(self):
        """Test that extraction follows the correct priority order."""
        # data.type should take precedence over properties.type and type
        node = {
            "id": "test",
            "type": "wrongType",
            "properties": {"type": "alsoWrong"},
            "data": {"type": "startNode"}
        }
        assert extract_node_type(node) == "start"
        
        # properties.type should take precedence over type
        node = {
            "id": "test",
            "type": "wrongType",
            "properties": {"type": "personJobNode"}
        }
        assert extract_node_type(node) == "person_job"
    
    def test_extract_raises_on_missing_type(self):
        """Test that extraction raises ValueError when no type is found."""
        test_nodes = [
            {"id": "node1"},
            {"id": "node2", "data": {}, "properties": {}},
            {"id": "node3", "data": {"label": "test"}},
        ]
        
        for node in test_nodes:
            with pytest.raises(ValueError) as exc_info:
                extract_node_type(node)
            assert "No type found" in str(exc_info.value)
            assert node.get("id", "unknown") in str(exc_info.value)


class TestNodeTypeEnumConsistency:
    """Test that NodeType enum is consistent with the conversion utilities."""
    
    def test_enum_values_are_backend_format(self):
        """Test that NodeType enum values use backend format."""
        expected_values = {
            NodeType.START: "start",
            NodeType.PERSON_JOB: "person_job",
            NodeType.PERSON_BATCH_JOB: "person_batch_job",
            NodeType.CONDITION: "condition",
            NodeType.DB: "db",
            NodeType.JOB: "job",
            NodeType.ENDPOINT: "endpoint"
        }
        
        for enum_member, expected_value in expected_values.items():
            assert enum_member.value == expected_value
    
    def test_all_enum_values_in_conversion_map(self):
        """Test that all NodeType enum values have corresponding frontend mappings."""
        backend_types = {member.value for member in NodeType}
        mapped_backend_types = set(FRONTEND_TO_BACKEND_TYPE_MAP.values())
        
        # All enum values should be in the conversion map
        assert backend_types <= mapped_backend_types
    
    def test_conversion_map_completeness(self):
        """Test that conversion maps cover all expected node types."""
        # All backend types from enum should have frontend equivalents
        for node_type in NodeType:
            backend_value = node_type.value
            # Should be able to convert to frontend and back
            frontend_value = normalize_node_type_to_frontend(backend_value)
            assert frontend_value.endswith("Node")
            assert normalize_node_type_to_backend(frontend_value) == backend_value


class TestRealWorldScenarios:
    """Test real-world node structures from frontend."""
    
    def test_frontend_node_structure(self):
        """Test typical frontend node structure."""
        frontend_node = {
            "id": "node_123",
            "type": "personJobNode",  # React Flow type
            "data": {
                "type": "person_job",  # Logical type
                "label": "Analyze Data",
                "personId": "analyst",
                "defaultPrompt": "Analyze this: {{data}}"
            },
            "position": {"x": 100, "y": 200}
        }
        
        # Should extract from data.type
        assert extract_node_type(frontend_node) == "person_job"
    
    def test_backend_node_structure(self):
        """Test typical backend node structure."""
        backend_node = {
            "id": "node_123",
            "properties": {
                "type": "person_job",
                "label": "Analyze Data",
                "personId": "analyst",
                "defaultPrompt": "Analyze this: {{data}}"
            }
        }
        
        # Should extract from properties.type
        assert extract_node_type(backend_node) == "person_job"
    
    def test_mixed_format_handling(self):
        """Test handling of mixed format scenarios."""
        test_cases = [
            # Frontend format in backend location
            {"properties": {"type": "personJobNode"}},
            # Backend format in frontend location
            {"data": {"type": "person_job"}},
            # Alias in various locations
            {"type": "personjob"},
            {"data": {"type": "personJob"}},
        ]
        
        for node in test_cases:
            assert extract_node_type(node) == "person_job"


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""
    
    def test_fallback_behavior(self):
        """Test that extraction has proper fallback behavior."""
        # Should check multiple locations in order
        nodes = [
            # Only top-level type
            {"type": "startNode"},
            # Only properties
            {"properties": {"type": "conditionNode"}},
            # Only data
            {"data": {"type": "endpointNode"}},
        ]
        
        expected = ["start", "condition", "endpoint"]
        for node, expected_type in zip(nodes, expected):
            assert extract_node_type(node) == expected_type
    
    def test_handles_empty_containers(self):
        """Test handling of empty data/properties containers."""
        nodes = [
            {"type": "jobNode", "data": {}, "properties": {}},
            {"type": "dbNode", "data": None, "properties": None},
        ]
        
        assert extract_node_type(nodes[0]) == "job"
        assert extract_node_type(nodes[1]) == "db"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])