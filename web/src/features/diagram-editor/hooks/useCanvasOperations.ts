/**
 * useCanvasOperations - Refactored version using focused hooks
 * 
 * This is a composite hook that brings together all the individual operation hooks
 * to provide the same interface as the original monolithic useCanvasOperations.
 */

import React, { useCallback, useRef } from 'react';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { useShallow } from 'zustand/react/shallow';
import { isWithinTolerance } from '@/shared/utils/math';
import { createHandlerTable } from '@/shared/utils/dispatchTable';

// Import focused operation hooks and types
import { 
  useCanvasInteractions,
  type DragState, 
  type ContextMenuState 
} from './useCanvasInteractions';
import type { NodeChange, EdgeChange, Connection, Node } from '@xyflow/react';
import { NodeID, ArrowID, PersonID, Vec2, HandleID, SelectableID, SelectableType, nodeId, personId, createHandleId, DomainNode, DomainArrow, DomainPerson, DomainHandle } from '@/core/types';
import { nodeToReact, graphQLTypeToNodeKind } from '@/features/diagram-editor/adapters/DiagramAdapter';
import { NodeKind } from '@/features/diagram-editor/types/node-kinds';
import { createCommonStoreSelector } from '@/core/store/selectorFactory';

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
}

export interface UseCanvasOperationsReturn {
  // Canvas State
  nodes: ReturnType<typeof nodeToReact>[];
  arrows: DomainArrow[];
  persons: PersonID[];
  handles: Map<HandleID, any>;
  
  // Selection State
  selectedId: string | null;
  selectedType: 'node' | 'arrow' | 'person' | null;
  selectedNodeId: NodeID | null;
  selectedArrowId: ArrowID | null;
  selectedPersonId: PersonID | null;
  hasSelection: boolean;
  isSelected: (id: string) => boolean;
  
  // Mode State
  isMonitorMode: boolean;
  isConnectable: boolean;
  
  // Node Operations
  addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => NodeID;
  updateNode: (id: NodeID, updates: Partial<DomainNode>) => void;
  deleteNode: (id: NodeID) => void;
  duplicateNode: (id: NodeID) => void;
  
  // Arrow Operations
  addArrow: (sourceHandle: HandleID, targetHandle: HandleID) => ArrowID | null;
  updateArrow: (id: ArrowID, updates: any) => void;
  deleteArrow: (id: ArrowID) => void;
  
  // Person Operations
  addPerson: (person: { label: string; service: string; model: string }) => PersonID;
  updatePerson: (id: PersonID, updates: any) => void;
  deletePerson: (id: PersonID) => void;
  getPersonById: (id: PersonID) => any;
  getArrowById: (id: ArrowID) => any;
  
  // Selection Operations
  select: (id: SelectableID, type: SelectableType) => void;
  clearSelection: () => void;
  
  // Execution State
  isNodeRunning: (id: NodeID) => boolean;
  getNodeState: (id: NodeID) => any;
  
  // Drag & Drop
  dragState: DragState;
  onNodeDragStart: (event: React.DragEvent, nodeType: string) => void;
  onNodeDragStartCanvas: (event: React.MouseEvent, node: Node) => void;
  onNodeDragStopCanvas: (event: React.MouseEvent, node: Node) => void;
  onPersonDragStart: (event: React.DragEvent, personId: string) => void;
  onDragOver: (event: React.DragEvent) => void;
  onNodeDrop: (event: React.DragEvent, projectPosition: (x: number, y: number) => Vec2) => void;
  onPersonDrop: (event: React.DragEvent, nodeId: NodeID) => void;
  onDragEnd: () => void;
  
  // Context Menu
  contextMenu: ContextMenuState;
  isContextMenuOpen: boolean;
  openContextMenu: (x: number, y: number, target: 'pane' | 'node' | 'edge', targetId?: NodeID) => void;
  closeContextMenu: () => void;
  handleDeleteSelected: () => void;
  handleDuplicateNode: (nodeId: NodeID) => void;
  
  // Keyboard Shortcuts
  registerShortcut: (key: string, handler: () => void) => void;
  unregisterShortcut: (key: string) => void;
  
  // Canvas Events
  onPaneClick: () => void;
  onPaneContextMenu: (event: React.MouseEvent) => void;
  onNodeContextMenu: (event: React.MouseEvent, nodeIdStr: string) => void;
  onEdgeContextMenu: (event: React.MouseEvent, edgeIdStr: string) => void;
  
