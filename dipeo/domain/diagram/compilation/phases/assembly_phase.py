"""Assembly phase for diagram compilation."""

from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram

from ..types import CompilationPhase
from .base import CompilationContext, PhaseInterface


class AssemblyPhase(PhaseInterface):
    """Phase 6: Assemble the final ExecutableDiagram with metadata."""

    @property
    def phase_type(self) -> CompilationPhase:
        return CompilationPhase.ASSEMBLY

    def execute(self, context: CompilationContext) -> None:
        """Assemble the final executable diagram."""
        if context.result.errors:
            return

        persons_metadata = self._build_persons_metadata(context)
        metadata = self._build_diagram_metadata(context, persons_metadata)

        context.result.diagram = ExecutableDiagram(
            nodes=context.typed_nodes,
            edges=context.typed_edges,
            execution_order=None,
            metadata=metadata,
        )

    def _build_persons_metadata(self, context: CompilationContext) -> dict:
        """Build persons metadata from domain diagram.

        Args:
            context: Compilation context

        Returns:
            Dictionary mapping person label to person configuration
        """
        persons_metadata = {}

        if not context.domain_diagram.persons:
            return persons_metadata

        for person in context.domain_diagram.persons:
            person_data = {
                "name": person.label,
                "service": person.llm_config.service.value
                if hasattr(person.llm_config.service, "value")
                else person.llm_config.service,
                "model": person.llm_config.model,
                "api_key_id": person.llm_config.api_key_id.value
                if hasattr(person.llm_config.api_key_id, "value")
                else person.llm_config.api_key_id,
            }

            if hasattr(person.llm_config, "temperature"):
                person_data["temperature"] = person.llm_config.temperature
            if hasattr(person.llm_config, "max_tokens"):
                person_data["max_tokens"] = person.llm_config.max_tokens
            if hasattr(person.llm_config, "system_prompt"):
                person_data["system_prompt"] = person.llm_config.system_prompt

            persons_metadata[person.label] = person_data

        return persons_metadata

    def _build_diagram_metadata(self, context: CompilationContext, persons_metadata: dict) -> dict:
        """Build complete diagram metadata.

        Args:
            context: Compilation context
            persons_metadata: Pre-built persons metadata

        Returns:
            Complete metadata dictionary for ExecutableDiagram
        """
        metadata = {
            "id": context.domain_diagram.metadata.id if context.domain_diagram.metadata else None,
            "name": context.domain_diagram.metadata.name
            if context.domain_diagram.metadata
            else None,
            "compilation_warnings": [w.message for w in context.result.warnings],
            "start_nodes": list(context.start_nodes),
            "person_nodes": context.person_nodes,
            "node_dependencies": {k: list(v) for k, v in context.node_dependencies.items()},
            "persons": persons_metadata,
            **context.result.metadata,
        }

        return metadata
