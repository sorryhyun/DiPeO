/**
 * useExecutionSocket - WebSocket event handling for execution
 * 
 * This hook handles all WebSocket communication related to execution,
 * including message sending, event subscription, and response handling.
 */

import { useEffect, useCallback, useRef } from 'react';
import { useWebSocketEventBus } from '../useWebSocketEventBus';
import { useEvent } from '../useEvent';
import type { WSMessage, DiagramState, InteractivePromptData, DiagramData, ExecutionOptions, ExecutionUpdate } from '@/types';
import { exportDiagramState } from '../useStoreSelectors';

export interface UseExecutionSocketOptions {
  autoConnect?: boolean;
  debug?: boolean;
  onExecutionStart?: (executionId: string, totalNodes: number) => void;
  onExecutionComplete?: (executionId: string, totalTokens?: number) => void;
  onExecutionError?: (executionId: string, error: string) => void;
  onExecutionAbort?: (executionId: string) => void;
  onNodeStart?: (nodeId: string, nodeType: string) => void;
  onNodeProgress?: (nodeId: string, progress: string) => void;
  onNodeComplete?: (nodeId: string, output?: unknown, tokenCount?: number) => void;
  onNodeSkipped?: (nodeId: string, reason?: string) => void;
  onNodeError?: (nodeId: string, error: string) => void;
  onNodePaused?: (nodeId: string) => void;
  onNodeResumed?: (nodeId: string) => void;
  onInteractivePrompt?: (prompt: InteractivePromptData) => void;
  onUpdate?: (update: ExecutionUpdate) => void;
}

export interface UseExecutionSocketReturn {
  isConnected: boolean;
  isReconnecting: boolean;
  executionId: string | null;
  
  // Actions
  execute: (diagram?: DiagramState, options?: ExecutionOptions) => Promise<void>;
  pauseNode: (nodeId: string) => void;
  resumeNode: (nodeId: string) => void;
  skipNode: (nodeId: string) => void;
  abort: () => void;
  respondToPrompt: (nodeId: string, response: string) => void;
  
  // Connection
  connect: () => void;
  disconnect: () => void;
}