  // React Flow Handlers
  onNodesChange: (changes: NodeChange[]) => void;
  onArrowsChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  
  // History
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  
  // Transactions
  transaction: (fn: () => void) => void;
}

// Helper hook for efficient Map to Array conversion with caching
function useCachedMapArray<K, V>(
  map: Map<K, V>,
  mapVersion?: number
): V[] {
  const cacheRef = useRef<{ array: V[]; size: number; version?: number }>({
    array: [],
    size: -1,
    version: -1
  });
  
  return React.useMemo(() => {
    if (cacheRef.current.size !== map.size || 
        (mapVersion !== undefined && cacheRef.current.version !== mapVersion)) {
      cacheRef.current = {
        array: Array.from(map.values()),
        size: map.size,
        version: mapVersion
      };
    }
    return cacheRef.current.array;
  }, [map.size, mapVersion]);
}

/**
 * Refactored useCanvasOperations that delegates to focused hooks
 * This maintains backward compatibility while improving performance
 */
export function useCanvasOperations(options: UseCanvasOperationsOptions = {}): UseCanvasOperationsReturn {
  const { shortcuts = {}, enableInteractions = true } = options;
  
  // Create a stable selector using common factory
  const storeSelector = React.useMemo(() => createCommonStoreSelector(), []);
  
  // Store state
  const storeState = useUnifiedStore(useShallow(storeSelector));
  
  // Get operations from focused hooks
  const canvasInteractions = useCanvasInteractions({ enabled: enableInteractions, shortcuts });
  
  // Convert Maps to arrays with efficient caching
  const arrows = useCachedMapArray(storeState.arrows, storeState.dataVersion) as DomainArrow[];
  const persons = useCachedMapArray(storeState.persons, storeState.dataVersion) as DomainPerson[];
  const domainNodes = useCachedMapArray(storeState.nodesMap, storeState.dataVersion) as DomainNode[];
  const domainHandles = useCachedMapArray(storeState.handlesMap, storeState.dataVersion) as DomainHandle[];
  
  // Create a pre-computed handle lookup by nodeId for O(1) access
  const handlesByNode = React.useMemo(() => {
    const lookup = new Map<NodeID, DomainHandle[]>();
    domainHandles.forEach(handle => {
      const handles = lookup.get(handle.nodeId as NodeID) || [];
      handles.push(handle);
      lookup.set(handle.nodeId as NodeID, handles);
    });
    return lookup;
  }, [domainHandles]);
  
  const nodes = React.useMemo(() => {
    return domainNodes.map(node => {
      const nodeHandles = handlesByNode.get(node.id as NodeID) || [];
      return nodeToReact(node, nodeHandles);
    });
  }, [domainNodes, handlesByNode]);
  
  // Derive selected IDs based on selectedType
  const selectedNodeId = storeState.selectedType === 'node' ? storeState.selectedId as NodeID : null;
  const selectedArrowId = storeState.selectedType === 'arrow' ? storeState.selectedId as ArrowID : null;
  const selectedPersonId = storeState.selectedType === 'person' ? storeState.selectedId as PersonID : null;
  
  // Get remaining operations from store that aren't yet extracted
  const storeOperations = useUnifiedStore(
    useShallow(state => ({
      // Transaction management
      transaction: state.transaction,
      
      // History operations
      undo: state.undo,
      redo: state.redo,
      canUndo: state.canUndo,
      canRedo: state.canRedo,
      
      // Mode state
      isMonitorMode: state.readOnly || state.executionReadOnly === true,
    }))
  );
  
  // Position update batching with requestAnimationFrame
  const positionUpdateQueueRef = useRef<Map<NodeID, { x: number; y: number }>>(new Map());
  const rafIdRef = useRef<number | undefined>(undefined);
  
  const processBatchedPositionUpdates = React.useCallback(() => {
    if (positionUpdateQueueRef.current.size === 0) return;
    
    storeState.transaction(() => {
      positionUpdateQueueRef.current.forEach((position, nodeId) => {
        storeState.updateNode(nodeId, { position });
      });
      positionUpdateQueueRef.current.clear();
    });
    
    rafIdRef.current = undefined;
  }, [storeState]);
  
  const batchPositionUpdate = React.useCallback((nodeId: NodeID, position: { x: number; y: number }) => {
    positionUpdateQueueRef.current.set(nodeId, position);
    
    if (!rafIdRef.current) {
      rafIdRef.current = requestAnimationFrame(processBatchedPositionUpdates);
    }
  }, [processBatchedPositionUpdates]);
  
  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, []);
  
  // React Flow handlers
  const nodeChangeHandlers = React.useMemo(() => 
    createHandlerTable<NodeChange['type'], [NodeChange, typeof storeState], void>({
      position: () => {
        // Position changes are handled inline to maintain proper order
      },
      dimensions: (change) => {
        if ('id' in change && 'dimensions' in change && change.dimensions) {
          // Could store dimensions here if needed in the future
        }
      },
      replace: () => {
        // Handle node replacement if needed
      },
      remove: (change, state) => {
        if ('id' in change) {
          state.deleteNode(change.id as NodeID);
        }
      },
      select: (change, state) => {
        if ('selected' in change && 'id' in change) {
          if (change.selected) {
            state.select(change.id as NodeID, 'node');
          } else if (state.selectedId === change.id) {
            state.clearSelection();
          }
        }
      },
      add: () => {
        // React Flow is initializing the node - this is expected behavior
      },
    }), []
  );

  const onNodesChange = React.useCallback((changes: NodeChange[]) => {
    if (storeOperations.isMonitorMode || storeState.isExecutionMode) return;
    
    changes.forEach((change) => {
      if (change.type === 'position' && change.position) {
        const node = storeState.nodesMap.get(change.id as NodeID);
        if (node) {
          const tolerance = change.dragging ? 5 : 0.01;
          const positionChanged = 
            !isWithinTolerance(node.position?.x || 0, change.position.x, tolerance) ||
            !isWithinTolerance(node.position?.y || 0, change.position.y, tolerance);
          
          if (positionChanged) {
            if (change.dragging) {
              return;
            } else {
              batchPositionUpdate(change.id as NodeID, change.position);
            }
          }
        }
      } else {
        nodeChangeHandlers.execute(change.type, change, storeState);
      }
    });
  }, [storeState, batchPositionUpdate, nodeChangeHandlers]);
  
  const onArrowsChange = React.useCallback((changes: EdgeChange[]) => {
    if (storeOperations.isMonitorMode || storeState.isExecutionMode) return;
    
    storeState.transaction(() => {
      changes.forEach((change) => {
        if (change.type === 'remove') {
          storeState.deleteArrow(change.id as ArrowID);
        }
      });
    });
  }, [storeState]);
  
  const onConnect = React.useCallback((connection: Connection) => {
    if (storeOperations.isMonitorMode || storeState.isExecutionMode) return;
    
    if (connection.source && connection.target && 
        connection.sourceHandle && connection.targetHandle) {
      const stripSuffix = (handleName: string): string => {
        const match = handleName.match(/^(.+)_\d+$/);
        return match && match[1] ? match[1] : handleName;
      };
      
      const sourceHandleId = createHandleId(
        nodeId(connection.source),
        stripSuffix(connection.sourceHandle)
      );
      const targetHandleId = createHandleId(
        nodeId(connection.target),
        stripSuffix(connection.targetHandle)
      );
      
      storeState.addArrow(sourceHandleId, targetHandleId);
    }
  }, [storeState]);
  
  // Helper methods
  const getPersonById = useCallback((id: PersonID) => {
    const person = storeState.persons.get(id);
    return person || null;
  }, [storeState.persons]);
  
  const getArrowById = useCallback((id: ArrowID) => {
    return storeState.arrows.get(id);
  }, [storeState.arrows]);
  
  const duplicateNode = useCallback((id: NodeID) => {
    const node = storeState.nodesMap.get(id);
    if (!node) return;
    
    const newPosition = {
      x: (node.position?.x || 0) + 50,
      y: (node.position?.y || 0) + 50
    };
    
    const newNodeId = storeState.addNode(
      graphQLTypeToNodeKind(node.type) as NodeKind,
      newPosition,
      { ...node.data }
    );
    
    storeState.select(newNodeId, 'node');
  }, [storeState]);
  
  const isNodeRunning = useCallback((id: NodeID) => {
    return storeState.runningNodes.has(id);
  }, [storeState.runningNodes]);
  
  const getNodeState = useCallback((id: NodeID) => {
    return storeState.nodeStates.get(id);
  }, [storeState.nodeStates]);
  
  const isSelected = useCallback((id: string) => {
    return storeState.selectedId === id;
  }, [storeState.selectedId]);
  
  const handleDeleteSelected = useCallback(() => {
    if (!enableInteractions || storeOperations.isMonitorMode) return;
    
    if (selectedNodeId) {
      storeState.deleteNode(selectedNodeId);
      storeState.clearSelection();
    } else if (selectedArrowId) {
      storeState.deleteArrow(selectedArrowId);
      storeState.clearSelection();
    } else if (selectedPersonId) {
      storeState.deletePerson(selectedPersonId);
      storeState.clearSelection();
    }
    canvasInteractions.closeContextMenu();
  }, [enableInteractions, selectedNodeId, selectedArrowId, selectedPersonId, storeState, storeOperations.isMonitorMode, canvasInteractions]);
  
  const handleDuplicateNode = useCallback((nodeId: NodeID) => {
    if (!enableInteractions || storeOperations.isMonitorMode) return;
    duplicateNode(nodeId);
    canvasInteractions.closeContextMenu();
  }, [enableInteractions, storeOperations.isMonitorMode, duplicateNode, canvasInteractions]);
  
  // Memoize the ID arrays
  const personIds = React.useMemo(
    () => persons.map((p: DomainPerson) => personId(p.id)),
    [persons]
  );
  
  // Return the full interface
  return {
    // Canvas State
    nodes,
    arrows,
    persons: personIds,
    handles: storeState.handlesMap,
    
    // Selection State
    selectedId: storeState.selectedId,
    selectedType: storeState.selectedType,
    selectedNodeId,
    selectedArrowId,
    selectedPersonId,
    hasSelection: storeState.selectedId !== null,
    isSelected,
    
    // Mode State
    isMonitorMode: storeOperations.isMonitorMode,
    isConnectable: !storeOperations.isMonitorMode && enableInteractions,
    
    // Node Operations
    addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => 
      storeState.addNode(type as NodeKind, position, data),
    updateNode: storeState.updateNode,
    deleteNode: storeState.deleteNode,
    duplicateNode,
    
    // Arrow Operations
    addArrow: storeState.addArrow,
    updateArrow: storeState.updateArrow,
    deleteArrow: storeState.deleteArrow,
    
    // Person Operations
    addPerson: (person: { label: string; service: string; model: string }) =>
      storeState.addPerson(person.label, person.service, person.model),
    updatePerson: storeState.updatePerson,
    deletePerson: storeState.deletePerson,
    getPersonById,
    getArrowById,
    
    // Selection Operations
    select: storeState.select,
    clearSelection: storeState.clearSelection,
    
    // Execution State
    isNodeRunning,
    getNodeState,
    
    // Drag & Drop
    dragState: canvasInteractions.dragState,
    onNodeDragStart: canvasInteractions.onNodeDragStart,
    onNodeDragStartCanvas: canvasInteractions.onNodeDragStartCanvas,
    onNodeDragStopCanvas: canvasInteractions.onNodeDragStopCanvas,
    onPersonDragStart: canvasInteractions.onPersonDragStart,
    onDragOver: canvasInteractions.onDragOver,
    onNodeDrop: canvasInteractions.onNodeDrop,
    onPersonDrop: canvasInteractions.onPersonDrop,
    onDragEnd: canvasInteractions.onDragEnd,
    
    // Context Menu
    contextMenu: canvasInteractions.contextMenu,
    isContextMenuOpen: canvasInteractions.isContextMenuOpen,
    openContextMenu: canvasInteractions.openContextMenu,
    closeContextMenu: canvasInteractions.closeContextMenu,
    handleDeleteSelected,
    handleDuplicateNode,
    
    // Keyboard Shortcuts
    registerShortcut: canvasInteractions.registerShortcut,
    unregisterShortcut: canvasInteractions.unregisterShortcut,
    
    // Canvas Events
    onPaneClick: canvasInteractions.onPaneClick,
    onPaneContextMenu: canvasInteractions.onPaneContextMenu,
    onNodeContextMenu: canvasInteractions.onNodeContextMenu,
    onEdgeContextMenu: canvasInteractions.onEdgeContextMenu,
    
    // React Flow Handlers
    onNodesChange,
    onArrowsChange,
    onConnect,
    
    // History
    undo: storeOperations.undo,
    redo: storeOperations.redo,
    canUndo: storeOperations.canUndo,
    canRedo: storeOperations.canRedo,
    
    // Transactions
    transaction: storeOperations.transaction,
  };
}