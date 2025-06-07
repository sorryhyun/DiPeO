/**
 * useExecutionV2 - Refactored execution hook combining state, socket, and UI
 * 
 * This is the main entry point that combines all execution-related functionality
 * in a clean, modular way.
 */

import { useCallback, useEffect } from 'react';
import { useExecutionState, type NodeStateV2 } from './useExecutionState';
import { useExecutionSocket } from './useExecutionSocket';
import { useExecutionUI } from './useExecutionUI';
import { useExecutionStore } from '@/stores/executionStore';
import { useCanvasSelectors } from '../useStoreSelectors';
import type { DiagramState, InteractivePromptData } from '@/types';
import type { ExecutionOptions, ExecutionUpdate } from '@/types/api';

export interface UseExecutionV2Options {
  autoConnect?: boolean;
  enableMonitoring?: boolean;
  debug?: boolean;
  showToasts?: boolean;
  onUpdate?: (update: ExecutionUpdate) => void;
}

export interface UseExecutionV2Return {
  // Connection state
  isConnected: boolean;
  isReconnecting: boolean;
  
  // Execution state
  isRunning: boolean;
  executionId: string | null;
  executionState: ReturnType<typeof useExecutionState>['executionState'];
  nodeStates: ReturnType<typeof useExecutionState>['nodeStates'];
  
  // UI state
  executionProgress: number;
  executionDuration: string;
  currentNodeName: string | null;
  interactivePrompt: InteractivePromptData | null;
  
  // Main actions
  execute: (diagram?: DiagramState, options?: ExecutionOptions) => Promise<void>;
  pauseNode: (nodeId: string) => void;
  resumeNode: (nodeId: string) => void;
  skipNode: (nodeId: string) => void;
  abort: () => void;
  respondToPrompt: (nodeId: string, response: string) => void;
  
  // Connection actions
  connect: () => void;
  disconnect: () => void;
  
  // UI helpers
  formatExecutionTime: (startTime: Date | null, endTime: Date | null) => string;
  formatTokenCount: (tokens: number) => string;
  getNodeStatusIcon: (status: NodeStateV2['status']) => string;
  getNodeStatusColor: (status: NodeStateV2['status']) => string;
}

export function useExecutionV2(options: UseExecutionV2Options = {}): UseExecutionV2Return {
  const { 
    autoConnect = true, 
    enableMonitoring: _enableMonitoring = false, 
    debug = false,
    showToasts = true,
    onUpdate
  } = options;

  // Get store actions
  const executionStore = useExecutionStore();
  const { nodes } = useCanvasSelectors();

  // Initialize sub-hooks
  const state = useExecutionState();
  const ui = useExecutionUI({ showToasts });
  
  // Initialize socket with callbacks
  const socket = useExecutionSocket({
    autoConnect,
    debug,
    onUpdate,
    
    // Execution events
    onExecutionStart: (executionId, totalNodes) => {
      state.startExecution(executionId, totalNodes);
      ui.showExecutionStart(executionId, totalNodes);
      executionStore.setRunContext({});
    },
    
    onExecutionComplete: (executionId, totalTokens) => {
      const duration = state.executionState.startTime 
        ? (new Date().getTime() - state.executionState.startTime.getTime()) / 1000
        : 0;
      state.completeExecution(totalTokens);
      ui.showExecutionComplete(executionId, duration, totalTokens);
    },
    
    onExecutionError: (_executionId, error) => {
      state.errorExecution(error);
      ui.showExecutionError(error);
    },
    
    onExecutionAbort: (_executionId) => {
      state.abortExecution();
      ui.showExecutionError('Execution aborted');
    },
    
    // Node events
    onNodeStart: (nodeId, nodeType) => {
      state.startNode(nodeId);
      ui.showNodeStart(nodeId, nodeType);
      executionStore.addRunningNode(nodeId);
      executionStore.setCurrentRunningNode(nodeId);
    },
    
    onNodeProgress: (nodeId, progress) => {
      state.updateNodeProgress(nodeId, progress);
    },
    
    onNodeComplete: (nodeId, output, tokenCount) => {
      const nodeType = nodes.find(n => n.id === nodeId)?.type || 'unknown';
      state.completeNode(nodeId, tokenCount);
      ui.showNodeComplete(nodeId, nodeType);
      executionStore.removeRunningNode(nodeId);
      
      // Update context if output is provided
      if (output && typeof output === 'object') {
        executionStore.setRunContext(output as Record<string, unknown>);
      }
    },
    
    onNodeSkipped: (nodeId, reason) => {
      state.skipNode(nodeId, reason);
      ui.showNodeSkipped(nodeId, reason);
      executionStore.addSkippedNode(nodeId, reason || 'Unknown reason');
      executionStore.removeRunningNode(nodeId);
    },
    
    onNodeError: (nodeId, error) => {
      state.errorNode(nodeId, error);
      ui.showNodeError(nodeId, error);
      executionStore.removeRunningNode(nodeId);
    },
    
    onNodePaused: (nodeId) => {
      state.pauseNode(nodeId);
    },
    
    onNodeResumed: (nodeId) => {
      state.resumeNode(nodeId);
    },
    
    onInteractivePrompt: (prompt) => {
      ui.setInteractivePrompt(prompt);
    }
  });

  // Update execution progress
  useEffect(() => {
    if (state.executionState.totalNodes > 0) {
      // Progress calculation: (state.executionState.completedNodes / state.executionState.totalNodes) * 100
      // Could be exposed if needed in the future
    }
  }, [state.executionState.completedNodes, state.executionState.totalNodes]);

  // Enhanced execute function
  const execute = useCallback(async (diagram?: DiagramState, options?: ExecutionOptions) => {
    // Reset state before starting
    state.resetState();
    executionStore.setRunContext({});
    executionStore.runningNodes.forEach(nodeId => executionStore.removeRunningNode(nodeId));
    ui.clearInteractivePrompt();
    
    try {
      await socket.execute(diagram, options);
    } catch (error) {
      console.error('Execution failed:', error);
      throw error;
    }
  }, [socket, state, executionStore, ui]);

  // Enhanced abort function
  const abort = useCallback(() => {
    socket.abort();
    state.abortExecution();
    executionStore.runningNodes.forEach(nodeId => executionStore.removeRunningNode(nodeId));
  }, [socket, state, executionStore]);

  // Enhanced respond to prompt
  const respondToPrompt = useCallback((nodeId: string, response: string) => {
    socket.respondToPrompt(nodeId, response);
    ui.clearInteractivePrompt();
  }, [socket, ui]);

  return {
    // Connection state
    isConnected: socket.isConnected,
    isReconnecting: socket.isReconnecting,
    
    // Execution state
    isRunning: state.executionState.isRunning,
    executionId: state.executionState.executionId,
    executionState: state.executionState,
    nodeStates: state.nodeStates,
    
    // UI state
    executionProgress: ui.executionProgress,
    executionDuration: ui.executionDuration,
    currentNodeName: ui.currentNodeName,
    interactivePrompt: ui.interactivePrompt,
    
    // Main actions
    execute,
    pauseNode: socket.pauseNode,
    resumeNode: socket.resumeNode,
    skipNode: socket.skipNode,
    abort,
    respondToPrompt,
    
    // Connection actions
    connect: socket.connect,
    disconnect: socket.disconnect,
    
    // UI helpers
    formatExecutionTime: ui.formatExecutionTime,
    formatTokenCount: ui.formatTokenCount,
    getNodeStatusIcon: ui.getNodeStatusIcon,
    getNodeStatusColor: ui.getNodeStatusColor
  };
}