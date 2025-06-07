import { useCallback } from 'react';
import { 
  useCanvasSelectors, 
  useExecutionSelectors, 
  useUIState, 
  useSelectedElement,
  useHistorySelectors,
  usePersons,
  exportDiagramState,
  loadDiagram as loadDiagramAction,
  clearDiagram
} from './useStoreSelectors';
import { useDiagramStore } from '@/stores';
import { useExecution } from './useExecution';
import { useFileOperations } from './useFileOperations';
import { useCanvasInteractions } from './useCanvasInteractions';
import { usePropertyManager } from './usePropertyManager';
import { DiagramState, Node, Arrow, Person } from '@/types';

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
}

/**
 * Master hook that combines all diagram-related functionality
 * This is the main entry point for components that need comprehensive diagram features
 */
export const useDiagram = (options: UseDiagramOptions = {}) => {
  const {
    autoConnect = true,
    enableMonitoring = false,
    enableFileOperations = true,
    enableInteractions = true,
    debug = false
  } = options;

  // =====================
  // CORE HOOKS
  // =====================

  // Canvas state and operations
  const canvas = useCanvasSelectors();
  
  // Diagram store operations
  const diagramStore = useDiagramStore();
  
  // Execution state and operations
  const execution = useExecutionSelectors();
  
  // UI state
  const ui = useUIState();
  const selection = useSelectedElement();
  
  // History operations
  const history = useHistorySelectors();
  
  // Person operations
  const persons = usePersons();
  
  // Realtime execution (WebSocket)
  const realtime = useExecution({
    autoConnect,
    enableMonitoring,
    debug
  });
  
  // File operations (conditional via maybe-hook)
  const fileOps = useMaybe(enableFileOperations, useFileOperations);
  
  // Canvas interactions (conditional via maybe-hook)
  const interactions = useMaybe(enableInteractions, () => useCanvasInteractions({
    onSave: fileOps?.exportJSON,
    onExport: fileOps?.exportJSON,
    onImport: fileOps?.importWithDialog,
  }));

  // =====================
  // CONVENIENCE METHODS
  // =====================

  // Property manager factory
  const createPropertyManager = useCallback(<T extends Record<string, unknown>>(
    entityId: string,
    entityType: 'node' | 'arrow' | 'person',
    initialData: T,
    options?: Parameters<typeof usePropertyManager>[3]
  ) => {
    return usePropertyManager(entityId, entityType, initialData, options);
  }, []);

  // Quick execution - no need for useCallback with stable realtime reference
  const run = (diagram?: DiagramState) => {
    return realtime.executeDiagram(diagram);
  };

  // Quick stop
  const stop = () => {
    return realtime.abort();
  };

  // Quick save
  const save = async (filename?: string) => {
    if (!fileOps) {
      console.warn('File operations not enabled');
      return;
    }
    return fileOps.saveJSON(filename);
  };

  // Quick load
  const load = async () => {
    if (!fileOps) {
      console.warn('File operations not enabled');
      return;
    }
    return fileOps.importWithDialog();
  };

  // Get diagram state - direct export, no wrapper needed
  const getDiagramState = exportDiagramState;

  // Load diagram state - direct action, no wrapper needed
  const loadDiagramState = loadDiagramAction;

  // =====================
  // ELEMENT OPERATIONS
  // =====================

  // Node operations - stable store references, no useCallback needed
  const addNode = (type: Node['type'], position: { x: number; y: number }) => {
    return canvas.addNode(type, position);
  };

  const updateNode = (nodeId: string, updates: Record<string, unknown>) => {
    return canvas.updateNode(nodeId, updates);
  };

  const deleteNode = (nodeId: string) => {
    canvas.deleteNode(nodeId);
    if (selection.selectedNodeId === nodeId) {
      selection.clearSelection();
    }
  };

  const getNode = (nodeId: string): Node | undefined => {
    return canvas.nodes.find(n => n.id === nodeId);
  };

  // Arrow operations
  const updateArrow = (arrowId: string, updates: Record<string, unknown>) => {
    return diagramStore.updateArrow(arrowId, updates);
  };

  const deleteArrow = (arrowId: string) => {
    canvas.deleteArrow(arrowId);
    if (selection.selectedArrowId === arrowId) {
      selection.clearSelection();
    }
  };

  const getArrow = (arrowId: string): Arrow | undefined => {
    return canvas.arrows.find(a => a.id === arrowId);
  };

  // Person operations
  const addPerson = (person: Omit<Person, 'id'>) => {
    return persons.addPerson(person);
  };

  const updatePerson = (personId: string, updates: Record<string, unknown>) => {
    return persons.updatePerson(personId, updates);
  };

  const deletePerson = (personId: string) => {
    persons.deletePerson(personId);
    if (selection.selectedPersonId === personId) {
      selection.clearSelection();
    }
  };

  const getPerson = (personId: string): Person | undefined => {
    return persons.getPersonById(personId);
  };

  // =====================
  // EXECUTION CONTROL
  // =====================

  // Direct delegation - realtime methods are stable
  const pauseNode = realtime.pauseNode;
  const resumeNode = realtime.resumeNode;
  const skipNode = realtime.skipNode;
  const respondToPrompt = realtime.respondToPrompt;

  // SELECTION OPERATIONS - selection methods are stable
  const selectNode = selection.setSelectedNodeId;
  const selectArrow = selection.setSelectedArrowId;
  const selectPerson = selection.setSelectedPersonId;
  const clearSelection = selection.clearSelection;

  // =====================
  // STATE QUERIES
  // =====================

  const isNodeRunning = (nodeId: string): boolean => {
    return execution.runningNodes.includes(nodeId);
  };

  const isNodeSkipped = (nodeId: string): boolean => {
    return Boolean(execution.skippedNodes[nodeId]);
  };

  const getNodeExecutionState = (nodeId: string) => {
    return {
      isRunning: execution.runningNodes.includes(nodeId),
      isCurrentlyRunning: execution.currentRunningNode === nodeId,
      isSkipped: Boolean(execution.skippedNodes[nodeId]),
      skipReason: execution.skippedNodes[nodeId]?.reason,
      runningState: execution.nodeRunningStates[nodeId] || false
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
    persons: persons.persons,
    
    // Execution data
    runningNodes: execution.runningNodes,
    currentRunningNode: execution.currentRunningNode,
    nodeRunningStates: execution.nodeRunningStates,
    skippedNodes: execution.skippedNodes,
    runContext: execution.runContext,
    
    // UI data
    selectedNodeId: selection.selectedNodeId,
    selectedArrowId: selection.selectedArrowId,
    selectedPersonId: selection.selectedPersonId,
    hasSelection: !!(selection.selectedNodeId || selection.selectedArrowId || selection.selectedPersonId),
    
    // State flags
    isMonitorMode: canvas.isMonitorMode,
    isRunning: realtime.isRunning,
    isConnected: realtime.isConnected,
    connectionState: realtime.connectionState,
    
    // ===== OPERATIONS =====
    // Diagram operations
    getDiagramState,
    loadDiagramState,
    clear: clearDiagram,
    
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
    // Basic execution
    run,
    stop,
    
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
    // Quick file ops
    save,
    load,
    
    // Full file operations (if enabled)
    ...(fileOps && {
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
    canUndo: history.canUndo,
    canRedo: history.canRedo,
    undo: history.undo,
    redo: history.redo,
    
    // ===== UTILITIES =====
    // Property manager factory
    createPropertyManager,
    
    // React Flow handlers (commonly needed)
    onNodesChange: canvas.onNodesChange,
    onArrowsChange: canvas.onArrowsChange,
    onConnect: canvas.onConnect,
    
    // Raw hook access for advanced use cases
    _canvas: canvas,
    _execution: execution,
    _ui: ui,
    _history: history,
    _realtime: realtime,
    _fileOps: fileOps,
    _interactions: interactions,
  };
};