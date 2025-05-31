import re
from fastapi import HTTPException

from ..exceptions import ValidationError
from .llm_service import LLMService
from .api_key_service import APIKeyService
from .memory_service import MemoryService
from ..utils.base_service import BaseService
from ..utils.arrow_utils import ArrowUtils


def round_position(position: dict) -> dict:
    """Round position coordinates to 2 decimal places."""
    return {
        "x": round(position["x"], 2),
        "y": round(position["y"], 2)
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
                    print(f"Replaced invalid apiKeyId {person['apiKeyId']} with {fallback['id']}")
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
    
    def import_uml(self, uml_text: str) -> dict:
        """Import UML text and convert to diagram state."""
        try:
            pairs = re.findall(r"(\w+)\s*->\s*(\w+)", uml_text)
            
            names = sorted({name for pair in pairs for name in pair})
            
            nodes = []
            for idx, name in enumerate(names):
                nodes.append({
                    "id": name,
                    "type": "agentNode",
                    "position": round_position({"x": idx * 200, "y": 0}),
                    "data": {"id": name, "label": name}
                })
            
            arrows = []
            for idx, (src, tgt) in enumerate(pairs):
                arrows.append({
                    "id": f"arrow-{idx}",
                    "source": src,
                    "target": tgt,
                    "type": "customArrow",
                    "data": {
                        "id": f"arrow-data-{idx}",
                        "sourceBlockId": src,
                        "targetBlockId": tgt,
                        "label": "",
                        "contentType": "variable"
                    }
                })
            
            diagram = {
                "nodes": nodes,
                "arrows": arrows,
                "apiKeys": []
            }
            return diagram
            
        except Exception as e:
            raise ValidationError(f"Failed to parse UML: {e}")
    
    def export_uml(self, diagram: dict) -> str:
        """Export diagram to UML text format."""
        try:
            self._validate_diagram(diagram)
            
            arrows = diagram.get('arrows', [])
            lines = ['@startuml']
            
            for edge in arrows:
                src = ArrowUtils.get_source(edge)
                tgt = ArrowUtils.get_target(edge)
                if src and tgt:
                    lines.append(f"{src} -> {tgt}")
            
            lines.append('@enduml')
            return '\n'.join(lines)
            
        except Exception as e:
            raise ValidationError(f"Failed to export UML: {e}")
    
    def import_yaml(self, yaml_text: str) -> dict:
        """Import YAML agent definitions and convert to diagram state."""
        return {
            "nodes": [],
            "arrows": [],
            "apiKeys": []
        }
    
