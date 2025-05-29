import re
from typing import Any, Dict, List, Tuple

from ..exceptions import DiagramExecutionError, ValidationError
from .llm_service import LLMService
from ..utils.base_service import BaseService
from ..utils.arrow_utils import ArrowUtils
from ..utils.diagram_migrator import DiagramMigrator


def round_position(position: dict) -> dict:
    """Round position coordinates to 2 decimal places."""
    return {
        "x": round(position["x"], 2),
        "y": round(position["y"], 2)
    }


class DiagramService(BaseService):
    """Service for handling diagram operations."""
    
    def __init__(self, llm_service: LLMService):
        super().__init__()
        self.llm_service = llm_service

    async def run_diagram(self, diagram: dict) -> Tuple[Dict[str, Any], float]:
        """Execute a diagram and return results."""
        try:
            from ..run_graph import DiagramExecutor

            self._validate_diagram(diagram)
            executor = DiagramExecutor(diagram)
            context, cost = await executor.run()
            return context, cost
        except Exception as e:
            raise DiagramExecutionError(f"Diagram execution failed: {e}")
    
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
            return DiagramMigrator.migrate(diagram)
            
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