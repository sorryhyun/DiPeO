/**
 * Arrow migration utilities
 * 
 * This module provides utilities to migrate arrow data,
 * particularly for setting branch data on condition node arrows.
 */

import { DomainArrow, DomainNode, handleId } from '@/core/types';
import { NodeType, parseHandleId } from '@dipeo/domain-models';

/**
 * Migrates arrows to ensure condition node arrows have proper branch data
 * and cleans up extraneous properties from arrow data
 * @param arrows - Array of arrows to migrate
 * @param nodes - Map of nodes for reference
 * @returns Updated arrows array
 */
export function migrateArrowBranchData(
  arrows: DomainArrow[],
  nodes: Map<string, DomainNode>
): DomainArrow[] {
  return arrows.map(arrow => {
    // First clean the arrow data to remove extraneous properties
    let migratedArrow = cleanArrowData(arrow);
    
    // Skip if arrow already has branch data
    if (migratedArrow.data?.branch) {
      return migratedArrow;
    }
    
    // Parse the source handle to get node ID and handle name
    const { nodeId, handleLabel } = parseHandleId(handleId(migratedArrow.source));
    
    // Check if source node is a condition node
    const sourceNode = nodes.get(nodeId);
    if (!sourceNode || sourceNode.type !== NodeType.CONDITION) {
      return migratedArrow;
    }
    
    // Check if handle name is True/False (case-insensitive)
    const handleNameLower = handleLabel.toLowerCase();
    if (handleNameLower === 'true' || handleNameLower === 'false') {
      // Create updated arrow with branch data
      return {
        ...migratedArrow,
        data: {
          ...(migratedArrow.data || {}),
          branch: handleNameLower
        }
      };
    }
    
    return migratedArrow;
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
  const { nodeId, handleLabel } = parseHandleId(handleId(arrow.source));
  const sourceNode = nodes.get(nodeId);
  
  if (!sourceNode || sourceNode.type !== NodeType.CONDITION) {
    return false;
  }
  
  const handleNameLower = handleLabel.toLowerCase();
  return handleNameLower === 'true' || handleNameLower === 'false';
}

/**
 * Cleans up arrow data by removing extraneous properties that shouldn't be stored
 * @param arrow - Arrow to clean up
 * @returns Cleaned arrow
 */
export function cleanArrowData(arrow: DomainArrow): DomainArrow {
  if (!arrow.data) {
    return arrow;
  }

  // Properties that should be removed from arrow data
  const propsToRemove = ['id', 'type', '_sourceNodeType', '_isFromConditionBranch'];
  
  // Create a copy of the data without the unwanted properties
  const cleanedData = Object.entries(arrow.data).reduce((acc, [key, value]) => {
    if (!propsToRemove.includes(key)) {
      acc[key] = value;
    }
    return acc;
  }, {} as Record<string, any>);

  // If data is empty after cleaning, set it to null
  const hasData = Object.keys(cleanedData).length > 0;
  
  return {
    ...arrow,
    data: hasData ? cleanedData : null
  };
}