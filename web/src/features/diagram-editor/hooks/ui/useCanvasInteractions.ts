/**
 * useCanvasInteractions - Focused hook for canvas user interactions
 * 
 * This hook handles drag & drop, context menus, and keyboard shortcuts
 * without mixing in data management concerns.
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import type { Node } from '@xyflow/react';
import { createNodeDragGhost } from '@/shared/utils/dragGhost';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { NodeID, PersonID, ArrowID, nodeId, personId } from '@/core/types';
import { Vec2, NodeType } from '@dipeo/domain-models';
import { useNodeOperations } from '../operations/useNodeOperations';
import { useArrowOperations } from '../operations/useArrowOperations';
import { usePersonOperations } from '../operations/usePersonOperations';

// Types
export interface ContextMenuState {
  position: { x: number; y: number } | null;
  target: 'pane' | 'node' | 'edge';
  targetId?: NodeID;
}

export interface DragState {
  isDragging: boolean;
  dragType: 'node' | 'person' | null;
  dragData?: string;
  draggedNodeId?: string;
}

export interface KeyboardShortcutsConfig {
  onDelete?: () => void;
  onEscape?: () => void;
  onSave?: () => void;
  onExport?: () => void;
  onImport?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onRun?: () => void;
  onSelectAll?: () => void;
  onDuplicate?: () => void;
}

export interface UseCanvasInteractionsOptions {
  enabled?: boolean;
  shortcuts?: KeyboardShortcutsConfig;
}

export interface UseCanvasInteractionsReturn {
  // Context Menu
  contextMenu: ContextMenuState;
  isContextMenuOpen: boolean;
  openContextMenu: (x: number, y: number, target: 'pane' | 'node' | 'edge', targetId?: NodeID) => void;
  closeContextMenu: () => void;
  
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
  
  // Keyboard Shortcuts
  registerShortcut: (key: string, handler: () => void) => void;
  unregisterShortcut: (key: string) => void;
  
  // Canvas Events
  onPaneClick: () => void;
  onPaneContextMenu: (event: React.MouseEvent) => void;
  onNodeContextMenu: (event: React.MouseEvent, nodeIdStr: string) => void;
  onEdgeContextMenu: (event: React.MouseEvent, edgeIdStr: string) => void;
  
  // Common Actions
  handleDeleteSelected: () => void;
  handleDuplicateSelected: () => void;
}

export function useCanvasInteractions(options: UseCanvasInteractionsOptions = {}): UseCanvasInteractionsReturn {
  const { enabled = true, shortcuts = {} } = options;
  
  // Store access for operations
  const store = useUnifiedStore;
  const isMonitorMode = useUnifiedStore(state => state.readOnly || state.executionReadOnly === true);
  const selectedId = useUnifiedStore(state => state.selectedId);
  const selectedType = useUnifiedStore(state => state.selectedType);
  
  // Domain operations hooks
  const nodeOps = useNodeOperations();
  const arrowOps = useArrowOperations();
  const personOps = usePersonOperations();
  
  // Local state
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    position: null,
    target: 'pane',
  });
  
  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    dragType: null,
  });
  
  // Refs
  const dragOffset = useRef({ x: 0, y: 0 });
  const shortcutHandlers = useRef<Map<string, () => void>>(new Map());
  
  // Context Menu
  const openContextMenu = useCallback((
    x: number, 
    y: number, 
    target: 'pane' | 'node' | 'edge',
    targetId?: NodeID
  ) => {
    if (!enabled || isMonitorMode) return;
    
    setContextMenu({ 
      position: { x, y }, 
      target,
      targetId 
    });
  }, [enabled, isMonitorMode]);
  
  const closeContextMenu = useCallback(() => {
    setContextMenu({ position: null, target: 'pane' });
  }, []);
  
  // Common Actions
  const handleDeleteSelected = useCallback(() => {
    if (!enabled || isMonitorMode) return;
    
    if (selectedType === 'node' && selectedId) {
      nodeOps.deleteNode(selectedId as NodeID);
    } else if (selectedType === 'arrow' && selectedId) {
      arrowOps.deleteArrow(selectedId as ArrowID);
    } else if (selectedType === 'person' && selectedId) {
      personOps.deletePerson(selectedId as PersonID);
    }
    store.getState().clearSelection();
    closeContextMenu();
  }, [enabled, isMonitorMode, selectedId, selectedType, nodeOps, arrowOps, personOps, store, closeContextMenu]);
  
  const handleDuplicateSelected = useCallback(() => {
    if (!enabled || isMonitorMode) return;
    
    if (selectedType === 'node' && selectedId) {
      const node = nodeOps.getNode(selectedId as NodeID);
      if (!node) return;
      
      const newPosition = {
        x: (node.position?.x || 0) + 50,
        y: (node.position?.y || 0) + 50
      };
      
      const newNodeId = nodeOps.addNode(
        node.type,
        newPosition,
        { ...node.data }
      );
      
      store.getState().select(newNodeId, 'node');
    }
    closeContextMenu();
  }, [enabled, isMonitorMode, selectedId, selectedType, nodeOps, store, closeContextMenu]);
  
  // Drag & Drop
  const onNodeDragStart = useCallback((event: React.DragEvent, nodeType: string) => {
    if (!enabled || isMonitorMode) return;
    
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
    
    const ghost = createNodeDragGhost(nodeType as NodeType);
    const ghostWidth = 200;
    const ghostHeight = 80;
    event.dataTransfer.setDragImage(ghost, ghostWidth / 2, ghostHeight / 2);
    
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    dragOffset.current = {
      x: event.clientX - (rect.left + rect.width / 2),
      y: event.clientY - (rect.top + rect.height / 2)
    };
    
    setDragState({
      isDragging: false,
      dragType: null,
      dragData: nodeType
    });
  }, [enabled, isMonitorMode]);
  
  const onNodeDragStartCanvas = useCallback(
    (_event: React.MouseEvent, node: Node) => {
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
  
  const onPersonDragStart = useCallback((event: React.DragEvent, personId: string) => {
    if (!enabled || isMonitorMode) return;
    
    event.dataTransfer.setData('application/person', personId);
    event.dataTransfer.effectAllowed = 'move';
    
    setDragState({
      isDragging: true,
      dragType: 'person',
      dragData: personId
    });
  }, [enabled, isMonitorMode]);
  
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);
  
  const onNodeDrop = useCallback((
    event: React.DragEvent, 
    projectPosition: (x: number, y: number) => Vec2
  ) => {
    if (!enabled || isMonitorMode) return;
    
    event.preventDefault();
    const type = event.dataTransfer.getData('application/reactflow');
    if (!type) return;
    
    const dropPosition = projectPosition(
      event.clientX - dragOffset.current.x, 
      event.clientY - dragOffset.current.y
    );
    
    nodeOps.addNode(type as NodeType, dropPosition);
    
    setDragState({
      isDragging: false,
      dragType: null,
    });
  }, [enabled, isMonitorMode, nodeOps]);
  
  const onPersonDrop = useCallback((
    event: React.DragEvent,
    nodeId: NodeID
  ) => {
    if (!enabled || isMonitorMode) return;
    
    event.preventDefault();
    const personIdStr = event.dataTransfer.getData('application/person');
    if (personIdStr) {
      nodeOps.updateNode(nodeId, { data: { person: personId(personIdStr) } });
    }
    
    setDragState({
      isDragging: false,
      dragType: null,
    });
  }, [enabled, isMonitorMode, nodeOps]);
  
  const onDragEnd = useCallback(() => {
    setDragState({
      isDragging: false,
      dragType: null,
    });
  }, []);
  
  // Keyboard Shortcuts
  const registerShortcut = useCallback((key: string, handler: () => void) => {
    shortcutHandlers.current.set(key, handler);
  }, []);
  
  const unregisterShortcut = useCallback((key: string) => {
    shortcutHandlers.current.delete(key);
  }, []);
  
  useEffect(() => {
    if (!enabled) return;
    
    const handleKeyDown = (e: KeyboardEvent) => {
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
        const state = store.getState();
        state.clearSelection();
        closeContextMenu();
        shortcuts.onEscape?.();
      }
      
      // Ctrl+S or Cmd+S for save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        shortcuts.onSave?.();
      }
      
      // Ctrl+E or Cmd+E for export
      if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        shortcuts.onExport?.();
      }
      
      // Ctrl+I or Cmd+I for import
      if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
        e.preventDefault();
        shortcuts.onImport?.();
      }
      
      // Ctrl+Z or Cmd+Z for undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (shortcuts.onUndo) {
          shortcuts.onUndo();
        } else {
          const state = store.getState();
          if (state.canUndo) state.undo();
        }
      }
      
      // Ctrl+Shift+Z or Cmd+Shift+Z for redo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
        e.preventDefault();
        if (shortcuts.onRedo) {
          shortcuts.onRedo();
        } else {
          const state = store.getState();
          if (state.canRedo) state.redo();
        }
      }
      
      // Ctrl+Y or Cmd+Y for redo (alternative)
      if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        e.preventDefault();
        if (shortcuts.onRedo) {
          shortcuts.onRedo();
        } else {
          const state = store.getState();
          if (state.canRedo) state.redo();
        }
      }
      
      // Ctrl+Enter or Cmd+Enter for run
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        shortcuts.onRun?.();
      }
      
      // Ctrl+A or Cmd+A for select all
      if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
        e.preventDefault();
        shortcuts.onSelectAll?.();
      }
      
      // Ctrl+D or Cmd+D for duplicate
      if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        if (shortcuts.onDuplicate) {
          shortcuts.onDuplicate();
        } else {
          handleDuplicateSelected();
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
  }, [enabled, shortcuts, handleDeleteSelected, handleDuplicateSelected, store, closeContextMenu]);
  
  // Canvas Events
  const onPaneClick = useCallback(() => {
    const state = store.getState();
    state.clearSelection();
    closeContextMenu();
  }, [store, closeContextMenu]);
  
  const onPaneContextMenu = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    openContextMenu(event.clientX, event.clientY, 'pane');
  }, [openContextMenu]);
  
  const onNodeContextMenu = useCallback((event: React.MouseEvent, nodeIdStr: string) => {
    event.preventDefault();
    event.stopPropagation();
    openContextMenu(event.clientX, event.clientY, 'node', nodeId(nodeIdStr));
  }, [openContextMenu]);
  
  const onEdgeContextMenu = useCallback((event: React.MouseEvent, edgeIdStr: string) => {
    event.preventDefault();
    event.stopPropagation();
    openContextMenu(event.clientX, event.clientY, 'edge', nodeId(edgeIdStr));
  }, [openContextMenu]);
  
  return {
    // Context Menu
    contextMenu,
    isContextMenuOpen: contextMenu.position !== null,
    openContextMenu,
    closeContextMenu,
    
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
    
    // Keyboard Shortcuts
    registerShortcut,
    unregisterShortcut,
    
    // Canvas Events
    onPaneClick,
    onPaneContextMenu,
    onNodeContextMenu,
    onEdgeContextMenu,
    
    // Common Actions
    handleDeleteSelected,
    handleDuplicateSelected,
  };
}