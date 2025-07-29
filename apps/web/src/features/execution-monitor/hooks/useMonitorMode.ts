/**
 * useMonitorMode - Hook to handle monitor mode auto-execution
 * 
 * This hook detects when the app is in monitor mode and automatically
 * starts execution of the loaded diagram.
 */

import { useEffect, useRef } from 'react';
import { useExecution } from './useExecution';
import { useDiagramLoader } from '@/features/diagram-editor/hooks/useDiagramLoader';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { useShallow } from 'zustand/react/shallow';
import { createCommonStoreSelector } from '@/core/store/selectorFactory';
import { type DomainDiagram, diagramId as createDiagramId } from '@/core/types';

export interface UseMonitorModeOptions {
  autoStart?: boolean;
  debug?: boolean;
}

export function useMonitorMode(options: UseMonitorModeOptions = {}) {
  const { autoStart = true, debug = false } = options;
  
  // Track if we've already started execution to prevent double-starts
  const hasStartedRef = useRef(false);
  
  // Get execution hook
  const execution = useExecution({ showToasts: true });
  
  // Get diagram loading state - but this won't load in execution mode without monitor mode anymore
  const { hasLoaded, diagramId } = useDiagramLoader();
  
  // Get diagram data from store
  const storeSelector = createCommonStoreSelector();
  const { nodes, arrows, persons, handles } = useUnifiedStore(useShallow(storeSelector));
  
  // Check if we're in monitor mode
  const isMonitorMode = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('monitor') === 'true' || !!params.get('executionId');
  };
  
  // Get diagram name from URL
  const getDiagramName = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('diagram');
  };
  
  // Get execution ID from URL
  const getExecutionId = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('executionId');
  };
  
  useEffect(() => {
    // Only proceed if:
    // 1. We're in monitor mode
    // 2. Auto-start is enabled
    // 3. We haven't already started execution
    // 4. We're not currently running
    if (!isMonitorMode() || !autoStart || hasStartedRef.current || execution.isRunning) {
      return;
    }
    
    const executionId = getExecutionId();
    const diagramName = getDiagramName();
    
    // Case 1: We have an executionId - connect to existing execution
    if (executionId) {
      console.log('Monitor mode: Connecting to existing execution:', executionId);
      hasStartedRef.current = true;
      
      // The execution is already running on the backend
      // Connect to it using the proper function
      const totalNodes = nodes.size || 0;
      execution.connectToExecution(executionId, totalNodes);
      
      return;
    }
    
    // Case 2: No executionId - start a new execution (original logic)
    if (!hasLoaded) {
      return;
    }
    
    if (!diagramName) {
      console.warn('Monitor mode enabled but no diagram specified in URL');
      return;
    }
    
    // Check if we have diagram data
    if (nodes.size === 0) {
      console.warn('Monitor mode: No nodes found in diagram');
      return;
    }
    
    // Mark that we've started to prevent double-starts
    hasStartedRef.current = true;
    
    // Prepare diagram data for execution
    const nodesArray = Array.from(nodes.values());
    const arrowsArray = Array.from(arrows.values());
    const personsArray = Array.from(persons.values());
    const handlesArray = Array.from(handles.values());
    
    const diagram: DomainDiagram = {
      nodes: nodesArray,
      arrows: arrowsArray,
      persons: personsArray,
      handles: handlesArray,
      metadata: {
        id: createDiagramId(diagramId || diagramName || 'temp-execution'),
        name: diagramName || 'Untitled Diagram',
        version: '1.0',
        created: new Date().toISOString(),
        modified: new Date().toISOString(),
        description: null,
        author: null,
        tags: []
      }
    };
    
    console.log('Monitor mode: Auto-starting execution for diagram:', diagramName);
    
    // Start execution with a delay to ensure UI and diagram are fully loaded
    setTimeout(() => {
      execution.execute(diagram, {
        debug,
        // Add any other execution options here
      }).catch(error => {
        console.error('Monitor mode: Failed to start execution:', error);
        // Reset the flag so user can manually retry if needed
        hasStartedRef.current = false;
      });
    }, 100);
    
  }, [hasLoaded, nodes.size, execution.isRunning, autoStart, debug, diagramId, execution]);
  
  // Reset hasStarted flag when URL changes
  useEffect(() => {
    const handleUrlChange = () => {
      const params = new URLSearchParams(window.location.search);
      const newDiagramName = params.get('diagram');
      const currentDiagramName = getDiagramName();
      
      if (newDiagramName !== currentDiagramName) {
        hasStartedRef.current = false;
      }
    };
    
    window.addEventListener('popstate', handleUrlChange);
    return () => window.removeEventListener('popstate', handleUrlChange);
  }, []);
  
  return {
    isMonitorMode: isMonitorMode(),
    diagramName: getDiagramName(),
    isExecuting: execution.isRunning,
    hasStarted: hasStartedRef.current,
    execution
  };
}