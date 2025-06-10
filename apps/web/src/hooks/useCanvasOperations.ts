/**
 * useCanvasOperations - Consolidated canvas hook combining all canvas-related functionality
 * 
 * This hook merges functionality from useCanvas and useCanvasInteractions to provide
 * a single interface for all canvas operations, interactions, and state management.
 */

import React, { useState, useCallback, useRef, useEffect, type DragEvent } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { type NodeChange, type EdgeChange, type Connection } from '@xyflow/react';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import { 
  nodeToReact,
  type NodeID, 
  type ArrowID, 
  type HandleID, 
  type PersonID, 
  nodeId, 
  personId, 
  handleId,
  type NodeKind,
  type Vec2,
  type LLMService, 
  type DomainNode,
  type DomainArrow,
  type DomainPerson
} from '@/types';

// =====================
// TYPES
// =====================

interface ContextMenuState {
  position: { x: number; y: number } | null;
  target: 'pane' | 'node' | 'edge';
  targetId?: NodeID;
}

interface DragState {
  isDragging: boolean;
  dragType: 'node' | 'person' | null;
  dragData?: string;
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
  // === Canvas State ===
  nodes: ReturnType<typeof nodeToReact>[];
  arrows: ArrowID[];
  persons: PersonID[];
  handles: Map<HandleID, any>;
  
  // === Selection State ===
  selectedId: string | null;
  selectedType: 'node' | 'arrow' | 'person' | null;
  selectedNodeId: NodeID | null;
  selectedArrowId: ArrowID | null;
  selectedPersonId: PersonID | null;
  hasSelection: boolean;
  isSelected: (id: string) => boolean;
  
  // === Mode State ===
  isMonitorMode: boolean;
  isConnectable: boolean;
  
  // === Node Operations ===
  addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => NodeID;
  updateNode: (id: NodeID, updates: Partial<DomainNode>) => void;
  deleteNode: (id: NodeID) => void;
  duplicateNode: (id: NodeID) => void;
  
  // === Arrow Operations ===
  addArrow: (sourceHandle: HandleID, targetHandle: HandleID) => ArrowID | null;
  updateArrow: (id: ArrowID, updates: any) => void;
  deleteArrow: (id: ArrowID) => void;
  
  // === Person Operations ===
  addPerson: (person: { label: string; service: string; model: string }) => PersonID;
  updatePerson: (id: PersonID, updates: any) => void;
  deletePerson: (id: PersonID) => void;
  getPersonById: (id: PersonID) => any;
  
  // === Selection Operations ===
  select: (id: string, type: 'node' | 'arrow' | 'person') => void;
  clearSelection: () => void;
  
  // === Execution State ===
  isNodeRunning: (id: NodeID) => boolean;
  getNodeState: (id: NodeID) => any;
  
  // === Drag & Drop ===
  dragState: DragState;
  onNodeDragStart: (event: DragEvent, nodeType: string) => void;
  onPersonDragStart: (event: DragEvent, personId: string) => void;
  onDragOver: (event: DragEvent) => void;
  onNodeDrop: (event: DragEvent, projectPosition: (x: number, y: number) => Vec2) => void;
  onPersonDrop: (event: DragEvent, nodeId: NodeID) => void;
  onDragEnd: () => void;
  
  // === Context Menu ===
  contextMenu: ContextMenuState;
  isContextMenuOpen: boolean;
  openContextMenu: (x: number, y: number, target: 'pane' | 'node' | 'edge', targetId?: NodeID) => void;
  closeContextMenu: () => void;
  handleDeleteSelected: () => void;
  handleDuplicateNode: (nodeId: NodeID) => void;
  
  // === Keyboard Shortcuts ===
  registerShortcut: (key: string, handler: () => void) => void;
  unregisterShortcut: (key: string) => void;
  
  // === Canvas Events ===
  onPaneClick: () => void;
  onPaneContextMenu: (event: React.MouseEvent) => void;
  onNodeContextMenu: (event: React.MouseEvent, nodeIdStr: string) => void;
  onEdgeContextMenu: (event: React.MouseEvent, edgeIdStr: string) => void;
  
