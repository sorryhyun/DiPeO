#!/usr/bin/env tsx

/**
 * Generate Python conversion utilities from TypeScript source
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import process from 'node:process';

const __dirname = dirname(fileURLToPath(import.meta.url));

const PYTHON_TEMPLATE = `"""
Single-source conversion utilities for DiPeO domain models.
This file is auto-generated from TypeScript - DO NOT EDIT.
"""

from typing import Dict, List, Tuple, Any, Optional
from dipeo_domain import (
    NodeType,
    HandleDirection,
    DataType,
    NodeID,
    ArrowID,
    HandleID,
    PersonID,
    ApiKeyID,
    DiagramID,
    ExecutionID,
    DomainNode,
    DomainArrow,
    DomainHandle,
    DomainDiagram,
    DomainPerson,
    DomainApiKey,
)


# ============================================================================
# Node Type Mapping
# ============================================================================

NODE_TYPE_MAP: Dict[str, NodeType] = {
    'start': NodeType.start,
    'person_job': NodeType.person_job,
    'personJob': NodeType.person_job,  # Frontend compatibility
    'condition': NodeType.condition,
    'job': NodeType.job,
    'endpoint': NodeType.endpoint,
    'db': NodeType.db,
    'user_response': NodeType.user_response,
    'userResponse': NodeType.user_response,  # Frontend compatibility
    'notion': NodeType.notion,
    'person_batch_job': NodeType.person_batch_job,
    'personBatchJob': NodeType.person_batch_job,  # Frontend compatibility
}

NODE_TYPE_REVERSE_MAP: Dict[NodeType, str] = {
    v: k for k, v in NODE_TYPE_MAP.items()
}


def node_kind_to_domain_type(kind: str) -> NodeType:
    """Convert frontend node type to domain node type."""
    domain_type = NODE_TYPE_MAP.get(kind)
    if not domain_type:
        raise ValueError(f"Unknown node kind: {kind}")
    return domain_type


def domain_type_to_node_kind(node_type: NodeType) -> str:
    """Convert domain node type to frontend node type."""
    kind = NODE_TYPE_REVERSE_MAP.get(node_type)
    if not kind:
        raise ValueError(f"Unknown node type: {node_type}")
    return kind


# ============================================================================
# Handle ID Management
# ============================================================================

def create_handle_id(node_id: NodeID, handle_label: str) -> HandleID:
    """Create a handle ID from node ID and handle label."""
    return HandleID(f"{node_id}:{handle_label}")


def parse_handle_id(handle_id: HandleID) -> Tuple[NodeID, str]:
    """Parse a handle ID into its components."""
    parts = handle_id.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid handle ID format: {handle_id}")
    
    node_id, handle_label = parts
    if not node_id or not handle_label:
        raise ValueError(f"Invalid handle ID format: {handle_id}")
    
    return NodeID(node_id), handle_label


# ============================================================================
# Handle Compatibility
# ============================================================================

def are_handles_compatible(
    source_handle: DomainHandle,
    target_handle: DomainHandle
) -> bool:
    """Check if two handles are compatible for connection."""
    # Opposite directions required
    if source_handle.direction == target_handle.direction:
        return False
    
    # Output must connect to input
    if source_handle.direction != HandleDirection.output:
        return False
    
    # Check data type compatibility
    return is_data_type_compatible(source_handle.data_type, target_handle.data_type)


def is_data_type_compatible(
    source_type: DataType,
    target_type: DataType
) -> bool:
    """Check if source data type is compatible with target data type."""
    # Same type is always compatible
    if source_type == target_type:
        return True
    
    # 'any' type is compatible with everything
    if source_type == DataType.any or target_type == DataType.any:
        return True
    
    # Type-specific compatibility rules
    compatibility_rules = {
        DataType.string: [DataType.any],
        DataType.number: [DataType.any],
        DataType.boolean: [DataType.any],
        DataType.object: [DataType.any],
        DataType.array: [DataType.any],
        DataType.any: list(DataType),
    }
    
    return target_type in compatibility_rules.get(source_type, [])


# ============================================================================
# Data Structure Conversions
# ============================================================================

def diagram_arrays_to_maps(
    nodes: List[DomainNode],
    arrows: List[DomainArrow],
    handles: List[DomainHandle],
    persons: List[DomainPerson],
    api_keys: Optional[List[DomainApiKey]] = None
) -> Dict[str, Dict[str, Any]]:
    """Convert array-based diagram to map-based structure."""
    return {
        "nodes": {n.id: n for n in nodes},
        "arrows": {a.id: a for a in arrows},
        "handles": {h.id: h for h in handles},
        "persons": {p.id: p for p in persons},
        "api_keys": {k.id: k for k in (api_keys or [])},
    }


def diagram_maps_to_arrays(
    nodes: Dict[NodeID, DomainNode],
    arrows: Dict[ArrowID, DomainArrow],
    handles: Dict[HandleID, DomainHandle],
    persons: Dict[PersonID, DomainPerson],
    api_keys: Optional[Dict[ApiKeyID, DomainApiKey]] = None
) -> Dict[str, List[Any]]:
    """Convert map-based diagram to array-based structure."""
    return {
        "nodes": list(nodes.values()),
        "arrows": list(arrows.values()),
        "handles": list(handles.values()),
        "persons": list(persons.values()),
        "api_keys": list(api_keys.values()) if api_keys else [],
    }


# ============================================================================
# Position Calculations
# ============================================================================

def calculate_handle_offset(
    direction: HandleDirection,
    index: int,
    total: int,
    node_width: int = 200,
    node_height: int = 100
) -> Dict[str, float]:
    """Calculate handle position offset based on direction."""
    spacing = 30
    start_offset = (total - 1) * spacing / 2
    
    if direction == HandleDirection.input:
        return {
            "x": node_width / 2,
            "y": -start_offset + (index * spacing),
        }
    elif direction == HandleDirection.output:
        return {
            "x": node_width / 2,
            "y": node_height + start_offset - (index * spacing),
        }
    else:
        return {"x": node_width / 2, "y": node_height / 2}


def calculate_handle_position(
    node_position: Dict[str, float],
    handle_offset: Dict[str, float]
) -> Dict[str, float]:
    """Calculate absolute handle position."""
    return {
        "x": node_position["x"] + handle_offset["x"],
        "y": node_position["y"] + handle_offset["y"],
    }


# ============================================================================
# Validation Utilities
# ============================================================================

def validate_node_data(
    node_type: NodeType,
    data: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """Validate node data based on node type."""
    errors = []
    
    # Type-specific validation rules
    if node_type in (NodeType.personJob, NodeType.personBatchJob):
        if not data.get("personId"):
            errors.append("Person ID is required for person job nodes")
        if not data.get("userPrompt") and not data.get("systemPrompt"):
            errors.append("Either user prompt or system prompt is required")
    
    elif node_type == NodeType.condition:
        if not data.get("personId"):
            errors.append("Person ID is required for condition nodes")
        if not data.get("prompt"):
            errors.append("Prompt is required for condition nodes")
    
    elif node_type == NodeType.db:
        if not data.get("operation"):
            errors.append("Database operation is required")
        if data.get("operation") not in ["query", "insert", "update", "delete"]:
            errors.append("Invalid database operation")
    
    elif node_type == NodeType.endpoint:
        if not data.get("method"):
            errors.append("HTTP method is required")
        if not data.get("url"):
            errors.append("URL is required")
    
    return len(errors) == 0, errors


def validate_arrow_connection(
    source_node: DomainNode,
    target_node: DomainNode,
    source_handle: DomainHandle,
    target_handle: DomainHandle
) -> Tuple[bool, List[str]]:
    """Validate arrow connection."""
    errors = []
    
    # Check handle ownership
    source_node_id, _ = parse_handle_id(source_handle.id)
    if source_node_id != source_node.id:
        errors.append("Source handle does not belong to source node")
    
    target_node_id, _ = parse_handle_id(target_handle.id)
    if target_node_id != target_node.id:
        errors.append("Target handle does not belong to target node")
    
    # Check handle compatibility
    if not are_handles_compatible(source_handle, target_handle):
        errors.append("Handles are not compatible for connection")
    
    # Node-specific connection rules
    if source_node.type == NodeType.start and source_node.data.get("connections", []):
        errors.append("Start node can only have one outgoing connection")
    
    if target_node.type == NodeType.start:
        errors.append("Cannot connect to start node")
    
    if source_node.type == NodeType.end:
        errors.append("Cannot connect from end node")
    
    return len(errors) == 0, errors


# ============================================================================
# Export all utilities
# ============================================================================

__all__ = [
    "NODE_TYPE_MAP",
    "NODE_TYPE_REVERSE_MAP",
    "node_kind_to_domain_type",
    "domain_type_to_node_kind",
    "create_handle_id",
    "parse_handle_id",
    "are_handles_compatible",
    "is_data_type_compatible",
    "diagram_arrays_to_maps",
    "diagram_maps_to_arrays",
    "calculate_handle_offset",
    "calculate_handle_position",
    "validate_node_data",
    "validate_arrow_connection",
]
`;

async function generateConversions() {
  try {
    // Create output directory
    const outputDir = join(__dirname, '../../python/dipeo_domain/src/dipeo_domain');
    await mkdir(outputDir, { recursive: true });
    
    // Write Python conversion utilities
    const outputPath = join(outputDir, 'conversions.py');
    await writeFile(outputPath, PYTHON_TEMPLATE);
    
    console.log('✅ Generated Python conversion utilities at:', outputPath);
  } catch (err) {
    console.error('❌ Failed to generate conversions:', err);
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  generateConversions();
}