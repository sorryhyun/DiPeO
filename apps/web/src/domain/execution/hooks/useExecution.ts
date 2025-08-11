/**
 * useExecution - GraphQL-based execution hook replacing WebSocket
 * 
 * This hook provides the same interface as useExecution but uses GraphQL
 * subscriptions and mutations instead of WebSocket.
 */

import React, { useCallback, useEffect } from 'react';
import { ApolloError } from '@apollo/client';
import { toast } from 'sonner';
import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import {type DomainDiagram, diagramId, executionId } from '@/infrastructure/types';
import type { ExecutionOptions, InteractivePromptData } from '@/domain/execution/types/execution';
import { EventType, NodeID, type ExecutionUpdate } from '@dipeo/models';
import { createCommonStoreSelector } from '@/infrastructure/store/selectorFactory';
import { useExecutionStreaming } from './useExecutionStreaming';
import { useExecutionState } from './useExecutionState';
import { useExecutionUpdates } from './useExecutionUpdates';
import { formatTime, getNodeIcon, getNodeColor } from '../utils/executionHelpers';
import { stripTypenames } from '@/lib/utils/graphql';

// Re-export types from state hook for backwards compatibility
export type { HookExecutionState, NodeState } from './useExecutionState';

export interface UseExecutionOptions {
  autoConnect?: boolean;
  enableMonitoring?: boolean;
  debug?: boolean;
  showToasts?: boolean;
  formatDuration?: boolean;
  onUpdate?: (update: ExecutionUpdate) => void;
}

export interface UseExecutionReturn {
  // State
  execution: import('./useExecutionState').HookExecutionState;
  nodeStates: Record<string, import('./useExecutionState').NodeState>;
  isRunning: boolean;
  isReconnecting: boolean;
  progress: number;
  duration: string;
  
  // Execution Actions
  execute: (diagram?: DomainDiagram, options?: ExecutionOptions) => Promise<void>;
  connectToExecution: (executionId: string, totalNodes?: number) => void;
  abort: () => void;
  
  // Node Actions
  pauseNode: (nodeId: string) => void;
  resumeNode: (nodeId: string) => void;
  skipNode: (nodeId: string) => void;
  
  // Interactive Prompt
  interactivePrompt: InteractivePromptData | null;
  respondToPrompt: (response: string) => void;
  
  // UI Helpers
  formatTime: (startTime: Date | null, endTime: Date | null) => string;
  getNodeIcon: (nodeType: string) => string;
  getNodeColor: (nodeType: string) => string;
  getNodeExecutionState: (nodeId: string) => import('./useExecutionState').NodeState | undefined;
  
  // Store integration
  currentRunningNode: string | null;
  nodeRunningStates: Record<string, boolean>;
  runContext: Record<string, unknown>;
  skippedNodes: Array<{ nodeId: string; reason: string }>;
  
  // Additional properties for compatibility
  runningNodes: Set<NodeID>;
  nodes?: Array<any>;
}


