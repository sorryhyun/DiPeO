import { useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { NodeExecutionStatus, EventType, type ExecutionUpdate } from '@dipeo/models';
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
      status: NodeExecutionStatus.RUNNING,
      timestamp: Date.now()
    });
    
    onUpdate?.({ 
      type: EventType.NODE_STATUS_CHANGED, 
      execution_id: executionId(executionIdRef.current!),
      node_id: nodeId(nodeIdStr),
      node_type: nodeType,
      status: NodeExecutionStatus.RUNNING, 
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
      status: NodeExecutionStatus.COMPLETED,
      timestamp: Date.now()
    });
    
    addToRunContext(output);
    
    onUpdate?.({ 
      type: EventType.NODE_STATUS_CHANGED, 
      execution_id: executionId(executionIdRef.current!),
      node_id: nodeId(nodeIdStr),
      tokens: tokenCount, 
      result: output, 
      status: NodeExecutionStatus.COMPLETED, 
      timestamp: new Date().toISOString() 
    });
  }, [incrementCompletedNodes, setCurrentNode, updateNodeState, executionActions, addToRunContext, onUpdate, executionIdRef, currentRunningNodeRef]);

  // Process execution subscription updates
  useEffect(() => {
    if (!executionUpdates) return;
    
    // Extract status from the data field (GraphQL subscription format)
    const status = executionUpdates.data?.status || executionUpdates.status;
    const error = executionUpdates.data?.error || executionUpdates.error;
    const tokenUsage = executionUpdates.data?.tokenUsage || executionUpdates.tokenUsage;
    
    if (status === 'COMPLETED' || status === 'MAXITER_REACHED') {
      const totalTokens = tokenUsage ? 
        (tokenUsage.input + tokenUsage.output + (tokenUsage.cached || 0)) : 
        undefined;
      
      completeExecution();
      executionActions.stopExecution();
      
      const tokensMsg = totalTokens ? ` (${totalTokens.toLocaleString()} tokens)` : '';
      const statusMsg = status === 'MAXITER_REACHED' ? 'reached max iterations' : 'completed';
      showThrottledToast('execution-complete', 'success', `Execution ${statusMsg}${tokensMsg}`);
      
      // Auto-exit is now handled by useMonitorMode
      // No need to check URL params here
      
      onUpdate?.({ 
        type: EventType.EXECUTION_STATUS_CHANGED, 
        execution_id: executionId(executionIdRef.current!),
        total_tokens: totalTokens,
        timestamp: new Date().toISOString() 
      });
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
      
      // Auto-exit is now handled by useMonitorMode
      // No need to check URL params here
    } else if (status === 'ABORTED') {
      errorExecution('Execution aborted');
      executionActions.stopExecution();
      
      showThrottledToast('execution-aborted', 'error', 'Execution aborted');
      
      onUpdate?.({ 
        type: EventType.EXECUTION_STATUS_CHANGED, 
        execution_id: executionId(executionIdRef.current!),
        timestamp: new Date().toISOString() 
      });
    }
  }, [executionUpdates, completeExecution, errorExecution, executionActions, showThrottledToast, onUpdate, executionIdRef]);

  // Process node subscription updates
  useEffect(() => {
    if (!nodeUpdates) return;
    
    // The nodeUpdates might be the data directly or wrapped in a data field
    const updateData = nodeUpdates.data || nodeUpdates;
    const status = updateData.status || '';
    const nodeIdStr = updateData.node_id || '';

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
        status: NodeExecutionStatus.FAILED,
        timestamp: Date.now(),
        error: updateData.error ?? undefined
      });
      
      showThrottledToast(`node-error-${nodeIdStr}`, 'error', `Node ${nodeIdStr.slice(0, 8)}... failed: ${updateData.error}`);
      
      onUpdate?.({ 
        type: EventType.EXECUTION_ERROR,
        execution_id: executionId(executionIdRef.current!),
        node_id: nodeId(nodeIdStr),
        error: updateData.error || undefined, 
        status: NodeExecutionStatus.FAILED, 
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
        status: NodeExecutionStatus.SKIPPED,
        timestamp: Date.now()
      });
      
      onUpdate?.({ 
        type: EventType.EXECUTION_UPDATE,
        execution_id: executionId(executionIdRef.current!),
        node_id: nodeId(nodeIdStr),
        status: NodeExecutionStatus.SKIPPED, 
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
        status: NodeExecutionStatus.PAUSED, 
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
        status: NodeExecutionStatus.RUNNING, 
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
      status: NodeExecutionStatus.PAUSED, 
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