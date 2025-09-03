"""Strategy for serializing/deserializing ExecutableDiagram format.

This format preserves the compiled state of a diagram, including:
- Strongly-typed executable nodes
- Resolved edges with transformation rules
- Pre-calculated execution metadata
- Validated state

Think of this as a "compiled binary" for diagrams - it saves the 
expensive compilation step and preserves all computed information.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from dipeo.domain.diagram.models.executable_diagram import (
    ExecutableDiagram,
    ExecutableEdgeV2,
    ExecutableNode,
)
from dipeo.diagram_generated import (
    DomainDiagram,
    NodeType,
    ContentType,
    Vec2,
)
from dipeo.diagram_generated.generated_nodes import create_executable_node

from dipeo.domain.diagram.utils import _JsonMixin
from .base_strategy import BaseConversionStrategy

log = logging.getLogger(__name__)


class ExecutableJsonStrategy(_JsonMixin, BaseConversionStrategy):
    """Compiled executable diagram format.
    
    This format exports the fully compiled ExecutableDiagram with:
    - Typed nodes (PersonJobNode, ConditionNode, etc.)
    - Resolved edges with transformation rules
    - Pre-calculated execution order and metadata
    
    Benefits:
    - Skip expensive compilation on load
    - Preserve all validation and resolution
    - Ship pre-compiled diagrams for production
    - Faster startup for complex diagrams
    """

    format_id = "executable"
    format_info = {
        "name": "Executable Diagram",
        "description": "Pre-compiled diagram format with resolved connections and typed nodes",
        "extension": ".executable.json",
        "supports_import": True,
        "supports_export": True,
    }

    def deserialize_to_executable(self, content: str) -> ExecutableDiagram:
        """Deserialize directly to ExecutableDiagram, skipping compilation."""
        data = self.parse(content)
        
        # Reconstruct typed nodes
        nodes = []
        for node_data in data.get("nodes", []):
            node_type = NodeType(node_data["type"])
            position = Vec2(x=node_data["position"]["x"], y=node_data["position"]["y"])
            
            # Create strongly-typed node from serialized data
            typed_node = create_executable_node(
                node_type=node_type,
                node_id=node_data["id"],
                position=position,
                label=node_data.get("label", ""),
                data=node_data.get("data", {})
            )
            nodes.append(typed_node)
        
        # Reconstruct edges with transformation rules
        edges = []
        for edge_data in data.get("edges", []):
            edge = ExecutableEdgeV2(
                id=edge_data["id"],
                source_node_id=edge_data["source_node_id"],
                target_node_id=edge_data["target_node_id"],
                source_output=edge_data.get("source_output", "default"),
                target_input=edge_data.get("target_input", "default"),
                content_type=ContentType(edge_data["content_type"]) if edge_data.get("content_type") else None,
                transform_rules=edge_data.get("transform_rules", {}),
                is_conditional=edge_data.get("is_conditional", False),
                requires_first_execution=edge_data.get("requires_first_execution", False),
                metadata=edge_data.get("metadata", {})
            )
            edges.append(edge)
        
        # Reconstruct execution order
        execution_order = data.get("execution_order", [])
        
        # Reconstruct metadata including validation results
        metadata = data.get("metadata", {})
        api_keys = data.get("api_keys", {})
        
        return ExecutableDiagram(
            nodes=nodes,
            edges=edges,
            execution_order=execution_order,
            metadata=metadata,
            api_keys=api_keys
        )

    def serialize_from_executable(self, diagram: ExecutableDiagram) -> str:
        """Serialize ExecutableDiagram preserving all compiled information."""
        data = {
            "format": "executable",
            "version": "1.0",
            "nodes": [self._serialize_node(node) for node in diagram.nodes],
            "edges": [self._serialize_edge(edge) for edge in diagram.edges],
            "execution_order": list(diagram.execution_order),
            "metadata": diagram.metadata,
            "execution_hints": diagram.get_execution_hints(),
        }
        
        return self.format(data)
    
    def _serialize_node(self, node: ExecutableNode) -> dict[str, Any]:
        """Serialize a typed executable node."""
        node_dict = node.to_dict()
        
        # Add the actual type value for reconstruction
        node_dict["type"] = node.type.value if hasattr(node.type, 'value') else str(node.type)
        
        # Extract data fields from typed node
        # This preserves all the strongly-typed fields
        data = {}
        exclude_fields = {"id", "type", "position", "label", "flipped", "metadata"}
        
        for field_name in dir(node):
            if not field_name.startswith("_") and field_name not in exclude_fields:
                value = getattr(node, field_name, None)
                if value is not None and not callable(value):
                    # Convert enums and special types to serializable format
                    if hasattr(value, 'value'):
                        data[field_name] = value.value
                    elif hasattr(value, 'model_dump'):
                        data[field_name] = value.model_dump()
                    else:
                        data[field_name] = value
        
        node_dict["data"] = data
        return node_dict
    
    def _serialize_edge(self, edge: ExecutableEdgeV2) -> dict[str, Any]:
        """Serialize an executable edge with all resolution data."""
        return {
            "id": edge.id,
            "source_node_id": edge.source_node_id,
            "target_node_id": edge.target_node_id,
            "source_output": edge.source_output,
            "target_input": edge.target_input,
            "content_type": edge.content_type.value if edge.content_type and hasattr(edge.content_type, 'value') else str(edge.content_type) if edge.content_type else None,
            "transform_rules": edge.transform_rules,
            "is_conditional": edge.is_conditional,
            "requires_first_execution": edge.requires_first_execution,
            "metadata": edge.metadata,
        }

    # Standard strategy interface (for compatibility)
    def deserialize_to_domain(self, content: str, diagram_path: str | None = None) -> DomainDiagram:
        """Convert executable format back to domain format.
        
        This is mainly for compatibility with the existing system.
        Normally you'd use deserialize_to_executable() directly.
        """
        # First deserialize to ExecutableDiagram
        executable = self.deserialize_to_executable(content)
        
        # Then use the domain compiler to convert back to DomainDiagram
        from dipeo.domain.diagram.compilation import DomainDiagramCompiler
        compiler = DomainDiagramCompiler()
        return compiler.decompile(executable)
    
    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        """Compile and serialize a domain diagram.
        
        This compiles the diagram first, then serializes the result.
        """
        from dipeo.domain.diagram.compilation import DomainDiagramCompiler
        compiler = DomainDiagramCompiler()
        executable = compiler.compile(diagram)
        return self.serialize_from_executable(executable)


    # Heuristics
    def detect_confidence(self, data: dict[str, Any]) -> float:
        """Detect if this is an executable format."""
        if data.get("format") == "executable":
            return 1.0
        if "edges" in data and any("transform_rules" in e for e in data.get("edges", [])):
            return 0.9
        return 0.1

    def quick_match(self, content: str) -> bool:
        """Quick check for executable format."""
        return '"format": "executable"' in content or '"transform_rules"' in content