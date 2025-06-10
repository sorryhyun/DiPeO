/**
 * useDiagramManager - Feature-based hook for diagram management
 * 
 * This hook provides high-level operations for managing diagrams including
 * creating, saving, loading, exporting, and executing diagrams.
 */

import { useState, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { useCanvasOperations } from './useCanvasOperations';
import { useExecution } from './useExecution';
import { useFileOperations } from './useFileOperations';
import { exportDiagramState, clearDiagram } from './useStoreSelectors';
import type { DomainDiagram, ExecutionOptions } from '@/types';

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
  exportDiagram: (format: 'json' | 'yaml' | 'llm-yaml') => Promise<void>;
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

function validateDiagramStructure(diagram: DomainDiagram): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Check for empty diagram
  if (Object.keys(diagram.nodes).length === 0) {
    errors.push('Diagram has no nodes');
    return { isValid: false, errors };
  }
  
  // Check for start node
  const hasStartNode = Object.values(diagram.nodes).some(node => node.type === 'start');
  if (!hasStartNode) {
    errors.push('Diagram must have at least one start node');
  }
  
  // Check for endpoint node
  const hasEndpoint = Object.values(diagram.nodes).some(node => node.type === 'endpoint');
  if (!hasEndpoint) {
    errors.push('Diagram should have at least one endpoint node');
  }
  
  // Check for unconnected nodes
  const connectedNodes = new Set<string>();
  Object.values(diagram.arrows).forEach(arrow => {
    const sourceNodeId = arrow.source.split(':')[0];
    const targetNodeId = arrow.target.split(':')[0];
    if (sourceNodeId) connectedNodes.add(sourceNodeId);
    if (targetNodeId) connectedNodes.add(targetNodeId);
  });
  
  const unconnectedNodes = Object.entries(diagram.nodes).filter(
    ([nodeId, node]) => !connectedNodes.has(nodeId) && node.type !== 'start'
  ).map(([nodeId]) => nodeId);
  
  if (unconnectedNodes.length > 0) {
    errors.push(`${unconnectedNodes.length} node(s) are not connected`);
  }
  
  // Check for person nodes without assigned persons
  Object.entries(diagram.nodes).forEach(([nodeId, node]) => {
    if ((node.type === 'person_job' || node.type === 'person_batch_job') && !node.data?.person) {
      errors.push(`Node ${nodeId} requires a person to be assigned`);
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
  const execution = useExecution();
  const fileOps = useFileOperations();
  
  // Track dirty state locally since store doesn't have it
  
  // Local state
  const [metadata, setMetadata] = useState<DiagramMetadata>({
    createdAt: new Date(),
    modifiedAt: new Date()
  });
  const [isDirty, setIsDirty] = useState(false);
  
  // Refs
  const autoSaveInterval$ef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  // Auto-save setup
  useCallback(() => {
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
    const diagram = exportDiagramState();
    if (!diagram) {
      toast.error('No diagram to save');
      return;
    }
    
    try {
      await fileOps.saveJSON(filename || `diagram-${Date.now()}.json`);
      setMetadata(prev => ({ ...prev, modifiedAt: new Date() }));
      setIsDirty(false);
      toast.success('Diagram saved successfully');
    } catch (error) {
      console.error('Failed to save diagram:', error);
      toast.error('Failed to save diagram');
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
  
  const exportDiagram = useCallback(async (format: 'json' | 'yaml' | 'llm-yaml') => {
    try {
      // Use appropriate export method based on format
      switch (format) {
        case 'json':
          await fileOps.exportJSON();
          break;
        case 'yaml':
          await fileOps.exportYAML();
          break;
        case 'llm-yaml':
          await fileOps.exportLLMYAML();
          break;
      }
      toast.success(`Diagram exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Failed to export diagram:', error);
      toast.error('Failed to export diagram');
    }
  }, [fileOps]);
  
  const importDiagram = useCallback(async () => {
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
    const diagram = exportDiagramState();
    if (!diagram) {
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
      await execution.execute(diagram, options);
    } catch (error) {
      console.error('Failed to execute diagram:', error);
      toast.error('Failed to execute diagram');
    }
  }, [execution]);
  
  const stopExecution = useCallback(() => {
    execution.abort();
  }, [execution]);
  
  const validateDiagram = useCallback(() => {
    const diagram = exportDiagramState();
    if (!diagram) {
      return { isValid: false, errors: ['No diagram to validate'] };
    }
    
    return validateDiagramStructure(diagram);
  }, []);
  
  const updateMetadata = useCallback((updates: Partial<DiagramMetadata>) => {
    setMetadata(prev => ({ ...prev, ...updates, modifiedAt: new Date() }));
    setIsDirty(true);
  }, []);
  
  const getDiagramStats = useCallback(() => {
    const diagram = exportDiagramState();
    if (!diagram) {
      return {
        totalNodes: 0,
        nodesByType: {},
        totalConnections: 0,
        unconnectedNodes: 0
      };
    }
    
    // Count nodes by type
    const nodesByType: Record<string, number> = {};
    Object.values(diagram.nodes).forEach(node => {
      nodesByType[node.type] = (nodesByType[node.type] || 0) + 1;
    });
    
    // Find unconnected nodes
    const connectedNodes = new Set<string>();
    Object.values(diagram.arrows).forEach(arrow => {
      const sourceNodeId = arrow.source.split(':')[0];
      const targetNodeId = arrow.target.split(':')[0];
      if (sourceNodeId) connectedNodes.add(sourceNodeId);
      if (targetNodeId) connectedNodes.add(targetNodeId);
    });
    
    const unconnectedNodes = Object.keys(diagram.nodes).filter(
      nodeId => !connectedNodes.has(nodeId)
    ).length;
    
    return {
      totalNodes: Object.keys(diagram.nodes).length,
      nodesByType,
      totalConnections: Object.keys(diagram.arrows).length,
      unconnectedNodes
    };
  }, []);
  
  // Mark dirty when canvas changes
  useCallback(() => {
    setIsDirty(true);
  }, [canvas.nodes, canvas.arrows]);
  
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
    exportDiagram,
    importDiagram,
    
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