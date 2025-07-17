"""Domain service for diagram operations."""

from datetime import datetime
from typing import Any

from dipeo.models import DomainDiagram


class DiagramOperationsService:
    """
    Domain service that encapsulates business logic for diagram operations.
    This includes cloning, transformations, and batch operations.
    """

    def clone_diagram(self, diagram: DomainDiagram, new_name: str, new_description: str | None = None) -> DomainDiagram:
        """
        Clone a diagram with a new name and optional description.
        This is pure business logic without any persistence operations.
        """
        # Generate new ID based on name and timestamp
        new_id = self._generate_diagram_id(new_name)
        
        # Clone the diagram with updated metadata
        cloned_diagram = DomainDiagram(
            metadata=diagram.metadata.model_copy(
                update={
                    "id": new_id,
                    "name": new_name,
                    "description": new_description or f"Cloned from {diagram.metadata.name}",
                    "createdAt": datetime.utcnow().isoformat(),
                    "updatedAt": datetime.utcnow().isoformat(),
                    # Reset version for cloned diagram
                    "version": "1.0.0" if hasattr(diagram.metadata, "version") else None,
                }
            ),
            nodes=diagram.nodes.copy() if diagram.nodes else {},
            arrows=diagram.arrows.copy() if diagram.arrows else {},
            persons=diagram.persons.copy() if diagram.persons else {},
            viewport=diagram.viewport.model_copy() if diagram.viewport else None,
        )
        
        return cloned_diagram

    def _generate_diagram_id(self, name: str) -> str:
        """
        Generate a unique diagram ID based on name and timestamp.
        This is a business rule for ID generation.
        """
        # Sanitize name for ID
        safe_name = name.lower().replace(' ', '-')
        # Remove special characters
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '-')
        # Add timestamp for uniqueness
        timestamp = int(datetime.utcnow().timestamp())
        return f"{safe_name}-{timestamp}"

    def prepare_diagram_update(
        self, 
        diagram: DomainDiagram, 
        updates: dict[str, Any]
    ) -> DomainDiagram:
        """
        Apply updates to a diagram according to business rules.
        """
        # Always update the timestamp when diagram is modified
        updates["updatedAt"] = datetime.utcnow().isoformat()
        
        # Update metadata
        metadata_updates = {k: v for k, v in updates.items() 
                         if hasattr(diagram.metadata, k)}
        
        if metadata_updates:
            updated_metadata = diagram.metadata.model_copy(update=metadata_updates)
        else:
            updated_metadata = diagram.metadata
        
        # Create updated diagram
        return DomainDiagram(
            metadata=updated_metadata,
            nodes=updates.get("nodes", diagram.nodes),
            arrows=updates.get("arrows", diagram.arrows),
            persons=updates.get("persons", diagram.persons),
            viewport=updates.get("viewport", diagram.viewport),
        )

    def batch_update_diagrams(
        self, 
        diagrams: list[DomainDiagram], 
        updates: dict[str, Any]
    ) -> list[DomainDiagram]:
        """
        Apply the same updates to multiple diagrams.
        """
        return [
            self.prepare_diagram_update(diagram, updates.copy())
            for diagram in diagrams
        ]


    def calculate_diagram_statistics(self, diagram: DomainDiagram) -> dict[str, Any]:
        """
        Calculate various statistics about a diagram.
        This is business logic about what metrics matter.
        """
        node_count = len(diagram.nodes) if diagram.nodes else 0
        arrow_count = len(diagram.arrows) if diagram.arrows else 0
        person_count = len(diagram.persons) if diagram.persons else 0
        
        # Count node types
        node_types = {}
        if diagram.nodes:
            for node in diagram.nodes.values():
                node_type = getattr(node, "type", "unknown")
                node_types[node_type] = node_types.get(node_type, 0) + 1
        
        return {
            "total_nodes": node_count,
            "total_arrows": arrow_count,
            "total_persons": person_count,
            "node_types": node_types,
            "complexity_score": node_count + arrow_count,  # Simple complexity metric
            "has_cycles": self._has_cycles(diagram),
            "is_connected": self._is_connected(diagram),
        }

    def _has_cycles(self, diagram: DomainDiagram) -> bool:
        """
        Check if the diagram has cycles (simplified implementation).
        """
        # This is a simplified check - a full implementation would use
        # graph algorithms like DFS to detect cycles
        return False  # Placeholder

    def _is_connected(self, diagram: DomainDiagram) -> bool:
        """
        Check if all nodes in the diagram are connected.
        """
        # This is a simplified check - a full implementation would use
        # graph traversal to check connectivity
        if not diagram.nodes or len(diagram.nodes) <= 1:
            return True
        return True  # Placeholder

    def generate_safe_filename(self, diagram_name: str, extension: str = ".json") -> str:
        """
        Generate a safe filename from a diagram name.
        This is a business rule about file naming.
        """
        # Remove or replace unsafe characters
        safe_name = "".join(
            c for c in diagram_name if c.isalnum() or c in " -_"
        )
        # Limit length
        safe_name = safe_name[:50]
        # Ensure extension
        if not safe_name.endswith(extension):
            safe_name += extension
        return safe_name