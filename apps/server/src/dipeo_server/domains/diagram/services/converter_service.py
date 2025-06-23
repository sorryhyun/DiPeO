"""Service for converting between different diagram formats."""

import logging
from typing import Any, Dict, List, Optional

import yaml
from dipeo_domain import (
    DomainDiagram,
    DomainNode,
    DomainArrow,
    DomainPerson,
    DomainHandle,
    DiagramMetadata,
    DomainApiKey,
)

from dipeo_core import BaseService, ValidationError


logger = logging.getLogger(__name__)


class DiagramConverterService(BaseService):
    """Converts between storage, domain, YAML, and execution formats."""

    def __init__(self):
        super().__init__()

    async def initialize(self) -> None:
        pass

    def storage_to_domain(self, storage_dict: Dict[str, Any]) -> DomainDiagram:
        """Convert storage format (dict of dicts) to domain format (lists)."""
        try:
            nodes = []
            if "nodes" in storage_dict and isinstance(storage_dict["nodes"], dict):
                for node_id, node_data in storage_dict["nodes"].items():
                    if "id" not in node_data:
                        node_data["id"] = node_id
                    nodes.append(DomainNode(**node_data))
            
            arrows = []
            if "arrows" in storage_dict and isinstance(storage_dict["arrows"], dict):
                for arrow_id, arrow_data in storage_dict["arrows"].items():
                    if "id" not in arrow_data:
                        arrow_data["id"] = arrow_id
                    arrows.append(DomainArrow(**arrow_data))
            
            persons = []
            if "persons" in storage_dict and isinstance(storage_dict["persons"], dict):
                for person_id, person_data in storage_dict["persons"].items():
                    if "id" not in person_data:
                        person_data["id"] = person_id
                    if "apiKeyId" in person_data and "api_key_id" not in person_data:
                        person_data["api_key_id"] = person_data.pop("apiKeyId")
                    if "modelName" in person_data and "model_name" not in person_data:
                        person_data["model_name"] = person_data.pop("modelName")
                    if "systemPrompt" in person_data and "system_prompt" not in person_data:
                        person_data["system_prompt"] = person_data.pop("systemPrompt")
                    persons.append(DomainPerson(**person_data))
            
            handles = []
            if "handles" in storage_dict and isinstance(storage_dict["handles"], dict):
                for handle_id, handle_data in storage_dict["handles"].items():
                    if "id" not in handle_data:
                        handle_data["id"] = handle_id
                    handles.append(DomainHandle(**handle_data))
            
            api_keys = []
            if "api_keys" in storage_dict and isinstance(storage_dict["api_keys"], dict):
                for key_id, key_data in storage_dict["api_keys"].items():
                    if "id" not in key_data:
                        key_data["id"] = key_id
                    api_keys.append(DomainApiKey(**key_data))
            elif "apiKeys" in storage_dict and isinstance(storage_dict["apiKeys"], dict):
                for key_id, key_data in storage_dict["apiKeys"].items():
                    if "id" not in key_data:
                        key_data["id"] = key_id
                    api_keys.append(DomainApiKey(**key_data))
            
            metadata_dict = storage_dict.get("metadata", {})
            metadata = None
            if metadata_dict:
                from datetime import datetime
                # Ensure required fields have defaults
                if "version" not in metadata_dict:
                    metadata_dict["version"] = "2.0.0"
                if "created" not in metadata_dict:
                    metadata_dict["created"] = datetime.now().isoformat()
                if "modified" not in metadata_dict:
                    metadata_dict["modified"] = datetime.now().isoformat()
                
                metadata = DiagramMetadata(**metadata_dict)
            
            return DomainDiagram(
                nodes=nodes,
                arrows=arrows,
                persons=persons,
                handles=handles,
                apiKeys=api_keys,
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"Failed to convert storage to domain: {e}")
            raise ValidationError(f"Invalid storage format: {e}")

    def domain_to_storage(self, diagram: DomainDiagram) -> Dict[str, Any]:
        """Convert domain format (lists) to storage format (dict of dicts)."""
        try:
            storage_dict = {
                "nodes": {},
                "arrows": {},
                "persons": {},
                "handles": {},
                "api_keys": {},
                "metadata": diagram.metadata.model_dump() if diagram.metadata else {},
            }
            
            if diagram.nodes:
                for node in diagram.nodes:
                    node_dict = node.model_dump()
                    storage_dict["nodes"][node.id] = node_dict
            
            if diagram.arrows:
                for arrow in diagram.arrows:
                    arrow_dict = arrow.model_dump()
                    storage_dict["arrows"][arrow.id] = arrow_dict
            
            if diagram.persons:
                for person in diagram.persons:
                    person_dict = person.model_dump()
                    if "api_key_id" in person_dict:
                        person_dict["apiKeyId"] = person_dict.pop("api_key_id")
                    if "model_name" in person_dict:
                        person_dict["modelName"] = person_dict.pop("model_name")
                    if "system_prompt" in person_dict:
                        person_dict["systemPrompt"] = person_dict.pop("system_prompt")
                    storage_dict["persons"][person.id] = person_dict
            
            if diagram.handles:
                for handle in diagram.handles:
                    handle_dict = handle.model_dump()
                    storage_dict["handles"][handle.id] = handle_dict
            
            if diagram.api_keys:
                for api_key in diagram.api_keys:
                    api_key_dict = api_key.model_dump()
                    storage_dict["api_keys"][api_key.id] = api_key_dict
            
            # Metadata ID has already been included if it exists via model_dump()
            
            return storage_dict
            
        except Exception as e:
            logger.error(f"Failed to convert domain to storage: {e}")
            raise ValidationError(f"Failed to convert domain model: {e}")

    def yaml_to_storage(self, yaml_content: str) -> Dict[str, Any]:
        """Convert YAML content to storage format."""
        try:
            data = yaml.safe_load(yaml_content)
            
            if not isinstance(data, dict):
                raise ValidationError("YAML content must be a dictionary")
            
            if self._is_storage_format(data):
                return data
            
            if "nodes" in data and isinstance(data.get("nodes"), list):
                data["nodes"] = {n["id"]: n for n in data["nodes"]}
            
            if "arrows" in data and isinstance(data.get("arrows"), list):
                data["arrows"] = {a["id"]: a for a in data["arrows"]}
            
            if "persons" in data and isinstance(data.get("persons"), list):
                data["persons"] = {p["id"]: p for p in data["persons"]}
            
            if "handles" in data and isinstance(data.get("handles"), list):
                data["handles"] = {h["id"]: h for h in data["handles"]}
            
            if "apiKeys" in data and "api_keys" not in data:
                data["api_keys"] = data.pop("apiKeys")
            
            if "api_keys" in data and isinstance(data.get("api_keys"), list):
                data["api_keys"] = {k["id"]: k for k in data["api_keys"]}
            
            data.setdefault("nodes", {})
            data.setdefault("arrows", {})
            data.setdefault("persons", {})
            data.setdefault("handles", {})
            data.setdefault("metadata", {})
            
            return data
            
        except yaml.YAMLError as e:
            raise ValidationError(f"Failed to parse YAML: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to convert YAML: {e}")

    def storage_to_yaml(self, storage_dict: Dict[str, Any]) -> str:
        """Convert storage format to YAML."""
        try:
            data = dict(storage_dict)
            
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
            raise ValidationError(f"Failed to convert to YAML: {e}")

    def storage_to_llm_yaml(self, storage_dict: Dict[str, Any]) -> str:
        """Convert storage format to LLM-friendly YAML."""
        try:
            nodes = storage_dict.get("nodes", {})
            arrows = storage_dict.get("arrows", {})
            persons = storage_dict.get("persons", {})
            
            flow = []
            for arrow_id, arrow in arrows.items():
                source_node_id = self._extract_node_id(arrow.get("source", ""))
                target_node_id = self._extract_node_id(arrow.get("target", ""))
                
                source_node = nodes.get(source_node_id)
                target_node = nodes.get(target_node_id)
                
                if source_node and target_node:
                    source_label = source_node.get("data", {}).get("label", source_node_id)
                    target_label = target_node.get("data", {}).get("label", target_node_id)
                    variable = arrow.get("data", {}).get("label", "")
                    
                    if variable and variable != "flow":
                        flow.append(f'{source_label} -> {target_label}: "{variable}"')
                    else:
                        flow.append(f"{source_label} -> {target_label}")
            
            prompts = {}
            for node_id, node in nodes.items():
                if node.get("type") in ["personJobNode", "person_job"]:
                    data = node.get("data", {})
                    label = data.get("label", node_id)
                    default_prompt = data.get("defaultPrompt", "")
                    if default_prompt:
                        prompts[label] = default_prompt
            
            agents = {}
            for person_id, person in persons.items():
                label = person.get("label", person_id)
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
            
            llm_yaml = {"flow": flow}
            if prompts:
                llm_yaml["prompts"] = prompts
            if agents:
                llm_yaml["agents"] = agents
            
            return yaml.dump(
                llm_yaml,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
            
        except Exception as e:
            raise ValidationError(f"Failed to export LLM YAML: {e}")

    def prepare_for_execution(
        self, diagram: DomainDiagram, api_keys: Dict[str, str]
    ) -> Dict[str, Any]:
        """Prepare a diagram for execution by the engine."""
        try:
            storage = self.domain_to_storage(diagram)
            
            storage["api_keys"] = api_keys
            
            execution_hints = {
                "start_nodes": [],
                "node_dependencies": {},
                "person_nodes": {},
            }
            
            for node_id, node in storage["nodes"].items():
                if node.get("type") == "start":
                    execution_hints["start_nodes"].append(node_id)
                
                if node.get("type") in ["personJobNode", "person_job"]:
                    node_data = node.get("data") or {}
                    person_id = node_data.get("personId") if isinstance(node_data, dict) else None
                    if person_id:
                        execution_hints["person_nodes"][node_id] = person_id
            
            for arrow_id, arrow in storage["arrows"].items():
                target_node_id = self._extract_node_id(arrow.get("target", ""))
                source_node_id = self._extract_node_id(arrow.get("source", ""))
                
                if target_node_id not in execution_hints["node_dependencies"]:
                    execution_hints["node_dependencies"][target_node_id] = []
                
                arrow_data = arrow.get("data") or {}
                execution_hints["node_dependencies"][target_node_id].append({
                    "source": source_node_id,
                    "variable": arrow_data.get("label", "flow") if isinstance(arrow_data, dict) else "flow",
                })
            
            storage["_execution_hints"] = execution_hints
            
            return storage
            
        except Exception as e:
            logger.error(f"Failed to prepare for execution: {e}")
            raise ValidationError(f"Failed to prepare diagram for execution: {e}")

    def _is_storage_format(self, data: Dict[str, Any]) -> bool:
        if "nodes" in data and isinstance(data["nodes"], dict):
            first_node = next(iter(data["nodes"].values()), None) if data["nodes"] else None
            if first_node and isinstance(first_node, dict):
                return True
        return False

    def _extract_node_id(self, connection: str) -> str:
        if ":" in connection:
            return connection.split(":", 1)[0]
        return connection