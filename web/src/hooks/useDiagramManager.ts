/**
 * useDiagramManager - Feature-based hook for diagram management
 * 
 * This hook provides high-level operations for managing diagrams including
 * creating, saving, loading, exporting, and executing diagrams.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { toast } from 'sonner';
import { useCanvasOperations } from './useCanvasOperations';
import { useExecution } from './useExecution';
import { useFileOperations } from './useFileOperations';
import { clearDiagram } from './useDiagramOperations';
import { useExport } from './useExport';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import type { ExecutionOptions } from '@/types';
import type { ExportFormat } from '@/stores';
import { DiagramFormat } from '@/__generated__/graphql';

// =====================
// TYPES
// =====================

export interface DiagramMetadata {
  name?: string;
  description?: string;
  createdAt?: Date;
  modifiedAt?: Date;
  version?: string;
}

export interface UseDiagramManagerOptions {
  autoSave?: boolean;
  autoSaveInterval?: number;
  confirmOnNew?: boolean;
  confirmOnLoad?: boolean;
}

export interface UseDiagramManagerReturn {
  // State
  isEmpty: boolean;
  isDirty: boolean;
  canExecute: boolean;
  nodeCount: number;
  arrowCount: number;
  personCount: number;
  metadata: DiagramMetadata;
  
  // Operations
  newDiagram: () => void;
  saveDiagram: (filename?: string) => Promise<void>;
  loadDiagramFromFile: (file: File) => Promise<void>;
  loadDiagramFromUrl: (url: string) => Promise<void>;
  exportDiagram: (format: DiagramFormat) => Promise<void>;
  importDiagram: () => Promise<void>;
  
  // Execution
  executeDiagram: (options?: ExecutionOptions) => Promise<void>;
  stopExecution: () => void;
  isExecuting: boolean;
  executionProgress: number;
  
  // Validation
  validateDiagram: () => { isValid: boolean; errors: string[] };
  
  // Metadata operations
  updateMetadata: (updates: Partial<DiagramMetadata>) => void;
  
  // History
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  
  // Utils
  getDiagramStats: () => {
    totalNodes: number;
    nodesByType: Record<string, number>;
    totalConnections: number;
    unconnectedNodes: number;
  };
  
  // Internal - for composition with other hooks
  _execution?: ReturnType<typeof useExecution>;
}

// =====================
// HELPERS
// =====================

function validateDiagramStructure(exportFormat: ExportFormat): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Check for empty diagram
  if (exportFormat.nodes.length === 0) {
    errors.push('Diagram has no nodes');
    return { isValid: false, errors };
  }
  
  // Check for start node
  const hasStartNode = exportFormat.nodes.some((node: any) => node.type === 'start');
  if (!hasStartNode) {
    errors.push('Diagram must have at least one start node');
  }
  
  // Check for endpoint node
  const hasEndpoint = exportFormat.nodes.some((node: any) => node.type === 'endpoint');
  if (!hasEndpoint) {
    errors.push('Diagram should have at least one endpoint node');
  }
  
  // Check for unconnected nodes
  const connectedNodes = new Set<string>();
  exportFormat.arrows.forEach((arrow: any) => {
    // Extract node IDs from handle format "nodeId:handleName"
    const sourceNodeId = arrow.source.split(':')[0];
    const targetNodeId = arrow.target.split(':')[0];
    if (sourceNodeId) connectedNodes.add(sourceNodeId);
    if (targetNodeId) connectedNodes.add(targetNodeId);
  });
  
  const unconnectedNodes = exportFormat.nodes.filter(
    (node: any) => !connectedNodes.has(node.id) && node.type !== 'start'
  ).map((node: any) => node.displayName || node.id);
  
  if (unconnectedNodes.length > 0) {
    errors.push(`${unconnectedNodes.length} node(s) are not connected`);
  }
  
  // Check for person nodes without assigned persons
  exportFormat.nodes.forEach((node: any) => {
    if ((node.type === 'person_job' || node.type === 'person_batch_job') && !node.data?.person) {
      errors.push(`Node ${node.displayName || node.id} requires a person to be assigned`);
    }
  });
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

// =====================
// MAIN HOOK
// =====================

export function useDiagramManager(options: UseDiagramManagerOptions = {}): UseDiagramManagerReturn {
  const {
    autoSave = false,
    autoSaveInterval = 30000, // 30 seconds
    confirmOnNew = true,
    confirmOnLoad = true
  } = options;
  
  // Get hooks
  const canvas = useCanvasOperations();
  const execution = useExecution({ showToasts: false });
  const fileOps = useFileOperations();
  const exportHook = useExport();
  
  // Track dirty state locally since store doesn't have it
  
  // Local state
  const [metadata, setMetadata] = useState<DiagramMetadata>({
    createdAt: new Date(),
    modifiedAt: new Date()
  });
  const [isDirty, setIsDirty] = useState(false);
  
  // Refs
  const autoSaveInterval$ef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  // Computed values
  const isEmpty = canvas.nodes.length === 0;
  const canExecute = !execution.isRunning && canvas.nodes.length > 0;
  const nodeCount = canvas.nodes.length;
  const arrowCount = canvas.arrows.length;
  const personCount = canvas.persons.length;
  
  // Operations
  const newDiagram = useCallback(() => {
    if (confirmOnNew && isDirty) {
      if (!window.confirm('You have unsaved changes. Do you want to discard them?')) {
        return;
      }
    }
    
    clearDiagram();
    setMetadata({
      createdAt: new Date(),
      modifiedAt: new Date()
    });
    setIsDirty(false);
    toast.success('New diagram created');
  }, [confirmOnNew, isDirty]);
  
  const saveDiagram = useCallback(async (filename?: string) => {
    // Check if there's anything to save
    const store = useUnifiedStore.getState();
    if (store.nodes.size === 0) {
      toast.error('No diagram to save');
      return;
    }
    
    try {
      // Generate a more user-friendly default filename if not provided
      const defaultFilename = filename || 'diagram';
      
      // Check if we have an existing diagram ID from URL params
      const urlParams = new URLSearchParams(window.location.search);
      const existingDiagramId = urlParams.get('diagram');
      
      // Use 'native' format for full fidelity saving
      const result = await fileOps.saveDiagramToServer(
        DiagramFormat.Native, 
        defaultFilename,
        existingDiagramId || undefined
      );
      
      // Only show success if save actually succeeded
      if (result) {
        setMetadata(prev => ({ ...prev, modifiedAt: new Date() }));
        setIsDirty(false);
        
        // Update URL if we got a new diagram ID
        if (result.diagramId && !existingDiagramId) {
          const newUrl = new URL(window.location.href);
          newUrl.searchParams.set('diagram', result.diagramId);
          window.history.replaceState({}, '', newUrl.toString());
        }
        
        toast.success('Diagram saved successfully');
      }
    } catch (error) {
      console.error('Failed to save diagram:', error);
      // Don't show another error toast - saveDiagramToServer already shows one
    }
  }, [fileOps]);
  
  const loadDiagramFromFile = useCallback(async (file: File) => {
    if (confirmOnLoad && isDirty) {
      if (!window.confirm('You have unsaved changes. Do you want to discard them?')) {
        return;
      }
    }
    
    try {
      await fileOps.importFile(file);
      setMetadata({
        name: file.name,
        modifiedAt: new Date()
      });
      setIsDirty(false);
      toast.success('Diagram loaded successfully');
    } catch (error) {
      console.error('Failed to load diagram:', error);
      toast.error('Failed to load diagram');
    }
  }, [confirmOnLoad, isDirty, fileOps]);
  
  const loadDiagramFromUrl = useCallback(async (url: string) => {
    if (confirmOnLoad && isDirty) {
      if (!window.confirm('You have unsaved changes. Do you want to discard them?')) {
        return;
      }
    }
    
    try {
      await fileOps.importFromURL(url);
      setMetadata({
        modifiedAt: new Date()
      });
      setIsDirty(false);
      toast.success('Diagram loaded successfully');
    } catch (error) {
      console.error('Failed to load diagram:', error);
      toast.error('Failed to load diagram from URL');
    }
  }, [confirmOnLoad, isDirty, fileOps]);
  
  const exportDiagramAs = useCallback(async (format: DiagramFormat) => {
    try {
      // Use unified export method with format
      if (format === DiagramFormat.Llm) {
        toast.error('LLM-readable format is not yet implemented');
        return;
      }
      // Export to server with format-specific extension
      await fileOps.exportAndDownload(format);
    } catch (error) {
      console.error('Failed to export diagram:', error);
      toast.error('Failed to export diagram');
    }
  }, [fileOps]);
  
  const importDiagramFile = useCallback(async () => {
    try {
      await fileOps.importWithDialog();
      setMetadata({
        modifiedAt: new Date()
      });
      setIsDirty(false);
      toast.success('Diagram imported successfully');
    } catch (error) {
      console.error('Failed to import diagram:', error);
      toast.error('Failed to import diagram');
    }
  }, [fileOps]);
  
  const executeDiagram = useCallback(async (options?: ExecutionOptions) => {
    // Get diagram in new export format
    const diagram = exportHook.exportDiagram();
    if (!diagram || diagram.nodes.length === 0) {
      toast.error('No diagram to execute');
      return;
    }
    
    // Validate before execution
    const validation = validateDiagramStructure(diagram);
    if (!validation.isValid) {
      toast.error(`Cannot execute diagram: ${validation.errors[0]}`);
      return;
    }
    
    try {
      // Get store state and convert to DomainDiagram format
      const store = useUnifiedStore.getState();
      const domainDiagram = {
        nodes: Object.fromEntries(store.nodes),
        arrows: Object.fromEntries(store.arrows),
        persons: Object.fromEntries(store.persons),
        handles: Object.fromEntries(store.handles),
        apiKeys: Object.fromEntries(store.apiKeys)
      };
      
      // Execute with DomainDiagram format - the execute function will convert to backend format
      await execution.execute(domainDiagram, options);
    } catch (error) {
      console.error('Failed to execute diagram:', error);
      toast.error('Failed to execute diagram');
    }
  }, [execution, exportHook]);
  
  const stopExecution = useCallback(() => {
    execution.abort();
  }, [execution]);
  
  const validateDiagram = useCallback(() => {
    // Use new export format for validation
    const diagram = exportHook.exportDiagram();
    if (!diagram || diagram.nodes.length === 0) {
      return { isValid: false, errors: ['No diagram to validate'] };
    }
    
    return validateDiagramStructure(diagram);
  }, [exportHook]);
  
  const updateMetadata = useCallback((updates: Partial<DiagramMetadata>) => {
    setMetadata(prev => ({ ...prev, ...updates, modifiedAt: new Date() }));
    setIsDirty(true);
  }, []);
  
  const getDiagramStats = useCallback(() => {
    // Work directly with store Maps for better performance
    const store = useUnifiedStore.getState();
    
    if (store.nodes.size === 0) {
      return {
        totalNodes: 0,
        nodesByType: {},
        totalConnections: 0,
        unconnectedNodes: 0
      };
    }
    
    // Count nodes by type
    const nodesByType: Record<string, number> = {};
    store.nodes.forEach(node => {
      nodesByType[node.type] = (nodesByType[node.type] || 0) + 1;
    });
    
    // Find unconnected nodes
    const connectedNodes = new Set<string>();
    store.arrows.forEach(arrow => {
      const sourceNodeId = arrow.source.split(':')[0];
      const targetNodeId = arrow.target.split(':')[0];
      if (sourceNodeId) connectedNodes.add(sourceNodeId);
      if (targetNodeId) connectedNodes.add(targetNodeId);
    });
    
    let unconnectedNodes = 0;
    store.nodes.forEach((_node, nodeId) => {
      if (!connectedNodes.has(nodeId)) {
        unconnectedNodes++;
      }
    });
    
    return {
      totalNodes: store.nodes.size,
      nodesByType,
      totalConnections: store.arrows.size,
      unconnectedNodes
    };
  }, []);
  
  // Mark dirty when canvas changes
  useEffect(() => {
    setIsDirty(true);
  }, [canvas.nodes, canvas.arrows]);
  
  // Auto-save setup
  useEffect(() => {
    if (autoSave && autoSaveInterval > 0) {
      if (autoSaveInterval$ef.current) {
        clearInterval(autoSaveInterval$ef.current);
      }
      
      autoSaveInterval$ef.current = setInterval(() => {
        if (isDirty && !execution.isRunning) {
          saveDiagram();
        }
      }, autoSaveInterval);
      
      return () => {
        if (autoSaveInterval$ef.current) {
          clearInterval(autoSaveInterval$ef.current);
        }
      };
    }
  }, [autoSave, autoSaveInterval, isDirty, execution.isRunning]);
  
  return {
    // State
    isEmpty,
    isDirty,
    canExecute,
    nodeCount,
    arrowCount,
    personCount,
    metadata,
    
    // Operations
    newDiagram,
    saveDiagram,
    loadDiagramFromFile,
    loadDiagramFromUrl,
    exportDiagram: exportDiagramAs,
    importDiagram: importDiagramFile,
    
    // Execution
    executeDiagram,
    stopExecution,
    isExecuting: execution.isRunning,
    executionProgress: execution.progress,
    
    // Validation
    validateDiagram,
    
    // Metadata operations
    updateMetadata,
    
    // History
    undo: canvas.undo,
    redo: canvas.redo,
    canUndo: canvas.canUndo,
    canRedo: canvas.canRedo,
    
    // Utils
    getDiagramStats,
    
    // Raw hook access for internal use
    _execution: execution
  };
}