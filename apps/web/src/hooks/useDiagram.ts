import { useCallback } from 'react';
import { 
  useCanvasSelectors, 
  useExecutionSelectors, 
  useUISelectors, 
  useHistorySelectors,
  usePersons,
  exportDiagramState,
  loadDiagram as loadDiagramAction,
  clearDiagram
} from './useStoreSelectors';
import { useDiagramStore } from '@/stores';
import { useRealtimeExecution } from './useRealtimeExecution';
import { useFileOperations } from './useFileOperations';
import { useCanvasInteractions } from './useCanvasInteractions';
import { usePropertyManager } from './usePropertyManager';
import { DiagramState, Node, Arrow, Person } from '@/types';

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
  const ui = useUISelectors();
  
  // History operations
  const history = useHistorySelectors();
  
  // Person operations
  const persons = usePersons();
  
  // Realtime execution (WebSocket)
  const realtime = useRealtimeExecution({
    autoConnect,
    enableMonitoring,
    debug
  });
  
  // File operations (conditional)
  const fileOps = enableFileOperations ? useFileOperations() : null;
  
  // Canvas interactions (conditional)
  const interactions = enableInteractions ? useCanvasInteractions({
    onSave: fileOps?.exportJSON,
    onExport: fileOps?.exportJSON,
    onImport: fileOps?.importWithDialog,
  }) : null;

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

  // Quick execution
  const run = useCallback(async (diagram?: DiagramState) => {
    return realtime.executeDiagram(diagram);
  }, [realtime]);

  // Quick stop
  const stop = useCallback(() => {
    return realtime.abort();
  }, [realtime]);

  // Quick save
  const save = useCallback(async (filename?: string) => {
    if (!fileOps) {
      console.warn('File operations not enabled');
      return;
    }
    return fileOps.saveJSON(filename);
  }, [fileOps]);

  // Quick load
  const load = useCallback(async () => {
    if (!fileOps) {
      console.warn('File operations not enabled');
      return;
    }
    return fileOps.importWithDialog();
  }, [fileOps]);

  // Get diagram state
  const getDiagramState = useCallback((): DiagramState => {
    return exportDiagramState();
  }, []);

  // Load diagram state
  const loadDiagramState = useCallback((diagram: DiagramState, source?: string) => {
    loadDiagramAction(diagram);
  }, []);

  // =====================
  // ELEMENT OPERATIONS
  // =====================

  // Node operations
  const addNode = useCallback((type: Node['type'], position: { x: number; y: number }) => {
    return canvas.addNode(type, position);
  }, [canvas]);

  const updateNode = useCallback((nodeId: string, updates: Record<string, unknown>) => {
    return canvas.updateNode(nodeId, updates);
  }, [canvas]);

  const deleteNode = useCallback((nodeId: string) => {
    canvas.deleteNode(nodeId);
    if (ui.selectedNodeId === nodeId) {
      ui.clearSelection();
    }
  }, [canvas, ui]);

  const getNode = useCallback((nodeId: string): Node | undefined => {
    return canvas.nodes.find(n => n.id === nodeId);
  }, [canvas.nodes]);

  // Arrow operations
  const updateArrow = useCallback((arrowId: string, updates: Record<string, unknown>) => {
    return diagramStore.updateArrow(arrowId, updates);
  }, [diagramStore]);

  const deleteArrow = useCallback((arrowId: string) => {
    canvas.deleteArrow(arrowId);
    if (ui.selectedArrowId === arrowId) {
      ui.clearSelection();
    }
  }, [canvas, ui]);

  const getArrow = useCallback((arrowId: string): Arrow | undefined => {
    return canvas.arrows.find(a => a.id === arrowId);
  }, [canvas.arrows]);

  // Person operations
  const addPerson = useCallback((person: Omit<Person, 'id'>) => {
    return persons.addPerson(person);
  }, [persons]);

  const updatePerson = useCallback((personId: string, updates: Record<string, unknown>) => {
    return persons.updatePerson(personId, updates);
  }, [persons]);

  const deletePerson = useCallback((personId: string) => {
    persons.deletePerson(personId);
    if (ui.selectedPersonId === personId) {
      ui.clearSelection();
    }
  }, [persons, ui]);

  const getPerson = useCallback((personId: string): Person | undefined => {
    return persons.getPersonById(personId);
  }, [persons]);

  // =====================
  // EXECUTION CONTROL
  // =====================

  const pauseNode = useCallback((nodeId: string) => {
    realtime.pauseNode(nodeId);
  }, [realtime]);

  const resumeNode = useCallback((nodeId: string) => {
    realtime.resumeNode(nodeId);
  }, [realtime]);

  const skipNode = useCallback((nodeId: string) => {
    realtime.skipNode(nodeId);
  }, [realtime]);

  const respondToPrompt = useCallback((nodeId: string, response: string) => {
    realtime.respondToPrompt(nodeId, response);
  }, [realtime]);

  // =====================
  // SELECTION OPERATIONS
  // =====================

  const selectNode = useCallback((nodeId: string) => {
    console.log('[useDiagram] Selecting node:', nodeId);
    ui.setSelectedNodeId(nodeId);
  }, [ui]);

  const selectArrow = useCallback((arrowId: string) => {
    console.log('[useDiagram] Selecting arrow:', arrowId);
    ui.setSelectedArrowId(arrowId);
  }, [ui]);

  const selectPerson = useCallback((personId: string) => {
    ui.setSelectedPersonId(personId);
  }, [ui]);

  const clearSelection = useCallback(() => {
    ui.clearSelection();
  }, [ui]);

  // =====================
  // STATE QUERIES
  // =====================

  const isNodeRunning = useCallback((nodeId: string): boolean => {
    return execution.runningNodes.includes(nodeId);
  }, [execution.runningNodes]);

  const isNodeSkipped = useCallback((nodeId: string): boolean => {
    return Boolean(execution.skippedNodes[nodeId]);
  }, [execution.skippedNodes]);

  const getNodeExecutionState = useCallback((nodeId: string) => {
    return {
      isRunning: isNodeRunning(nodeId),
      isCurrentlyRunning: execution.currentRunningNode === nodeId,
      isSkipped: isNodeSkipped(nodeId),
      skipReason: execution.skippedNodes[nodeId]?.reason,
      runningState: execution.nodeRunningStates[nodeId] || false
    };
  }, [execution, isNodeRunning, isNodeSkipped]);

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
    selectedNodeId: ui.selectedNodeId,
    selectedArrowId: ui.selectedArrowId,
    selectedPersonId: ui.selectedPersonId,
    hasSelection: !!(ui.selectedNodeId || ui.selectedArrowId || ui.selectedPersonId),
    
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