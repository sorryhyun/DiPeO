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
      type: EventType.NODE_STATUS_CHANGED, 
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
      type: EventType.NODE_STATUS_CHANGED, 
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
    
    // Log all updates for debugging
    console.log('[useExecutionUpdates] Received update:', {
      event_type: executionUpdates.event_type,
      data: executionUpdates.data,
      full: executionUpdates
    });
    
    // Check if this is a node event
    const eventType = executionUpdates.event_type;
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
    console.log('[useExecutionUpdates] Parsed eventData:', eventData);
    
    // Handle batch updates
    if (eventType === 'BATCH_UPDATE' && eventData.events && Array.isArray(eventData.events)) {
      console.log('[useExecutionUpdates] Processing batch update with', eventData.events.length, 'events');
      
      // Process each event in the batch
      for (const event of eventData.events) {
        const batchEventType = event.type;
        const batchEventData = event.data || {};
        
        // Handle node status changes from batch
        if (batchEventType === 'NODE_STATUS_CHANGED') {
          const nodeIdStr = batchEventData.node_id || '';
          const nodeType = batchEventData.node_type || '';
          const nodeStatus = batchEventData.status || '';
          
          if (nodeIdStr && nodeStatus) {
            console.log('[useExecutionUpdates] Batch NODE_STATUS_CHANGED:', { nodeIdStr, nodeType, nodeStatus });
            
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
        // Handle legacy node events from batch
        else if (batchEventType === 'node_started' || batchEventType === 'node_completed') {
          const nodeIdStr = event.data?.nodeId || '';
          const nodeType = event.data?.nodeType || '';
          
          if (batchEventType === 'node_started' && nodeIdStr) {
            console.log('[useExecutionUpdates] Batch node_started:', { nodeIdStr, nodeType });
            handleNodeStart(nodeIdStr, nodeType);
          } else if (batchEventType === 'node_completed' && nodeIdStr) {
            const tokenCount = event.data?.tokens_used || event.data?.metrics?.tokens || undefined;
            const output = event.data?.output || event.data?.result || undefined;
            console.log('[useExecutionUpdates] Batch node_completed:', { nodeIdStr, tokenCount });
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
    if (eventType === 'EXECUTION_STATUS_CHANGED' || eventType === 'EXECUTION_COMPLETED') {
      console.log('[useExecutionUpdates] EXECUTION_STATUS_CHANGED event:', { status, eventData });
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
          type: EventType.EXECUTION_STATUS_CHANGED, 
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
          type: EventType.EXECUTION_STATUS_CHANGED, 
          execution_id: executionId(executionIdRef.current!),
          timestamp: new Date().toISOString() 
        });
        return; // Don't process further
      }
    }
    
    // Handle node events (with throttling)
    if (eventType === 'NODE_STATUS_CHANGED') {
      const nodeIdStr = eventData.node_id || eventData.nodeId || '';
      const nodeType = eventData.node_type || eventData.nodeType || '';
      const nodeStatus = eventData.status || '';
      
      console.log('[useExecutionUpdates] NODE_STATUS_CHANGED - Extracting fields:', {
        nodeIdStr,
        nodeType,
        nodeStatus,
        eventDataKeys: Object.keys(eventData),
        eventDataType: typeof eventData,
      });
      
      if (nodeIdStr && nodeStatus) {
        console.log('[useExecutionUpdates] ✅ Node status changed:', { nodeIdStr, nodeType, nodeStatus });
        
        if (nodeStatus === 'RUNNING') {
          handleNodeStart(nodeIdStr, nodeType);
        } else if (nodeStatus === 'COMPLETED' || nodeStatus === 'MAXITER_REACHED') {
          const tokenCount = eventData.tokens_used || eventData.metrics?.tokens || undefined;
          const output = eventData.output || eventData.result || undefined;
          handleNodeComplete(nodeIdStr, tokenCount, output);
        } else if (nodeStatus === 'FAILED') {
          updateNodeState(nodeIdStr, {
            status: 'error',
            endTime: new Date(),
            error: eventData.error || 'Unknown error'
          });
          
          executionActions.updateNodeExecution(nodeId(nodeIdStr), {
            status: Status.FAILED,
            timestamp: Date.now(),
            error: eventData.error ?? undefined
          });
          
          showThrottledToast(`node-error-${nodeIdStr}`, 'error', `Node ${nodeIdStr.slice(0, 8)}... failed: ${eventData.error}`);
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
      } else {
        console.warn('[useExecutionUpdates] NODE_STATUS_CHANGED event missing node_id or status:', eventData);
      }
      return;
    } else if (eventType === 'NODE_STARTED') {
      const nodeIdStr = eventData.node_id || eventData.nodeId || '';
      const nodeType = eventData.node_type || eventData.nodeType || '';
      
      if (nodeIdStr) {
        console.log('[useExecutionUpdates] ✅ Node started event:', { nodeIdStr, nodeType });
        handleNodeStart(nodeIdStr, nodeType);
      } else {
        console.warn('[useExecutionUpdates] NODE_STARTED event missing node_id:', eventData);
      }
      return;
    } else if (eventType === 'NODE_COMPLETED') {
      const nodeIdStr = eventData.node_id || eventData.nodeId || '';
      const tokenCount = eventData.tokens_used || eventData.metrics?.tokens || undefined;
      const output = eventData.output || eventData.result || undefined;
      
      if (nodeIdStr) {
        console.log('[useExecutionUpdates] ✅ Node completed event:', { nodeIdStr, tokenCount, output });
        handleNodeComplete(nodeIdStr, tokenCount, output);
      } else {
        console.warn('[useExecutionUpdates] NODE_COMPLETED event missing node_id:', eventData);
      }
      return;
    }
  }, [executionUpdates, handleNodeStart, handleNodeComplete, completeExecution, errorExecution, executionActions, showThrottledToast, onUpdate, executionIdRef, updateNodeState, addSkippedNode, incrementCompletedNodes, setCurrentNode]);

  // Process node subscription updates - DEPRECATED
  // Node updates are now handled through executionUpdates with event_type NODE_STARTED/NODE_COMPLETED
  useEffect(() => {
    if (!nodeUpdates) return;
    
    // This code path is deprecated - nodeUpdates is always undefined
    // Node events are now processed in the executionUpdates effect above
    console.warn('[useExecutionUpdates] Deprecated nodeUpdates path - this should not be reached');
    
    // The nodeUpdates might be the data directly or wrapped in a data field
    const updateData = nodeUpdates.data || nodeUpdates;
    const status = updateData.status || '';
    const nodeIdStr = updateData.node_id || '';
    
    console.log('[useExecutionUpdates] Node update received (deprecated path):', { status, nodeIdStr, updateData });

    if (status === 'RUNNING' && nodeIdStr) {
      handleNodeStart(nodeIdStr, updateData.node_type);
    } else if ((status === 'COMPLETED' || status === 'MAXITER_REACHED') && nodeIdStr) {
      handleNodeComplete(nodeIdStr, updateData.tokens_used || undefined, updateData.output);
      
      // Check if all nodes are done and we should complete the execution
      if (status === 'MAXITER_REACHED') {
        const totalNodes = state.execution.totalNodes;
        const completedNodes = state.execution.completedNodes + 1; // +1 for the current node
        
        if (completedNodes >= totalNodes && state.execution.isRunning) {
          // All nodes done, complete the execution
          completeExecution();
          executionActions.stopExecution();
          
          showThrottledToast('execution-maxiter', 'success', 'Execution completed (max iterations reached)');
          
          onUpdate?.({ 
            type: EventType.EXECUTION_STATUS_CHANGED, 
            execution_id: executionId(executionIdRef.current!),
            timestamp: new Date().toISOString() 
          });
        }
      }
    } else if (status === 'FAILED' && nodeIdStr) {
      updateNodeState(nodeIdStr, {
        status: 'error',
        endTime: new Date(),
        error: updateData.error || 'Unknown error'
      });
      
      executionActions.updateNodeExecution(nodeId(nodeIdStr), {
        status: Status.FAILED,
        timestamp: Date.now(),
        error: updateData.error ?? undefined
      });
      
      showThrottledToast(`node-error-${nodeIdStr}`, 'error', `Node ${nodeIdStr.slice(0, 8)}... failed: ${updateData.error}`);
      
      onUpdate?.({ 
        type: EventType.EXECUTION_ERROR,
        execution_id: executionId(executionIdRef.current!),
        node_id: nodeId(nodeIdStr),
        error: updateData.error || undefined, 
        status: Status.FAILED, 
        timestamp: new Date().toISOString() 
      });
    } else if (status === 'SKIPPED' && nodeIdStr) {
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
      
      onUpdate?.({ 
        type: EventType.EXECUTION_UPDATE,
        execution_id: executionId(executionIdRef.current!),
        node_id: nodeId(nodeIdStr),
        status: Status.SKIPPED, 
        timestamp: new Date().toISOString() 
      });
    } else if (status === 'PAUSED' && nodeIdStr) {
      updateNodeState(nodeIdStr, {
        status: 'paused'
      });
      
      onUpdate?.({ 
        type: EventType.NODE_STATUS_CHANGED, 
        execution_id: executionId(executionIdRef.current!),
        node_id: nodeId(nodeIdStr),
        status: Status.PAUSED, 
        timestamp: new Date().toISOString() 
      });
    }
    
    // Handle progress updates
    if (updateData.progress && nodeIdStr) {
      updateNodeState(nodeIdStr, {
        progress: updateData.progress
      });
      
      onUpdate?.({ 
        type: EventType.NODE_PROGRESS, 
        execution_id: executionId(executionIdRef.current!),
        node_id: nodeId(nodeIdStr),
        status: Status.RUNNING, 
        timestamp: new Date().toISOString() 
      });
    }
  }, [nodeUpdates, handleNodeStart, handleNodeComplete, updateNodeState, incrementCompletedNodes, addSkippedNode, executionActions, showThrottledToast, onUpdate, executionIdRef, state, completeExecution]);

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