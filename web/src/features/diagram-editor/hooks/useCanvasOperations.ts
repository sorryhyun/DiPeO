/**
 * @deprecated Use explicit composition of useCanvas, useCanvasInteractions, and domain operation hooks instead.
 * 
 * Example:
 * ```ts
 * const canvas = useCanvas();
 * const interactions = useCanvasInteractions();
 * const nodeOps = useNodeOperations();
 * const arrowOps = useArrowOperations();
 * const personOps = usePersonOperations();
 * ```
 * 
 * useCanvasOperations - Composite hook that combines focused hooks
 * 
 * This hook provides backward compatibility by composing useCanvas and 
 * useCanvasInteractions without duplicating their logic.
 */

import React, { useCallback } from 'react';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { useShallow } from 'zustand/react/shallow';
import { useCanvas } from './ui/useCanvas';
import { useCanvasInteractions } from './ui/useCanvasInteractions';
import { SelectableID, SelectableType, personId, DomainNode, DomainPerson } from '@/core/types';
import { Vec2, NodeType } from '@dipeo/domain-models';
import type { NodeID, ArrowID, PersonID, HandleID  } from '@dipeo/domain-models';


// Type definitions

interface KeyboardShortcutsConfig {
  onDelete?: () => void;
  onEscape?: () => void;
  onSave?: () => void;
  onExport?: () => void;
  onImport?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onRun?: () => void;
}

export interface UseCanvasOperationsOptions {
  shortcuts?: KeyboardShortcutsConfig;
  enableInteractions?: boolean;
  readOnly?: boolean;
}

export interface UseCanvasOperationsReturn extends 
  Omit<ReturnType<typeof useCanvas>, 'persons'>,
  Omit<ReturnType<typeof useCanvasInteractions>, 'handleDuplicateSelected'> {
  
  // Additional operations not in focused hooks
  persons: PersonID[];
  selectedNodeId: NodeID | null;
  selectedArrowId: ArrowID | null;
  selectedPersonId: PersonID | null;
  hasSelection: boolean;
  isSelected: (id: string) => boolean;
  
  // Store operations exposed for convenience
  addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => NodeID;
  updateNode: (id: NodeID, updates: Partial<DomainNode>) => void;
  deleteNode: (id: NodeID) => void;
  duplicateNode: (id: NodeID) => void;
  
  addArrow: (sourceHandle: HandleID, targetHandle: HandleID) => ArrowID | null;
  updateArrow: (id: ArrowID, updates: any) => void;
  deleteArrow: (id: ArrowID) => void;
  
  addPerson: (person: { label: string; service: string; model: string }) => PersonID;
  updatePerson: (id: PersonID, updates: any) => void;
  deletePerson: (id: PersonID) => void;
  getPersonById: (id: PersonID) => any;
  getArrowById: (id: ArrowID) => any;
  
  select: (id: SelectableID, type: SelectableType) => void;
  clearSelection: () => void;
  selectedId: string | null;
  selectedType: 'node' | 'arrow' | 'person' | null;
  
  isNodeRunning: (id: NodeID) => boolean;
  getNodeState: (id: NodeID) => any;
  
  handleDuplicateNode: (nodeId: NodeID) => void;
  
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  
  transaction: (fn: () => void) => void;
}

/**
 * Composite hook that truly composes focused hooks without duplication
 */
