/**
 * useExecution - Consolidated execution hook combining state, WebSocket, and UI
 * 
 * This hook centralizes all execution-related functionality that was previously
 * split across useExecutionState, useExecutionUI, and useExecutionV2.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { shallow } from 'zustand/shallow';
import { useWebSocketEventBus } from './useWebSocketEventBus';
import { useCanvasOperations } from './useCanvasOperations';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import type { DomainDiagram, InteractivePromptData, ExecutionOptions, ExecutionUpdate, NodeID } from '@/types';
import { NodeKind } from '@/types/primitives/enums';

// ========== Types ==========

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
  // Connection state
  isConnected: boolean;
  isReconnecting: boolean;
  
  // Execution state
  isRunning: boolean;
  executionId: string | null;
  execution: ExecutionState;
  nodes: Record<string, NodeState>;
  
  // Node-specific state
  getNodeExecutionState: (nodeId: NodeID) => {
    isRunning: boolean;
    isCurrentRunning: boolean;
    nodeRunningState: boolean;
    isSkipped: boolean;
    skipReason: string | undefined;
  };
  
  // Execution selectors
  runContext: Record<string, unknown>;
  runningNodes: NodeID[];
  currentRunningNode: NodeID | null;
  nodeRunningStates: Record<string, boolean>;
  skippedNodes: Record<string, { reason: string }>;
  
  // UI state
  progress: number;
  duration: string;
  currentNodeName: string | null;
  interactivePrompt: InteractivePromptData | null;
  
  // Main actions
  execute: (diagram?: DomainDiagram, options?: ExecutionOptions) => Promise<void>;
  pauseNode: (nodeId: NodeID) => void;
  resumeNode: (nodeId: NodeID) => void;
  skipNode: (nodeId: NodeID) => void;
  abort: () => void;
  respondToPrompt: (nodeId: NodeID, response: string) => void;
  
  // Execution actions
  addRunningNode: (nodeId: NodeID) => void;
  removeRunningNode: (nodeId: NodeID) => void;
  setCurrentRunningNode: (nodeId: NodeID | null) => void;
  setRunContext: (context: Record<string, unknown>) => void;
  addSkippedNode: (nodeId: NodeID, reason: string) => void;
  reset: () => void;
  
  // Connection actions
  connect: () => void;
  disconnect: () => void;
  
  // UI helpers
  formatTime: (startTime: Date | null, endTime: Date | null) => string;
  formatTokens: (tokens: number) => string;
  getNodeIcon: (status: NodeState['status']) => string;
  getNodeColor: (status: NodeState['status']) => string;
}

// ========== Initial States ==========

const initialExecutionState: ExecutionState = {
  isRunning: false,
  executionId: null,
  totalNodes: 0,
  completedNodes: 0,
  currentNode: null,
  startTime: null,
  endTime: null,
  error: null
};

const createDefaultNodeState = (): NodeState => ({
  status: 'pending',
  startTime: null,
  endTime: null
});

// ========== Helper Functions ==========

function formatTimeInternal(startTime: Date | null, endTime: Date | null, formatDuration: boolean): string {
  if (!startTime) return '0s';
  
  const end = endTime || new Date();
  const totalSeconds = Math.floor((end.getTime() - startTime.getTime()) / 1000);
  
  if (!formatDuration) return `${totalSeconds}s`;
  
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  } else {
    return `${seconds}s`;
  }
}

// ========== Main Hook ==========

// Track if WebSocket connection has been initialized globally
let globalConnectionInitialized = false;

export function useExecution(options: UseExecutionOptions = {}): UseExecutionReturn {
  const { 
    autoConnect = false, // Changed default to false 
    debug = false,
    showToasts = true,
    formatDuration = true,
    onUpdate
  } = options;

  // Store hooks
  const { nodes: canvasNodes } = useCanvasOperations();
  
  // Get execution actions from store
  const executionActions = useUnifiedStore(
    state => ({
      startExecution: state.startExecution,
      stopExecution: state.stopExecution,
      reset: () => {
        state.stopExecution();
        state.execution.nodeStates.clear();
        state.execution.context = {};
      },
      addRunningNode: (nodeId: NodeID) => {
        state.execution.runningNodes.add(nodeId);
      },
      removeRunningNode: (nodeId: NodeID) => {
        state.execution.runningNodes.delete(nodeId);
      },
      setCurrentRunningNode: (nodeId: NodeID | null) => {
        if (nodeId) {
          state.execution.runningNodes.clear();
          state.execution.runningNodes.add(nodeId);
        }
      },
      setRunContext: (context: Record<string, unknown>) => {
        state.execution.context = context;
      },
      addSkippedNode: (nodeId: NodeID, reason: string) => {
        state.updateNodeExecution(nodeId, { 
          status: 'skipped', 
          error: reason,
          timestamp: Date.now()
        });
      },
    }),
    shallow
  );
  
  // State
  const [execution, setExecution] = useState<ExecutionState>(initialExecutionState);
  const [nodeStates, setNodeStates] = useState<Record<string, NodeState>>({});
  const [interactivePrompt, setInteractivePrompt] = useState<InteractivePromptData | null>(null);
  const [currentNodeName, setCurrentNodeName] = useState<string | null>(null);
  
  // UI State
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState('0s');
  
  // Refs
  const executionIdRef = useRef<string | null>(null);
  const durationInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  // WebSocket - only auto-connect if not already initialized
  const shouldAutoConnect = autoConnect && !globalConnectionInitialized;
  if (shouldAutoConnect) {
    globalConnectionInitialized = true;
  }
  
  const { 
    isConnected, 
    isReconnecting, 
    send, 
    on, 
    connect, 
    disconnect,
    waitForConnection 
  } = useWebSocketEventBus({ autoConnect: shouldAutoConnect, debug });

  // ========== Execution Actions ==========

  const startExecution = useCallback((executionId: string, totalNodes: number) => {
    const now = new Date();
    setExecution({
      isRunning: true,
      executionId,
      totalNodes,
      completedNodes: 0,
      currentNode: null,
      startTime: now,
      endTime: null,
      error: null
    });
    setNodeStates({});
    setProgress(0);
    
    // Start duration timer
    if (durationInterval.current) clearInterval(durationInterval.current);
    durationInterval.current = setInterval(() => {
      const formattedTime = formatTimeInternal(now, null, formatDuration);
      setDuration(formattedTime);
    }, 1000);

    if (showToasts) {
      toast.info(`Execution started with ${totalNodes} nodes`);
    }
  }, [showToasts]);

  const completeExecution = useCallback((totalTokens?: number) => {
    setExecution(prev => ({
      ...prev,
      isRunning: false,
      currentNode: null,
      endTime: new Date(),
      error: null
    }));
    
    if (durationInterval.current) {
      clearInterval(durationInterval.current);
      durationInterval.current = null;
    }
    
    setProgress(100);
    
    if (showToasts) {
      const finalDuration = execution.startTime 
        ? (new Date().getTime() - execution.startTime.getTime()) / 1000
        : 0;
      const message = totalTokens 
        ? `Execution completed in ${finalDuration.toFixed(1)}s (${formatTokens(totalTokens)} tokens)`
        : `Execution completed in ${finalDuration.toFixed(1)}s`;
      toast.success(message);
    }
  }, [showToasts, execution.startTime]);

  const errorExecution = useCallback((error: string) => {
    setExecution(prev => ({
      ...prev,
      isRunning: false,
      currentNode: null,
      endTime: new Date(),
      error
    }));
    
    if (durationInterval.current) {
      clearInterval(durationInterval.current);
      durationInterval.current = null;
    }
    
    if (showToasts) {
      toast.error(`Execution failed: ${error}`);
    }
  }, [showToasts]);

  // ========== Node Actions ==========

  const startNode = useCallback((nodeId: string, nodeType: NodeKind) => {
    setExecution(prev => ({ ...prev, currentNode: nodeId }));
    setNodeStates(prev => ({
      ...prev,
      [nodeId]: {
        status: 'running',
        startTime: new Date(),
        endTime: null
      }
    }));
    
    setCurrentNodeName(`${nodeType} (${nodeId.slice(0, 8)}...)`);
    
    if (showToasts && nodeType === 'user_response') {
      toast.info('Waiting for user input...');
    }
  }, [showToasts]);

  const completeNode = useCallback((nodeId: string, tokenCount?: number) => {
    setExecution(prev => ({
      ...prev,
      completedNodes: prev.completedNodes + 1,
      currentNode: prev.currentNode === nodeId ? null : prev.currentNode
    }));
    
    setNodeStates(prev => {
      const currentNode = prev[nodeId] || createDefaultNodeState();
      return {
        ...prev,
        [nodeId]: {
          ...currentNode,
          status: 'completed' as const,
          endTime: new Date(),
          tokenCount
        }
      };
    });
    
    if (currentNodeName?.includes(nodeId.slice(0, 8))) {
      setCurrentNodeName(null);
    }
    
    // Update progress
    if (execution.totalNodes > 0) {
      setProgress(Math.round(((execution.completedNodes + 1) / execution.totalNodes) * 100));
    }
  }, [currentNodeName, execution.completedNodes, execution.totalNodes]);

  // ========== Event Handlers ==========

  useEffect(() => {
    const handlers = {
      'execution_started': (data: any) => {
        executionIdRef.current = data.execution_id;
        startExecution(data.execution_id, data.total_nodes || 0);
        executionActions.setRunContext({});
        onUpdate?.({ type: 'execution_started', ...data });
      },
      
      'execution_complete': (data: any) => {
        executionIdRef.current = null;
        completeExecution(data.total_tokens);
        onUpdate?.({ type: 'execution_complete', ...data });
      },
      
      'execution_error': (data: any) => {
        executionIdRef.current = null;
        errorExecution(data.error);
        onUpdate?.({ type: 'execution_error', ...data });
      },
      
      'execution_aborted': () => {
        executionIdRef.current = null;
        errorExecution('Execution aborted');
        onUpdate?.({ type: 'execution_aborted' });
      },
      
      'node_start': (data: any) => {
        startNode(data.node_id, data.node_type);
        executionActions.addRunningNode(data.node_id);
        executionActions.setCurrentRunningNode(data.node_id);
        onUpdate?.({ type: 'node_start', ...data });
      },
      
      'node_progress': (data: any) => {
        setNodeStates(prev => ({
          ...prev,
          [data.node_id]: {
            ...prev[data.node_id],
            progress: data.progress
          }
        }));
        onUpdate?.({ type: 'node_progress', ...data });
      },
      
      'node_complete': (data: any) => {
        completeNode(data.node_id, data.token_count);
        executionActions.removeRunningNode(data.node_id);
        
        if (data.output && typeof data.output === 'object') {
          executionActions.setRunContext(data.output as Record<string, unknown>);
        }
        onUpdate?.({ type: 'node_complete', ...data });
      },
      
      'node_skipped': (data: any) => {
        setExecution(prev => ({
          ...prev,
          completedNodes: prev.completedNodes + 1
        }));
        
        setNodeStates(prev => ({
          ...prev,
          [data.node_id]: {
            ...prev[data.node_id],
            status: 'skipped',
            endTime: new Date(),
            skipReason: data.reason
          }
        }));
        
        executionActions.addSkippedNode(data.node_id, data.reason || 'Unknown reason');
        executionActions.removeRunningNode(data.node_id);
        
        if (showToasts && data.reason) {
          toast.warning(`Node ${data.node_id.slice(0, 8)}... skipped: ${data.reason}`);
        }
        
        onUpdate?.({ type: 'node_skipped', ...data });
      },
      
      'node_error': (data: any) => {
        setNodeStates(prev => ({
          ...prev,
          [data.node_id]: {
            ...prev[data.node_id],
            status: 'error',
            endTime: new Date(),
            error: data.error
          }
        }));
        
        executionActions.removeRunningNode(data.node_id);
        
        if (showToasts) {
          toast.error(`Node ${data.node_id.slice(0, 8)}... failed: ${data.error}`);
        }
        
        onUpdate?.({ type: 'node_error', ...data });
      },
      
      'node_paused': (data: any) => {
        setNodeStates(prev => ({
          ...prev,
          [data.node_id]: {
            ...prev[data.node_id],
            status: 'paused'
          }
        }));
        onUpdate?.({ type: 'node_paused', ...data });
      },
      
      'node_resumed': (data: any) => {
        setNodeStates(prev => ({
          ...prev,
          [data.node_id]: {
            ...prev[data.node_id],
            status: 'running'
          }
        }));
        onUpdate?.({ type: 'node_resumed', ...data });
      },
      
      'interactive_prompt_request': (data: any) => {
        setInteractivePrompt(data);
        onUpdate?.({ type: 'interactive_prompt_request', ...data });
      }
    };
    
    // Register all handlers
    Object.entries(handlers).forEach(([event, handler]) => {
      on(event, handler);
    });
  }, [on, startExecution, completeExecution, errorExecution, startNode, completeNode, 
      executionActions, canvasNodes, showToasts, onUpdate]);

  // ========== Main Actions ==========

  const execute = useCallback(async (diagram?: DomainDiagram, options?: ExecutionOptions) => {
    // Reset state
    setExecution(initialExecutionState);
    setNodeStates({});
    setInteractivePrompt(null);
    setProgress(0);
    setDuration('0s');
    executionActions.setRunContext({});
    executionActions.reset();
    
    try {
      await waitForConnection();
      
      // Convert DomainDiagram to backend format if provided
      let backendDiagram = diagram;
      if (diagram) {
        // Backend expects nodes and arrows as arrays, but persons as object
         
        backendDiagram = {
          nodes: Object.values(diagram.nodes || {}),
          arrows: Object.values(diagram.arrows || {}),
          persons: diagram.persons || {},  // Keep as object
          api_keys: diagram.apiKeys || {}   // Backend expects snake_case
        } as any;
      }
      
      send({
        type: 'execute_diagram',
        diagram: backendDiagram,
        options
      });
    } catch (error) {
      console.error('Execution failed:', error);
      throw error;
    }
  }, [send, waitForConnection, executionActions]);

  const pauseNode = useCallback((nodeId: NodeID) => {
    send({ type: 'pause_node', node_id: nodeId });
  }, [send]);

  const resumeNode = useCallback((nodeId: NodeID) => {
    send({ type: 'resume_node', node_id: nodeId });
  }, [send]);

  const skipNode = useCallback((nodeId: NodeID) => {
    send({ type: 'skip_node', node_id: nodeId });
  }, [send]);

  const abort = useCallback(() => {
    if (executionIdRef.current) {
      send({
        type: 'abort_execution',
        execution_id: executionIdRef.current
      });
    }
    errorExecution('Execution aborted');
    executionActions.reset();
  }, [send, errorExecution, executionActions]);

  const respondToPrompt = useCallback((nodeId: NodeID, response: string) => {
    send({
      type: 'interactive_response',
      node_id: nodeId,
      response
    });
    setInteractivePrompt(null);
  }, [send]);

  // ========== Formatters ==========

  const formatTime = useCallback((startTime: Date | null, endTime: Date | null): string => {
    return formatTimeInternal(startTime, endTime, formatDuration);
  }, [formatDuration]);

  const formatTokens = useCallback((tokens: number): string => {
    if (tokens < 1000) return `${tokens}`;
    if (tokens < 1000000) return `${(tokens / 1000).toFixed(1)}k`;
    return `${(tokens / 1000000).toFixed(2)}M`;
  }, []);

  const getNodeIcon = useCallback((status: NodeState['status']): string => {
    const icons: Record<NodeState['status'], string> = {
      pending: '⏳',
      running: '🔄', 
      completed: '✅',
      skipped: '⏭️',
      error: '❌',
      paused: '⏸️'
    };
    return icons[status] || '❓';
  }, []);

  const getNodeColor = useCallback((status: NodeState['status']): string => {
    const colors: Record<NodeState['status'], string> = {
      pending: 'text-gray-500',
      running: 'text-blue-500',
      completed: 'text-green-500',
      skipped: 'text-yellow-500',
      error: 'text-red-500',
      paused: 'text-orange-500'
    };
    return colors[status] || 'text-gray-400';
  }, []);

  // Cleanup
  useEffect(() => {
    return () => {
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
      }
    };
  }, []);

  // Get store state for selectors
  const storeState = useUnifiedStore(
    state => ({
      runContext: state.execution.context,
      runningNodes: Array.from(state.execution.runningNodes),
      nodeStates: state.execution.nodeStates,
    }),
    shallow
  );

  // Helper function to get node execution state
  const getNodeExecutionState = useCallback((nodeId: NodeID) => {
    const isRunning = storeState.runningNodes.includes(nodeId);
    const nodeState = storeState.nodeStates.get(nodeId);
    const isSkipped = nodeState?.status === 'skipped';
    
    return {
      isRunning,
      isCurrentRunning: isRunning,
      nodeRunningState: isRunning,
      isSkipped,
      skipReason: nodeState?.error,
    };
  }, [storeState.runningNodes, storeState.nodeStates]);

  // Computed values
  const currentRunningNode = storeState.runningNodes[0] || null;
  const nodeRunningStates = Object.fromEntries(
    Array.from(storeState.nodeStates.entries()).map(([id, state]) => [id, state.status === 'running'])
  );
  const skippedNodes = Object.fromEntries(
    Array.from(storeState.nodeStates.entries())
      .filter(([_, state]) => state.status === 'skipped')
      .map(([id, state]) => [id, { reason: state.error || 'Skipped' }])
  );

  return {
    // Connection state
    isConnected,
    isReconnecting,
    
    // Execution state
    isRunning: execution.isRunning,
    executionId: execution.executionId,
    execution,
    nodes: nodeStates,
    
    // Node-specific state
    getNodeExecutionState,
    
    // Execution selectors
    runContext: storeState.runContext,
    runningNodes: storeState.runningNodes,
    currentRunningNode,
    nodeRunningStates,
    skippedNodes,
    
    // UI state
    progress,
    duration,
    currentNodeName,
    interactivePrompt,
    
    // Main actions
    execute,
    pauseNode,
    resumeNode,
    skipNode,
    abort,
    respondToPrompt,
    
    // Execution actions
    addRunningNode: executionActions.addRunningNode,
    removeRunningNode: executionActions.removeRunningNode,
    setCurrentRunningNode: executionActions.setCurrentRunningNode,
    setRunContext: executionActions.setRunContext,
    addSkippedNode: executionActions.addSkippedNode,
    reset: executionActions.reset,
    
    // Connection actions
    connect,
    disconnect,
    
    // UI helpers
    formatTime,
    formatTokens,
    getNodeIcon,
    getNodeColor
  };
}