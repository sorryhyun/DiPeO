/**
 * Facade module that provides a clean API for using the typed connection system
 * This module wraps the typed-connection utilities to work seamlessly with the existing store
 */

import { useDiagramStore } from '@/stores/diagramStore';
import { Arrow } from '@/types';
import { HandleID } from '@/types/branded';
import { 
  validateConnection as validateTypedConnection,
  findValidTargets as findTypedTargets,
  findValidSources as findTypedSources,
  validateConnections as validateTypedConnections
} from './typed-connection';
import { convertNodeMap, legacyNodeToDiagramNode } from './diagram-bridge';

/**
 * Validate a connection using the typed system with the current store state
 */
export function useTypedConnectionValidation() {
  const nodes = useDiagramStore(state => state.nodes);
  const arrows = useDiagramStore(state => state.arrowList());

  /**
   * Validate a single connection
   */
  const validateConnection = (arrow: Arrow): { valid: boolean; error?: string } => {
    const diagramNodes = convertNodeMap(nodes);
    return validateTypedConnection(arrow, diagramNodes);
  };

  /**
   * Validate multiple connections
   */
  const validateConnections = (arrowsToValidate: Arrow[]) => {
    const diagramNodes = convertNodeMap(nodes);
    return validateTypedConnections(arrowsToValidate, diagramNodes);
  };

  /**
   * Find valid targets for a source handle
   */
  const findValidTargets = (sourceNodeId: string, sourceHandleName: string) => {
    const diagramNodes = convertNodeMap(nodes);
    return findTypedTargets(sourceNodeId, sourceHandleName, diagramNodes);
  };

  /**
   * Find valid sources for a target handle
   */
  const findValidSources = (targetNodeId: string, targetHandleName: string) => {
    const diagramNodes = convertNodeMap(nodes);
    return findTypedSources(targetNodeId, targetHandleName, diagramNodes);
  };

  /**
   * Check if a specific connection is valid
   */
  const canConnect = (sourceHandleId: HandleID, targetHandleId: HandleID): boolean => {
    const arrow: Arrow = {
      id: 'temp' as any,
      source: sourceHandleId,
      target: targetHandleId
    };
    const result = validateConnection(arrow);
    return result.valid;
  };

  /**
   * Get all valid connections from the current arrows
   */
  const getValidConnections = () => {
    const diagramNodes = convertNodeMap(nodes);
    const result = validateTypedConnections(arrows, diagramNodes);
    return result.valid;
  };

  /**
   * Get all invalid connections with errors
   */
  const getInvalidConnections = () => {
    const diagramNodes = convertNodeMap(nodes);
    const result = validateTypedConnections(arrows, diagramNodes);
    return result.invalid;
  };

  return {
    validateConnection,
    validateConnections,
    findValidTargets,
    findValidSources,
    canConnect,
    getValidConnections,
    getInvalidConnections
  };
}

/**
 * Hook to get typed node information
 */
export function useTypedNode(nodeId: string) {
  const node = useDiagramStore(state => state.nodes.get(nodeId));
  
  if (!node) return null;
  
  return legacyNodeToDiagramNode(node);
}

/**
 * Hook to get all nodes as DiagramNodes
 */
export function useTypedNodes() {
  const nodes = useDiagramStore(state => state.nodes);
  return convertNodeMap(nodes);
}