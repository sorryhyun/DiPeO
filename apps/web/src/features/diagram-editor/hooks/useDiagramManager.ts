import { useState, useCallback, useRef, useEffect } from 'react';
import { toast } from 'sonner';
import { useCanvas } from './ui/useCanvas';
import { useExecution } from '@/features/execution-monitor/hooks/useExecution';
import { useFileOperations } from '@/features/diagram-editor/hooks';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { useDebouncedSave } from '@/shared/hooks/useDebouncedSave';
import { useShallow } from 'zustand/react/shallow';
import type { ExecutionOptions } from '@/features/execution-monitor/types/execution';
import { DiagramFormat } from '@dipeo/domain-models';

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



export function useDiagramManager(options: UseDiagramManagerOptions = {}): UseDiagramManagerReturn {
  const {
    autoSave = false,
    autoSaveInterval = 30000, // 30 seconds
    confirmOnNew = true,
    confirmOnLoad = true
  } = options;
  
  const canvas = useCanvas({ readOnly: false });
  const execution = useExecution({ showToasts: false });
  const fileOps = useFileOperations();
  
  const storeOps = useUnifiedStore(
    useShallow(state => ({
      nodes: state.nodes,
      arrows: state.arrows,
      handles: state.handles,
      persons: state.persons,
      
      clearDiagram: state.clearDiagram,
      validateDiagram: state.validateDiagram,
      getDiagramStats: state.getDiagramStats,
      transaction: state.transaction,
      clearSelection: state.clearSelection,
      clearAll: state.clearAll,
      
      undo: state.undo,
      redo: state.redo,
      canUndo: state.canUndo,
      canRedo: state.canRedo,
    }))
  );
  
  const [metadata, setMetadata] = useState<DiagramMetadata>({
    createdAt: new Date(),
    modifiedAt: new Date()
  });
  const [isDirty, setIsDirty] = useState(false);
  
  
  const isEmpty = canvas.nodesArray.length === 0;
  const canExecute = !execution.isRunning && canvas.nodesArray.length > 0;
  const nodeCount = canvas.nodesArray.length;
  const arrowCount = canvas.arrowsArray.length;
  const personCount = canvas.personsArray.length;
  
  const { debouncedSave, cancelPendingSave } = useDebouncedSave({
    delay: autoSaveInterval,
    onSave: async (filename: string) => {
      if (storeOps.nodes.size === 0) return;
      
      try {
        await fileOps.saveDiagram(filename, DiagramFormat.NATIVE);
        setIsDirty(false);
      } catch (error) {
        console.error('Auto-save failed:', error);
      }
    },
    enabled: autoSave
  });
  
  const newDiagram = useCallback(() => {
    if (confirmOnNew && isDirty) {
      if (!window.confirm('You have unsaved changes. Do you want to discard them?')) {
        return;
      }
    }
    
    storeOps.clearAll();
    
    setMetadata({
      createdAt: new Date(),
      modifiedAt: new Date()
    });
    setIsDirty(false);
  }, [confirmOnNew, isDirty, storeOps]);
  
  const saveDiagram = useCallback(async (filename?: string) => {
    if (storeOps.nodes.size === 0) {
      toast.error('No diagram to save');
      return;
    }
    
    try {
      const defaultFilename = filename || 'diagram';
      
      const result = await fileOps.saveDiagram(defaultFilename, DiagramFormat.NATIVE);
      
      if (result) {
        setMetadata(prev => ({ ...prev, modifiedAt: new Date() }));
        setIsDirty(false);
      }
    } catch (error) {
      console.error('Failed to save diagram:', error);
    }
  }, [fileOps]);
  
  const loadDiagramFromFile = useCallback(async (file: File) => {
    if (confirmOnLoad && isDirty) {
      if (!window.confirm('You have unsaved changes. Do you want to discard them?')) {
        return;
      }
    }
    
    try {
      await fileOps.loadDiagram(file);
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
  
  
  const exportDiagramAs = useCallback(async (format: DiagramFormat) => {
    try {
      // Use unified export method with format
      // Export to server with format-specific extension
      await fileOps.downloadAs(format);
    } catch (error) {
      console.error('Failed to export diagram:', error);
      toast.error('Failed to export diagram');
    }
  }, [fileOps]);
  
  const importDiagramFile = useCallback(async () => {
    try {
      await fileOps.loadWithDialog();
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
    if (storeOps.nodes.size === 0) {
      toast.error('No diagram to execute');
      return;
    }
    
    const validation = storeOps.validateDiagram();
    if (!validation.isValid) {
      toast.error(`Cannot execute diagram: ${validation.errors[0]}`);
      return;
    }
    
    try {
      const domainDiagram = {
        nodes: Array.from(storeOps.nodes.values()),
        arrows: Array.from(storeOps.arrows.values()),
        persons: Array.from(storeOps.persons.values()),
        handles: Array.from(storeOps.handles.values()),
        nodeCount: storeOps.nodes.size,
        arrowCount: storeOps.arrows.size,
        personCount: storeOps.persons.size
      };
      
      await execution.execute(domainDiagram, options);
    } catch (error) {
      console.error('Failed to execute diagram:', error);
      toast.error('Failed to execute diagram');
    }
  }, [execution]);
  
  const stopExecution = useCallback(() => {
    execution.abort();
  }, [execution]);
  
  const validateDiagram = useCallback(() => {
    return storeOps.validateDiagram();
  }, [storeOps]);
  
  const updateMetadata = useCallback((updates: Partial<DiagramMetadata>) => {
    setMetadata(prev => ({ ...prev, ...updates, modifiedAt: new Date() }));
    setIsDirty(true);
  }, []);
  
  const getDiagramStats = useCallback(() => {
    return storeOps.getDiagramStats();
  }, [storeOps]);
  
  const isInitialMount = useRef(true);
  const dataVersion = useUnifiedStore(state => state.dataVersion);
  const initialDataVersion = useRef(dataVersion);
  
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    
    // Update the data version reference to prevent infinite loops
    if (dataVersion !== initialDataVersion.current) {
      initialDataVersion.current = dataVersion;
      setIsDirty(true);
      
      if (autoSave && !execution.isRunning) {
        debouncedSave('quicksave.json');
      }
    }
  }, [dataVersion, autoSave, execution.isRunning, debouncedSave]);
  
  useEffect(() => {
    return () => {
      cancelPendingSave();
    };
  }, [cancelPendingSave]);
  
  return {
    isEmpty,
    isDirty,
    canExecute,
    nodeCount,
    arrowCount,
    personCount,
    metadata,
    
    newDiagram,
    saveDiagram,
    loadDiagramFromFile,
    exportDiagram: exportDiagramAs,
    importDiagram: importDiagramFile,
    
    executeDiagram,
    stopExecution,
    isExecuting: execution.isRunning,
    executionProgress: execution.progress,
    
    // Validation
    validateDiagram,
    
    // Metadata operations
    updateMetadata,
    
    // History
    undo: storeOps.undo,
    redo: storeOps.redo,
    canUndo: storeOps.canUndo,
    canRedo: storeOps.canRedo,
    
    // Utils
    getDiagramStats,
    
    // Raw hook access for internal use
    _execution: execution
  };
}