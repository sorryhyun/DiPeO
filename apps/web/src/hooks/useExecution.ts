/**
 * useExecution - Consolidated execution hook combining state, WebSocket, and UI
 * 
 * This hook centralizes all execution-related functionality that was previously
 * split across useExecutionState, useExecutionUI, and useExecutionV2.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { useShallow } from 'zustand/react/shallow';
import { useWebSocketEventBus } from './useWebSocketEventBus';
import { useCanvasOperations } from './useCanvasOperations';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import { onWebSocketEvent } from '@/utils/websocket/event-bus';
import type { DomainDiagram, InteractivePromptData, ExecutionOptions, ExecutionUpdate, NodeID } from '@/types';
import { NodeKind } from '@/types/primitives/enums';
import { createCommonStoreSelector } from '@/stores/selectorFactory';
import { NODE_ICONS, NODE_COLORS } from '@/config/nodeMeta';

// Types

export interface ExecutionState {
  isRunning: boolean;
  executionId: string | null;
  totalNodes: number;
  completedNodes: number;
  currentNode: string | null;
  startTime: Date | null;
  endTime: Date | null;
  error: string | null;
}

export interface NodeState {
  status: 'pending' | 'running' | 'completed' | 'skipped' | 'error' | 'paused';
  startTime: Date | null;
  endTime: Date | null;
  progress?: string;
  error?: string;
  tokenCount?: number;
  skipReason?: string;
}

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
  execution: ExecutionState;
  nodeStates: Record<string, NodeState>;
  isRunning: boolean;
  isReconnecting: boolean;
  progress: number;
  duration: string;
  
  // Execution Actions
  execute: (diagram?: DomainDiagram, options?: ExecutionOptions) => Promise<void>;
  abort: () => void;
  
  // Node Actions
  pauseNode: (nodeId: string) => void;
  resumeNode: (nodeId: string) => void;
  skipNode: (nodeId: string) => void;
  
  // Interactive Prompt
  interactivePrompt: InteractivePromptData | null;
  respondToPrompt: (response: string) => void;
  
  // Connection
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  
  // UI Helpers
  formatTime: (startTime: Date | null, endTime: Date | null) => string;
  getNodeIcon: (nodeType: string) => string;
  getNodeColor: (nodeType: string) => string;
  getNodeExecutionState: (nodeId: string) => NodeState | undefined;
  
  // Store integration
  currentRunningNode: string | null;
  nodeRunningStates: Record<string, boolean>;
  runContext: Record<string, unknown>;
  skippedNodes: Array<{ nodeId: string; reason: string }>;
  
  // Additional properties for compatibility
  runningNodes: Set<NodeID>;
  nodes?: any[];
}

// ========== Constants ==========

const initialExecutionState: ExecutionState = {
  isRunning: false,
  executionId: null,
  totalNodes: 0,
  completedNodes: 0,
  currentNode: null,
  startTime: null,
  endTime: null,
  error: null,
};

// Node visualization constants are now imported from nodeMeta

// ========== Main Hook ==========

export function useExecution(options: UseExecutionOptions = {}): UseExecutionReturn {
  const {
    autoConnect = false,
    showToasts = true,
    formatDuration = true,
    onUpdate
  } = options;
  
  // Memoized selector using common factory
  const executionStoreSelector = React.useMemo(createCommonStoreSelector, []);
  const executionActions = useUnifiedStore(useShallow(executionStoreSelector));
  
  // State
  const [execution, setExecution] = useState<ExecutionState>(initialExecutionState);
  const [nodeStates, setNodeStates] = useState<Record<string, NodeState>>({});
  const [interactivePrompt, setInteractivePrompt] = useState<InteractivePromptData | null>(null);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState('0s');
  
  // Refs
  const executionIdRef = useRef<string | null>(null);
  const durationInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<Date | null>(null);
  const runContextRef = useRef<Record<string, unknown>>({});
  const skippedNodesRef = useRef<Array<{ nodeId: string; reason: string }>>([]);
  const currentRunningNodeRef = useRef<string | null>(null);
  
  // Canvas operations
  const { nodes: canvasNodes } = useCanvasOperations();
  
  // WebSocket
  const {
    isConnected,
    isReconnecting,
    send,
    connect,
    disconnect,
    waitForConnection
  } = useWebSocketEventBus();
  
  // ========== State Management Functions ==========
  
  const startExecution = useCallback((executionId: string, totalNodes: number) => {
    const now = new Date();
    startTimeRef.current = now;
    
    setExecution({
      isRunning: true,
      executionId,
      totalNodes,
      completedNodes: 0,
      currentNode: null,
      startTime: now,
      endTime: null,
      error: null,
    });
    
    // Start duration timer
    if (formatDuration) {
      durationInterval.current = setInterval(() => {
        if (startTimeRef.current) {
          const elapsed = Date.now() - startTimeRef.current.getTime();
          const seconds = Math.floor(elapsed / 1000);
          const minutes = Math.floor(seconds / 60);
          
          if (minutes > 0) {
            setDuration(`${minutes}m ${seconds % 60}s`);
          } else {
            setDuration(`${seconds}s`);
          }
        }
      }, 1000);
    }
  }, [formatDuration]);
  
  const completeExecution = useCallback((totalTokens?: number) => {
    setExecution(prev => ({
      ...prev,
      isRunning: false,
      endTime: new Date(),
      error: null,
    }));
    
    if (durationInterval.current) {
      clearInterval(durationInterval.current);
      durationInterval.current = null;
    }
    
    if (showToasts) {
      const tokensMsg = totalTokens ? ` (${totalTokens.toLocaleString()} tokens)` : '';
      toast.success(`Execution completed${tokensMsg}`);
    }
  }, [showToasts]);
  
  const errorExecution = useCallback((error: string) => {
    setExecution(prev => ({
      ...prev,
      isRunning: false,
      endTime: new Date(),
      error,
    }));
    
    if (durationInterval.current) {
      clearInterval(durationInterval.current);
      durationInterval.current = null;
    }
    
    if (showToasts) {
      toast.error(`Execution failed: ${error}`);
    }
  }, [showToasts]);
  
  const startNode = useCallback((nodeId: string, nodeType: string) => {
    setExecution(prev => ({
      ...prev,
      currentNode: nodeId,
    }));
    
    setNodeStates(prev => ({
      ...prev,
      [nodeId]: {
        status: 'running',
        startTime: new Date(),
        endTime: null,
      }
    }));
    
    if (showToasts) {
      const nodeIcon = NODE_ICONS[nodeType as NodeKind] || '📦';
      const node = canvasNodes.find(n => n.id === nodeId);
      const nodeLabel = node?.data?.label || nodeId.slice(0, 8);
      toast.info(`${nodeIcon} Running: ${nodeLabel}...`);
    }
  }, [showToasts, canvasNodes]);
  
  const completeNode = useCallback((nodeId: string, tokenCount?: number) => {
    setExecution(prev => ({
      ...prev,
      completedNodes: prev.completedNodes + 1,
      currentNode: prev.currentNode === nodeId ? null : prev.currentNode,
    }));
    
    setNodeStates(prev => ({
      ...prev,
      [nodeId]: {
        ...(prev[nodeId] || { startTime: null, endTime: null }),
        status: 'completed' as const,
        endTime: new Date(),
        tokenCount,
      }
    }));
  }, []);
  
  // ========== Stable Event Handlers ==========
  
  // Create stable handler references using useCallback
  const handleExecutionStarted = useCallback((data: any) => {
    executionIdRef.current = data.execution_id;
    startExecution(data.execution_id, data.total_nodes || 0);
    runContextRef.current = {};
    skippedNodesRef.current = [];
    currentRunningNodeRef.current = null;
    executionActions.startExecution(data.execution_id);
    onUpdate?.({ type: 'execution_started', ...data });
  }, [startExecution, executionActions, onUpdate]);
  
  const handleExecutionComplete = useCallback((data: any) => {
    executionIdRef.current = null;
    completeExecution(data.total_tokens);
    executionActions.stopExecution();
    onUpdate?.({ type: 'execution_complete', ...data });
  }, [completeExecution, executionActions, onUpdate]);
  
  const handleExecutionError = useCallback((data: any) => {
    executionIdRef.current = null;
    errorExecution(data.error);
    executionActions.stopExecution();
    onUpdate?.({ type: 'execution_error', ...data });
  }, [errorExecution, executionActions, onUpdate]);
  
  const handleExecutionAborted = useCallback(() => {
    executionIdRef.current = null;
    errorExecution('Execution aborted');
    executionActions.stopExecution();
    onUpdate?.({ type: 'execution_aborted' });
  }, [errorExecution, executionActions, onUpdate]);
  
  const handleNodeStart = useCallback((data: any) => {
    startNode(data.node_id, data.node_type);
    currentRunningNodeRef.current = data.node_id;
    executionActions.updateNodeExecution(data.node_id as NodeID, {
      status: 'running',
      timestamp: Date.now()
    });
    onUpdate?.({ type: 'node_start', ...data });
  }, [startNode, executionActions, onUpdate]);
  
  const handleNodeProgress = useCallback((data: any) => {
    setNodeStates(prev => ({
      ...prev,
      [data.node_id]: {
        ...prev[data.node_id],
        progress: data.progress
      }
    }));
    onUpdate?.({ type: 'node_progress', ...data });
  }, [onUpdate]);
  
  const handleNodeComplete = useCallback((data: any) => {
    completeNode(data.node_id, data.token_count);
    if (currentRunningNodeRef.current === data.node_id) {
      currentRunningNodeRef.current = null;
    }
    executionActions.updateNodeExecution(data.node_id as NodeID, {
      status: 'completed',
      timestamp: Date.now()
    });
    
    if (data.output && typeof data.output === 'object') {
      runContextRef.current = { ...runContextRef.current, ...data.output };
    }
    onUpdate?.({ type: 'node_complete', ...data });
  }, [completeNode, executionActions, onUpdate]);
  
  const handleNodeSkipped = useCallback((data: any) => {
    setExecution(prev => ({
      ...prev,
      completedNodes: prev.completedNodes + 1
    }));
    
    setNodeStates(prev => ({
      ...prev,
      [data.node_id]: {
        ...(prev[data.node_id] || { startTime: null, endTime: null }),
        status: 'skipped' as const,
        endTime: new Date(),
        skipReason: data.reason
      }
    }));
    
    skippedNodesRef.current.push({ nodeId: data.node_id, reason: data.reason || 'Unknown reason' });
    executionActions.updateNodeExecution(data.node_id as NodeID, {
      status: 'skipped',
      timestamp: Date.now()
    });
    
    if (showToasts && data.reason) {
      toast.warning(`Node ${data.node_id.slice(0, 8)}... skipped: ${data.reason}`);
    }
    
    onUpdate?.({ type: 'node_skipped', ...data });
  }, [executionActions, showToasts, onUpdate]);
  
  const handleNodeError = useCallback((data: any) => {
    setNodeStates(prev => ({
      ...prev,
      [data.node_id]: {
        ...(prev[data.node_id] || { startTime: null, endTime: null }),
        status: 'error' as const,
        endTime: new Date(),
        error: data.error
      }
    }));
    
    executionActions.updateNodeExecution(data.node_id as NodeID, {
      status: 'failed',
      timestamp: Date.now(),
      error: data.error
    });
    
    if (showToasts) {
      toast.error(`Node ${data.node_id.slice(0, 8)}... failed: ${data.error}`);
    }
    
    onUpdate?.({ type: 'node_error', ...data });
  }, [executionActions, showToasts, onUpdate]);
  
  const handleNodePaused = useCallback((data: any) => {
    setNodeStates(prev => ({
      ...prev,
      [data.node_id]: {
        ...(prev[data.node_id] || { startTime: null, endTime: null }),
        status: 'paused' as const
      }
    }));
    onUpdate?.({ type: 'node_paused', ...data });
  }, [onUpdate]);
  
  const handleNodeResumed = useCallback((data: any) => {
    setNodeStates(prev => ({
      ...prev,
      [data.node_id]: {
        ...(prev[data.node_id] || { startTime: null, endTime: null }),
        status: 'running' as const
      }
    }));
    onUpdate?.({ type: 'node_resumed', ...data });
  }, [onUpdate]);
  
  const handleInteractivePrompt = useCallback((data: any) => {
    setInteractivePrompt(data);
    onUpdate?.({ type: 'interactive_prompt_request', ...data });
  }, [onUpdate]);
  
  // Register WebSocket event handlers using stable references
  useEffect(() => {
    const unsubscribers = [
      onWebSocketEvent('execution_started', handleExecutionStarted),
      onWebSocketEvent('execution_complete', handleExecutionComplete),
      onWebSocketEvent('execution_error', handleExecutionError),
      onWebSocketEvent('execution_aborted', handleExecutionAborted),
      onWebSocketEvent('node_start', handleNodeStart),
      onWebSocketEvent('node_progress', handleNodeProgress),
      onWebSocketEvent('node_complete', handleNodeComplete),
      onWebSocketEvent('node_skipped', handleNodeSkipped),
      onWebSocketEvent('node_error', handleNodeError),
      onWebSocketEvent('node_paused', handleNodePaused),
      onWebSocketEvent('node_resumed', handleNodeResumed),
      onWebSocketEvent('interactive_prompt_request', handleInteractivePrompt)
    ];
    
    // Cleanup function
    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [
    handleExecutionStarted,
    handleExecutionComplete,
    handleExecutionError,
    handleExecutionAborted,
    handleNodeStart,
    handleNodeProgress,
    handleNodeComplete,
    handleNodeSkipped,
    handleNodeError,
    handleNodePaused,
    handleNodeResumed,
    handleInteractivePrompt
  ]);
  
  // ========== Main Actions ==========
  
  const execute = useCallback(async (diagram?: DomainDiagram, options?: ExecutionOptions) => {
    // Reset state
    setExecution(initialExecutionState);
    setNodeStates({});
    setInteractivePrompt(null);
    setProgress(0);
    setDuration('0s');
    runContextRef.current = {};
    skippedNodesRef.current = [];
    currentRunningNodeRef.current = null;
    
    try {
      await waitForConnection();
      
      const message = diagram ? {
        type: 'execute_diagram',
        diagram: {
          ...diagram,
          // Ensure we're sending arrays (nodes/arrows/persons are Records)
          nodes: Object.values(diagram.nodes),
          arrows: Object.values(diagram.arrows),
          persons: Object.values(diagram.persons),
        },
        ...options
      } : {
        type: 'execute_current',
        ...options
      };
      
      send(message);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to execute diagram';
      errorExecution(errorMessage);
      throw error;
    }
  }, [send, waitForConnection, errorExecution]);
  
  const pauseNode = useCallback((nodeId: string) => {
    send({ type: 'pause_node', node_id: nodeId });
  }, [send]);
  
  const resumeNode = useCallback((nodeId: string) => {
    send({ type: 'resume_node', node_id: nodeId });
  }, [send]);
  
  const skipNode = useCallback((nodeId: string) => {
    send({ type: 'skip_node', node_id: nodeId });
  }, [send]);
  
  const abort = useCallback(() => {
    if (executionIdRef.current) {
      send({ type: 'abort_execution', execution_id: executionIdRef.current });
    } else if (execution.isRunning) {
      // Fallback abort
      errorExecution('Execution aborted');
      executionActions.stopExecution();
    }
  }, [send, errorExecution, executionActions, execution.isRunning]);
  
  const respondToPrompt = useCallback((response: string) => {
    send({
      type: 'interactive_prompt_response',
      execution_id: executionIdRef.current,
      response
    });
    setInteractivePrompt(null);
  }, [send]);
  
  // ========== UI Helpers ==========
  
  const formatTime = useCallback((startTime: Date | null, endTime: Date | null): string => {
    if (!startTime) return formatDuration ? '0s' : '-';
    
    const end = endTime || new Date();
    const elapsed = Math.floor((end.getTime() - startTime.getTime()) / 1000);
    
    if (!formatDuration) return `${elapsed}s`;
    
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    
    return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
  }, [formatDuration]);
  
  const getNodeIcon = useCallback((nodeType: string): string => {
    return NODE_ICONS[nodeType as NodeKind] || '📦';
  }, []);
  
  const getNodeColor = useCallback((nodeType: string): string => {
    return NODE_COLORS[nodeType as NodeKind] || '#6b7280';
  }, []);
  
  // ========== Effects ==========
  
  // Auto-connect on mount if requested
  useEffect(() => {
    if (autoConnect && !isConnected && !isReconnecting) {
      connect();
    }
  }, [autoConnect, isConnected, isReconnecting, connect]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
      }
    };
  }, []);
  
  // Track current node name for UI
  const currentNodeName = React.useMemo(() => {
    if (!execution.currentNode) return null;
    const node = canvasNodes.find(n => n.id === execution.currentNode);
    return node?.data?.label || execution.currentNode;
  }, [execution.currentNode, canvasNodes]);
  
  // Update progress
  useEffect(() => {
    if (currentNodeName) {
      const node = canvasNodes.find(n => n.id === execution.currentNode);
      const nodeType = node?.type as NodeKind;
      const nodeIcon = NODE_ICONS[nodeType] || '📦';
      // Progress message with icon and name
      if (showToasts) {
        console.log(`${nodeIcon} Processing: ${currentNodeName}`);
      }
    }
    
    // Update progress
    if (execution.totalNodes > 0) {
      setProgress(Math.round(((execution.completedNodes + 1) / execution.totalNodes) * 100));
    }
  }, [currentNodeName, execution.completedNodes, execution.totalNodes, canvasNodes, showToasts]);
  
  // ========== Return ==========
  
  const getNodeExecutionState = useCallback((nodeId: string): NodeState | undefined => {
    return nodeStates[nodeId];
  }, [nodeStates]);
  
  const nodeRunningStates = React.useMemo(() => {
    const states: Record<string, boolean> = {};
    if (executionActions.runningNodes instanceof Set) {
      executionActions.runningNodes.forEach((nodeId: NodeID) => {
        states[nodeId] = true;
      });
    }
    return states;
  }, [executionActions.runningNodes]);
  
  return {
    // State
    execution,
    nodeStates,
    isRunning: execution.isRunning,
    isReconnecting,
    progress,
    duration,
    
    // Execution Actions
    execute,
    abort,
    
    // Node Actions
    pauseNode,
    resumeNode,
    skipNode,
    
    // Interactive Prompt
    interactivePrompt,
    respondToPrompt,
    
    // Connection
    isConnected,
    connect: async () => connect(),
    disconnect,
    
    // UI Helpers
    formatTime,
    getNodeIcon,
    getNodeColor,
    getNodeExecutionState,
    
    // Store integration
    currentRunningNode: currentRunningNodeRef.current,
    nodeRunningStates,
    runContext: runContextRef.current,
    skippedNodes: skippedNodesRef.current,
    
    // Additional properties for compatibility
    runningNodes: executionActions.runningNodes,
    nodes: canvasNodes,
  };
}