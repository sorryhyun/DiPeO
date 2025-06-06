import { useState, useCallback, useRef, useEffect, type DragEvent } from 'react';
import { useCanvasSelectors } from './store/useCanvasSelectors';
import { useUISelectors } from './store/useUISelectors';
import { useHistorySelectors } from './store/useHistorySelectors';
import { Node } from '@/types/core';

// =====================
// TYPES
// =====================

export interface ContextMenuState {
  position: { x: number; y: number } | null;
  target: 'pane' | 'node' | 'edge';
  targetId?: string;
}

export interface DragState {
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
}

// =====================
// MAIN HOOK
// =====================

export const useCanvasInteractions = (shortcuts?: KeyboardShortcutsConfig) => {
  // Store selectors
  const { 
    addNode, 
    updateNode, 
    deleteNode, 
    deleteArrow, 
    isMonitorMode 
  } = useCanvasSelectors();
  const { 
    selectedNodeId, 
    selectedArrowId, 
    clearSelection 
  } = useUISelectors();
  const { undo, redo, canUndo, canRedo } = useHistorySelectors();

  // Local state
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
    targetId?: string
  ) => {
    if (isMonitorMode) return; // No context menu in monitor mode
    
    setContextMenu({ 
      position: { x, y }, 
      target,
      targetId 
    });
  }, [isMonitorMode]);

  const closeContextMenu = useCallback(() => {
    setContextMenu({ position: null, target: 'pane' });
  }, []);

  // Context menu actions
  const handleDeleteSelected = useCallback(() => {
    if (isMonitorMode) return;
    
    if (selectedNodeId) {
      deleteNode(selectedNodeId);
      clearSelection();
    } else if (selectedArrowId) {
      deleteArrow(selectedArrowId);
      clearSelection();
    }
    closeContextMenu();
  }, [selectedNodeId, selectedArrowId, deleteNode, deleteArrow, clearSelection, closeContextMenu, isMonitorMode]);

  const handleDuplicateNode = useCallback((nodeId: string) => {
    if (isMonitorMode) return;
    
    // Implementation would need access to the actual node data
    // This is a placeholder for the duplicate functionality
    console.log('Duplicate node:', nodeId);
    closeContextMenu();
  }, [closeContextMenu, isMonitorMode]);

  // =====================
  // DRAG AND DROP
  // =====================

  // Handle drag start for node types from sidebar
  const onNodeDragStart = useCallback((event: DragEvent, nodeType: string) => {
    if (isMonitorMode) return;
    
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
  }, [isMonitorMode]);

  // Handle drag start for persons from sidebar
  const onPersonDragStart = useCallback((event: DragEvent, personId: string) => {
    if (isMonitorMode) return;
    
    event.dataTransfer.setData('application/person', personId);
    event.dataTransfer.effectAllowed = 'move';

    setDragState({
      isDragging: true,
      dragType: 'person',
      dragData: personId
    });
  }, [isMonitorMode]);

  // Handle drag over for canvas drop zone
  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop for adding nodes to canvas
  const onNodeDrop = useCallback((
    event: DragEvent, 
    projectPosition: (x: number, y: number) => { x: number; y: number }
  ) => {
    if (isMonitorMode) return;
    
    event.preventDefault();
    const type = event.dataTransfer.getData('application/reactflow');
    if (!type) return;
    
    // Get the drop position - this should be where the cursor is
    const dropPosition = projectPosition(event.clientX, event.clientY);
    
    // Add the node at the drop position
    addNode(type as Node['type'], dropPosition);

    setDragState({
      isDragging: false,
      dragType: null,
    });
  }, [addNode, isMonitorMode]);

  // Handle person drop on nodes (for PersonJob nodes)
  const onPersonDrop = useCallback((
    event: DragEvent,
    nodeId: string
  ) => {
    if (isMonitorMode) return;
    
    event.preventDefault();
    const personId = event.dataTransfer.getData('application/person');
    if (personId) {
      updateNode(nodeId, { personId });
    }

    setDragState({
      isDragging: false,
      dragType: null,
    });
  }, [updateNode, isMonitorMode]);

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
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if typing in input fields
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      // Delete key
      if (e.key === 'Delete') {
        e.preventDefault();
        if (shortcuts?.onDelete) {
          shortcuts.onDelete();
        } else {
          handleDeleteSelected();
        }
      }
      
      // Escape key
      if (e.key === 'Escape') {
        e.preventDefault();
        clearSelection();
        closeContextMenu();
        if (shortcuts?.onEscape) {
          shortcuts.onEscape();
        }
      }
      
      // Ctrl+S or Cmd+S for save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (shortcuts?.onSave) {
          shortcuts.onSave();
        }
      }
      
      // Ctrl+E or Cmd+E for export
      if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        if (shortcuts?.onExport) {
          shortcuts.onExport();
        }
      }
      
      // Ctrl+I or Cmd+I for import
      if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
        e.preventDefault();
        if (shortcuts?.onImport) {
          shortcuts.onImport();
        }
      }
      
      // Ctrl+Z or Cmd+Z for undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (canUndo) {
          undo();
        }
      }
      
      // Ctrl+Shift+Z or Cmd+Shift+Z for redo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
        e.preventDefault();
        if (canRedo) {
          redo();
        }
      }
      
      // Ctrl+Y or Cmd+Y for redo (alternative)
      if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        e.preventDefault();
        if (canRedo) {
          redo();
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
    shortcuts, 
    handleDeleteSelected, 
    clearSelection, 
    closeContextMenu, 
    undo, 
    redo, 
    canUndo, 
    canRedo
  ]);

  // =====================
  // CANVAS EVENTS
  // =====================

  // Handle canvas pane click
  const onPaneClick = useCallback(() => {
    clearSelection();
    closeContextMenu();
  }, [clearSelection, closeContextMenu]);

  // Handle canvas pane context menu
  const onPaneContextMenu = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    openContextMenu(event.clientX, event.clientY, 'pane');
  }, [openContextMenu]);

  // Handle node context menu
  const onNodeContextMenu = useCallback((event: React.MouseEvent, nodeId: string) => {
    event.preventDefault();
    event.stopPropagation();
    openContextMenu(event.clientX, event.clientY, 'node', nodeId);
  }, [openContextMenu]);

  // Handle edge context menu
  const onEdgeContextMenu = useCallback((event: React.MouseEvent, edgeId: string) => {
    event.preventDefault();
    event.stopPropagation();
    openContextMenu(event.clientX, event.clientY, 'edge', edgeId);
  }, [openContextMenu]);

  // =====================
  // RETURN INTERFACE
  // =====================

  return {
    // Context menu
    contextMenu,
    isContextMenuOpen: contextMenu.position !== null,
    openContextMenu,
    closeContextMenu,
    
    // Context menu actions
    handleDeleteSelected,
    handleDuplicateNode,
    
    // Drag and drop
    dragState,
    onNodeDragStart,
    onPersonDragStart,
    onDragOver,
    onNodeDrop,
    onPersonDrop,
    onDragEnd,
    
    // Keyboard shortcuts
    registerShortcut,
    unregisterShortcut,
    
    // Canvas events
    onPaneClick,
    onPaneContextMenu,
    onNodeContextMenu,
    onEdgeContextMenu,
    
    // State
    isMonitorMode,
    selectedNodeId,
    selectedArrowId,
    
    // History
    canUndo,
    canRedo,
    undo,
    redo,
  };
};