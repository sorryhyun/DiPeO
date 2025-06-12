import { useCallback } from 'react';
import { useCanvasOperations } from './useCanvasOperations';
import { useUIState } from './useStoreSelectors';
import { clearDiagram } from './useDiagramOperations';
import { useExport } from './useExport';
import { useDiagramManager } from './useDiagramManager';
import { useExecution } from './useExecution';
import { usePropertyManager } from './usePropertyManager';
import { useFileOperations } from './useFileOperations';
import type { 
  DomainNode, 
  DomainArrow, 
  DomainPerson,
  NodeID, 
  ArrowID, 
  PersonID,
  NodeKind
} from '@/types';

// Maybe-hook helper
function useMaybe<T>(enabled: boolean, useHook: () => T): T | null {
  // Call the hook unconditionally to satisfy Rules of Hooks
  const hookResult = useHook();
  // Return null if not enabled, but the hook is still called
  return enabled ? hookResult : null;
}

export interface UseDiagramOptions {
  autoConnect?: boolean;
  enableMonitoring?: boolean;
  enableFileOperations?: boolean;
  enableInteractions?: boolean;
  debug?: boolean;
  // Diagram manager options
  autoSave?: boolean;
  autoSaveInterval?: number;
  confirmOnNew?: boolean;
  confirmOnLoad?: boolean;
}

/**
 * Master hook that combines all diagram-related functionality
 * This is the main entry point for components that need comprehensive diagram features
 */
