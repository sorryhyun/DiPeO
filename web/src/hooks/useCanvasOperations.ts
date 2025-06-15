/**
 * useCanvasOperations - Consolidated canvas hook combining all canvas-related functionality
 * 
 * This hook merges functionality from useCanvas and useCanvasInteractions to provide
 * a single interface for all canvas operations, interactions, and state management.
 */

import React, { useState, useCallback, useRef, useEffect, type DragEvent } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { type NodeChange, type EdgeChange, type Connection, type Node } from '@xyflow/react';
import { isWithinTolerance } from '@/utils/math';
import { createHandlerTable } from '@/utils/dispatchTable';
import { createNodeDragGhost } from '@/utils/dragGhost';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import { 
  nodeToReact,
  graphQLTypeToNodeKind,
  type NodeID, 
  type ArrowID, 
  type HandleID, 
  type PersonID,
  type NodeKind, 
  nodeId, 
  personId, 
  handleId,
  createHandleId,
  type Vec2,
  type DomainNode,
  type DomainArrow,
  type DomainPerson,
  type DomainHandle
} from '@/types';
import type { SelectableID, SelectableType } from '@/stores/slices/uiSlice';

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
    // Only recompute if size or version changed
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

// Types

interface ContextMenuState {
  position: { x: number; y: number } | null;
  target: 'pane' | 'node' | 'edge';
  targetId?: NodeID;
}

interface DragState {
  isDragging: boolean;
  dragType: 'node' | 'person' | null;
  dragData?: string;
  draggedNodeId?: string; // For tracking existing node being dragged
}

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
  onNodeDragStart: (event: DragEvent, nodeType: string) => void;
  onNodeDragStartCanvas: (event: React.MouseEvent, node: Node) => void;
  onNodeDragStopCanvas: (event: React.MouseEvent, node: Node) => void;
  onPersonDragStart: (event: DragEvent, personId: string) => void;
  onDragOver: (event: DragEvent) => void;
  onNodeDrop: (event: DragEvent, projectPosition: (x: number, y: number) => Vec2) => void;
  onPersonDrop: (event: DragEvent, nodeId: NodeID) => void;
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

// Main Hook

// Import the common selector factory
import { createCommonStoreSelector } from '@/stores/selectorFactory';

