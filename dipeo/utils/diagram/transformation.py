"""Pure transformation functions for diagrams."""

from typing import Dict, Any, List, Optional
from copy import deepcopy
from dipeo.models import DomainDiagram, DomainNode, DomainArrow, NodeType
from dipeo.models import parse_handle_id, extract_node_id_from_handle


class DiagramTransformer:
    """Pure functions for diagram transformations."""
    
    @staticmethod
    def merge_diagrams(diagram1: DomainDiagram, diagram2: DomainDiagram) -> DomainDiagram:
        """Merge two diagrams into one."""
        # Deep copy to avoid modifying originals
        merged_nodes = deepcopy(diagram1.nodes) + deepcopy(diagram2.nodes)
        merged_arrows = deepcopy(diagram1.arrows) + deepcopy(diagram2.arrows)
        merged_persons = deepcopy(diagram1.persons) + deepcopy(diagram2.persons)
        
        # Update IDs to avoid conflicts
        id_mapping = {}
        for i, node in enumerate(merged_nodes[len(diagram1.nodes):]):
            old_id = node.id
            new_id = f"{old_id}_d2"
            node.id = new_id
            id_mapping[old_id] = new_id
        
        # Update arrow references
        for arrow in merged_arrows[len(diagram1.arrows):]:
            source_node_id, source_handle, source_type = parse_handle_id(arrow.source)
            target_node_id, target_handle, target_type = parse_handle_id(arrow.target)
            
            if source_node_id in id_mapping:
                arrow.source = f"{id_mapping[source_node_id]}-{source_handle.value}-{source_type}"
            if target_node_id in id_mapping:
                arrow.target = f"{id_mapping[target_node_id]}-{target_handle.value}-{target_type}"
        
        return DomainDiagram(
            metadata=diagram1.metadata,
            nodes=merged_nodes,
            arrows=merged_arrows,
            persons=merged_persons,
            viewport=diagram1.viewport
        )
    
    @staticmethod
    def extract_subgraph(
        diagram: DomainDiagram, 
        node_ids: List[str]
    ) -> DomainDiagram:
        """Extract a subgraph containing only specified nodes."""
        node_id_set = set(node_ids)
        
        # Filter nodes
        sub_nodes = [n for n in diagram.nodes if n.id in node_id_set]
        
        # Filter arrows that connect nodes in the subgraph
        sub_arrows = []
        for arrow in diagram.arrows:
            source_id = extract_node_id_from_handle(arrow.source)
            target_id = extract_node_id_from_handle(arrow.target)
            if source_id in node_id_set and target_id in node_id_set:
                sub_arrows.append(arrow)
        
        # Keep all persons (they might be referenced by nodes)
        return DomainDiagram(
            metadata=diagram.metadata,
            nodes=sub_nodes,
            arrows=sub_arrows,
            persons=diagram.persons,
            viewport=diagram.viewport
        )
    
    @staticmethod
    def optimize_layout(diagram: DomainDiagram) -> DomainDiagram:
        """Optimize the visual layout of a diagram."""
        # This is a placeholder for layout optimization
        # In a real implementation, this would use graph layout algorithms
        optimized = deepcopy(diagram)
        
        # Simple grid layout as example
        cols = 4
        spacing = 200
        
        for i, node in enumerate(optimized.nodes):
            row = i // cols
            col = i % cols
            node.position = {
                "x": col * spacing + 100,
                "y": row * spacing + 100
            }
        
        return optimized
    
    @staticmethod
    def add_node_prefix(diagram: DomainDiagram, prefix: str) -> DomainDiagram:
        """Add a prefix to all node IDs in a diagram."""
        transformed = deepcopy(diagram)
        id_mapping = {}
        
        # Update node IDs
        for node in transformed.nodes:
            old_id = node.id
            new_id = f"{prefix}_{old_id}"
            node.id = new_id
            id_mapping[old_id] = new_id
        
        # Update arrow references
        for arrow in transformed.arrows:
            source_node_id, source_handle, source_type = parse_handle_id(arrow.source)
            target_node_id, target_handle, target_type = parse_handle_id(arrow.target)
            
            if source_node_id in id_mapping:
                arrow.source = f"{id_mapping[source_node_id]}-{source_handle.value}-{source_type}"
            if target_node_id in id_mapping:
                arrow.target = f"{id_mapping[target_node_id]}-{target_handle.value}-{target_type}"
        
        return transformed
    
    @staticmethod
    def remove_orphaned_arrows(diagram: DomainDiagram) -> DomainDiagram:
        """Remove arrows that reference non-existent nodes."""
        node_ids = set(n.id for n in diagram.nodes)
        
        valid_arrows = []
        for arrow in diagram.arrows:
            source_id = extract_node_id_from_handle(arrow.source)
            target_id = extract_node_id_from_handle(arrow.target)
            
            if source_id in node_ids and target_id in node_ids:
                valid_arrows.append(arrow)
        
        return DomainDiagram(
            metadata=diagram.metadata,
            nodes=diagram.nodes,
            arrows=valid_arrows,
            persons=diagram.persons,
            viewport=diagram.viewport
        )