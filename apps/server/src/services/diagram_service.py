import yaml
import logging
from fastapi import HTTPException

from ..exceptions import ValidationError
from .llm_service import LLMService
from .api_key_service import APIKeyService
from .memory_service import MemoryService
from ..utils.base_service import BaseService

logger = logging.getLogger(__name__)


def round_position(position: dict) -> dict:
    """Round position coordinates to 1 decimal places."""
    return {
        "x": round(position["x"], 1),
        "y": round(position["y"], 1)
    }


class DiagramService(BaseService):
    """Service for handling diagram operations."""
    
    def __init__(self, llm_service: LLMService, api_key_service: APIKeyService, memory_service: MemoryService):
        super().__init__()
        self.llm_service = llm_service
        self.api_key_service = api_key_service
        self.memory_service = memory_service


    def _validate_and_fix_api_keys(self, diagram: dict) -> None:
        """Validate and fix API keys in diagram persons."""
        valid_api_keys = {key["id"] for key in self.api_key_service.list_api_keys()}

        # Fix invalid API key references in persons
        for person in diagram.get("persons", []):
            if person.get("apiKeyId") and person["apiKeyId"] not in valid_api_keys:
                # Try to find a fallback key for the same service
                all_keys = self.api_key_service.list_api_keys()
                fallback = next(
                    (k for k in all_keys if k["service"] == person.get("service")),
                    None
                )
                if fallback:
                    logger.info(f"Replaced invalid apiKeyId {person['apiKeyId']} with {fallback['id']}")
                    person["apiKeyId"] = fallback["id"]
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No valid API key found for service: {person.get('service')}"
                    )
    
    def _validate_diagram(self, diagram: dict) -> None:
        """Validate diagram structure."""
        if not isinstance(diagram, dict):
            raise ValidationError("Diagram must be a dictionary")
        
        self.validate_required_fields(diagram, ["nodes", "arrows"])
        
        if not isinstance(diagram["nodes"], list):
            raise ValidationError("Nodes must be a list")
        
        if not isinstance(diagram["arrows"], list):
            raise ValidationError("arrows must be a list")
    
    def import_yaml(self, yaml_text: str) -> dict:
        """Import YAML agent definitions and convert to diagram state."""
        try:
            # Parse YAML content
            data = yaml.safe_load(yaml_text)
            
            # If the data is already in diagram format, validate and return it
            if isinstance(data, dict) and "nodes" in data and "arrows" in data:
                self._validate_diagram(data)
                # Ensure all required fields are present
                data.setdefault("persons", [])
                data.setdefault("apiKeys", [])
                return data
            
            # Otherwise, return an empty diagram structure
            # The frontend handles more complex YAML formats (LLM-friendly format)
            return {
                "nodes": [],
                "arrows": [],
                "persons": [],
                "apiKeys": []
            }
            
        except yaml.YAMLError as e:
            raise ValidationError(f"Failed to parse YAML: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to import YAML: {e}")
    
    def export_llm_yaml(self, diagram: dict) -> str:
        """Export diagram to LLM-friendly YAML format.
        
        Note: This is a basic implementation. For sophisticated LLM YAML export,
        use the CLI tool which leverages the frontend TypeScript converters:
        `python tool.py convert diagram.json output.llm-yaml`
        """
        try:
            # Basic LLM-friendly format export
            nodes = diagram.get("nodes", [])
            arrows = diagram.get("arrows", [])
            persons = diagram.get("persons", [])
            
            # Create simple flow representation
            flow = []
            for arrow in arrows:
                source_node = next((n for n in nodes if n["id"] == arrow["source"]), None)
                target_node = next((n for n in nodes if n["id"] == arrow["target"]), None)
                
                if source_node and target_node:
                    source_label = source_node.get("data", {}).get("label", arrow["source"])
                    target_label = target_node.get("data", {}).get("label", arrow["target"])
                    variable = arrow.get("data", {}).get("label", "")
                    
                    if variable and variable != "flow":
                        flow.append(f'{source_label} -> {target_label}: "{variable}"')
                    else:
                        flow.append(f'{source_label} -> {target_label}')
            
            # Extract prompts from PersonJob nodes
            prompts = {}
            for node in nodes:
                if node.get("type") == "personJobNode":
                    data = node.get("data", {})
                    label = data.get("label", node["id"])
                    default_prompt = data.get("defaultPrompt", "")
                    if default_prompt:
                        prompts[label] = default_prompt
            
            # Extract agent configurations
            agents = {}
            for person in persons:
                label = person.get("label", person["id"])
                config = {}
                if person.get("modelName") and person["modelName"] != "gpt-4":
                    config["model"] = person["modelName"]
                if person.get("service") and person["service"] != "openai":
                    config["service"] = person["service"]
                if person.get("systemPrompt"):
                    config["system"] = person["systemPrompt"]
                
                if config:
                    agents[label] = config
            
            # Build LLM YAML structure
            llm_yaml = {"flow": flow}
            if prompts:
                llm_yaml["prompts"] = prompts
            if agents:
                llm_yaml["agents"] = agents
            
            return yaml.dump(llm_yaml, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
        except Exception as e:
            raise ValidationError(f"Failed to export LLM YAML: {e}")
    
