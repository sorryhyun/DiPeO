/**
 * useExecutionGraphQL - GraphQL-based execution hook replacing WebSocket
 * 
 * This hook provides the same interface as useExecution but uses GraphQL
 * subscriptions and mutations instead of WebSocket.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSubscription, useMutation, ApolloError } from '@apollo/client';
import { toast } from 'sonner';
import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import type { DomainDiagram, InteractivePromptData, ExecutionOptions, ExecutionUpdate, NodeID, ExecutionID } from '@/types';
import { nodeId, executionId } from '@/types';
import { NodeKind } from '@/types/primitives/enums';
import { createCommonStoreSelector } from '@/stores/selectorFactory';
import { NODE_ICONS, NODE_COLORS } from '@/config/nodeMeta';
import {
  ExecutionUpdatesDocument,
  NodeUpdatesDocument,
  InteractivePromptsDocument,
  ExecuteDiagramDocument,
  ControlExecutionDocument,
  SubmitInteractiveResponseDocument,
  ExecutionUpdatesSubscription,
  NodeUpdatesSubscription,
  InteractivePromptsSubscription,
  ExecutionStatus,
} from '@/generated/graphql';

// Types (same as original)
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
  
  // Connection (for compatibility)
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

// Constants
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

// Throttle utility
function throttle<T extends (...args: any[]) => any>(fn: T, delay: number): T {
  let lastCall = 0;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let lastArgs: Parameters<T> | null = null;
  
  return ((...args: Parameters<T>) => {
    const now = Date.now();
    lastArgs = args;
    
    if (now - lastCall >= delay) {
      lastCall = now;
      fn(...args);
    } else if (!timeoutId) {
      timeoutId = setTimeout(() => {
        if (lastArgs) {
          lastCall = Date.now();
          fn(...lastArgs);
        }
        timeoutId = null;
        lastArgs = null;
      }, delay - (now - lastCall));
    }
  }) as T;
}

// Main Hook
export function useExecutionGraphQL(options: UseExecutionOptions = {}): UseExecutionReturn {
  const {
    showToasts = true,
    formatDuration = true,
    onUpdate
  } = options;
  
  // Store integration
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
  
  // GraphQL Mutations
  const [executeDiagramMutation] = useMutation(ExecuteDiagramDocument);
  const [controlExecutionMutation] = useMutation(ControlExecutionDocument);
  const [submitInteractiveResponseMutation] = useMutation(SubmitInteractiveResponseDocument);
  
  // GraphQL Subscriptions
  const { data: executionData } = useSubscription<ExecutionUpdatesSubscription>(
    ExecutionUpdatesDocument,
    {
      variables: { executionId: executionIdRef.current! },
      skip: !executionIdRef.current,
    }
  );
  
  const { data: nodeData } = useSubscription<NodeUpdatesSubscription>(
    NodeUpdatesDocument,
    {
      variables: { executionId: executionIdRef.current! },
      skip: !executionIdRef.current,
    }
  );
  
  const { data: promptData } = useSubscription<InteractivePromptsSubscription>(
    InteractivePromptsDocument,
    {
      variables: { executionId: executionIdRef.current! },
      skip: !executionIdRef.current,
    }
  );
  
  // State Management Functions
  const startExecution = useCallback((executionId: string, totalNodes: number) => {
    const now = new Date();
    startTimeRef.current = now;
    executionIdRef.current = executionId;
    
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
  
  // Process execution subscription updates
  useEffect(() => {
    if (!executionData?.executionUpdates) return;
    
    const update = executionData.executionUpdates;
    
    if (update.status === ExecutionStatus.Completed) {
      completeExecution(update.tokenUsage?.total);
      executionActions.stopExecution();
      onUpdate?.({ type: 'execution_complete', totalTokens: update.tokenUsage?.total });
    } else if (update.status === ExecutionStatus.Failed && update.error) {
      errorExecution(update.error);
      executionActions.stopExecution();
      onUpdate?.({ type: 'execution_error', error: update.error });
    } else if (update.status === ExecutionStatus.Aborted) {
      errorExecution('Execution aborted');
      executionActions.stopExecution();
      onUpdate?.({ type: 'execution_aborted' });
    }
  }, [executionData, completeExecution, errorExecution, executionActions, onUpdate]);
  
  // Throttled node update handlers
  const handleNodeStart = useCallback(throttle((nodeIdStr: string, nodeType: string) => {
    setExecution(prev => ({
      ...prev,
      currentNode: nodeIdStr,
    }));
    
    setNodeStates(prev => ({
      ...prev,
      [nodeIdStr]: {
        status: 'running',
        startTime: new Date(),
        endTime: null,
      }
    }));
    
    currentRunningNodeRef.current = nodeIdStr;
    executionActions.updateNodeExecution(nodeId(nodeIdStr), {
      status: 'running',
      timestamp: Date.now()
    });
    onUpdate?.({ type: 'node_start', nodeId: nodeId(nodeIdStr), nodeType: nodeType });
  }, 50), [executionActions, onUpdate]);
  
  const handleNodeComplete = useCallback(throttle((nodeIdStr: string, tokenCount?: number, output?: any) => {
    setExecution(prev => ({
      ...prev,
      completedNodes: prev.completedNodes + 1,
      currentNode: prev.currentNode === nodeIdStr ? null : prev.currentNode,
    }));
    
    setNodeStates(prev => ({
      ...prev,
      [nodeIdStr]: {
        ...(prev[nodeIdStr] || { startTime: null, endTime: null }),
        status: 'completed' as const,
        endTime: new Date(),
        tokenCount,
      }
    }));
    
    if (currentRunningNodeRef.current === nodeIdStr) {
      currentRunningNodeRef.current = null;
    }
    
    executionActions.updateNodeExecution(nodeId(nodeIdStr), {
      status: 'completed',
      timestamp: Date.now()
    });
    
    if (output && typeof output === 'object') {
      runContextRef.current = { ...runContextRef.current, ...output };
    }
    
    onUpdate?.({ type: 'node_complete', nodeId: nodeId(nodeIdStr), tokens: tokenCount, output });
  }, 50), [executionActions, onUpdate]);
  
  // Process node subscription updates
  useEffect(() => {
    if (!nodeData?.nodeUpdates) return;
    
    const update = nodeData.nodeUpdates;
    
    if (update.status === 'running') {
      handleNodeStart(update.nodeId, update.nodeType);
    } else if (update.status === 'completed') {
      handleNodeComplete(update.nodeId, update.tokensUsed || undefined, update.output);
    } else if (update.status === 'failed') {
      setNodeStates(prev => ({
        ...prev,
        [update.nodeId]: {
          ...(prev[update.nodeId] || { startTime: null, endTime: null }),
          status: 'error' as const,
          endTime: new Date(),
          error: update.error || 'Unknown error'
        }
      }));
      
      executionActions.updateNodeExecution(nodeId(update.nodeId), {
        status: 'failed',
        timestamp: Date.now(),
        error: update.error ?? undefined
      });
      
      if (showToasts) {
        toast.error(`Node ${update.nodeId.slice(0, 8)}... failed: ${update.error}`);
      }
      
      onUpdate?.({ type: 'node_error', nodeId: nodeId(update.nodeId), error: update.error || undefined });
    } else if (update.status === 'skipped') {
      setExecution(prev => ({
        ...prev,
        completedNodes: prev.completedNodes + 1
      }));
      
      setNodeStates(prev => ({
        ...prev,
        [update.nodeId]: {
          ...(prev[update.nodeId] || { startTime: null, endTime: null }),
          status: 'skipped' as const,
          endTime: new Date(),
        }
      }));
      
      skippedNodesRef.current.push({ nodeId: update.nodeId, reason: 'Skipped' });
      executionActions.updateNodeExecution(nodeId(update.nodeId), {
        status: 'skipped',
        timestamp: Date.now()
      });
      
      onUpdate?.({ type: 'node_skipped', nodeId: nodeId(update.nodeId) });
    } else if (update.status === 'paused') {
      setNodeStates(prev => ({
        ...prev,
        [update.nodeId]: {
          ...(prev[update.nodeId] || { startTime: null, endTime: null }),
          status: 'paused' as const
        }
      }));
      onUpdate?.({ type: 'node_paused', nodeId: nodeId(update.nodeId) });
    }
    
    // Handle progress updates
    if (update.progress) {
      setNodeStates(prev => ({
        ...prev,
        [update.nodeId]: {
          ...prev[update.nodeId],
          progress: update.progress || undefined
        } as NodeState
      }));
      onUpdate?.({ type: 'node_progress', nodeId: nodeId(update.nodeId), progress: update.progress });
    }
  }, [nodeData, handleNodeStart, handleNodeComplete, executionActions, showToasts, onUpdate]);
  
  // Process interactive prompt updates
  useEffect(() => {
    if (!promptData?.interactivePrompts) return;
    
    const prompt = promptData.interactivePrompts;
    setInteractivePrompt({
      executionId: executionId(prompt.executionId),
      nodeId: nodeId(prompt.nodeId),
      prompt: prompt.prompt,
      timeout: prompt.timeoutSeconds || undefined,
    });
    onUpdate?.({ type: 'interactive_prompt_request', nodeId: nodeId(prompt.nodeId), message: prompt.prompt, executionId: executionId(prompt.executionId) });
  }, [promptData, onUpdate]);
  
  // Main Actions
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
      const result = await executeDiagramMutation({
        variables: {
          input: {
            diagramId: diagram?.metadata?.id || 'current',
            variables: (options as any)?.variables || {},
            debugMode: options?.debug || false,
            timeout: (options as any)?.timeout,
            maxIterations: (options as any)?.maxIterations
          }
        }
      });
      
      if (result.data?.executeDiagram.success && result.data.executeDiagram.executionId) {
        const totalNodes = diagram ? Object.keys(diagram.nodes).length : 0;
        startExecution(result.data.executeDiagram.executionId, totalNodes);
        executionActions.startExecution(result.data.executeDiagram.executionId);
        onUpdate?.({ type: 'execution_started', executionId: executionId(result.data.executeDiagram.executionId), total_nodes: totalNodes });
      } else {
        throw new Error(result.data?.executeDiagram.error || 'Failed to start execution');
      }
    } catch (error) {
      const errorMessage = error instanceof ApolloError ? error.message : 'Failed to execute diagram';
      errorExecution(errorMessage);
      throw error;
    }
  }, [executeDiagramMutation, startExecution, executionActions, errorExecution, onUpdate]);
  
  const controlExecution = useCallback(async (action: string, nodeId?: string) => {
    if (!executionIdRef.current) return;
    
    try {
      await controlExecutionMutation({
        variables: {
          input: {
            executionId: executionIdRef.current,
            action,
            nodeId
          }
        }
      });
    } catch (error) {
      if (showToasts) {
        toast.error(`Failed to ${action}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  }, [controlExecutionMutation, showToasts]);
  
  const pauseNode = useCallback((nodeId: string) => {
    controlExecution('pause', nodeId);
  }, [controlExecution]);
  
  const resumeNode = useCallback((nodeId: string) => {
    controlExecution('resume', nodeId);
  }, [controlExecution]);
  
  const skipNode = useCallback((nodeId: string) => {
    controlExecution('skip', nodeId);
  }, [controlExecution]);
  
  const abort = useCallback(() => {
    if (executionIdRef.current) {
      controlExecution('abort');
    } else if (execution.isRunning) {
      errorExecution('Execution aborted');
      executionActions.stopExecution();
    }
  }, [controlExecution, errorExecution, executionActions, execution.isRunning]);
  
  const respondToPrompt = useCallback(async (response: string) => {
    if (!executionIdRef.current || !interactivePrompt) return;
    
    try {
      await submitInteractiveResponseMutation({
        variables: {
          input: {
            executionId: executionIdRef.current,
            nodeId: interactivePrompt.nodeId,
            response
          }
        }
      });
      setInteractivePrompt(null);
    } catch (error) {
      if (showToasts) {
        toast.error(`Failed to submit response: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  }, [submitInteractiveResponseMutation, interactivePrompt, showToasts]);
  
  // UI Helpers
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
  
  const getNodeExecutionState = useCallback((nodeId: string): NodeState | undefined => {
    return nodeStates[nodeId];
  }, [nodeStates]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
      }
      executionIdRef.current = null;
    };
  }, []);
  
  // Update progress
  useEffect(() => {
    if (execution.totalNodes > 0) {
      setProgress(Math.round(((execution.completedNodes + 1) / execution.totalNodes) * 100));
    }
  }, [execution.completedNodes, execution.totalNodes]);
  
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
    abort,
    
    // Node Actions
    pauseNode,
    resumeNode,
    skipNode,
    
    // Interactive Prompt
    interactivePrompt,
    respondToPrompt,
    
    // Connection (for compatibility)
    isConnected: true, // GraphQL is always "connected"
    connect: async () => {}, // No-op for GraphQL
    disconnect: () => {}, // No-op for GraphQL
    
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
    nodes: Array.from(executionActions.nodes.values()),
  };
}