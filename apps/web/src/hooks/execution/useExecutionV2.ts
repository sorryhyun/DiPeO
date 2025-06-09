/**
 * useExecutionV2 - Refactored execution hook combining state, socket, and UI
 * 
 * This is the main entry point that combines all execution-related functionality
 * in a clean, modular way.
 */

import { useCallback, useEffect, useRef } from 'react';
import { useExecutionState, type NodeStateV2 } from './useExecutionState';
import { useWebSocketEventBus } from '../useWebSocketEventBus';
import { useExecutionUI } from './useExecutionUI';
import { useExecutionStore } from '@/stores/executionStore';
import { useCanvasSelectors } from '../useStoreSelectors';
import type { DomainDiagram, DomainNode } from '@/types/domain';
import type { InteractivePromptData, ExecutionOptions, ExecutionUpdate } from '@/types/runtime';
import type { NodeID } from '@/types/branded';
import {NodeKind} from "@/types";

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
  execute: (diagram?: DomainDiagram, options?: ExecutionOptions) => Promise<void>;
  pauseNode: (nodeId: NodeID) => void;
  resumeNode: (nodeId: NodeID) => void;
  skipNode: (nodeId: NodeID) => void;
  abort: () => void;
  respondToPrompt: (nodeId: NodeID, response: string) => void;
  
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
  
  // Initialize WebSocket Event Bus
  const { 
    isConnected, 
    isReconnecting, 
    send, 
    on, 
    connect, 
    disconnect,
    waitForConnection 
  } = useWebSocketEventBus({ autoConnect, debug });
  
  // Track current execution ID
  const executionIdRef = useRef<string | null>(null);

  // Register event handlers
  useEffect(() => {
    // Execution events
    on('execution_started', (data: any) => {
      executionIdRef.current = data.execution_id;
      state.startExecution(data.execution_id, data.total_nodes || 0);
      ui.showExecutionStart(data.execution_id, data.total_nodes || 0);
      executionStore.setRunContext({});
      onUpdate?.({ type: 'execution_started', ...data });
    });

    on('execution_complete', (data: any) => {
      executionIdRef.current = null;
      const duration = state.executionState.startTime 
        ? (new Date().getTime() - state.executionState.startTime.getTime()) / 1000
        : 0;
      state.completeExecution(data.total_tokens);
      ui.showExecutionComplete(data.execution_id, duration, data.total_tokens);
      onUpdate?.({ type: 'execution_complete', ...data });
    });

    on('execution_error', (data: any) => {
      executionIdRef.current = null;
      state.errorExecution(data.error);
      ui.showExecutionError(data.error);
      onUpdate?.({ type: 'execution_error', ...data });
    });

    on('execution_aborted', (data: any) => {
      executionIdRef.current = null;
      state.abortExecution();
      ui.showExecutionError('Execution aborted');
      onUpdate?.({ type: 'execution_aborted', ...data });
    });

    // Node events
    on('node_start', (data: any) => {
      state.startNode(data.node_id);
      ui.showNodeStart(data.node_id, data.node_type);
      executionStore.addRunningNode(data.node_id);
      executionStore.setCurrentRunningNode(data.node_id);
      onUpdate?.({ type: 'node_start', ...data });
    });

    on('node_progress', (data: any) => {
      state.updateNodeProgress(data.node_id, data);
      onUpdate?.({ type: 'node_progress', ...data });
    });

    on('node_complete', (data: any) => {
      const nodeType = nodes.find((n: DomainNode) => n.id === data.node_id)?.type || 'unknown';
      state.completeNode(data.node_id, data.token_count);
      ui.showNodeComplete(data.node_id, nodeType);
      executionStore.removeRunningNode(data.node_id);
      
      // Update context if output is provided
      if (data.output && typeof data.output === 'object') {
        executionStore.setRunContext(data.output as Record<string, unknown>);
      }
      onUpdate?.({ type: 'node_complete', ...data });
    });

    on('node_skipped', (data: any) => {
      state.skipNode(data.node_id, data.reason);
      ui.showNodeSkipped(data.node_id, data.reason);
      executionStore.addSkippedNode(data.node_id, data.reason || 'Unknown reason');
      executionStore.removeRunningNode(data.node_id);
      onUpdate?.({ type: 'node_skipped', ...data });
    });

    on('node_error', (data: any) => {
      state.errorNode(data.node_id, data.error);
      ui.showNodeError(data.node_id, data.error);
      executionStore.removeRunningNode(data.node_id);
      onUpdate?.({ type: 'node_error', ...data });
    });

    on('node_paused', (data: any) => {
      state.pauseNode(data.node_id);
      onUpdate?.({ type: 'node_paused', ...data });
    });

    on('node_resumed', (data: any) => {
      state.resumeNode(data.node_id);
      onUpdate?.({ type: 'node_resumed', ...data });
    });

    on('interactive_prompt_request', (data: any) => {
      ui.setInteractivePrompt(data);
      onUpdate?.({ type: 'interactive_prompt_request', ...data });
    });
  }, [on, state, ui, executionStore, nodes, onUpdate]);

  // Update execution progress
  useEffect(() => {
    if (state.executionState.totalNodes > 0) {
      // Progress calculation: (state.executionState.completedNodes / state.executionState.totalNodes) * 100
      // Could be exposed if needed in the future
    }
  }, [state.executionState.completedNodes, state.executionState.totalNodes]);

  // Execute diagram
  const execute = useCallback(async (diagram?: DomainDiagram, options?: ExecutionOptions) => {
    // Reset state before starting
    state.resetState();
    executionStore.setRunContext({});
    executionStore.runningNodes.forEach((nodeId: NodeID) => executionStore.removeRunningNode(nodeId));
    ui.clearInteractivePrompt();
    
    try {
      await waitForConnection();
      send({
        type: 'execute_diagram',
        diagram,
        options
      });
    } catch (error) {
      console.error('Execution failed:', error);
      throw error;
    }
  }, [send, waitForConnection, state, executionStore, ui]);

  // Control actions
  const pauseNode = useCallback((nodeId: NodeID) => {
    send({
      type: 'pause_node',
      node_id: nodeId
    });
  }, [send]);

  const resumeNode = useCallback((nodeId: NodeID) => {
    send({
      type: 'resume_node',
      node_id: nodeId
    });
  }, [send]);

  const skipNode = useCallback((nodeId: NodeID) => {
    send({
      type: 'skip_node',
      node_id: nodeId
    });
  }, [send]);

  const abort = useCallback(() => {
    if (executionIdRef.current) {
      send({
        type: 'abort_execution',
        execution_id: executionIdRef.current
      });
    }
    state.abortExecution();
    executionStore.runningNodes.forEach((nodeId: NodeID) => executionStore.removeRunningNode(nodeId));
  }, [send, state, executionStore]);

  const respondToPrompt = useCallback((nodeId: NodeID, response: string) => {
    send({
      type: 'interactive_response',
      node_id: nodeId,
      response
    });
    ui.clearInteractivePrompt();
  }, [send, ui]);

  return {
    // Connection state
    isConnected,
    isReconnecting,
    
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
    pauseNode,
    resumeNode,
    skipNode,
    abort,
    respondToPrompt,
    
    // Connection actions
    connect,
    disconnect,
    
    // UI helpers
    formatExecutionTime: ui.formatExecutionTime,
    formatTokenCount: ui.formatTokenCount,
    getNodeStatusIcon: ui.getNodeStatusIcon,
    getNodeStatusColor: ui.getNodeStatusColor
  };
}