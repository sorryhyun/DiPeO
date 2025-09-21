import { useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { Status, EventType, type ExecutionUpdate, JsonValue } from '@dipeo/models';
import { nodeId, executionId } from '@/infrastructure/types';
import { useExecutionState } from './useExecutionState';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';

interface UseExecutionUpdatesProps {
  state: ReturnType<typeof useExecutionState>;
  executionActions: any; // Store actions
  showToasts?: boolean;
  onUpdate?: (update: ExecutionUpdate) => void;
  executionUpdates?: any;
  nodeUpdates?: any;
  interactivePrompts?: any;
}

const THROTTLE_DELAY = 50; // ms
const TOAST_THROTTLE_DELAY = 2000; // ms - Prevent toast spam (increased from 1000ms)

export function useExecutionUpdates({
  state,
  executionActions,
  showToasts = true,
  onUpdate,
  executionUpdates,
  nodeUpdates,
  interactivePrompts,
}: UseExecutionUpdatesProps) {
  const {
    completeExecution,
    errorExecution,
    updateNodeState,
    setCurrentNode,
    incrementCompletedNodes,
    setInteractivePrompt,
    addToRunContext,
    addSkippedNode,
    executionIdRef,
    currentRunningNodeRef,
  } = state;

  // Refs for throttling
  const lastNodeStartRef = useRef<{ [nodeId: string]: number }>({});
  const lastNodeCompleteRef = useRef<{ [nodeId: string]: number }>({});
  const lastToastRef = useRef<{ [key: string]: number }>({});

  // Throttled toast function to prevent spam
  const showThrottledToast = useCallback((key: string, type: 'success' | 'error' | 'info', message: string) => {
    if (!showToasts) return;

    const now = Date.now();
    const lastToast = lastToastRef.current[key] || 0;

    if (now - lastToast < TOAST_THROTTLE_DELAY) {
      return;
    }

    lastToastRef.current[key] = now;
    toast[type](message);
  }, [showToasts]);

  // Handle node start with manual throttling
  const handleNodeStart = useCallback((nodeIdStr: string, nodeType: string) => {
    const now = Date.now();
    const lastCall = lastNodeStartRef.current[nodeIdStr] || 0;

    if (now - lastCall < THROTTLE_DELAY) {
      return;
    }

    lastNodeStartRef.current[nodeIdStr] = now;

    setCurrentNode(nodeIdStr);

    updateNodeState(nodeIdStr, {
      status: 'running', // Hook uses lowercase
      startTime: new Date(),
      endTime: null,
    });

    executionActions.updateNodeExecution(nodeId(nodeIdStr), {
      status: Status.RUNNING,
      timestamp: Date.now()
    });

    onUpdate?.({
      type: EventType.NODE_STARTED,
      execution_id: executionId(executionIdRef.current!),
      node_id: nodeId(nodeIdStr),
      node_type: nodeType,
      status: Status.RUNNING,
      timestamp: new Date().toISOString()
    });
  }, [setCurrentNode, updateNodeState, executionActions, onUpdate, executionIdRef]);

  // Handle node complete with manual throttling
  const handleNodeComplete = useCallback((nodeIdStr: string, tokenCount?: number, output?: unknown) => {
    const now = Date.now();
    const lastCall = lastNodeCompleteRef.current[nodeIdStr] || 0;

    if (now - lastCall < THROTTLE_DELAY) {
      return;
    }

    lastNodeCompleteRef.current[nodeIdStr] = now;

    incrementCompletedNodes();

    if (currentRunningNodeRef.current === nodeIdStr) {
      setCurrentNode(null);
    }

    updateNodeState(nodeIdStr, {
      status: 'completed',
      endTime: new Date(),
      tokenCount,
    });

    executionActions.updateNodeExecution(nodeId(nodeIdStr), {
      status: Status.COMPLETED,
      timestamp: Date.now()
    });

    addToRunContext(output);

    onUpdate?.({
      type: EventType.NODE_STARTED,
      execution_id: executionId(executionIdRef.current!),
      node_id: nodeId(nodeIdStr),
      tokens: tokenCount,
      result: output as JsonValue | undefined,
      status: Status.COMPLETED,
      timestamp: new Date().toISOString()
    });
  }, [incrementCompletedNodes, setCurrentNode, updateNodeState, executionActions, addToRunContext, onUpdate, executionIdRef, currentRunningNodeRef]);

  // Process execution subscription updates
  useEffect(() => {
    if (!executionUpdates) return;

    // Log all updates for debugging (commented out to reduce noise)
    // console.log('[useExecutionUpdates] Received update:', {
    //   event_type: executionUpdates.event_type,
    //   data: executionUpdates.data,
    //   full: executionUpdates
    // });

    // Check if this is a node event
    // The GraphQL subscription returns 'type' field, not 'event_type'
    const eventType = executionUpdates.type || executionUpdates.event_type;
    // Parse the data field if it's a string (JSON)
    let eventData = executionUpdates.data || {};
    if (typeof eventData === 'string') {
      try {
        eventData = JSON.parse(eventData);
      } catch (e) {
        console.error('[useExecutionUpdates] Failed to parse data:', e);
        eventData = {};
      }
    }
    // console.log('[useExecutionUpdates] Parsed eventData:', eventData);

    // Handle keepalive events - just acknowledge and skip
    // These events are sent to maintain the WebSocket connection
    if (eventType === 'KEEPALIVE' || eventType === 'keepalive') {
      // Silently ignore keepalive events - they're just for maintaining the connection
      return;
    }

    // Handle batch updates
    if (eventType === 'BATCH_UPDATE' && eventData.events && Array.isArray(eventData.events)) {
      console.log('[useExecutionUpdates] Processing batch update with', eventData.events.length, 'events');

      // Process each event in the batch
      for (const event of eventData.events) {
        const batchEventType = event.type;
        const batchEventData = event.data || {};

        // Handle node events from batch
        if (batchEventType === 'NODE_STARTED') {
          const nodeIdStr = batchEventData.node_id || '';
          const nodeType = batchEventData.node_type || '';
          if (nodeIdStr) {
            handleNodeStart(nodeIdStr, nodeType);
          }
        } else if (batchEventType === 'NODE_COMPLETED') {
          const nodeIdStr = batchEventData.node_id || '';
          const tokenCount = batchEventData.tokens_used || batchEventData.metrics?.tokens || undefined;
          const output = batchEventData.output || batchEventData.result || undefined;
          if (nodeIdStr) {
            handleNodeComplete(nodeIdStr, tokenCount, output);
          }
        } else if (batchEventType === 'NODE_ERROR') {
          const nodeIdStr = batchEventData.node_id || '';
          const nodeType = batchEventData.node_type || '';
          const nodeStatus = batchEventData.status || '';

          if (nodeIdStr && nodeStatus) {
            // console.log('[useExecutionUpdates] Batch NODE_STATUS_CHANGED:', { nodeIdStr, nodeType, nodeStatus });

            if (nodeStatus === 'RUNNING') {
              handleNodeStart(nodeIdStr, nodeType);
            } else if (nodeStatus === 'COMPLETED' || nodeStatus === 'MAXITER_REACHED') {
              const tokenCount = batchEventData.tokens_used || batchEventData.metrics?.tokens || undefined;
              const output = batchEventData.output || batchEventData.result || undefined;
              handleNodeComplete(nodeIdStr, tokenCount, output);
            } else if (nodeStatus === 'FAILED') {
              updateNodeState(nodeIdStr, {
                status: 'error',
                endTime: new Date(),
                error: batchEventData.error || 'Unknown error'
              });

              executionActions.updateNodeExecution(nodeId(nodeIdStr), {
                status: Status.FAILED,
                timestamp: Date.now(),
                error: batchEventData.error ?? undefined
              });

              showThrottledToast(`node-error-${nodeIdStr}`, 'error', `Node ${nodeIdStr.slice(0, 8)}... failed: ${batchEventData.error}`);
            } else if (nodeStatus === 'SKIPPED') {
              incrementCompletedNodes();

              updateNodeState(nodeIdStr, {
                status: 'skipped',
                endTime: new Date(),
              });

              addSkippedNode(nodeIdStr, 'Skipped');
              executionActions.updateNodeExecution(nodeId(nodeIdStr), {
                status: Status.SKIPPED,
                timestamp: Date.now()
              });
            }
          }
        }
        // Handle node events from batch
        else if (batchEventType === 'node_started' || batchEventType === 'node_completed') {
          const nodeIdStr = event.data?.nodeId || '';
          const nodeType = event.data?.nodeType || '';

          if (batchEventType === 'node_started' && nodeIdStr) {
            // console.log('[useExecutionUpdates] Batch node_started:', { nodeIdStr, nodeType });
            handleNodeStart(nodeIdStr, nodeType);
          } else if (batchEventType === 'node_completed' && nodeIdStr) {
            const tokenCount = event.data?.tokens_used || event.data?.metrics?.tokens || undefined;
            const output = event.data?.output || event.data?.result || undefined;
            // console.log('[useExecutionUpdates] Batch node_completed:', { nodeIdStr, tokenCount });
            handleNodeComplete(nodeIdStr, tokenCount, output);
          }
        }
      }
      return; // Don't process the batch wrapper as an individual event
    }

    // Check for critical execution-level events FIRST (no throttling for these)
    const status = eventData.status || executionUpdates.status;
    const error = eventData.error || executionUpdates.error;
    const tokenUsage = eventData.tokenUsage || executionUpdates.tokenUsage;

    // Handle EXECUTION completion events immediately (bypass throttling)
    if (eventType === 'EXECUTION_COMPLETED') {
      // Only log important status changes
      if (status === 'COMPLETED' || status === 'FAILED' || status === 'ABORTED') {
        console.log('[useExecutionUpdates] Execution status:', status);
      }
      if (status === 'COMPLETED' || status === 'MAXITER_REACHED') {
        const totalTokens = tokenUsage ?
          (tokenUsage.input + tokenUsage.output + (tokenUsage.cached || 0)) :
          undefined;

        completeExecution();
        executionActions.stopExecution();

        const tokensMsg = totalTokens ? ` (${totalTokens.toLocaleString()} tokens)` : '';
        const statusMsg = status === 'MAXITER_REACHED' ? 'reached max iterations' : 'completed';
        showThrottledToast('execution-complete', 'success', `Execution ${statusMsg}${tokensMsg}`);

        onUpdate?.({
          type: EventType.EXECUTION_COMPLETED,
          execution_id: executionId(executionIdRef.current!),
          total_tokens: totalTokens,
          timestamp: new Date().toISOString()
        });
        return; // Don't process further
      } else if (status === 'FAILED' && error) {
        errorExecution(error);
        executionActions.stopExecution();

        showThrottledToast('execution-error', 'error', `Execution failed: ${error}`);

        onUpdate?.({
          type: EventType.EXECUTION_ERROR,
          execution_id: executionId(executionIdRef.current!),
          error,
          timestamp: new Date().toISOString()
        });
        return; // Don't process further
      } else if (status === 'ABORTED') {
        errorExecution('Execution aborted');
        executionActions.stopExecution();

        showThrottledToast('execution-aborted', 'error', 'Execution aborted');

        onUpdate?.({
          type: EventType.EXECUTION_COMPLETED,
          execution_id: executionId(executionIdRef.current!),
          timestamp: new Date().toISOString()
        });
        return; // Don't process further
      } else if (status === 'TIMEOUT' || status === 'TIMED_OUT') {
        errorExecution('Execution timed out');
        executionActions.stopExecution();

        showThrottledToast('execution-timeout', 'error', 'Execution timed out');

        onUpdate?.({
          type: EventType.EXECUTION_COMPLETED,
          execution_id: executionId(executionIdRef.current!),
          timestamp: new Date().toISOString()
        });
        return; // Don't process further
      }
    }

    // Handle node events (with throttling)
    if (eventType === 'NODE_STARTED') {
      const nodeIdStr = executionUpdates.node_id || '';
      const nodeType = executionUpdates.node_type || '';

      if (nodeIdStr) {
        // console.log('[useExecutionUpdates] ✅ Node started event:', { nodeIdStr, nodeType });
        handleNodeStart(nodeIdStr, nodeType);
      } else {
        console.warn('[useExecutionUpdates] NODE_STARTED event missing node_id:', executionUpdates);
      }
      return;
    } else if (eventType === 'NODE_COMPLETED') {
      const nodeIdStr = executionUpdates.node_id || '';
      const tokenCount = executionUpdates.tokens_used || executionUpdates.metrics?.tokens || undefined;
      const output = executionUpdates.output || executionUpdates.result || undefined;

      if (nodeIdStr) {
        // console.log('[useExecutionUpdates] ✅ Node completed event:', { nodeIdStr, tokenCount, output });
        handleNodeComplete(nodeIdStr, tokenCount, output);
      } else {
        console.warn('[useExecutionUpdates] NODE_COMPLETED event missing node_id:', executionUpdates);
      }
      return;
    } else if (eventType === 'NODE_ERROR') {
      const nodeIdStr = executionUpdates.node_id || '';
      const error = executionUpdates.error || 'Unknown error';

      if (nodeIdStr) {
        updateNodeState(nodeIdStr, {
          status: 'error',
          endTime: new Date(),
          error
        });

        executionActions.updateNodeExecution(nodeId(nodeIdStr), {
          status: Status.FAILED,
          timestamp: Date.now(),
          error
        });

        showThrottledToast(`node-error-${nodeIdStr}`, 'error', `Node ${nodeIdStr.slice(0, 8)}... failed: ${error}`);
      }
      return;
    }
  }, [executionUpdates, handleNodeStart, handleNodeComplete, completeExecution, errorExecution, executionActions, showThrottledToast, onUpdate, executionIdRef, updateNodeState, addSkippedNode, incrementCompletedNodes, setCurrentNode]);

  // Runtime assertion for deprecated nodeUpdates format
  // All node updates should now come through executionUpdates with event_type NODE_STARTED/NODE_COMPLETED
  useEffect(() => {
    if (nodeUpdates) {
      console.error('[useExecutionUpdates] Unexpected legacy nodeUpdates format detected. Node events should be delivered through executionUpdates with event_type NODE_STARTED/NODE_COMPLETED');
      // Log the unexpected event shape for debugging
      console.error('Legacy nodeUpdates shape:', nodeUpdates);
    }
  }, [nodeUpdates]);

  // Process interactive prompt updates
  useEffect(() => {
    if (!interactivePrompts) return;

    setInteractivePrompt({
      executionId: executionId(interactivePrompts.execution_id),
      nodeId: nodeId(interactivePrompts.node_id),
      prompt: interactivePrompts.prompt,
      timeout: interactivePrompts.timeout_seconds || undefined,
    });

    onUpdate?.({
      type: EventType.INTERACTIVE_PROMPT,
      execution_id: executionId(executionIdRef.current!),
      node_id: nodeId(interactivePrompts.node_id),
      status: Status.PAUSED,
      timestamp: new Date().toISOString()
    });
  }, [interactivePrompts, setInteractivePrompt, onUpdate, executionIdRef]);

  // Cleanup refs on unmount
  useEffect(() => {
    return () => {
      lastNodeStartRef.current = {};
      lastNodeCompleteRef.current = {};
    };
  }, []);
}
