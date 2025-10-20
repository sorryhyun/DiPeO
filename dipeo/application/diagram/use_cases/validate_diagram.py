"""Use case for validating diagrams."""

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.base.validator import ValidationResult
from dipeo.domain.diagram.validation.diagram_validator import DiagramValidator


class ValidateDiagramUseCase:
    """Validates diagram structure and business rules.

    Delegates to DiagramValidator which combines structural validation (compiler)
    and business validation (person refs, API keys, etc).
    """

    def __init__(self, diagram_validator: DiagramValidator | None = None):
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
