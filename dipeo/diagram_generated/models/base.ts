/**
 * Base interfaces for diagram-generated node types
 * This file provides the foundation types that auto-generated node models extend from
 * 
 * IMPORTANT: This is NOT part of the @dipeo/domain-models package
 * These are runtime-generated types created by the diagram-based code generation system
 */

import { NodeType, Vec2, NodeID } from '../../models/src/diagram';

/**
 * Base interface for all generated node types
 * Used by auto-generated node models from diagram specifications
 */
export interface BaseNode {
  id: NodeID;
  type: NodeType;
  position: Vec2;
  data: Record<string, any>;
}

/**
 * Type guard to check if an object is a BaseNode
 */
export function isBaseNode(obj: any): obj is BaseNode {
  return (
    obj &&
    typeof obj === 'object' &&
    'id' in obj &&
    'type' in obj &&
    'position' in obj &&
    'data' in obj &&
    typeof obj.position === 'object' &&
    'x' in obj.position &&
    'y' in obj.position
  );
}