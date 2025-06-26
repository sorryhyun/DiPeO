/**
 * Arrow migration utilities
 * 
 * This module provides utilities to migrate arrow data,
 * particularly for setting branch data on condition node arrows.
 */

import { DomainArrow, DomainNode, parseHandleId, handleId } from '@/core/types';
import { NodeType } from '@dipeo/domain-models';

/**
 * Migrates arrows to ensure condition node arrows have proper branch data
 * @param arrows - Array of arrows to migrate
 * @param nodes - Map of nodes for reference
 * @returns Updated arrows array
 */
export function migrateArrowBranchData(
  arrows: DomainArrow[],
  nodes: Map<string, DomainNode>
): DomainArrow[] {
  return arrows.map(arrow => {
    // Skip if arrow already has branch data
    if (arrow.data?.branch) {
      return arrow;
    }
    
    // Parse the source handle to get node ID and handle name
    const { nodeId, handleName } = parseHandleId(handleId(arrow.source));
    
    // Check if source node is a condition node
    const sourceNode = nodes.get(nodeId);
    if (!sourceNode || sourceNode.type !== NodeType.CONDITION) {
      return arrow;
    }
    
    // Check if handle name is True/False (case-insensitive)
    const handleNameLower = handleName.toLowerCase();
    if (handleNameLower === 'true' || handleNameLower === 'false') {
      // Create updated arrow with branch data
      return {
        ...arrow,
        data: {
          ...(arrow.data || {}),
          branch: handleNameLower
        }
      };
    }
    
    return arrow;
  });
}

/**
 * Checks if an arrow needs branch data migration
 * @param arrow - Arrow to check
 * @param nodes - Map of nodes for reference
 * @returns True if migration is needed
 */
export function needsBranchDataMigration(
  arrow: DomainArrow,
  nodes: Map<string, DomainNode>
): boolean {
  // Already has branch data
  if (arrow.data?.branch) {
    return false;
  }
  
  // Check if from condition node with True/False handle
  const { nodeId, handleName } = parseHandleId(handleId(arrow.source));
  const sourceNode = nodes.get(nodeId);
  
  if (!sourceNode || sourceNode.type !== NodeType.CONDITION) {
    return false;
  }
  
  const handleNameLower = handleName.toLowerCase();
  return handleNameLower === 'true' || handleNameLower === 'false';
}