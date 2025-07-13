"""Diagram validation logic"""

from typing import Any

from dipeo.core import ValidationError
from dipeo.models import DomainDiagram

from dipeo.application.services.apikey_service import APIKeyService


class DiagramValidator:
    def __init__(self, api_key_service: APIKeyService | None = None):
        self.api_key_service = api_key_service

    def validate(
        self, diagram: DomainDiagram | dict[str, Any], context: str = "general"
    ) -> list[str]:
        errors = []

        if isinstance(diagram, dict):
            if context == "storage" or context == "execution":
                return self._validate_backend_format(diagram, context)
            try:
                diagram = DomainDiagram.model_validate(diagram)
            except Exception as e:
                errors.append(f"Invalid diagram format: {e!s}")
                return errors

        if not diagram.nodes:
            errors.append("Diagram must have at least one node")

        node_ids = {node.id for node in diagram.nodes} if diagram.nodes else set()

        if context == "execution":
            start_nodes = (
                [n for n in diagram.nodes if n.type == "start"] if diagram.nodes else []
            )
            if not start_nodes:
                errors.append(
                    "Diagram must have at least one 'start' node for execution"
                )

        if diagram.arrows:
            for arrow in diagram.arrows:
                if ":" in arrow.source:
                    source_node_id, _ = arrow.source.split(":", 1)
                else:
                    source_node_id = arrow.source

                if ":" in arrow.target:
                    target_node_id, _ = arrow.target.split(":", 1)
                else:
                    target_node_id = arrow.target

                if source_node_id not in node_ids:
                    errors.append(
                        f"Arrow '{arrow.id}' references non-existent source node '{source_node_id}'"
                    )
                if target_node_id not in node_ids:
                    errors.append(
                        f"Arrow '{arrow.id}' references non-existent target node '{target_node_id}'"
                    )

        person_ids = (
            {person.id for person in diagram.persons} if diagram.persons else set()
        )

        if diagram.nodes:
            for node in diagram.nodes:
                if node.type in ["person_job", "person_batch_job"] and node.data:
                    person_id = node.data.get("personId")
                    if person_id and person_id not in person_ids:
                        errors.append(
                            f"Node '{node.id}' references non-existent person '{person_id}'"
                        )

        if self.api_key_service and diagram.persons:
            for person in diagram.persons:
                if person.api_key_id and not self.api_key_service.get_api_key(
                    person.api_key_id
                ):
                    errors.append(
                        f"Person '{person.id}' references non-existent API key '{person.api_key_id}'"
                    )

        return errors

    def _validate_backend_format(
        self, diagram: dict[str, Any], context: str = "backend"
    ) -> list[str]:
        errors = []

        nodes = diagram.get("nodes", {})
        if not nodes:
            errors.append("Diagram must have at least one node")

        if not isinstance(nodes, dict):
            errors.append("Nodes must be a dictionary with node IDs as keys")
            return errors

        node_ids = set(nodes.keys())
        if context == "execution":
            start_nodes = [
                nid
                for nid, node in nodes.items()
                if node.get("type") == "start"
                or node.get("data", {}).get("type") == "start"
            ]
            if not start_nodes:
                errors.append(
                    "Diagram must have at least one 'start' node for execution"
                )

        arrows = diagram.get("arrows", {})
        if isinstance(arrows, dict):
            for arrow_id, arrow in arrows.items():
                source = arrow.get("source", "")
                if ":" in source:
                    source_node_id, _ = source.split(":", 1)
                else:
                    source_node_id = source

                target = arrow.get("target", "")
                if ":" in target:
                    target_node_id, _ = target.split(":", 1)
                else:
                    target_node_id = target

                if source_node_id not in node_ids:
                    errors.append(
                        f"Arrow '{arrow_id}' references non-existent source node '{source_node_id}'"
                    )
                if target_node_id not in node_ids:
                    errors.append(
                        f"Arrow '{arrow_id}' references non-existent target node '{target_node_id}'"
                    )

        persons = diagram.get("persons", {})
        if isinstance(persons, dict):
            person_ids = set(persons.keys())

            for node_id, node in nodes.items():
                node_type = node.get("type", "")
                if node_type in [
                    "person_job",
                    "person_batch_job",
                    "personJobNode",
                    "personBatchJobNode",
                ]:
                    node_data = node.get("data", {})
                    person_id = node_data.get("personId")
                    if person_id and person_id not in person_ids:
                        errors.append(
                            f"Node '{node_id}' references non-existent person '{person_id}'"
                        )

            if self.api_key_service:
                for person_id, person in persons.items():
                    api_key_id = person.get("apiKeyId") or person.get("api_key_id")
                    if api_key_id and not self.api_key_service.get_api_key(api_key_id):
                        errors.append(
                            f"Person '{person_id}' references non-existent API key '{api_key_id}'"
                        )

        return errors

    def validate_or_raise(
        self, diagram: DomainDiagram | dict[str, Any], context: str = "general"
    ) -> None:
        errors = self.validate(diagram, context)
        if errors:
            raise ValidationError("; ".join(errors))

    def is_valid(
        self, diagram: DomainDiagram | dict[str, Any], context: str = "general"
    ) -> bool:
        return len(self.validate(diagram, context)) == 0


__all__ = ["DiagramValidator"]