export function useCanvasOperations(options: UseCanvasOperationsOptions = {}): UseCanvasOperationsReturn {
  const { shortcuts = {}, enableInteractions = true, readOnly = false } = options;
  
  // Use the focused hooks
  const canvas = useCanvas({ readOnly });
  const interactions = useCanvasInteractions({ enabled: enableInteractions && !readOnly, shortcuts });
  
  // Get additional store operations not in focused hooks
  const storeOps = useUnifiedStore(
    useShallow(state => ({
      // Selection state
      selectedId: state.selectedId,
      selectedType: state.selectedType,
      
      // CRUD operations
      addNode: state.addNode,
      updateNode: state.updateNode,
      deleteNode: state.deleteNode,
      addArrow: state.addArrow,
      updateArrow: state.updateArrow,
      deleteArrow: state.deleteArrow,
      addPerson: state.addPerson,
      updatePerson: state.updatePerson,
      deletePerson: state.deletePerson,
      select: state.select,
      clearSelection: state.clearSelection,
      
      // History
      undo: state.undo,
      redo: state.redo,
      canUndo: state.canUndo,
      canRedo: state.canRedo,
      
      // Transactions
      transaction: state.transaction,
      
      // Execution state
      getRunningNodes: state.getRunningNodes,
      getCompletedNodes: state.getCompletedNodes,
      getFailedNodes: state.getFailedNodes,
      
      // Data access
      persons: state.persons,
      nodes: state.nodes,
      arrows: state.arrows,
    }))
  );
  
  // Derive selected IDs
  const selectedNodeId = storeOps.selectedType === 'node' ? storeOps.selectedId as NodeID : null;
  const selectedArrowId = storeOps.selectedType === 'arrow' ? storeOps.selectedId as ArrowID : null;
  const selectedPersonId = storeOps.selectedType === 'person' ? storeOps.selectedId as PersonID : null;
  
  // Additional helper methods
  const getPersonById = useCallback((id: PersonID) => {
    return storeOps.persons.get(id) || null;
  }, [storeOps.persons]);
  
  const getArrowById = useCallback((id: ArrowID) => {
    return storeOps.arrows.get(id) || null;
  }, [storeOps.arrows]);
  
  const duplicateNode = useCallback((id: NodeID) => {
    const node = storeOps.nodes.get(id);
    if (!node) return;
    
    const newPosition = {
      x: (node.position?.x || 0) + 50,
      y: (node.position?.y || 0) + 50
    };
    
    const newNodeId = storeOps.addNode(
      node.type,
      newPosition,
      { ...node.data }
    );
    
    storeOps.select(newNodeId, 'node');
  }, [storeOps]);
  
  const isNodeRunning = useCallback((id: NodeID) => {
    const runningNodes = storeOps.getRunningNodes();
    return runningNodes.some(node => node.id === id);
  }, [storeOps]);
  
  const getNodeState = useCallback((id: NodeID) => {
    // For now, return a simple state based on running/completed/failed
    const runningNodes = storeOps.getRunningNodes();
    const completedNodes = storeOps.getCompletedNodes();
    const failedNodes = storeOps.getFailedNodes();
    
    if (runningNodes.some(n => n.id === id)) return { status: 'running' };
    if (completedNodes.some(n => n.id === id)) return { status: 'completed' };
    if (failedNodes.some(n => n.id === id)) return { status: 'failed' };
    return null;
  }, [storeOps]);
  
  const isSelected = useCallback((id: string) => {
    return storeOps.selectedId === id;
  }, [storeOps.selectedId]);
  
  const handleDuplicateNode = useCallback((nodeId: NodeID) => {
    if (!enableInteractions || canvas.isMonitorMode) return;
    duplicateNode(nodeId);
    interactions.closeContextMenu();
  }, [enableInteractions, canvas.isMonitorMode, duplicateNode, interactions]);
  
  // Convert person Map to ID array
  const personIds = React.useMemo(
    () => canvas.personsArray.map((p: DomainPerson) => personId(p.id)),
    [canvas.personsArray]
  );
  
  // Spread all properties from focused hooks and add additional ones
  return {
    // From useCanvas
    ...canvas,
    
    // From useCanvasInteractions (except handleDuplicateSelected which we override)
    ...interactions,
    
    // Additional selection state
    selectedId: storeOps.selectedId,
    selectedType: storeOps.selectedType,
    selectedNodeId,
    selectedArrowId,
    selectedPersonId,
    hasSelection: storeOps.selectedId !== null,
    isSelected,
    
    // Person IDs array
    persons: personIds,
    
    // Store operations
    addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => 
      storeOps.addNode(type as NodeType, position, data),
    updateNode: storeOps.updateNode,
    deleteNode: storeOps.deleteNode,
    duplicateNode,
    
    addArrow: storeOps.addArrow,
    updateArrow: storeOps.updateArrow,
    deleteArrow: storeOps.deleteArrow,
    
    addPerson: (person: { label: string; service: string; model: string }) =>
      storeOps.addPerson(person.label, person.service, person.model),
    updatePerson: storeOps.updatePerson,
    deletePerson: storeOps.deletePerson,
    getPersonById,
    getArrowById,
    
    select: storeOps.select,
    clearSelection: storeOps.clearSelection,
    
    // Execution state helpers
    isNodeRunning,
    getNodeState,
    
    // Override the duplicate handler to work with nodes
    handleDuplicateNode,
    
    // History
    undo: storeOps.undo,
    redo: storeOps.redo,
    canUndo: storeOps.canUndo,
    canRedo: storeOps.canRedo,
    
    // Transactions
    transaction: storeOps.transaction,
  };
}