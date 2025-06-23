"""Service for converting between different diagram formats."""

import logging
from typing import Any, Dict

import yaml
from dipeo_core import BaseService, ValidationError
from dipeo_domain import (
    DiagramMetadata,
    DomainApiKey,
    DomainArrow,
    DomainDiagram,
    DomainHandle,
    DomainNode,
    DomainPerson,
    Vec2,
)

from .models import (
    BackendDiagram,
    ExecutionHint,
    ExecutionHints,
    ReadableFlow,
)

logger = logging.getLogger(__name__)


class DiagramConverterService(BaseService):
    """Converts between backend, domain, YAML, and execution formats."""

    def __init__(self):
        super().__init__()

    async def initialize(self) -> None:
        pass

    def backend_to_domain(self, backend_diagram: BackendDiagram) -> DomainDiagram:
        """Convert backend format (dict of dicts) to domain format (lists)."""
        try:
            # Convert to domain format
            nodes = []
            for node_id, node_data in backend_diagram.nodes.items():
                # Ensure ID is set
                if isinstance(node_data, dict) and node_data.get("id") != node_id:
                    node_data["id"] = node_id
                nodes.append(DomainNode(**node_data))

            arrows = []
            for arrow_id, arrow_data in backend_diagram.arrows.items():
                # Ensure ID is set
                if isinstance(arrow_data, dict) and arrow_data.get("id") != arrow_id:
                    arrow_data["id"] = arrow_id
                arrows.append(DomainArrow(**arrow_data))

            persons = []
            for person_id, person_data in backend_diagram.persons.items():
                # Ensure ID is set
                if isinstance(person_data, dict) and person_data.get("id") != person_id:
                    person_data["id"] = person_id
                persons.append(DomainPerson(**person_data))

            handles = []
            for handle_id, handle_data in backend_diagram.handles.items():
                # Ensure ID is set
                if isinstance(handle_data, dict) and handle_data.get("id") != handle_id:
                    handle_data["id"] = handle_id
                handles.append(DomainHandle(**handle_data))

            api_keys = []
            for key_id, key_data in backend_diagram.api_keys.items():
                # Ensure ID is set
                if isinstance(key_data, dict) and key_data.get("id") != key_id:
                    key_data["id"] = key_id
                api_keys.append(DomainApiKey(**key_data))

            metadata = None
            if backend_diagram.metadata:
                metadata = DiagramMetadata(**backend_diagram.metadata)

            return DomainDiagram(
                nodes=nodes,
                arrows=arrows,
                persons=persons,
                handles=handles,
                apiKeys=api_keys,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Failed to convert backend to domain: {e}")
            raise ValidationError(f"Invalid backend format: {e}") from e

    def domain_to_backend(self, diagram: DomainDiagram) -> Dict[str, Any]:
        """Convert domain format (lists) to backend format (dict of dicts)."""
        try:
            # Create BackendDiagram model
            backend_model = BackendDiagram()

            # Convert nodes
            if diagram.nodes:
                for node in diagram.nodes:
                    node_dict = node.model_dump()
                    # DomainNode already has data as Dict[str, Any]
                    # Ensure data exists with label
                    if "data" not in node_dict or not node_dict["data"]:
                        node_dict["data"] = {"label": node.id}
                    else:
                        # Ensure label exists in data
                        if "label" not in node_dict["data"]:
                            node_dict["data"]["label"] = node.id

                    # Ensure position exists using Vec2 model
                    if "position" not in node_dict:
                        position = Vec2(x=0, y=0)
                        node_dict["position"] = position.model_dump()

                    # Just store the dict directly
                    backend_model.nodes[node.id] = node_dict

            # Convert arrows
            if diagram.arrows:
                for arrow in diagram.arrows:
                    arrow_dict = arrow.model_dump()
                    # Ensure arrow has data dict
                    if "data" not in arrow_dict:
                        arrow_dict["data"] = {}
                    elif arrow_dict["data"] and "label" not in arrow_dict["data"]:
                        # Ensure default label exists
                        arrow_dict["data"]["label"] = "flow"
                    backend_model.arrows[arrow.id] = arrow_dict

            # Convert persons
            if diagram.persons:
                for person in diagram.persons:
                    backend_model.persons[person.id] = person.model_dump()

            # Convert handles
            if diagram.handles:
                for handle in diagram.handles:
                    backend_model.handles[handle.id] = handle.model_dump()

            # Convert API keys
            if diagram.api_keys:
                for api_key in diagram.api_keys:
                    backend_model.api_keys[api_key.id] = api_key.model_dump()

            # Convert metadata
            if diagram.metadata:
                backend_model.metadata = diagram.metadata.model_dump()

            # Return as dict with proper field names
            return backend_model.model_dump(by_alias=True)

        except Exception as e:
            logger.error(f"Failed to convert domain to backend: {e}")
            raise ValidationError(f"Failed to convert domain model: {e}") from e

    def light_to_backend(self, yaml_content: str) -> Dict[str, Any]:
        """Convert light YAML content to backend format."""
        try:
            data = yaml.safe_load(yaml_content)

            if not isinstance(data, dict):
                raise ValidationError("YAML content must be a dictionary")

            if self._is_backend_format(data):
                # Validate and return via Pydantic model
                backend_model = BackendDiagram(**data)
                return backend_model.model_dump(by_alias=True)

            # Convert list formats to backend formats
            backend_model = BackendDiagram()

            if "nodes" in data:
                if isinstance(data["nodes"], list):
                    for node_data in data["nodes"]:
                        node_id = node_data.get("id")
                        if node_id:
                            # Node data is already in the correct format
                            # Each node type has its own specific data structure

                            # Position is already in the correct format (x, y)

                            backend_model.nodes[node_id] = node_data
                elif isinstance(data["nodes"], dict):
                    for node_id, node_data in data["nodes"].items():
                        if "id" not in node_data:
                            node_data["id"] = node_id
                        backend_model.nodes[node_id] = node_data

            if "arrows" in data:
                if isinstance(data["arrows"], list):
                    for arrow_data in data["arrows"]:
                        arrow_id = arrow_data.get("id")
                        if arrow_id:
                            # Arrow data is a simple dict with optional label
                            if "data" in arrow_data and arrow_data["data"] and "label" not in arrow_data["data"]:
                                arrow_data["data"]["label"] = "flow"
                            backend_model.arrows[arrow_id] = arrow_data
                elif isinstance(data["arrows"], dict):
                    for arrow_id, arrow_data in data["arrows"].items():
                        if "id" not in arrow_data:
                            arrow_data["id"] = arrow_id
                        backend_model.arrows[arrow_id] = arrow_data

            if "persons" in data:
                if isinstance(data["persons"], list):
                    for person_data in data["persons"]:
                        person_id = person_data.get("id")
                        if person_id:
                            backend_model.persons[person_id] = person_data
                elif isinstance(data["persons"], dict):
                    for person_id, person_data in data["persons"].items():
                        if "id" not in person_data:
                            person_data["id"] = person_id
                        backend_model.persons[person_id] = person_data

            if "handles" in data:
                if isinstance(data["handles"], list):
                    for handle_data in data["handles"]:
                        handle_id = handle_data.get("id")
                        if handle_id:
                            backend_model.handles[handle_id] = handle_data
                elif isinstance(data["handles"], dict):
                    for handle_id, handle_data in data["handles"].items():
                        if "id" not in handle_data:
                            handle_data["id"] = handle_id
                        backend_model.handles[handle_id] = handle_data

            # Handle legacy apiKeys field
            if "apiKeys" in data and "api_keys" not in data:
                data["api_keys"] = data.pop("apiKeys")

            if "api_keys" in data:
                if isinstance(data["api_keys"], list):
                    for key_data in data["api_keys"]:
                        key_id = key_data.get("id")
                        if key_id:
                            backend_model.api_keys[key_id] = key_data
                elif isinstance(data["api_keys"], dict):
                    for key_id, key_data in data["api_keys"].items():
                        if "id" not in key_data:
                            key_data["id"] = key_id
                        backend_model.api_keys[key_id] = key_data

            if data.get("metadata"):
                backend_model.metadata = data["metadata"]

            return backend_model.model_dump(by_alias=True)

        except yaml.YAMLError as e:
            raise ValidationError(f"Failed to parse YAML: {e}") from e
        except Exception as e:
            raise ValidationError(f"Failed to convert YAML: {e}") from e

    def backend_to_light(self, backend_diagram: BackendDiagram) -> str:
        """Convert backend format to light YAML."""
        try:
            # Use the backend diagram directly
            backend_model = backend_diagram

            # Convert to dict, excluding empty collections
            data = backend_model.model_dump(by_alias=True, exclude_none=True)

            # Remove empty collections
            if not data.get("handles"):
                data.pop("handles", None)
            if not data.get("persons"):
                data.pop("persons", None)
            if not data.get("api_keys"):
                data.pop("api_keys", None)

            return yaml.dump(
                data,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        except Exception as e:
            raise ValidationError(f"Failed to convert to YAML: {e}") from e

    def backend_to_readable(self, backend_diagram: BackendDiagram) -> str:
        try:
            # Use the backend diagram directly
            backend_model = backend_diagram

            flow = []
            for arrow in backend_model.arrows.values():
                source_node_id = self._extract_node_id(arrow.get("source", ""))
                target_node_id = self._extract_node_id(arrow.get("target", ""))

                source_node = backend_model.nodes.get(source_node_id)
                target_node = backend_model.nodes.get(target_node_id)

                if source_node and target_node:
                    # Get node labels directly from data
                    source_data = source_node.get("data", {})
                    target_data = target_node.get("data", {})
                    source_label = source_data.get("label", "")
                    target_label = target_data.get("label", "")

                    # Get arrow label
                    arrow_data = arrow.get("data", {})
                    variable = arrow_data.get("label", "")

                    if variable and variable != "flow":
                        flow.append(f'{source_label} -> {target_label}: "{variable}"')
                    else:
                        flow.append(f"{source_label} -> {target_label}")

            prompts = {}
            for node in backend_model.nodes.values():
                if node.get("type") in ["personJobNode", "person_job"]:
                    node_data = node.get("data", {})
                    # Get label and prompt directly from dict
                    label = node_data.get("label", "")
                    default_prompt = node_data.get("defaultPrompt") or node_data.get("default_prompt")
                    if default_prompt:
                        prompts[label] = default_prompt

            agents = {}
            for person in backend_model.persons.values():
                label = person.get("label", "")
                config = {}

                model_name = person.get("modelName") or person.get("model_name")
                if model_name and model_name != "gpt-4":
                    config["model"] = model_name

                service = person.get("service")
                if service and service != "openai":
                    config["service"] = service

                system_prompt = person.get("systemPrompt") or person.get("system_prompt")
                if system_prompt:
                    config["system"] = system_prompt

                if config:
                    agents[label] = config

            readable_model = ReadableFlow(
                flow=flow,
                prompts=prompts if prompts else None,
                agents=agents if agents else None,
            )

            return yaml.dump(
                readable_model.model_dump(exclude_none=True),
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        except Exception as e:
            raise ValidationError(f"Failed to export LLM YAML: {e}") from e

    def prepare_for_execution(
        self, diagram: DomainDiagram, api_keys: Dict[str, str]
    ) -> Dict[str, Any]:
        """Prepare a diagram for execution by the engine."""
        try:
            backend_dict = self.domain_to_backend(diagram)

            # Create BackendDiagram model
            backend_model = BackendDiagram(**backend_dict)

            # Update API keys
            for key_id, key_value in api_keys.items():
                if key_id not in backend_model.api_keys:
                    backend_model.api_keys[key_id] = {
                        "id": key_id,
                        "name": key_id,
                        "service": "openai",  # Default, should be updated
                        "key": key_value
                    }

            # Build execution hints
            hints = ExecutionHints()

            for node_id, node in backend_model.nodes.items():
                if node.get("type") == "start":
                    hints.start_nodes.append(node_id)

                if node.get("type") in ["personJobNode", "person_job"]:
                    person_id = node.get("data", {}).get("personId", node.get("data", {}).get("person_id"))
                    if person_id:
                        hints.person_nodes[node_id] = person_id

            for arrow in backend_model.arrows.values():
                target_node_id = self._extract_node_id(arrow.get("target", ""))
                source_node_id = self._extract_node_id(arrow.get("source", ""))

                if target_node_id not in hints.node_dependencies:
                    hints.node_dependencies[target_node_id] = []

                arrow_label = arrow.get("data", {}).get("label") if arrow.get("data") else None
                hint = ExecutionHint(
                    source=source_node_id,
                    variable=arrow_label if arrow_label else "flow"
                )
                hints.node_dependencies[target_node_id].append(hint)

            # Return as dict including execution hints
            result = backend_model.model_dump(by_alias=True)
            result["_execution_hints"] = hints.model_dump()

            return result

        except Exception as e:
            logger.error(f"Failed to prepare for execution: {e}")
            raise ValidationError(f"Failed to prepare diagram for execution: {e}") from e

    def _is_backend_format(self, data: Dict[str, Any]) -> bool:
        if "nodes" in data and isinstance(data["nodes"], dict):
            first_node = next(iter(data["nodes"].values()), None) if data["nodes"] else None
            if first_node and isinstance(first_node, dict):
                return True
        return False

    def _extract_node_id(self, connection: str) -> str:
        if ":" in connection:
            return connection.split(":", 1)[0]
        return connection
