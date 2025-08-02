"""
Tests for data transformation and content type handling in input resolution.

This test suite focuses on the transformation rules and content type conversions
that occur during input resolution.
"""

import pytest
import json
from typing import Any, Dict
from unittest.mock import Mock, MagicMock

from dipeo.application.execution.resolution.input_resolution import TypedInputResolutionService
from dipeo.diagram_generated import NodeType
from dipeo.core.execution.node_output import BaseNodeOutput
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableEdge, ExecutableNode


class TestDataTransformation:
    """Test suite for data transformation during input resolution."""
    
    @pytest.fixture
    def service(self):
        """Create input resolution service instance."""
        return TypedInputResolutionService()
    
    @pytest.fixture
    def mock_diagram(self):
        """Create a mock executable diagram."""
        diagram = Mock(spec=ExecutableDiagram)
        diagram.edges = []
        return diagram
    
    @pytest.fixture
    def create_edge(self):
        """Factory for creating mock edges with transformation rules."""
        def _create_edge(
            source_node_id="source",
            target_node_id="target",
            source_output="default",
            target_input="default",
            data_transform=None,
            metadata=None
        ):
            edge = Mock(spec=ExecutableEdge)
            edge.source_node_id = source_node_id
            edge.target_node_id = target_node_id
            edge.source_output = source_output
            edge.target_input = target_input
            edge.data_transform = data_transform
            edge.metadata = metadata or {}
            return edge
        return _create_edge
    
    def test_json_string_to_object_transformation(self, service, mock_diagram, create_edge):
        """Test transformation of JSON strings to objects."""
        edge = create_edge(data_transform={"content_type": "object"})
        mock_diagram.edges = [edge]
        
        # Test valid JSON object
        node_outputs = {
            "source": {"value": '{"name": "test", "count": 42, "active": true}'}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": {"name": "test", "count": 42, "active": True}}
    
    def test_json_array_to_object_transformation(self, service, mock_diagram, create_edge):
        """Test transformation of JSON arrays."""
        edge = create_edge(data_transform={"content_type": "object"})
        mock_diagram.edges = [edge]
        
        # Test valid JSON array
        node_outputs = {
            "source": {"value": '[1, 2, 3, "test", true, null]'}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": [1, 2, 3, "test", True, None]}
    
    def test_nested_json_transformation(self, service, mock_diagram, create_edge):
        """Test transformation of deeply nested JSON structures."""
        edge = create_edge(data_transform={"content_type": "object"})
        mock_diagram.edges = [edge]
        
        nested_json = {
            "level1": {
                "level2": {
                    "level3": {
                        "data": "deep_value"
                    },
                    "array": [1, 2, {"nested": "in_array"}]
                }
            }
        }
        
        node_outputs = {
            "source": {"value": json.dumps(nested_json)}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": nested_json}
    
    def test_invalid_json_handling(self, service, mock_diagram, create_edge):
        """Test handling of invalid JSON strings."""
        edge = create_edge(data_transform={"content_type": "object"})
        mock_diagram.edges = [edge]
        
        # Test various invalid JSON cases
        invalid_cases = [
            "not json at all",
            "{invalid: json}",  # Missing quotes
            "{'single': 'quotes'}",  # Single quotes
            "{\"unclosed\": \"object\"",  # Unclosed brace
            "NaN",  # Not a valid JSON value
            "",  # Empty string
            "   ",  # Whitespace only
        ]
        
        for invalid_json in invalid_cases:
            node_outputs = {
                "source": {"value": invalid_json}
            }
            
            result = service.resolve_inputs_for_node(
                node_id="target",
                node_type=NodeType.API_JOB,
                diagram=mock_diagram,
                node_outputs=node_outputs
            )
            
            # Should preserve original value when JSON parsing fails
            assert result == {"default": invalid_json}
    
    def test_non_string_with_object_content_type(self, service, mock_diagram, create_edge):
        """Test object content type with non-string values."""
        edge = create_edge(data_transform={"content_type": "object"})
        mock_diagram.edges = [edge]
        
        # Test with already parsed object
        obj_value = {"already": "parsed", "number": 123}
        node_outputs = {
            "source": {"value": obj_value}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        # Should pass through unchanged
        assert result == {"default": obj_value}
    
    def test_conversation_state_content_type(self, service, mock_diagram, create_edge):
        """Test conversation_state content type handling."""
        edge = create_edge(data_transform={"content_type": "conversation_state"})
        mock_diagram.edges = [edge]
        
        conversation_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "context": {"session_id": "123"}
        }
        
        node_outputs = {
            "source": {"value": conversation_data}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.PERSON_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        # Should pass through conversation data
        assert result == {"default": conversation_data}
    
    def test_custom_content_types(self, service, mock_diagram, create_edge):
        """Test handling of custom content types."""
        # Test various content types that don't have special handling
        content_types = ["text", "html", "xml", "binary", "custom_type"]
        
        for content_type in content_types:
            edge = create_edge(data_transform={"content_type": content_type})
            mock_diagram.edges = [edge]
            
            test_value = f"<data>Content for {content_type}</data>"
            node_outputs = {
                "source": {"value": test_value}
            }
            
            result = service.resolve_inputs_for_node(
                node_id="target",
                node_type=NodeType.API_JOB,
                diagram=mock_diagram,
                node_outputs=node_outputs
            )
            
            # Should pass through without transformation
            assert result == {"default": test_value}
    
    def test_multiple_transformation_rules(self, service, mock_diagram, create_edge):
        """Test edges with multiple transformation rules."""
        # Create edge with multiple transformation rules
        edge = create_edge(
            data_transform={
                "content_type": "object",
                "extract_path": "data.result",
                "format": "uppercase"
            }
        )
        mock_diagram.edges = [edge]
        
        # Note: Current implementation only handles content_type
        # This test documents current behavior
        node_outputs = {
            "source": {"value": '{"data": {"result": "test_value"}}'}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        # Currently only content_type transformation is applied
        assert result == {"default": {"data": {"result": "test_value"}}}
    
    def test_edge_metadata_labels(self, service, mock_diagram, create_edge):
        """Test edge metadata label handling."""
        edge = create_edge(
            metadata={"label": "custom_input_name"},
            data_transform={"content_type": "object"}
        )
        mock_diagram.edges = [edge]
        
        node_outputs = {
            "source": {"value": '{"labeled": "data"}'}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        # Should use metadata label as input key
        assert result == {"custom_input_name": {"labeled": "data"}}
    
    def test_source_output_key_with_transformation(self, service, mock_diagram, create_edge):
        """Test transformation with specific source output keys."""
        edge = create_edge(
            source_output="processed_data",
            data_transform={"content_type": "object"}
        )
        mock_diagram.edges = [edge]
        
        node_outputs = {
            "source": {
                "value": {
                    "raw_data": "unprocessed",
                    "processed_data": '{"status": "complete", "items": [1, 2, 3]}'
                }
            }
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": {"status": "complete", "items": [1, 2, 3]}}
    
    def test_special_json_values(self, service, mock_diagram, create_edge):
        """Test transformation of special JSON values.
        
        Note: Current implementation only parses JSON that starts with '{' or '[',
        so JSON primitives are not parsed.
        """
        edge = create_edge(data_transform={"content_type": "object"})
        mock_diagram.edges = [edge]
        
        # Test that JSON primitives are NOT parsed (current behavior)
        special_cases = [
            "null",
            "true",
            "false",
            "0",
            "-1.5",
            '"string"',
            '""',
        ]
        
        for json_str in special_cases:
            node_outputs = {
                "source": {"value": json_str}
            }
            
            result = service.resolve_inputs_for_node(
                node_id="target",
                node_type=NodeType.API_JOB,
                diagram=mock_diagram,
                node_outputs=node_outputs
            )
            
            # JSON primitives should pass through as strings (current behavior)
            assert result == {"default": json_str}
        
        # Test that objects and arrays ARE parsed
        parseable_cases = [
            ('{"key": "value"}', {"key": "value"}),
            ('[1, 2, 3]', [1, 2, 3]),
            ('{}', {}),
            ('[]', []),
        ]
        
        for json_str, expected in parseable_cases:
            node_outputs = {
                "source": {"value": json_str}
            }
            
            result = service.resolve_inputs_for_node(
                node_id="target",
                node_type=NodeType.API_JOB,
                diagram=mock_diagram,
                node_outputs=node_outputs
            )
            
            assert result == {"default": expected}
    
    def test_unicode_in_json(self, service, mock_diagram, create_edge):
        """Test JSON transformation with Unicode characters."""
        edge = create_edge(data_transform={"content_type": "object"})
        mock_diagram.edges = [edge]
        
        unicode_json = {
            "emoji": "🎉🎊",
            "chinese": "你好世界",
            "arabic": "مرحبا بالعالم",
            "special": "café ñoño"
        }
        
        node_outputs = {
            "source": {"value": json.dumps(unicode_json, ensure_ascii=False)}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": unicode_json}
    
    def test_large_json_transformation(self, service, mock_diagram, create_edge):
        """Test transformation of large JSON structures."""
        edge = create_edge(data_transform={"content_type": "object"})
        mock_diagram.edges = [edge]
        
        # Create a large JSON structure
        large_data = {
            f"item_{i}": {
                "id": i,
                "data": f"value_{i}" * 10,
                "nested": {
                    "level": i % 5,
                    "tags": [f"tag_{j}" for j in range(5)]
                }
            }
            for i in range(100)
        }
        
        node_outputs = {
            "source": {"value": json.dumps(large_data)}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": large_data}
        assert len(result["default"]) == 100


class TestContentTypeSpecialCases:
    """Test special cases and edge behaviors for content type handling."""
    
    @pytest.fixture
    def service(self):
        """Create input resolution service instance."""
        return TypedInputResolutionService()
    
    @pytest.fixture
    def mock_diagram(self):
        """Create a mock executable diagram."""
        diagram = Mock(spec=ExecutableDiagram)
        diagram.edges = []
        return diagram
    
    def test_json_with_whitespace(self, service, mock_diagram):
        """Test JSON parsing with various whitespace patterns."""
        edge = Mock(spec=ExecutableEdge)
        edge.source_node_id = "source"
        edge.target_node_id = "target"
        edge.source_output = "default"
        edge.target_input = "default"
        edge.metadata = {}
        edge.data_transform = {"content_type": "object"}
        mock_diagram.edges = [edge]
        
        # Test JSON with extra whitespace
        whitespace_cases = [
            '  {"key": "value"}  ',  # Leading/trailing spaces
            '\n{"key": "value"}\n',  # Newlines
            '\t{"key": "value"}\t',  # Tabs
            ' \n\t{"key": "value"}\t\n ',  # Mixed whitespace
        ]
        
        for json_str in whitespace_cases:
            node_outputs = {
                "source": {"value": json_str}
            }
            
            result = service.resolve_inputs_for_node(
                node_id="target",
                node_type=NodeType.API_JOB,
                diagram=mock_diagram,
                node_outputs=node_outputs
            )
            
            assert result == {"default": {"key": "value"}}
    
    def test_json_starts_with_array(self, service, mock_diagram):
        """Test detection of JSON arrays vs objects."""
        edge = Mock(spec=ExecutableEdge)
        edge.source_node_id = "source"
        edge.target_node_id = "target"
        edge.source_output = "default"
        edge.target_input = "default"
        edge.metadata = {}
        edge.data_transform = {"content_type": "object"}
        mock_diagram.edges = [edge]
        
        # Test that arrays are properly detected and parsed
        array_json = '[{"id": 1}, {"id": 2}, {"id": 3}]'
        node_outputs = {
            "source": {"value": array_json}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        assert result == {"default": [{"id": 1}, {"id": 2}, {"id": 3}]}
    
    def test_no_content_type_transformation(self, service, mock_diagram):
        """Test behavior when no content_type is specified."""
        edge = Mock(spec=ExecutableEdge)
        edge.source_node_id = "source"
        edge.target_node_id = "target"
        edge.source_output = "default"
        edge.target_input = "default"
        edge.metadata = {}
        edge.data_transform = {}  # Empty transform rules
        mock_diagram.edges = [edge]
        
        # JSON string should not be parsed without content_type
        node_outputs = {
            "source": {"value": '{"should": "not", "be": "parsed"}'}
        }
        
        result = service.resolve_inputs_for_node(
            node_id="target",
            node_type=NodeType.API_JOB,
            diagram=mock_diagram,
            node_outputs=node_outputs
        )
        
        # Should pass through as string
        assert result == {"default": '{"should": "not", "be": "parsed"}'}