/**
 * useCanvasOperations - Consolidated canvas hook combining all canvas-related functionality
 * 
 * This hook merges functionality from useCanvas and useCanvasInteractions to provide
 * a single interface for all canvas operations, interactions, and state management.
 */

import React, { useState, useCallback, useRef, useEffect, type DragEvent } from 'react';
import { shallow } from 'zustand/shallow';
import { useReactFlow, type NodeChange, type EdgeChange, type Connection } from '@xyflow/react';
import { useUnifiedStore } from '@/stores/useUnifiedStore';
import { nodeToReact } from '@/types/framework/adapters';
import { type NodeID, type ArrowID, type HandleID, type PersonID, nodeId, personId } from '@/types/branded';
import type { NodeKind } from '@/types/primitives/enums';
import type { Vec2 } from '@/types/primitives/geometry';
import type { LLMService, DomainNode } from '@/types';

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
  addPerson: (person: { name: string; service: string; model: string }) => PersonID;
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

export function useCanvasOperations(options: UseCanvasOperationsOptions = {}): UseCanvasOperationsReturn {
  const { shortcuts = {}, enableInteractions = true } = options;
  
  // Get React Flow instance
  const { getViewport } = useReactFlow();
  
  // Store state
  const storeState = useUnifiedStore(
    state => {
      // Convert domain nodes to React Flow format with handles
      const domainNodes = Array.from(state.nodes.values());
      const nodes = domainNodes.map(node => {
        const nodeHandles = Array.from(state.handles.values()).filter(h => h.nodeId === node.id);
        return nodeToReact(node, nodeHandles);
      });
      
      const arrows = Array.from(state.arrows.values());
      const persons = Array.from(state.persons.values());
      
      return {
        // State
        nodes,
        arrows,
        persons,
        handles: state.handles,
        isMonitorMode: state.readOnly,
        
        // Selection
        selectedId: state.selectedId,
        selectedType: state.selectedType,
        
        // Node operations
        addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => 
          state.addNode(type as NodeKind, position, data),
        updateNode: state.updateNode,
        deleteNode: state.deleteNode,
        
        // Arrow operations
        addArrow: state.addArrow,
        updateArrow: state.updateArrow,
        deleteArrow: state.deleteArrow,
        
        // Person operations
        addPerson: (person: { name: string; service: string; model: string }) => 
          state.addPerson(person.name, person.service as LLMService, person.model),
        updatePerson: state.updatePerson,
        deletePerson: state.deletePerson,
        getPersonById: (id: PersonID) => state.persons.get(id),
        
        // Selection
        select: state.select,
        clearSelection: state.clearSelection,
        
        // Derived state helpers
        isNodeRunning: (id: NodeID) => state.execution.runningNodes.has(id),
        getNodeState: (id: NodeID) => state.execution.nodeStates.get(id),
        isSelected: (id: string) => state.selectedId === id,
        
        // React Flow handlers
        onNodesChange: (changes: NodeChange[]) => {
          if (state.readOnly) return;
          
          changes.forEach((change) => {
            if (change.type === 'position' && change.position && change.dragging !== false) {
              state.updateNode(change.id as NodeID, { position: change.position });
            } else if (change.type === 'remove') {
              state.deleteNode(change.id as NodeID);
            }
          });
        },
        
        onArrowsChange: (changes: EdgeChange[]) => {
          if (state.readOnly) return;
          
          changes.forEach((change) => {
            if (change.type === 'remove') {
              state.deleteArrow(change.id as ArrowID);
            }
          });
        },
        
        onConnect: (connection: Connection) => {
          if (state.readOnly) return;
          
          if (connection.source && connection.target && 
              connection.sourceHandle && connection.targetHandle) {
            state.addArrow(
              connection.sourceHandle as HandleID,
              connection.targetHandle as HandleID
            );
          }
        },
        
        // Batch operations
        transaction: state.transaction,
        
        // History
        undo: state.undo,
        redo: state.redo,
        canUndo: state.history.undoStack.length > 0,
        canRedo: state.history.redoStack.length > 0,
      };
    },
    shallow
  );
  
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
    
    const node = storeState.nodes.find(n => n.id === nodeId);
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
    
    // Calculate offset from element center and scale by current zoom
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    const { zoom } = getViewport();
    dragOffset.current = {
      x: (event.clientX - (rect.left + rect.width / 2)) / zoom,
      y: (event.clientY - (rect.top + rect.height / 2)) / zoom
    };
    
    setDragState({
      isDragging: true,
      dragType: 'node',
      dragData: nodeType
    });
  }, [enableInteractions, storeState.isMonitorMode, getViewport]);
  
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
    
    // Get the drop position adjusted by the drag offset (scaled by current zoom)
    const { zoom } = getViewport();
    const dropPosition = projectPosition(
      event.clientX - dragOffset.current.x * zoom, 
      event.clientY - dragOffset.current.y * zoom
    );
    
    // Add the node at the drop position
    storeState.addNode(type as NodeKind, dropPosition);
    
    setDragState({
      isDragging: false,
      dragType: null,
    });
  }, [enableInteractions, storeState, getViewport]);
  
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
    nodes: storeState.nodes,
    arrows: storeState.arrows.map(a => a.id),
    persons: storeState.persons.map(p => p.id),
    handles: storeState.handles,
    
    // === Selection State ===
    selectedId: storeState.selectedId,
    selectedType: storeState.selectedType,
    selectedNodeId,
    selectedArrowId,
    selectedPersonId,
    hasSelection: storeState.selectedId !== null,
    isSelected: storeState.isSelected,
    
    // === Mode State ===
    isMonitorMode: storeState.isMonitorMode,
    isConnectable: !storeState.isMonitorMode && enableInteractions,
    
    // === Node Operations ===
    addNode: storeState.addNode,
    updateNode: storeState.updateNode,
    deleteNode: storeState.deleteNode,
    duplicateNode: handleDuplicateNode,
    
    // === Arrow Operations ===
    addArrow: storeState.addArrow,
    updateArrow: storeState.updateArrow,
    deleteArrow: storeState.deleteArrow,
    
    // === Person Operations ===
    addPerson: storeState.addPerson,
    updatePerson: storeState.updatePerson,
    deletePerson: storeState.deletePerson,
    getPersonById: storeState.getPersonById,
    
    // === Selection Operations ===
    select: storeState.select,
    clearSelection: storeState.clearSelection,
    
    // === Execution State ===
    isNodeRunning: storeState.isNodeRunning,
    getNodeState: storeState.getNodeState,
    
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
    onNodesChange: storeState.onNodesChange,
    onArrowsChange: storeState.onArrowsChange,
    onConnect: storeState.onConnect,
    
    // === History ===
    undo: storeState.undo,
    redo: storeState.redo,
    canUndo: storeState.canUndo,
    canRedo: storeState.canRedo,
    
    // === Transactions ===
    transaction: storeState.transaction,
  };
}