export const useDiagram = (options: UseDiagramOptions = {}) => {
  const {
    autoConnect = false, // Changed to false - connection should be managed at app level
    enableMonitoring = false,
    enableFileOperations = true,
    enableInteractions = true,
    debug = false,
    // Diagram manager options
    autoSave = false,
    autoSaveInterval = 30000,
    confirmOnNew = true,
    confirmOnLoad = true
  } = options;

  // =====================
  // CORE HOOKS
  // =====================

  // Canvas state and operations (includes nodes, arrows, persons, history, selection)
  const canvas = useCanvasOperations({ enableInteractions });
  
  // Diagram management (includes file ops, execution, validation)
  const manager = useDiagramManager({
    autoSave,
    autoSaveInterval,
    confirmOnNew,
    confirmOnLoad
  });
  
  // UI state
  const ui = useUIState();
  
  // Derive selection helpers
  const selection = {
    selectedNodeId: canvas.selectedType === 'node' ? canvas.selectedId : null,
    selectedArrowId: canvas.selectedType === 'arrow' ? canvas.selectedId : null,
    selectedPersonId: canvas.selectedType === 'person' ? canvas.selectedId : null,
    setSelectedNodeId: (id: NodeID | null) => {
      if (id) canvas.select(id, 'node');
      else canvas.clearSelection();
    },
    setSelectedArrowId: (id: ArrowID | null) => {
      if (id) canvas.select(id, 'arrow');
      else canvas.clearSelection();
    },
    setSelectedPersonId: (id: PersonID | null) => {
      if (id) canvas.select(id, 'person');
      else canvas.clearSelection();
    },
    clearSelection: canvas.clearSelection
  };
  
  // Additional execution hook for realtime features
  const realtime = useExecution({
    autoConnect,
    enableMonitoring,
    showToasts: false,
    debug
  });
  
  // File operations (conditional) - use from manager if enabled
  const fileOps = useMaybe(enableFileOperations, useFileOperations);
  
  // Note: Canvas interactions are now integrated into useCanvasOperations
  // The shortcuts are passed through the options
  const interactions = enableInteractions ? {
    ...canvas,
    // Additional interaction-specific methods are already in canvas
  } : null;

  // =====================
  // CONVENIENCE METHODS
  // =====================

  // Property manager factory
  const createPropertyManager = useCallback(<T extends Record<string, unknown>>(
    entityId: NodeID | ArrowID | PersonID,
    entityType: 'node' | 'arrow' | 'person',
    initialData: T,
    options?: Parameters<typeof usePropertyManager>[3]
  ) => {
    return usePropertyManager(entityId, entityType, initialData, options);
  }, []);

  // Get the export hook for diagram operations
  const exportHook = useExport();
  
  // Get diagram state - uses new export format
  const getDiagramState = exportHook.exportDiagram;

  // Load diagram state - uses new import format
  const loadDiagramState = exportHook.importDiagram;

  // =====================
  // ELEMENT OPERATIONS
  // =====================

  // Node operations - stable store references, no useCallback needed
  const addNode = (type: NodeKind, position: { x: number; y: number }) => {
    return canvas.addNode(type, position);
  };

  const updateNode = (nodeId: NodeID, updates: Record<string, unknown>) => {
    return canvas.updateNode(nodeId, updates);
  };

  const deleteNode = (nodeId: NodeID) => {
    canvas.deleteNode(nodeId);
    if (selection.selectedNodeId === nodeId) {
      selection.clearSelection();
    }
  };

  const getNode = (nodeId: NodeID): DomainNode | undefined => {
    return canvas.nodes.find(n => n.id === nodeId) as DomainNode | undefined;
  };

  // Arrow operations
  const updateArrow = (arrowId: ArrowID, updates: Record<string, unknown>) => {
    return canvas.updateArrow(arrowId, updates);
  };

  const deleteArrow = (arrowId: ArrowID) => {
    canvas.deleteArrow(arrowId);
    if (selection.selectedArrowId === arrowId) {
      selection.clearSelection();
    }
  };

  // Note: Arrow data is not directly available in the new architecture
  // You should access arrow data through the store if needed
  const getArrow = (_arrowId: ArrowID): DomainArrow | undefined => {
    // Arrow data access would require direct store access
    return undefined;
  };

  // Person operations
  const addPerson = (person: Omit<DomainPerson, 'id'>) => {
    return canvas.addPerson({
      label: person.label,
      service: person.service,
      model: person.model
    });
  };

  const updatePerson = (personId: PersonID, updates: Record<string, unknown>) => {
    return canvas.updatePerson(personId, updates);
  };

  const deletePerson = (personId: PersonID) => {
    canvas.deletePerson(personId);
    if (selection.selectedPersonId === personId) {
      selection.clearSelection();
    }
  };

  const getPerson = (personId: PersonID): DomainPerson | undefined => {
    return canvas.getPersonById(personId);
  };

  // =====================
  // EXECUTION CONTROL
  // =====================

  // Direct delegation - realtime methods are stable
  const pauseNode = realtime.pauseNode;
  const resumeNode = realtime.resumeNode;
  const skipNode = realtime.skipNode;
  const respondToPrompt = realtime.respondToPrompt;

  // SELECTION OPERATIONS - wrap to handle string -> branded type conversion
  const selectNode = useCallback((id: string | NodeID | null) => {
    if (typeof id === 'string') {
      selection.setSelectedNodeId(id as NodeID);
    } else {
      selection.setSelectedNodeId(id);
    }
  }, [selection]);
  
  const selectArrow = useCallback((id: string | ArrowID | null) => {
    if (typeof id === 'string') {
      selection.setSelectedArrowId(id as ArrowID);
    } else {
      selection.setSelectedArrowId(id);
    }
  }, [selection]);
  
  const selectPerson = useCallback((id: string | PersonID | null) => {
    if (typeof id === 'string') {
      selection.setSelectedPersonId(id as PersonID);
    } else {
      selection.setSelectedPersonId(id);
    }
  }, [selection]);
  
  const clearSelection = selection.clearSelection;

  // =====================
  // STATE QUERIES
  // =====================

  const isNodeRunning = (nodeId: NodeID): boolean => {
    return realtime.runningNodes.has(nodeId);
  };

  const isNodeSkipped = (nodeId: NodeID): boolean => {
    return realtime.skippedNodes.some(skipped => skipped.nodeId === nodeId);
  };

  const getNodeExecutionState = (nodeId: NodeID) => {
    const skippedNode = realtime.skippedNodes.find(skipped => skipped.nodeId === nodeId);
    return {
      isRunning: realtime.runningNodes.has(nodeId),
      isCurrentlyRunning: realtime.currentRunningNode === nodeId,
      isSkipped: Boolean(skippedNode),
      skipReason: skippedNode?.reason,
      runningState: realtime.nodeRunningStates[nodeId] || false
    };
  };

  // =====================
  // RETURN INTERFACE
  // =====================

  return {
    // ===== DATA =====
    // Canvas data
    nodes: canvas.nodes,
    arrows: canvas.arrows,
    persons: canvas.persons,
    
    // Execution data
    runningNodes: realtime.runningNodes,
    currentRunningNode: realtime.currentRunningNode,
    nodeRunningStates: realtime.nodeRunningStates,
    skippedNodes: realtime.skippedNodes,
    runContext: realtime.runContext,
    
    // UI data
    selectedNodeId: selection.selectedNodeId,
    selectedArrowId: selection.selectedArrowId,
    selectedPersonId: selection.selectedPersonId,
    hasSelection: !!(selection.selectedNodeId || selection.selectedArrowId || selection.selectedPersonId),
    
    // State flags
    isMonitorMode: canvas.isMonitorMode,
    isRunning: manager.isExecuting,
    isConnected: realtime.isConnected,
    connectionState: realtime.isReconnecting ? 'reconnecting' : (realtime.isConnected ? 'connected' : 'disconnected'),
    
    // ===== OPERATIONS =====
    // Diagram operations
    getDiagramState,
    loadDiagramState,
    clear: clearDiagram, // Note: clearDiagram is still valid to use
    
    // Node operations
    addNode,
    updateNode,
    deleteNode,
    getNode,
    
    // Arrow operations
    updateArrow,
    deleteArrow,
    getArrow,
    
    // Person operations
    addPerson,
    updatePerson,
    deletePerson,
    getPerson,
    
    // Selection operations
    selectNode,
    selectArrow,
    selectPerson,
    clearSelection,
    
    // ===== EXECUTION =====
    // Basic execution - use manager's methods
    run: manager.executeDiagram,
    stop: manager.stopExecution,
    
    // Node control
    pauseNode,
    resumeNode,
    skipNode,
    respondToPrompt,
    
    // State queries
    isNodeRunning,
    isNodeSkipped,
    getNodeExecutionState,
    
    // ===== FILE OPERATIONS =====
    // Quick file ops - use manager's methods
    save: manager.saveDiagram,
    load: manager.importDiagram,
    
    // Full file operations (if enabled)
    ...(enableFileOperations && fileOps && {
      // Import operations
      importFile: fileOps.importFile,
      importWithDialog: fileOps.importWithDialog,
      importFromURL: fileOps.importFromURL,
      
      // Export operations
      exportJSON: fileOps.exportJSON,
      exportYAML: fileOps.exportYAML,
      exportLLMYAML: fileOps.exportLLMYAML,
      exportAllFormats: fileOps.exportAllFormats,
      
      // Save operations
      saveJSON: fileOps.saveJSON,
      saveYAML: fileOps.saveYAML,
      saveLLMYAML: fileOps.saveLLMYAML,
      
      // Download operations
      download: fileOps.download,
      downloadJSON: fileOps.downloadJSON,
      downloadYAML: fileOps.downloadYAML,
      downloadLLMYAML: fileOps.downloadLLMYAML,
      
      // Conversion operations
      convertJSONtoYAML: fileOps.convertJSONtoYAML,
      cloneDiagram: fileOps.cloneDiagram,
      
      // State
      isProcessingFile: fileOps.isProcessing,
      isDownloading: fileOps.isDownloading,
    }),
    
    // ===== INTERACTIONS =====
    // Canvas interactions (if enabled)
    ...(interactions && {
      // Context menu
      contextMenu: interactions.contextMenu,
      isContextMenuOpen: interactions.isContextMenuOpen,
      openContextMenu: interactions.openContextMenu,
      closeContextMenu: interactions.closeContextMenu,
      
      // Drag and drop
      dragState: interactions.dragState,
      onNodeDragStart: interactions.onNodeDragStart,
      onNodeDragStartCanvas: interactions.onNodeDragStartCanvas,
      onNodeDragStopCanvas: interactions.onNodeDragStopCanvas,
      onPersonDragStart: interactions.onPersonDragStart,
      onDragOver: interactions.onDragOver,
      onNodeDrop: interactions.onNodeDrop,
      onPersonDrop: interactions.onPersonDrop,
      onDragEnd: interactions.onDragEnd,
      
      // Canvas events
      onPaneClick: interactions.onPaneClick,
      onPaneContextMenu: interactions.onPaneContextMenu,
      onNodeContextMenu: interactions.onNodeContextMenu,
      onEdgeContextMenu: interactions.onEdgeContextMenu,
      
      // Keyboard shortcuts
      registerShortcut: interactions.registerShortcut,
      unregisterShortcut: interactions.unregisterShortcut,
    }),
    
    // ===== HISTORY =====
    canUndo: canvas.canUndo,
    canRedo: canvas.canRedo,
    undo: canvas.undo,
    redo: canvas.redo,
    
    // ===== MANAGER FEATURES =====
    // Additional features from manager
    isDirty: manager.isDirty,
    canExecute: manager.canExecute,
    isEmpty: manager.isEmpty,
    nodeCount: manager.nodeCount,
    arrowCount: manager.arrowCount,
    personCount: manager.personCount,
    metadata: manager.metadata,
    updateMetadata: manager.updateMetadata,
    validateDiagram: manager.validateDiagram,
    getDiagramStats: manager.getDiagramStats,
    newDiagram: manager.newDiagram,
    exportDiagram: manager.exportDiagram,
    loadDiagramFromFile: manager.loadDiagramFromFile,
    loadDiagramFromUrl: manager.loadDiagramFromUrl,
    executionProgress: manager.executionProgress,
    
    // ===== UTILITIES =====
    // Property manager factory
    createPropertyManager,
    
    // React Flow handlers (commonly needed)
    onNodesChange: canvas.onNodesChange,
    onArrowsChange: canvas.onArrowsChange,
    onConnect: canvas.onConnect,
    
    // Raw hook access for advanced use cases
    _canvas: canvas,
    _execution: realtime,
    _ui: ui,
    _history: history,
    _realtime: realtime,
    _fileOps: fileOps,
    _interactions: interactions,
    _manager: manager,
  };
};