export function useExecutionSocket(options: UseExecutionSocketOptions = {}): UseExecutionSocketReturn {
  const {
    autoConnect = true,
    debug = false,
    onExecutionStart,
    onExecutionComplete,
    onExecutionError,
    onExecutionAbort,
    onNodeStart,
    onNodeProgress,
    onNodeComplete,
    onNodeSkipped,
    onNodeError,
    onNodePaused,
    onNodeResumed,
    onInteractivePrompt,
    onUpdate
  } = options;

  const { isConnected, isReconnecting, send, on, connect, disconnect } = useWebSocketEventBus({ 
    autoConnect, 
    debug 
  });
  
  const executionIdRef = useRef<string | null>(null);
  const executionResolveRef = useRef<(() => void) | null>(null);
  const executionRejectRef = useRef<((error: Error) => void) | null>(null);

  // Stable callbacks
  const stableOnExecutionStart = useEvent(onExecutionStart || (() => {}));
  const stableOnExecutionComplete = useEvent(onExecutionComplete || (() => {}));
  const stableOnExecutionError = useEvent(onExecutionError || (() => {}));
  const stableOnExecutionAbort = useEvent(onExecutionAbort || (() => {}));
  const stableOnNodeStart = useEvent(onNodeStart || (() => {}));
  const stableOnNodeProgress = useEvent(onNodeProgress || (() => {}));
  const stableOnNodeComplete = useEvent(onNodeComplete || (() => {}));
  const stableOnNodeSkipped = useEvent(onNodeSkipped || (() => {}));
  const stableOnNodeError = useEvent(onNodeError || (() => {}));
  const stableOnNodePaused = useEvent(onNodePaused || (() => {}));
  const stableOnNodeResumed = useEvent(onNodeResumed || (() => {}));
  const stableOnInteractivePrompt = useEvent(onInteractivePrompt || (() => {}));
  const stableOnUpdate = useEvent(onUpdate || (() => {}));

  // Set up event handlers
  useEffect(() => {
    // Execution events
    on('execution_started', (message: WSMessage) => {
      const executionId = message.execution_id as string;
      const totalNodes = message.total_nodes as number || 0;
      executionIdRef.current = executionId;
      stableOnExecutionStart(executionId, totalNodes);
    });

    on('execution_complete', (message: WSMessage) => {
      const executionId = message.execution_id as string;
      const totalTokens = message.total_token_count as number;
      stableOnExecutionComplete(executionId, totalTokens);
      if (executionResolveRef.current) {
        executionResolveRef.current();
        executionResolveRef.current = null;
        executionRejectRef.current = null;
      }
      executionIdRef.current = null;
    });

    on('execution_error', (message: WSMessage) => {
      const executionId = message.execution_id as string;
      const error = message.error as string;
      stableOnExecutionError(executionId, error);
      if (executionRejectRef.current) {
        executionRejectRef.current(new Error(error));
        executionResolveRef.current = null;
        executionRejectRef.current = null;
      }
      executionIdRef.current = null;
    });

    on('execution_aborted', (message: WSMessage) => {
      const executionId = message.execution_id as string;
      stableOnExecutionAbort(executionId);
      if (executionRejectRef.current) {
        executionRejectRef.current(new Error('Execution aborted'));
        executionResolveRef.current = null;
        executionRejectRef.current = null;
      }
      executionIdRef.current = null;
    });

    // Node events
    on('node_start', (message: WSMessage) => {
      const nodeId = message.nodeId as string;
      const nodeType = message.node_type as string;
      stableOnNodeStart(nodeId, nodeType);
      if (stableOnUpdate) {
        stableOnUpdate(convertToExecutionUpdate(message));
      }
    });

    on('node_progress', (message: WSMessage) => {
      const nodeId = message.nodeId as string;
      const progress = message.message as string || '';
      stableOnNodeProgress(nodeId, progress);
    });

    on('node_complete', (message: WSMessage) => {
      const nodeId = message.nodeId as string;
      const output = message.output;
      const tokenCount = message.token_count as number;
      stableOnNodeComplete(nodeId, output, tokenCount);
      if (stableOnUpdate) {
        stableOnUpdate(convertToExecutionUpdate(message));
      }
    });

    on('node_skipped', (message: WSMessage) => {
      const nodeId = message.nodeId as string;
      const reason = message.reason as string;
      stableOnNodeSkipped(nodeId, reason);
    });

    on('node_error', (message: WSMessage) => {
      const nodeId = message.nodeId as string;
      const error = message.error as string;
      stableOnNodeError(nodeId, error);
    });

    // Control events
    on('node_paused', (message: WSMessage) => {
      const nodeId = message.nodeId as string;
      stableOnNodePaused(nodeId);
    });

    on('node_resumed', (message: WSMessage) => {
      const nodeId = message.nodeId as string;
      stableOnNodeResumed(nodeId);
    });

    // Interactive events
    on('interactive_prompt', (message: WSMessage) => {
      const prompt: InteractivePromptData = {
        nodeId: message.nodeId as string,
        executionId: message.executionId as string || executionIdRef.current || '',
        prompt: message.prompt as string,
        context: message.context as InteractivePromptData['context']
      };
      stableOnInteractivePrompt(prompt);
    });
  }, [on, stableOnExecutionStart, stableOnExecutionComplete, stableOnExecutionError, 
      stableOnExecutionAbort, stableOnNodeStart, stableOnNodeProgress, 
      stableOnNodeComplete, stableOnNodeSkipped, stableOnNodeError, 
      stableOnNodePaused, stableOnNodeResumed, stableOnInteractivePrompt, stableOnUpdate]);

  // Execute diagram
  const execute = useCallback(async (diagram?: DiagramState, options: ExecutionOptions = {}) => {
    const diagramData = diagram || exportDiagramState();
    
    // Convert to API format
    const apiDiagram: DiagramData = {
      nodes: diagramData.nodes || [],
      arrows: diagramData.arrows || [],
      persons: diagramData.persons || [],
      apiKeys: diagramData.apiKeys || []
    };

    return new Promise<void>((resolve, reject) => {
      executionResolveRef.current = resolve;
      executionRejectRef.current = reject;

      send({
        type: 'execute_diagram',
        diagram: apiDiagram,
        options: {
          continueOnError: options.continueOnError ?? false,
          allowPartial: options.allowPartial ?? false,
          debugMode: options.debugMode ?? false
        }
      });
    });
  }, [send]);

  // Control actions
  const pauseNode = useCallback((nodeId: string) => {
    if (executionIdRef.current) {
      send({
        type: 'pause_node',
        nodeId,
        executionId: executionIdRef.current
      });
    }
  }, [send]);

  const resumeNode = useCallback((nodeId: string) => {
    if (executionIdRef.current) {
      send({
        type: 'resume_node',
        nodeId,
        executionId: executionIdRef.current
      });
    }
  }, [send]);

  const skipNode = useCallback((nodeId: string) => {
    if (executionIdRef.current) {
      send({
        type: 'skip_node',
        nodeId,
        executionId: executionIdRef.current
      });
    }
  }, [send]);

  const abort = useCallback(() => {
    if (executionIdRef.current) {
      send({
        type: 'abort_execution',
        executionId: executionIdRef.current
      });
    }
  }, [send]);

  const respondToPrompt = useCallback((nodeId: string, response: string) => {
    if (executionIdRef.current) {
      send({
        type: 'interactive_response',
        nodeId,
        executionId: executionIdRef.current,
        response
      });
    }
  }, [send]);

  return {
    isConnected,
    isReconnecting,
    executionId: executionIdRef.current,
    execute,
    pauseNode,
    resumeNode,
    skipNode,
    abort,
    respondToPrompt,
    connect,
    disconnect
  };
}

// Helper function to convert WSMessage to ExecutionUpdate
function convertToExecutionUpdate(message: WSMessage): ExecutionUpdate {
  return {
    type: message.type,
    executionId: message.executionId as string,
    nodeId: message.nodeId as string,
    nodeType: message.node_type as string,
    output: message.output,
    output_preview: message.output_preview as string,
    context: message.context as Record<string, unknown>,
    totalTokens: message.total_tokens as number,
    tokens: message.tokens as number,
    error: message.error as string,
    timestamp: message.timestamp as string,
    conversationId: message.conversation_id as string,
    message: message.message
  };
}