export function useCanvasOperations(options: UseCanvasOperationsOptions = {}): UseCanvasOperationsReturn {
  const { shortcuts = {}, enableInteractions = true } = options;
  
  // Create a stable selector using common factory
  const storeSelector = React.useMemo(() => createCommonStoreSelector(), []);
  
  // Store state
  const storeState = useUnifiedStore(useShallow(storeSelector));
  
  // Convert Maps to arrays with efficient caching
  const arrows = useCachedMapArray(storeState.arrows, storeState.dataVersion) as DomainArrow[];
  const persons = useCachedMapArray(storeState.persons, storeState.dataVersion) as DomainPerson[];
  
  // Wrapped operations
  const wrappedOperations = React.useMemo(() => ({
    addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => 
      storeState.addNode(type as NodeKind, position, data),
    
    addPerson: (person: { label: string; service: string; model: string }) =>
      storeState.addPerson(person.label, person.service, person.model),
    
    getPersonById: (id: PersonID) => storeState.persons.get(id),
    getArrowById: (id: ArrowID) => storeState.arrows.get(id),
    
    // Derived state helpers
    isNodeRunning: (id: NodeID) => storeState.runningNodes.has(id),
    getNodeState: (id: NodeID) => storeState.nodeStates.get(id),
    isSelected: (id: string) => storeState.selectedId === id,
  }), [storeState]);
  
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
  // Create node change handler table
  const nodeChangeHandlers = React.useMemo(() => 
    createHandlerTable<NodeChange['type'], [NodeChange, typeof storeState], void>({
      position: () => {
        // Position changes are handled inline to maintain proper order
      },
      dimensions: (change) => {
        // Dimensions are handled by React Flow internally
        // We can optionally store them if needed for layout calculations
        if ('id' in change && 'dimensions' in change && change.dimensions) {
          // Could store dimensions here if needed in the future
        }
      },
      replace: () => {
        // Handle node replacement if needed
        // This is typically used when React Flow updates internal state
      },
      remove: (change, state) => {
        if ('id' in change) {
          state.deleteNode(change.id as NodeID);
        }
      },
      select: (change, state) => {
        // Handle selection changes
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
        // Our nodes already exist in the store, so no action needed
        // This prevents the "node not initialized" warning
      },
    }), []
  );

  const onNodesChange = React.useCallback((changes: NodeChange[]) => {
    if (storeState.isMonitorMode || storeState.isExecutionMode) return;
    
    // Process all changes synchronously to maintain React Flow's expectations
    changes.forEach((change) => {
      if (change.type === 'position' && change.position) {
        const node = storeState.nodesMap.get(change.id as NodeID);
        if (node) {
          // Use smaller tolerance for more responsive dragging
          const tolerance = change.dragging ? 5 : 0.01;
          const positionChanged = 
            !isWithinTolerance(node.position?.x || 0, change.position.x, tolerance) ||
            !isWithinTolerance(node.position?.y || 0, change.position.y, tolerance);
          
          if (positionChanged) {
            if (change.dragging) {
              // Don't update store during dragging - let React Flow handle it
              // This prevents the "node not initialized" warning
              return;
            } else {
              // Batch updates when drag ends for history recording
              batchPositionUpdate(change.id as NodeID, change.position);
            }
          }
        }
      } else {
        // Handle other changes through the handler table
        nodeChangeHandlers.execute(change.type, change, storeState);
      }
    });
  }, [storeState, batchPositionUpdate, nodeChangeHandlers]);
  
  const onArrowsChange = React.useCallback((changes: EdgeChange[]) => {
    if (storeState.isMonitorMode || storeState.isExecutionMode) return;
    
    storeState.transaction(() => {
      changes.forEach((change) => {
        if (change.type === 'remove') {
          storeState.deleteArrow(change.id as ArrowID);
        }
      });
    });
  }, [storeState]);
  
  const onConnect = React.useCallback((connection: Connection) => {
    if (storeState.isMonitorMode || storeState.isExecutionMode) return;
    
    if (connection.source && connection.target && 
        connection.sourceHandle && connection.targetHandle) {
      // Strip any numeric suffixes that React Flow might have added (e.g., _1, _2)
      const stripSuffix = (handleName: string): string => {
        const match = handleName.match(/^(.+)_\d+$/);
        return match && match[1] ? match[1] : handleName;
      };
      
      // Create proper handle IDs from node IDs and handle names (without suffixes)
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
  
  // Convert domain nodes to React Flow format with handles
  // Use cached arrays for better performance
  const domainNodes = useCachedMapArray(storeState.nodesMap, storeState.dataVersion) as DomainNode[];
  const domainHandles = useCachedMapArray(storeState.handlesMap, storeState.dataVersion) as DomainHandle[];
  
  // Create a pre-computed handle lookup by nodeId for O(1) access
  const handlesByNode = React.useMemo(() => {
    const lookup = new Map<NodeID, DomainHandle[]>();
    domainHandles.forEach(handle => {
      const handles = lookup.get(nodeId(handle.nodeId)) || [];
      handles.push(handle);
      lookup.set(nodeId(handle.nodeId), handles);
    });
    return lookup;
  }, [domainHandles]);
  
  const nodes = React.useMemo(() => {
    return domainNodes.map(node => {
      // O(1) lookup instead of O(n) filter
      const nodeHandles = handlesByNode.get(node.id as NodeID) || [];
      return nodeToReact(node, nodeHandles);
    });
  }, [domainNodes, handlesByNode]);
  
  // Derive selected IDs based on selectedType
  const selectedNodeId = storeState.selectedType === 'node' ? storeState.selectedId as NodeID : null;
  const selectedArrowId = storeState.selectedType === 'arrow' ? storeState.selectedId as ArrowID : null;
  const selectedPersonId = storeState.selectedType === 'person' ? storeState.selectedId as PersonID : null;
  
  // Local state for interactions
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    position: null,
    target: 'pane',
  });
  
  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    dragType: null,
  });
  
  // Refs for drag handling
  const dragOffset = useRef({ x: 0, y: 0 });
  const shortcutHandlers = useRef<Map<string, () => void>>(new Map());
  
  // =====================
  // CONTEXT MENU
  // =====================
  
  const openContextMenu = useCallback((
    x: number, 
    y: number, 
    target: 'pane' | 'node' | 'edge',
    targetId?: NodeID
  ) => {
    if (!enableInteractions || storeState.isMonitorMode) return;
    
    setContextMenu({ 
      position: { x, y }, 
      target,
      targetId 
    });
  }, [enableInteractions, storeState.isMonitorMode]);
  
  const closeContextMenu = useCallback(() => {
    setContextMenu({ position: null, target: 'pane' });
  }, []);
  
  // Context menu actions
  const handleDeleteSelected = useCallback(() => {
    if (!enableInteractions || storeState.isMonitorMode) return;
    
    if (selectedNodeId) {
      storeState.deleteNode(selectedNodeId);
      storeState.clearSelection();
    } else if (selectedArrowId) {
      storeState.deleteArrow(selectedArrowId);
      storeState.clearSelection();
    }
    closeContextMenu();
  }, [enableInteractions, selectedNodeId, selectedArrowId, storeState, closeContextMenu]);
  
  const handleDuplicateNode = useCallback((nodeId: NodeID) => {
    if (!enableInteractions || storeState.isMonitorMode) return;
    
    const node = storeState.nodesMap.get(nodeId);
    if (!node) return;
    
    // Create a duplicate with offset position
    const newPosition = {
      x: (node.position?.x || 0) + 50,
      y: (node.position?.y || 0) + 50
    };
    
    const newNodeId = storeState.addNode(
      graphQLTypeToNodeKind(node.type) as NodeKind,
      newPosition,
      { ...node.data }
    );
    
    // Select the new node
    storeState.select(newNodeId, 'node');
    closeContextMenu();
  }, [enableInteractions, storeState, closeContextMenu]);
  
  // =====================
  // DRAG AND DROP
  // =====================
  
  // Handle drag start for node types from sidebar
  // Handle dragging existing nodes on canvas
  const onNodeDragStartCanvas = useCallback(
    (event: React.MouseEvent, node: Node) => {
      // React Flow doesn't provide drag events for nodes, only mouse events
      // So we can't use native drag ghost for existing nodes on canvas
      // We'll keep the current behavior of not showing a preview for canvas nodes
      setDragState({
        isDragging: false,
        dragType: null,
        draggedNodeId: node.id,
      });
    },
    []
  );

  const onNodeDragStopCanvas = useCallback(
    (_event: React.MouseEvent, _node: Node) => {
      setDragState({
        isDragging: false,
        dragType: null,
        draggedNodeId: undefined,
      });
    },
    []
  );

  const onNodeDragStart = useCallback((event: DragEvent, nodeType: string) => {
    if (!enableInteractions || storeState.isMonitorMode) return;
    
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
    
    // Create and set the drag ghost image
    const ghost = createNodeDragGhost(nodeType as NodeKind);
    // Center the ghost image on the cursor
    const ghostWidth = 200; // Approximate width of the ghost element
    const ghostHeight = 80; // Approximate height of the ghost element
    event.dataTransfer.setDragImage(ghost, ghostWidth / 2, ghostHeight / 2);
    
    // Calculate offset from element center
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    dragOffset.current = {
      x: event.clientX - (rect.left + rect.width / 2),
      y: event.clientY - (rect.top + rect.height / 2)
    };
    
    // No need to set drag state for preview since we're using native ghost
    setDragState({
      isDragging: false,
      dragType: null,
      dragData: nodeType
    });
  }, [enableInteractions, storeState.isMonitorMode]);
  
  // Handle drag start for persons from sidebar
  const onPersonDragStart = useCallback((event: DragEvent, personId: string) => {
    if (!enableInteractions || storeState.isMonitorMode) return;
    
    event.dataTransfer.setData('application/person', personId);
    event.dataTransfer.effectAllowed = 'move';
    
    setDragState({
      isDragging: true,
      dragType: 'person',
      dragData: personId
    });
  }, [enableInteractions, storeState.isMonitorMode]);
  
  // Handle drag over for canvas drop zone
  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);
  
  // Handle drop for adding nodes to canvas
  const onNodeDrop = useCallback((
    event: DragEvent, 
    projectPosition: (x: number, y: number) => Vec2
  ) => {
    if (!enableInteractions || storeState.isMonitorMode) return;
    
    event.preventDefault();
    const type = event.dataTransfer.getData('application/reactflow');
    if (!type) return;
    
    // Get the drop position adjusted by the drag offset
    const dropPosition = projectPosition(
      event.clientX - dragOffset.current.x, 
      event.clientY - dragOffset.current.y
    );
    
    // Add the node at the drop position
    storeState.addNode(type as NodeKind, dropPosition);
    
    setDragState({
      isDragging: false,
      dragType: null,
    });
  }, [enableInteractions, storeState]);
  
  // Handle person drop on nodes (for PersonJob nodes)
  const onPersonDrop = useCallback((
    event: DragEvent,
    nodeId: NodeID
  ) => {
    if (!enableInteractions || storeState.isMonitorMode) return;
    
    event.preventDefault();
    const personIdStr = event.dataTransfer.getData('application/person');
    if (personIdStr) {
      // Update the data property with the person ID
      storeState.updateNode(nodeId, { data: { person: personId(personIdStr) } });
    }
    
    setDragState({
      isDragging: false,
      dragType: null,
    });
  }, [enableInteractions, storeState]);
  
  // Handle drag end
  const onDragEnd = useCallback(() => {
    setDragState({
      isDragging: false,
      dragType: null,
    });
  }, []);
  
  // =====================
  // KEYBOARD SHORTCUTS
  // =====================
  
  // Register a keyboard shortcut
  const registerShortcut = useCallback((key: string, handler: () => void) => {
    shortcutHandlers.current.set(key, handler);
  }, []);
  
  // Unregister a keyboard shortcut
  const unregisterShortcut = useCallback((key: string) => {
    shortcutHandlers.current.delete(key);
  }, []);
  
  // Default keyboard shortcuts
  useEffect(() => {
    if (!enableInteractions) return;
    
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if typing in input fields
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }
      
      // Delete key
      if (e.key === 'Delete') {
        e.preventDefault();
        if (shortcuts.onDelete) {
          shortcuts.onDelete();
        } else {
          handleDeleteSelected();
        }
      }
      
      // Escape key
      if (e.key === 'Escape') {
        e.preventDefault();
        storeState.clearSelection();
        closeContextMenu();
        if (shortcuts.onEscape) {
          shortcuts.onEscape();
        }
      }
      
      // Ctrl+S or Cmd+S for save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (shortcuts.onSave) {
          shortcuts.onSave();
        }
      }
      
      // Ctrl+E or Cmd+E for export
      if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        if (shortcuts.onExport) {
          shortcuts.onExport();
        }
      }
      
      // Ctrl+I or Cmd+I for import
      if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
        e.preventDefault();
        if (shortcuts.onImport) {
          shortcuts.onImport();
        }
      }
      
      // Ctrl+Z or Cmd+Z for undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (shortcuts.onUndo) {
          shortcuts.onUndo();
        } else if (storeState.canUndo) {
          storeState.undo();
        }
      }
      
      // Ctrl+Shift+Z or Cmd+Shift+Z for redo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
        e.preventDefault();
        if (shortcuts.onRedo) {
          shortcuts.onRedo();
        } else if (storeState.canRedo) {
          storeState.redo();
        }
      }
      
      // Ctrl+Y or Cmd+Y for redo (alternative)
      if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        e.preventDefault();
        if (shortcuts.onRedo) {
          shortcuts.onRedo();
        } else if (storeState.canRedo) {
          storeState.redo();
        }
      }
      
      // Ctrl+Enter or Cmd+Enter for run
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (shortcuts.onRun) {
          shortcuts.onRun();
        }
      }
      
      // Check custom shortcuts
      const customHandler = shortcutHandlers.current.get(e.key);
      if (customHandler) {
        e.preventDefault();
        customHandler();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    enableInteractions,
    shortcuts, 
    handleDeleteSelected, 
    storeState,
    closeContextMenu
  ]);
  
  // =====================
  // CANVAS EVENTS
  // =====================
  
  // Handle canvas pane click
  const onPaneClick = useCallback(() => {
    storeState.clearSelection();
    closeContextMenu();
  }, [storeState, closeContextMenu]);
  
  // Handle canvas pane context menu
  const onPaneContextMenu = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    openContextMenu(event.clientX, event.clientY, 'pane');
  }, [openContextMenu]);
  
  // Handle node context menu
  const onNodeContextMenu = useCallback((event: React.MouseEvent, nodeIdStr: string) => {
    event.preventDefault();
    event.stopPropagation();
    openContextMenu(event.clientX, event.clientY, 'node', nodeId(nodeIdStr));
  }, [openContextMenu]);
  
  // Handle edge context menu
  const onEdgeContextMenu = useCallback((event: React.MouseEvent, edgeIdStr: string) => {
    event.preventDefault();
    event.stopPropagation();
    openContextMenu(event.clientX, event.clientY, 'edge', nodeId(edgeIdStr));
  }, [openContextMenu]);
  
  // =====================
  // RETURN INTERFACE
  // =====================
  
  // Memoize the ID arrays to avoid recreating on every render
  // This is already optimized since persons is cached
  const personIds = React.useMemo(
    () => persons.map((p: DomainPerson) => personId(p.id)),
    [persons]
  );
  
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
    isSelected: wrappedOperations.isSelected,
    
    // Mode State
    isMonitorMode: storeState.isMonitorMode,
    isConnectable: !storeState.isMonitorMode && enableInteractions,
    
    // Node Operations
    addNode: wrappedOperations.addNode,
    updateNode: storeState.updateNode,
    deleteNode: storeState.deleteNode,
    duplicateNode: handleDuplicateNode,
    
    // Arrow Operations
    addArrow: storeState.addArrow,
    updateArrow: storeState.updateArrow,
    deleteArrow: storeState.deleteArrow,
    
    // Person Operations
    addPerson: wrappedOperations.addPerson,
    updatePerson: storeState.updatePerson,
    deletePerson: storeState.deletePerson,
    getPersonById: wrappedOperations.getPersonById,
    getArrowById: wrappedOperations.getArrowById,
    
    // Selection Operations
    select: storeState.select,
    clearSelection: storeState.clearSelection,
    
    // Execution State
    isNodeRunning: wrappedOperations.isNodeRunning,
    getNodeState: wrappedOperations.getNodeState,
    
    // Drag & Drop
    dragState,
    onNodeDragStart,
    onNodeDragStartCanvas,
    onNodeDragStopCanvas,
    onPersonDragStart,
    onDragOver,
    onNodeDrop,
    onPersonDrop,
    onDragEnd,
    
    // Context Menu
    contextMenu,
    isContextMenuOpen: contextMenu.position !== null,
    openContextMenu,
    closeContextMenu,
    handleDeleteSelected,
    handleDuplicateNode,
    
    // Keyboard Shortcuts
    registerShortcut,
    unregisterShortcut,
    
    // Canvas Events
    onPaneClick,
    onPaneContextMenu,
    onNodeContextMenu,
    onEdgeContextMenu,
    
    // React Flow Handlers
    onNodesChange,
    onArrowsChange,
    onConnect,
    
    // History
    undo: storeState.undo,
    redo: storeState.redo,
    canUndo: storeState.canUndo,
    canRedo: storeState.canRedo,
    
    // Transactions
    transaction: storeState.transaction,
  };
}