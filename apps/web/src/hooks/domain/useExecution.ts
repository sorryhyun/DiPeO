import { useState, useCallback, useEffect, useMemo } from 'react';
import { useStream, type StreamProtocol } from '../core/useStream';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import { 
  EventType, 
  ExecutionStatus,
  NodeExecutionStatus,
  type ExecutionUpdate,
  type DomainDiagram 
} from '@dipeo/models';
import {
  useExecuteDiagramMutation,
  useControlExecutionMutation,
  useSendInteractiveResponseMutation
} from '@/__generated__/graphql';
import { stripTypenames } from '@/lib/utils/graphql';

export interface ExecutionState {
  id: string | null;
  status: ExecutionStatus | NodeExecutionStatus;
  startTime: Date | null;
  endTime: Date | null;
  totalNodes: number;
  completedNodes: number;
  failedNodes: number;
  error: string | null;
}

export interface NodeState {
  nodeId: string;
  status: NodeExecutionStatus;
  startTime: Date | null;
  endTime: Date | null;
  output?: any;
  error?: string;
  logs: string[];
}

export interface UseExecutionOptions {
  protocol?: StreamProtocol;
  endpoint?: string;
  showToasts?: boolean;
  autoConnect?: boolean;
  debug?: boolean;
}

export interface UseExecutionReturn {
  execution: ExecutionState;
  nodeStates: Record<string, NodeState>;
  isRunning: boolean;
  progress: number;
  
  execute: (diagram?: DomainDiagram, options?: Record<string, any>) => Promise<void>;
  connectToExecution: (executionId: string) => void;
  abort: () => Promise<void>;
  pause: () => Promise<void>;
  resume: () => Promise<void>;
  
  pauseNode: (nodeId: string) => Promise<void>;
  resumeNode: (nodeId: string) => Promise<void>;
  skipNode: (nodeId: string) => Promise<void>;
  
  clearExecution: () => void;
  
  connected: boolean;
  connecting: boolean;
  streamError: Error | null;
}

const DEFAULT_OPTIONS: UseExecutionOptions = {
  protocol: 'sse',
  endpoint: '/api/execution/stream',
  showToasts: true,
  autoConnect: false,
  debug: false
};

