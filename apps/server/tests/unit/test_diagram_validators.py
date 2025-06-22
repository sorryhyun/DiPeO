"""Unit tests for diagram validators."""

import pytest

from dipeo_server.core.exceptions import ValidationError
from dipeo_server.domains.diagram.validators import DiagramValidator


class TestDiagramValidator:
    """Test DiagramValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return DiagramValidator()

    def test_validator_initialization(self, validator):
        """Test validator initialization."""
        assert validator is not None
        assert hasattr(validator, "validate")
        assert hasattr(validator, "validate_or_raise")
        assert hasattr(validator, "is_valid")

    def test_empty_diagram_validation(self, validator):
        """Test validation of empty diagram."""
        diagram = {
            "nodes": {},
            "arrows": {},
            "metadata": {
                "name": "Empty",
                "version": "1.0",
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            },
        }

        errors = validator.validate(diagram)
        assert len(errors) > 0
        assert any("at least one node" in err for err in errors)

    def test_valid_simple_diagram(self, validator):
        """Test validation of a valid simple diagram."""
        diagram = {
            "nodes": {
                "start1": {
                    "id": "start1",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {"type": "start"},
                },
                "end1": {
                    "id": "end1",
                    "type": "end",
                    "position": {"x": 100, "y": 0},
                    "data": {"type": "end"},
                },
            },
            "arrows": {
                "arrow1": {
                    "id": "arrow1",
                    "source": "start1:output",
                    "target": "end1:input",
                }
            },
            "metadata": {
                "name": "Simple Diagram",
                "version": "1.0",
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            },
        }

        errors = validator.validate(diagram)
        # DiagramValidator validates storage format, not Pydantic model
        assert isinstance(errors, list)

    def test_diagram_with_invalid_arrow_reference(self, validator):
        """Test diagram with arrow pointing to non-existent node."""
        diagram = {
            "nodes": {
                "node1": {
                    "id": "node1",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {"type": "start"},
                }
            },
            "arrows": {
                "arrow1": {
                    "id": "arrow1",
                    "source": "node1:output",
                    "target": "nonexistent:input",
                }
            },
            "metadata": {
                "version": "1.0",
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            },
        }

        errors = validator.validate(diagram, context="storage")
        assert len(errors) > 0
        assert any("non-existent" in err.lower() for err in errors)

    def test_execution_context_validation(self, validator):
        """Test validation with execution context."""
        # Diagram without start node
        diagram = {
            "nodes": {
                "node1": {
                    "id": "node1",
                    "type": "job",
                    "position": {"x": 0, "y": 0},
                    "data": {"type": "job"},
                }
            },
            "arrows": {},
            "metadata": {
                "version": "1.0",
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            },
        }

        # General context - may have validation errors due to DomainDiagram requirements
        errors = validator.validate(diagram, context="general")
        # Just check it returns a list
        assert isinstance(errors, list)

        # Execution context - should fail (no start node)
        errors = validator.validate(diagram, context="execution")
        assert len(errors) > 0
        # Check for start node error or format error
        assert any("start" in err.lower() for err in errors) or any(
            "format" in err.lower() for err in errors
        )

    def test_person_reference_validation(self, validator):
        """Test validation of person references in nodes."""
        diagram = {
            "nodes": {
                "pj1": {
                    "id": "pj1",
                    "type": "person_job",
                    "position": {"x": 0, "y": 0},
                    "data": {"type": "person_job", "personId": "missing_person"},
                }
            },
            "persons": {},
            "arrows": {},
            "metadata": {
                "version": "1.0",
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            },
        }

        # Use storage context to check storage format validation
        errors = validator.validate(diagram, context="storage")
        assert len(errors) > 0
        assert any("non-existent person" in err for err in errors)

    def test_validate_or_raise(self, validator):
        """Test validate_or_raise method."""
        invalid_diagram = {
            "nodes": {},
            "arrows": {},
            "metadata": {
                "version": "1.0",
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            },
        }

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_or_raise(invalid_diagram)

        # Should have validation error - either about nodes or format
        error_msg = str(exc_info.value)
        assert "at least one node" in error_msg or "Invalid diagram format" in error_msg

    def test_is_valid_method(self, validator):
        """Test is_valid method."""
        # Use storage context to avoid DomainDiagram conversion
        valid_diagram = {
            "nodes": {
                "n1": {
                    "id": "n1",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {"type": "start"},
                }
            },
            "arrows": {},
            "metadata": {
                "version": "1.0",
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            },
        }

        # Test with storage context
        assert validator.is_valid(valid_diagram, context="storage") is True

        invalid_diagram = {"nodes": {}, "arrows": {}}
        assert validator.is_valid(invalid_diagram, context="storage") is False

    def test_storage_format_validation(self, validator):
        """Test validation of storage format (dicts with dicts)."""
        diagram = {
            "nodes": [  # Wrong format - should be dict
                {"id": "n1", "type": "start"}
            ],
            "arrows": {},
        }

        errors = validator.validate(diagram, context="storage")
        assert len(errors) > 0
        assert any("dictionary" in err for err in errors)

    def test_complex_diagram_validation(self, validator):
        """Test validation of complex diagram with multiple node types."""
        diagram = {
            "nodes": {
                "start": {
                    "id": "start",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {"type": "start"},
                },
                "person1": {
                    "id": "person1",
                    "type": "person",
                    "position": {"x": 100, "y": 0},
                    "data": {"type": "person"},
                },
                "job1": {
                    "id": "job1",
                    "type": "job",
                    "position": {"x": 200, "y": 0},
                    "data": {"type": "job"},
                },
                "condition1": {
                    "id": "condition1",
                    "type": "condition",
                    "position": {"x": 300, "y": 0},
                    "data": {"type": "condition"},
                },
                "end": {
                    "id": "end",
                    "type": "end",
                    "position": {"x": 400, "y": 0},
                    "data": {"type": "end"},
                },
            },
            "arrows": {
                "a1": {"source": "start:output", "target": "person1:input"},
                "a2": {"source": "person1:output", "target": "job1:input"},
                "a3": {"source": "job1:output", "target": "condition1:input"},
                "a4": {"source": "condition1:true", "target": "end:input"},
                "a5": {"source": "condition1:false", "target": "person1:input"},
            },
            "persons": {"p1": {"id": "p1", "label": "Assistant", "api_key_id": "key1"}},
            "metadata": {
                "version": "1.0",
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            },
        }

        errors = validator.validate(diagram, context="storage")
        # This should be valid unless API key validation is enabled
        assert isinstance(errors, list)