// Main Hook
export function useExecution(options: UseExecutionOptions = {}): UseExecutionReturn {
  const {
    showToasts = true,
    formatDuration = true,
    onUpdate
  } = options;
  
  // Store integration
  const executionStoreSelector = React.useMemo(createCommonStoreSelector, []);
  const executionActions = useUnifiedStore(useShallow(executionStoreSelector));
  
  // State management
  const state = useExecutionState();
  const {
    execution,
    nodeStates,
    interactivePrompt,
    progress,
    duration,
    executionIdRef,
    currentRunningNodeRef,
    runContextRef,
    skippedNodesRef,
    startExecution,
    connectToExecution,
    resetState,
    errorExecution,
    updateProgress,
  } = state;
  
  // Streaming operations (GraphQL or SSE)
  // Use execution.executionId from state instead of ref for reactivity
  const currentExecutionId = execution.executionId || executionIdRef.current;
  console.log('[useExecution] Setting up streaming with executionId:', currentExecutionId);
  const streaming = useExecutionStreaming({ 
    executionId: currentExecutionId,
    skip: !currentExecutionId
  });
  
  // Process subscription updates
  useExecutionUpdates({
    state,
    executionActions,
    showToasts,
    onUpdate,
    executionUpdates: streaming.executionUpdates,
    nodeUpdates: streaming.nodeUpdates,
    interactivePrompts: streaming.interactivePrompts,
  });

  // Main Actions
  const execute = useCallback(async (diagram?: DomainDiagram, options?: ExecutionOptions) => {
    resetState();
    
    try {
      // Prepare diagram data for execution
      const diagramData = diagram ? {
        nodes: diagram.nodes.reduce((acc: Record<string, unknown>, node) => {
          return { ...acc, [node.id]: stripTypenames(node) };
        }, {}),
        arrows: diagram.arrows.reduce((acc: Record<string, unknown>, arrow) => ({ 
          ...acc, 
          [arrow.id]: stripTypenames(arrow) 
        }), {}),
        persons: diagram.persons.reduce((acc: Record<string, unknown>, person) => ({ 
          ...acc, 
          [person.id]: stripTypenames(person) 
        }), {}),
        handles: diagram.handles?.reduce((acc: Record<string, unknown>, handle) => ({ 
          ...acc, 
          [handle.id]: stripTypenames(handle) 
        }), {}) || {},
        metadata: stripTypenames(diagram.metadata)
      } : null;

      const result = await streaming.executeDiagram({
        variables: {
          input: {
            diagram_data: diagramData,
            diagram_id: diagramData ? undefined : diagram?.metadata?.id || diagramId('current'),
            variables: (options as ExecutionOptions & { variables?: Record<string, unknown> })?.variables || {},
            debug_mode: options?.debug || false,
            timeout_seconds: (options as ExecutionOptions & { timeout?: number })?.timeout,
            max_iterations: (options as ExecutionOptions & { maxIterations?: number })?.maxIterations
          }
        }
      });
      
      if (result.data?.execute_diagram?.success && result.data.execute_diagram.execution?.id) {
        const execId = result.data.execute_diagram.execution.id;
        const totalNodes = diagram ? (diagram.nodes || []).length : 0;
        startExecution(execId, totalNodes, formatDuration);
        executionActions.startExecution(execId);
        onUpdate?.({ type: EventType.EXECUTION_STATUS_CHANGED, execution_id: executionId(execId), timestamp: new Date().toISOString() });
      } else {
        throw new Error(result.data?.execute_diagram?.error || 'Failed to start execution');
      }
    } catch (error) {
      const errorMessage = error instanceof ApolloError ? error.message : 'Failed to execute diagram';
      errorExecution(errorMessage);
      if (showToasts) {
        toast.error(errorMessage);
      }
      throw error;
    }
  }, [streaming, startExecution, executionActions, errorExecution, onUpdate, resetState, formatDuration, showToasts]);

  const controlExecution = useCallback(async (action: string, nodeIdStr?: string) => {
    if (!executionIdRef.current) return;
    
    try {
      await streaming.controlExecution({
        variables: {
          input: {
            execution_id: executionIdRef.current,
            action,
            node_id: nodeIdStr
          }
        }
      });
    } catch (error) {
      if (showToasts) {
        toast.error(`Failed to ${action}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  }, [streaming, showToasts]);

  const pauseNode = useCallback((nodeIdStr: string) => {
    void controlExecution('pause', nodeIdStr);
  }, [controlExecution]);

  const resumeNode = useCallback((nodeIdStr: string) => {
    void controlExecution('resume', nodeIdStr);
  }, [controlExecution]);

  const skipNode = useCallback((nodeIdStr: string) => {
    void controlExecution('skip', nodeIdStr);
  }, [controlExecution]);

  const abort = useCallback(() => {
    if (executionIdRef.current) {
      void controlExecution('abort');
    } else if (execution.isRunning) {
      errorExecution('Execution aborted');
      executionActions.stopExecution();
    }
  }, [controlExecution, errorExecution, executionActions, execution.isRunning]);

  const respondToPrompt = useCallback(async (response: string) => {
    if (!executionIdRef.current || !interactivePrompt) return;
    
    try {
      await streaming.submitInteractiveResponse({
        variables: {
          input: {
            executionId: executionIdRef.current,
            nodeId: interactivePrompt.nodeId,
            response
          }
        }
      });
      state.setInteractivePrompt(null);
    } catch (error) {
      if (showToasts) {
        toast.error(`Failed to submit response: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  }, [streaming, interactivePrompt, showToasts, state]);

  // UI Helpers
  const formatTimeHelper = useCallback((startTime: Date | null, endTime: Date | null): string => {
    return formatTime(startTime, endTime, formatDuration);
  }, [formatDuration]);

  const getNodeExecutionState = useCallback((nodeIdStr: string) => {
    return nodeStates[nodeIdStr];
  }, [nodeStates]);

  // Update progress
  useEffect(() => {
    updateProgress(execution.totalNodes, execution.completedNodes);
  }, [execution.completedNodes, execution.totalNodes, updateProgress]);

  // Compatibility properties
  const nodeRunningStates = React.useMemo(() => {
    const states: Record<string, boolean> = {};
    if (executionActions.runningNodes instanceof Set) {
      executionActions.runningNodes.forEach((nodeId: NodeID) => {
        states[nodeId] = true;
      });
    }
    return states;
  }, [executionActions.runningNodes]);

  // Connect to existing execution (for monitor mode with executionId)
  const connectToExecutionWithStore = useCallback((executionIdStr: string, totalNodes?: number) => {
    const nodesArray = Array.from(executionActions.nodes.values());
    connectToExecution(executionIdStr, totalNodes || nodesArray.length);
    executionActions.startExecution(executionIdStr);
    onUpdate?.({ type: EventType.EXECUTION_STATUS_CHANGED, execution_id: executionId(executionIdStr), timestamp: new Date().toISOString() });
  }, [connectToExecution, executionActions, onUpdate]);

  return {
    // State
    execution,
    nodeStates,
    isRunning: execution.isRunning,
    isReconnecting: false, // GraphQL handles reconnection automatically
    progress,
    duration,
    
    // Execution Actions
    execute,
    connectToExecution: connectToExecutionWithStore,
    abort,
    
    // Node Actions
    pauseNode,
    resumeNode,
    skipNode,
    
    // Interactive Prompt
    interactivePrompt,
    respondToPrompt,
    
    // UI Helpers
    formatTime: formatTimeHelper,
    getNodeIcon,
    getNodeColor,
    getNodeExecutionState,
    
    // Store integration
    currentRunningNode: currentRunningNodeRef.current,
    nodeRunningStates,
    runContext: runContextRef.current,
    skippedNodes: skippedNodesRef.current,
    runningNodes: executionActions.runningNodes,
    nodes: Array.from(executionActions.nodes.values()),
  };
}