/**
 * useDiagramManager - Feature-based hook for diagram management
 * 
 * This hook provides high-level operations for managing diagrams including
 * creating, saving, loading, exporting, and executing diagrams.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { toast } from 'sonner';
import { useCanvas } from './ui/useCanvas';
import { useExecution } from '@/features/execution-monitor/hooks/useExecution';
import { useFileOperations } from '@/shared/hooks/useFileOperations';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { useDebouncedSave } from '@/shared/hooks/useDebouncedSave';
import { useShallow } from 'zustand/react/shallow';
import type { ExecutionOptions } from '@/features/execution-monitor/types';
import { DiagramFormat } from '@dipeo/domain-models';

// TYPES

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



// MAIN HOOK

export function useDiagramManager(options: UseDiagramManagerOptions = {}): UseDiagramManagerReturn {
  const {
    autoSave = false,
    autoSaveInterval = 30000, // 30 seconds
    confirmOnNew = true,
    confirmOnLoad = true
  } = options;
  
  // Get hooks
  const canvas = useCanvas({ readOnly: false });
  const execution = useExecution({ showToasts: false });
  const fileOps = useFileOperations();
  
  // Get store operations
  const storeOps = useUnifiedStore(
    useShallow(state => ({
      // Data
      nodes: state.nodes,
      arrows: state.arrows,
      handles: state.handles,
      persons: state.persons,
      apiKeys: state.apiKeys,
      
      // Operations
      clearDiagram: state.clearDiagram,
      validateDiagram: state.validateDiagram,
      getDiagramStats: state.getDiagramStats,
      transaction: state.transaction,
      clearSelection: state.clearSelection,
      clearAll: state.clearAll,
      
      // History
      undo: state.undo,
      redo: state.redo,
      canUndo: state.canUndo,
      canRedo: state.canRedo,
    }))
  );
  
  // Local state
  const [metadata, setMetadata] = useState<DiagramMetadata>({
    createdAt: new Date(),
    modifiedAt: new Date()
  });
  const [isDirty, setIsDirty] = useState(false);
  
  // Refs
  const autoSaveInterval$ef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  // Computed values
  const isEmpty = canvas.nodesArray.length === 0;
  const canExecute = !execution.isRunning && canvas.nodesArray.length > 0;
  const nodeCount = canvas.nodesArray.length;
  const arrowCount = canvas.arrowsArray.length;
  const personCount = canvas.personsArray.length;
  
  // Debounced save for auto-save
  const { debouncedSave, saveImmediately, cancelPendingSave } = useDebouncedSave({
    delay: 1000, // 1 second debounce
    onSave: async (filename: string) => {
      if (storeOps.nodes.size === 0) return;
      
      // Check if we have an existing diagram ID from URL params
      const urlParams = new URLSearchParams(window.location.search);
      const existingDiagramId = urlParams.get('diagram');
      
      await fileOps.saveDiagramToServer(
        DiagramFormat.NATIVE, 
        filename,
        existingDiagramId || undefined
      );
      
      setIsDirty(false);
    },
    enabled: autoSave
  });
  
  // Operations
  const newDiagram = useCallback(() => {
    if (confirmOnNew && isDirty) {
      if (!window.confirm('You have unsaved changes. Do you want to discard them?')) {
        return;
      }
    }
    
    // Clear all diagram data
    storeOps.clearAll();
    
    setMetadata({
      createdAt: new Date(),
      modifiedAt: new Date()
    });
    setIsDirty(false);
    toast.success('New diagram created');
  }, [confirmOnNew, isDirty]);
  
  const saveDiagram = useCallback(async (filename?: string) => {
    // Check if there's anything to save
    if (storeOps.nodes.size === 0) {
      toast.error('No diagram to save');
      return;
    }
    
    try {
      // Generate a more user-friendly default filename if not provided
      const defaultFilename = filename || 'diagram';
      
      // If it's quicksave, use debounced save immediately (cancels any pending)
      if (defaultFilename === 'quicksave') {
        await saveImmediately(defaultFilename);
      } else {
        // For regular saves, save directly
        // Check if we have an existing diagram ID from URL params
        const urlParams = new URLSearchParams(window.location.search);
        const existingDiagramId = urlParams.get('diagram');
        
        // Use 'native' format for full fidelity saving
        const result = await fileOps.saveDiagramToServer(
          DiagramFormat.NATIVE, 
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
      }
    } catch (error) {
      console.error('Failed to save diagram:', error);
      // Don't show another error toast - saveDiagramToServer already shows one
    }
  }, [fileOps, saveImmediately]);
  
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
    // Check if there's a diagram to execute
    if (storeOps.nodes.size === 0) {
      toast.error('No diagram to execute');
      return;
    }
    
    // Validate before execution
    const validation = storeOps.validateDiagram();
    if (!validation.isValid) {
      toast.error(`Cannot execute diagram: ${validation.errors[0]}`);
      return;
    }
    
    try {
      // Get store state and convert to ReactDiagram format
      const domainDiagram = {
        nodes: Array.from(storeOps.nodes.values()),
        arrows: Array.from(storeOps.arrows.values()),
        persons: Array.from(storeOps.persons.values()),
        handles: Array.from(storeOps.handles.values()),
        apiKeys: Array.from(storeOps.apiKeys.values()),
        nodeCount: storeOps.nodes.size,
        arrowCount: storeOps.arrows.size,
        personCount: storeOps.persons.size
      };
      
      // Execute with ReactDiagram format - the execute function will convert to backend format
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
  
  // Mark dirty when canvas changes and trigger debounced auto-save
  useEffect(() => {
    setIsDirty(true);
    
    // Trigger debounced auto-save if enabled
    if (autoSave && !execution.isRunning) {
      debouncedSave('quicksave');
    }
  }, [canvas.nodesArray, canvas.arrowsArray, autoSave, execution.isRunning, debouncedSave]);
  
  // Clean up pending saves on unmount
  useEffect(() => {
    return () => {
      cancelPendingSave();
    };
  }, [cancelPendingSave]);
  
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