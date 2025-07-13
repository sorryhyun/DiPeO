// State hooks for computed and derived state

import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '../unifiedStore';
import { NodeID, NodeType } from '@/core/types';

// === UI State ===

/**
 * Get computed UI state
 */
export const useUIState = () => useUnifiedStore(
  useShallow(state => ({
    selectedId: state.selectedId,
    selectedType: state.selectedType,
    activeCanvas: state.activeCanvas,
    hasSelection: state.selectedId !== null,
    hasHighlight: state.highlightedPersonId !== null,
    readOnly: state.readOnly,
    isExecuting: state.execution.isRunning,
    canEdit: !state.readOnly && !state.execution.isRunning,
    canExecute: !state.execution.isRunning && state.nodesArray.length > 0,
  }))
);

// === Selection State ===

/**
 * Check if a specific entity is selected
 */
export const useIsSelected = (entityId: string | null, entityType: 'node' | 'arrow' | 'person') =>
  useUnifiedStore(state => 
    state.selectedId === entityId && state.selectedType === entityType
  );

/**
 * Check if a node is executing
 */
export const useIsNodeExecuting = (nodeId: string | null) =>
  useUnifiedStore(state => nodeId ? state.execution.runningNodes.has(nodeId as NodeID) : false);

// === Execution State ===

/**
 * Get execution progress state
 */
export const useExecutionProgress = () => useUnifiedStore(state => {
  const totalNodes = state.nodesArray.length;
  const completedNodes = Array.from(state.execution.nodeStates.values())
    .filter(node => node.status === 'COMPLETED').length;
  
  return {
    isRunning: state.execution.isRunning,
    progress: totalNodes > 0 ? (completedNodes / totalNodes) * 100 : 0,
    completedNodes,
    totalNodes,
  };
});

/**
 * Check if execution is paused
 */
export const useIsExecutionPaused = () =>
  useUnifiedStore(state => state.execution.isPaused);

// === Diagram State ===

/**
 * Get diagram statistics
 */
export const useDiagramStats = () => useUnifiedStore(state => ({
  nodeCount: state.nodes.size,
  arrowCount: state.arrows.size,
  personCount: state.persons.size,
  handleCount: state.handles.size,
  isEmpty: state.nodes.size === 0,
}));

/**
 * Check if diagram has unsaved changes
 */
export const useHasUnsavedChanges = () => useUnifiedStore(_state => {
  // This could be enhanced to track actual changes
  // For now, return false as we don't track changes yet
  return false;
});

// === Person State ===

/**
 * Get persons grouped by service
 */
export const usePersonsByService = () => useUnifiedStore(state => {
  const grouped = new Map<string, typeof state.personsArray>();
  
  state.personsArray.forEach(person => {
    const service = person.llm_config?.service || 'unknown';
    if (!grouped.has(service)) {
      grouped.set(service, []);
    }
    grouped.get(service)!.push(person);
  });
  
  return grouped;
});

/**
 * Check if a specific API key is in use
 */
export const useIsApiKeyInUse = (apiKeyId: string | null) =>
  useUnifiedStore(state => 
    apiKeyId ? state.personsArray.some(p => p.llm_config?.api_key_id === apiKeyId) : false
  );

// === Validation State ===

/**
 * Get diagram validation state
 */
export const useDiagramValidation = () => useUnifiedStore(state => {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  // Check for disconnected nodes
  const connectedNodes = new Set<string>();
  state.arrowsArray.forEach(arrow => {
    connectedNodes.add(arrow.source);
    connectedNodes.add(arrow.target);
  });
  
  const disconnectedNodes = state.nodesArray.filter(
    node => !connectedNodes.has(node.id)
  );
  
  if (disconnectedNodes.length > 0) {
    warnings.push(`${disconnectedNodes.length} disconnected node(s)`);
  }
  
  // Check for nodes without persons
  const nodesWithoutPersons = state.nodesArray.filter(
    node => node.type === NodeType.PERSON_JOB && !node.data.person
  );
  
  if (nodesWithoutPersons.length > 0) {
    errors.push(`${nodesWithoutPersons.length} person node(s) without assigned persons`);
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
});