"""Use case for validating diagrams."""

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.base.validator import ValidationResult
from dipeo.domain.diagram.validation.diagram_validator import DiagramValidator


class ValidateDiagramUseCase:
    """Use case for validating diagram structure and business rules.

    This use case delegates all validation to DiagramValidator, which combines:
    - Structural validation (via compiler): schema, types, connections
    - Business validation (via business validators): person refs, API keys

    The compiler is the single source of truth for structural validation.
    """

    def __init__(self, diagram_validator: DiagramValidator | None = None):
        """Initialize the use case.

        Args:
            diagram_validator: Optional validator, creates default if not provided
        """
        self.diagram_validator = diagram_validator or DiagramValidator()

    def validate(self, domain_diagram: DomainDiagram) -> ValidationResult:
        """Validate a domain diagram with both structural and business rules.

        Args:
            domain_diagram: The diagram to validate

        Returns:
            ValidationResult containing errors and warnings from both
            structural validation (compiler) and business validation
        """
        return self.diagram_validator.validate(domain_diagram)
