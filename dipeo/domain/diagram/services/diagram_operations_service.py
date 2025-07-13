"""Domain service for diagram operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from dipeo.models import DomainDiagram


class DiagramOperationsService:
    """
    Domain service that encapsulates business logic for diagram operations.
    This includes cloning, transformations, and batch operations.
    """

    def clone_diagram(self, diagram: DomainDiagram, new_name: str, new_description: Optional[str] = None) -> DomainDiagram:
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
        updates: Dict[str, Any]
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
        diagrams: List[DomainDiagram], 
        updates: Dict[str, Any]
    ) -> List[DomainDiagram]:
        """
        Apply the same updates to multiple diagrams.
        """
        return [
            self.prepare_diagram_update(diagram, updates.copy())
            for diagram in diagrams
        ]

    def merge_diagrams(
        self, 
        primary: DomainDiagram, 
        secondary: DomainDiagram,
        merge_name: str
    ) -> DomainDiagram:
        """
        Merge two diagrams into a new one.
        Nodes from secondary are added with a prefix to avoid ID conflicts.
        """
        # Generate new ID for merged diagram
        merged_id = self._generate_diagram_id(merge_name)
        
        # Merge nodes with prefix for secondary diagram
        merged_nodes = primary.nodes.copy() if primary.nodes else {}
        
        if secondary.nodes:
            for node_id, node in secondary.nodes.items():
                # Add prefix to avoid conflicts
                prefixed_id = f"merged_{node_id}"
                merged_nodes[prefixed_id] = node.model_copy() if hasattr(node, "model_copy") else node
        
        # Merge arrows (update node references)
        merged_arrows = primary.arrows.copy() if primary.arrows else {}
        
        if secondary.arrows:
            for arrow_id, arrow in secondary.arrows.items():
                # Update arrow to reference prefixed nodes
                if hasattr(arrow, "from_node") and hasattr(arrow, "to_node"):
                    arrow_copy = arrow.model_copy()
                    arrow_copy.from_node = f"merged_{arrow.from_node}"
                    arrow_copy.to_node = f"merged_{arrow.to_node}"
                    merged_arrows[f"merged_{arrow_id}"] = arrow_copy
                else:
                    merged_arrows[f"merged_{arrow_id}"] = arrow
        
        # Merge persons
        merged_persons = primary.persons.copy() if primary.persons else {}
        if secondary.persons:
            merged_persons.update(secondary.persons)
        
        # Create merged diagram
        return DomainDiagram(
            metadata=primary.metadata.model_copy(
                update={
                    "id": merged_id,
                    "name": merge_name,
                    "description": f"Merged from {primary.metadata.name} and {secondary.metadata.name}",
                    "createdAt": datetime.utcnow().isoformat(),
                    "updatedAt": datetime.utcnow().isoformat(),
                }
            ),
            nodes=merged_nodes,
            arrows=merged_arrows,
            persons=merged_persons,
            viewport=primary.viewport,  # Use primary's viewport
        )

    def extract_subdiagram(
        self,
        diagram: DomainDiagram,
        node_ids: List[str],
        subdiagram_name: str
    ) -> DomainDiagram:
        """
        Extract a subset of nodes into a new diagram.
        """
        # Filter nodes
        extracted_nodes = {
            node_id: node
            for node_id, node in (diagram.nodes or {}).items()
            if node_id in node_ids
        }
        
        # Filter arrows (only include if both nodes are in the subset)
        extracted_arrows = {}
        if diagram.arrows:
            for arrow_id, arrow in diagram.arrows.items():
                if (hasattr(arrow, "from_node") and hasattr(arrow, "to_node") and
                    arrow.from_node in node_ids and arrow.to_node in node_ids):
                    extracted_arrows[arrow_id] = arrow
        
        # Create new diagram with extracted components
        return DomainDiagram(
            metadata=diagram.metadata.model_copy(
                update={
                    "id": self._generate_diagram_id(subdiagram_name),
                    "name": subdiagram_name,
                    "description": f"Extracted from {diagram.metadata.name}",
                    "createdAt": datetime.utcnow().isoformat(),
                    "updatedAt": datetime.utcnow().isoformat(),
                }
            ),
            nodes=extracted_nodes,
            arrows=extracted_arrows,
            persons=diagram.persons.copy() if diagram.persons else {},
            viewport=diagram.viewport,
        )

    def calculate_diagram_statistics(self, diagram: DomainDiagram) -> Dict[str, Any]:
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