  // === React Flow Handlers ===
  onNodesChange: (changes: NodeChange[]) => void;
  onArrowsChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  
  // === History ===
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  
  // === Transactions ===
  transaction: (fn: () => void) => void;
}

// =====================
// MAIN HOOK
// =====================

// Import the store type
import type { UnifiedStore } from '@/stores/unifiedStore.types';

// Create a stable selector using useMemo
const createStoreSelector = () => (state: UnifiedStore) => ({
  // Raw data from store
  nodesMap: state.nodes,
  handlesMap: state.handles,
  
  arrows: state.arrows,
  persons: state.persons,
  isMonitorMode: state.readOnly,
  
  // Selection
  selectedId: state.selectedId,
  selectedType: state.selectedType,
  
  // Store actions (these are stable references)
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
  
  // Execution
  runningNodes: state.execution.runningNodes,
  nodeStates: state.execution.nodeStates,
  
  // History
  transaction: state.transaction,
  undo: state.undo,
  redo: state.redo,
  canUndo: state.history.undoStack.length > 0,
  canRedo: state.history.redoStack.length > 0,
});

export function useCanvasOperations(options: UseCanvasOperationsOptions = {}): UseCanvasOperationsReturn {
  const { shortcuts = {}, enableInteractions = true } = options;
  
  // Create a stable selector
  const storeSelector = React.useMemo(() => createStoreSelector(), []);
  
  // Store state
  const storeState = useUnifiedStore(useShallow(storeSelector));
  
  // Convert Maps to arrays
  const arrows = React.useMemo(
    () => Array.from(storeState.arrows.values()) as DomainArrow[],
    [storeState.arrows]
  );
  
  const persons = React.useMemo(
    () => Array.from(storeState.persons.values()) as DomainPerson[],
    [storeState.persons]
  );
  
  // Wrapped operations
  const wrappedOperations = React.useMemo(() => ({
    addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => 
      storeState.addNode(type as NodeKind, position, data),
    
    addPerson: (person: { label: string; service: string; model: string }) =>
      storeState.addPerson(person.label, person.service as LLMService, person.model),
    
    getPersonById: (id: PersonID) => storeState.persons.get(id),
    
    // Derived state helpers
    isNodeRunning: (id: NodeID) => storeState.runningNodes.has(id),
    getNodeState: (id: NodeID) => storeState.nodeStates.get(id),
    isSelected: (id: string) => storeState.selectedId === id,
  }), [storeState]);
  
  // React Flow handlers
  const onNodesChange = React.useCallback((changes: NodeChange[]) => {
    if (storeState.isMonitorMode) return;
    
    storeState.transaction(() => {
      changes.forEach((change) => {
        switch (change.type) {
          case 'position':
            if (change.position && !change.dragging) {
              // Only update position when dragging ends to prevent update loops
              const node = storeState.nodesMap.get(change.id as NodeID);
              if (node) {
                // Check if position actually changed (with tolerance for floating point)
                const tolerance = 0.01;
                const positionChanged = 
                  Math.abs((node.position?.x || 0) - change.position.x) > tolerance ||
                  Math.abs((node.position?.y || 0) - change.position.y) > tolerance;
                
                if (positionChanged) {
                  storeState.updateNode(change.id as NodeID, { position: change.position });
                }
              }
            }
            break;
          case 'dimensions':
            // Dimensions are handled by React Flow internally
            // We don't need to store them in our domain model
            break;
          case 'replace':
            // Handle node replacement if needed
            // This is typically used when React Flow updates internal state
            break;
          case 'remove':
            storeState.deleteNode(change.id as NodeID);
            break;
          case 'select':
            // Handle selection changes if needed
            if (change.selected) {
              storeState.select(change.id, 'node');
            }
            break;
          case 'add':
            // React Flow is initializing the node - no action needed as node already exists in store
            break;
          default: {
            // Type-safe exhaustive check
            const _exhaustiveCheck: never = change;
            break;
          }
        }
      });
    });
  }, [storeState]);
  
  const onArrowsChange = React.useCallback((changes: EdgeChange[]) => {
    if (storeState.isMonitorMode) return;
    
    storeState.transaction(() => {
      changes.forEach((change) => {
        if (change.type === 'remove') {
          storeState.deleteArrow(change.id as ArrowID);
        }
      });
    });
  }, [storeState]);
  
  const onConnect = React.useCallback((connection: Connection) => {
    if (storeState.isMonitorMode) return;
    
    if (connection.source && connection.target && 
        connection.sourceHandle && connection.targetHandle) {
      // Create proper handle IDs from node IDs and handle names
      const sourceHandleId = handleId(
        nodeId(connection.source),
        connection.sourceHandle
      );
      const targetHandleId = handleId(
        nodeId(connection.target),
        connection.targetHandle
      );
      
      storeState.addArrow(sourceHandleId, targetHandleId);
    }
  }, [storeState]);
  
  // Convert domain nodes to React Flow format with handles
  // Use size as dependency to only recompute when nodes/handles are added/removed
  const nodesSize = storeState.nodesMap.size;
  const handlesSize = storeState.handlesMap.size;
  
  const nodes = React.useMemo(() => {
    const domainNodes = Array.from(storeState.nodesMap.values());
    return domainNodes.map(node => {
      const nodeHandles = Array.from(storeState.handlesMap.values()).filter(h => h.nodeId === node.id);
      return nodeToReact(node, nodeHandles);
    });
  }, [nodesSize, handlesSize, storeState.nodesMap, storeState.handlesMap]);
  
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
      node.type as NodeKind,
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
  const onNodeDragStart = useCallback((event: DragEvent, nodeType: string) => {
    if (!enableInteractions || storeState.isMonitorMode) return;
    
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
    
    // Calculate offset from element center
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    dragOffset.current = {
      x: event.clientX - (rect.left + rect.width / 2),
      y: event.clientY - (rect.top + rect.height / 2)
    };
    
    setDragState({
      isDragging: true,
      dragType: 'node',
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
  
  return {
    // === Canvas State ===
    nodes,
    arrows: arrows.map(a => a.id),
    persons: persons.map(p => p.id),
    handles: storeState.handlesMap,
    
    // === Selection State ===
    selectedId: storeState.selectedId,
    selectedType: storeState.selectedType,
    selectedNodeId,
    selectedArrowId,
    selectedPersonId,
    hasSelection: storeState.selectedId !== null,
    isSelected: wrappedOperations.isSelected,
    
    // === Mode State ===
    isMonitorMode: storeState.isMonitorMode,
    isConnectable: !storeState.isMonitorMode && enableInteractions,
    
    // === Node Operations ===
    addNode: wrappedOperations.addNode,
    updateNode: storeState.updateNode,
    deleteNode: storeState.deleteNode,
    duplicateNode: handleDuplicateNode,
    
    // === Arrow Operations ===
    addArrow: storeState.addArrow,
    updateArrow: storeState.updateArrow,
    deleteArrow: storeState.deleteArrow,
    
    // === Person Operations ===
    addPerson: wrappedOperations.addPerson,
    updatePerson: storeState.updatePerson,
    deletePerson: storeState.deletePerson,
    getPersonById: wrappedOperations.getPersonById,
    
    // === Selection Operations ===
    select: storeState.select,
    clearSelection: storeState.clearSelection,
    
    // === Execution State ===
    isNodeRunning: wrappedOperations.isNodeRunning,
    getNodeState: wrappedOperations.getNodeState,
    
    // === Drag & Drop ===
    dragState,
    onNodeDragStart,
    onPersonDragStart,
    onDragOver,
    onNodeDrop,
    onPersonDrop,
    onDragEnd,
    
    // === Context Menu ===
    contextMenu,
    isContextMenuOpen: contextMenu.position !== null,
    openContextMenu,
    closeContextMenu,
    handleDeleteSelected,
    handleDuplicateNode,
    
    // === Keyboard Shortcuts ===
    registerShortcut,
    unregisterShortcut,
    
    // === Canvas Events ===
    onPaneClick,
    onPaneContextMenu,
    onNodeContextMenu,
    onEdgeContextMenu,
    
    // === React Flow Handlers ===
    onNodesChange,
    onArrowsChange,
    onConnect,
    
    // === History ===
    undo: storeState.undo,
    redo: storeState.redo,
    canUndo: storeState.canUndo,
    canRedo: storeState.canRedo,
    
    // === Transactions ===
    transaction: storeState.transaction,
  };
}