export function useExecution(options: UseExecutionOptions = {}): UseExecutionReturn {
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options };
  const { protocol, endpoint, showToasts, autoConnect, debug } = mergedOptions;
  
  const store = useUnifiedStore();
  const [executeDiagram] = useExecuteDiagramMutation();
  const [controlExecution] = useControlExecutionMutation();
  const [submitResponse] = useSendInteractiveResponseMutation();
  
  const [execution, setExecution] = useState<ExecutionState>({
    id: null,
    status: ExecutionStatus.PENDING,
    startTime: null,
    endTime: null,
    totalNodes: 0,
    completedNodes: 0,
    failedNodes: 0,
    error: null
  });
  
  const [nodeStates, setNodeStates] = useState<Record<string, NodeState>>({});
  
  const stream = useStream<ExecutionUpdate>('execution', {
    protocol: protocol!,
    endpoint: endpoint!,
    bufferSize: 1000,
    reconnect: true,
    reconnectDelay: 3000,
    showToasts: false,
    onMessage: (update) => {
      if ('type' in update) {
        handleExecutionUpdate(update as ExecutionUpdate);
      } else if ('node_id' in update) {
        handleNodeUpdate(update as ExecutionUpdate);
      }
    },
    onConnect: () => {
      if (debug) console.log('[Execution] Stream connected');
    },
    onDisconnect: (reason) => {
      if (debug) console.log('[Execution] Stream disconnected:', reason);
    },
    onError: (error) => {
      console.error('[Execution] Stream error:', error);
    }
  });
  
  const handleExecutionUpdate = useCallback((update: ExecutionUpdate) => {
    if (debug) console.log('[Execution] Update:', update);
    
    switch (update.type) {
      case EventType.EXECUTION_STATUS_CHANGED:
        setExecution(prev => ({
          ...prev,
          status: (update as any).status || prev.status,
          error: (update as any).error || prev.error
        }));
        
        if ((update as any).status === ExecutionStatus.COMPLETED) {
          setExecution(prev => ({
            ...prev,
            endTime: new Date()
          }));
          store.stopExecution();
        } else if ((update as any).status === ExecutionStatus.FAILED) {
          setExecution(prev => ({
            ...prev,
            endTime: new Date(),
            error: (update as any).error || 'Execution failed'
          }));
          store.stopExecution();
        }
        break;
        
      case EventType.EXECUTION_UPDATE:
        // Handle general execution updates
        if (debug) console.log('[Execution] General update');
        break;
        
      case EventType.EXECUTION_ERROR:
        setExecution(prev => ({
          ...prev,
          status: ExecutionStatus.FAILED,
          endTime: new Date(),
          error: (update as any).error || 'Execution failed'
        }));
        store.stopExecution();
        break;
    }
  }, [debug, store]);
  
  const handleNodeUpdate = useCallback((update: ExecutionUpdate) => {
    if (debug) console.log('[Execution] Node update:', update);
    
    const nodeId = (update as any).node_id;
    if (!nodeId) return;
    
    setNodeStates(prev => {
      const existing = prev[nodeId] || {
        nodeId,
        status: NodeExecutionStatus.PENDING,
        startTime: null,
        endTime: null,
        output: undefined,
        error: undefined,
        logs: []
      };
      
      const newState: NodeState = {
        ...existing,
        status: (update as any).status || existing.status,
        output: (update as any).output || existing.output,
        error: (update as any).error || existing.error,
        logs: (update as any).log ? [...existing.logs, (update as any).log] : existing.logs
      };
      
      if ((update as any).status === NodeExecutionStatus.RUNNING && !existing.startTime) {
        newState.startTime = new Date();
      } else if ([NodeExecutionStatus.COMPLETED, NodeExecutionStatus.FAILED].includes((update as any).status)) {
        newState.endTime = new Date();
      }
      
      return {
        ...prev,
        [nodeId]: newState
      };
    });
    
    if ((update as any).status === NodeExecutionStatus.COMPLETED) {
      setExecution(prev => ({
        ...prev,
        completedNodes: prev.completedNodes + 1
      }));
      store.updateNode(nodeId, { data: { ...store.getNode(nodeId)?.data, isRunning: false } });
    } else if ((update as any).status === NodeExecutionStatus.FAILED) {
      setExecution(prev => ({
        ...prev,
        failedNodes: prev.failedNodes + 1
      }));
      store.updateNode(nodeId, { data: { ...store.getNode(nodeId)?.data, isRunning: false, hasError: true } });
    } else if ((update as any).status === NodeExecutionStatus.RUNNING) {
      store.updateNode(nodeId, { data: { ...store.getNode(nodeId)?.data, isRunning: true } });
    }
  }, [debug, store]);
  
  const execute = useCallback(async (diagram?: DomainDiagram, options?: Record<string, any>) => {
    try {
      const diagramData = diagram || JSON.parse(store.exportDiagram());
      
      const { data } = await executeDiagram({
        variables: {
          input: {
            diagram_data: {
              nodes: stripTypenames(diagramData.nodes),
              arrows: stripTypenames(diagramData.arrows),
              persons: stripTypenames(diagramData.persons),
              handles: stripTypenames(diagramData.handles || [])
            },
            variables: options?.variables || {},
            debug_mode: options?.debug || debug,
            timeout_seconds: options?.timeout,
            max_iterations: options?.maxIterations
          }
        }
      });
      
      if (data?.execute_diagram?.success && data.execute_diagram.execution?.id) {
        const executionId = data.execute_diagram.execution.id;
        
        setExecution({
          id: executionId,
          status: ExecutionStatus.PENDING,
          startTime: new Date(),
          endTime: null,
          totalNodes: diagramData.nodes.length,
          completedNodes: 0,
          failedNodes: 0,
          error: null
        });
        
        setNodeStates({});
        
        const streamEndpoint = `${endpoint}?executionId=${executionId}`;
        stream.connect();
      } else {
        throw new Error(data?.execute_diagram?.error || 'Failed to start execution');
      }
    } catch (error) {
      console.error('[Execution] Failed to execute:', error);
      setExecution(prev => ({
        ...prev,
        status: ExecutionStatus.FAILED,
        error: error instanceof Error ? error.message : 'Failed to execute'
      }));
      throw error;
    }
  }, [store, executeDiagram, debug, endpoint, stream]);
  
  const connectToExecution = useCallback((executionId: string) => {
    setExecution(prev => ({
      ...prev,
      id: executionId
    }));
    
    const streamEndpoint = `${endpoint}?executionId=${executionId}`;
    stream.connect();
  }, [endpoint, stream]);
  
  const abort = useCallback(async () => {
    if (!execution.id) return;
    
    try {
      await controlExecution({
        variables: {
          input: {
            execution_id: execution.id,
            action: 'abort'
          }
        }
      });
      
      stream.disconnect();
      setExecution(prev => ({
        ...prev,
        status: ExecutionStatus.ABORTED,
        endTime: new Date()
      }));
    } catch (error) {
      console.error('[Execution] Failed to abort:', error);
    }
  }, [execution.id, controlExecution, stream]);
  
  const pause = useCallback(async () => {
    if (!execution.id) return;
    
    await controlExecution({
      variables: {
        input: {
          execution_id: execution.id,
          action: 'pause'
        }
      }
    });
  }, [execution.id, controlExecution]);
  
  const resume = useCallback(async () => {
    if (!execution.id) return;
    
    await controlExecution({
      variables: {
        input: {
          execution_id: execution.id,
          action: 'resume'
        }
      }
    });
  }, [execution.id, controlExecution]);
  
  const pauseNode = useCallback(async (nodeId: string) => {
    if (!execution.id) return;
    
    await controlExecution({
      variables: {
        input: {
          execution_id: execution.id,
          action: 'pause',
          reason: `Pausing at node ${nodeId}`
        }
      }
    });
  }, [execution.id, controlExecution]);
  
  const resumeNode = useCallback(async (nodeId: string) => {
    if (!execution.id) return;
    
    await controlExecution({
      variables: {
        input: {
          execution_id: execution.id,
          action: 'resume',
          reason: `Resuming from node ${nodeId}`
        }
      }
    });
  }, [execution.id, controlExecution]);
  
  const skipNode = useCallback(async (nodeId: string) => {
    if (!execution.id) return;
    
    await controlExecution({
      variables: {
        input: {
          execution_id: execution.id,
          action: 'skip',
          reason: `Skipping node ${nodeId}`
        }
      }
    });
  }, [execution.id, controlExecution]);
  
  const clearExecution = useCallback(() => {
    stream.disconnect();
    setExecution({
      id: null,
      status: ExecutionStatus.PENDING,
      startTime: null,
      endTime: null,
      totalNodes: 0,
      completedNodes: 0,
      failedNodes: 0,
      error: null
    });
    setNodeStates({});
    store.stopExecution();
  }, [stream, store]);
  
  const isRunning = execution.status === ExecutionStatus.RUNNING || execution.status === NodeExecutionStatus.RUNNING;
  const progress = execution.totalNodes > 0 
    ? (execution.completedNodes / execution.totalNodes) * 100 
    : 0;
  
  useEffect(() => {
    if (autoConnect && execution.id) {
      stream.connect();
    }
    
    return () => {
      stream.disconnect();
    };
  }, [autoConnect, execution.id]);
  
  return {
    execution,
    nodeStates,
    isRunning,
    progress,
    
    execute,
    connectToExecution,
    abort,
    pause,
    resume,
    
    pauseNode,
    resumeNode,
    skipNode,
    
    clearExecution,
    
    connected: stream.connected,
    connecting: stream.connecting,
    streamError: stream.error
  };
}