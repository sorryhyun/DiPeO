import { useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { NodeExecutionStatus, ExecutionStatus, EventType, type ExecutionUpdate } from '@dipeo/domain-models';
import { nodeId, executionId } from '@/core/types';
import { useExecutionState } from './useExecutionState';
import { useUnifiedStore } from '@/core/store/unifiedStore';

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
      status: 'running',
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
    
    if (executionUpdates.status === ExecutionStatus.COMPLETED || executionUpdates.status === 'MAXITER_REACHED') {
      const totalTokens = executionUpdates.tokenUsage ? 
        (executionUpdates.tokenUsage.input + executionUpdates.tokenUsage.output + (executionUpdates.tokenUsage.cached || 0)) : 
        undefined;
      
      completeExecution();
      executionActions.stopExecution();
      
      const tokensMsg = totalTokens ? ` (${totalTokens.toLocaleString()} tokens)` : '';
      const statusMsg = executionUpdates.status === 'MAXITER_REACHED' ? 'reached max iterations' : 'completed';
      showThrottledToast('execution-complete', 'success', `Execution ${statusMsg}${tokensMsg}`);
      
      // Auto-exit is now handled by useMonitorMode
      // No need to check URL params here
      
      onUpdate?.({ 
        type: EventType.EXECUTION_STATUS_CHANGED, 
        execution_id: executionId(executionIdRef.current!),
        total_tokens: totalTokens,
        timestamp: new Date().toISOString() 
      });
    } else if (executionUpdates.status === ExecutionStatus.FAILED && executionUpdates.error) {
      errorExecution(executionUpdates.error);
      executionActions.stopExecution();
      
      showThrottledToast('execution-error', 'error', `Execution failed: ${executionUpdates.error}`);
      
      onUpdate?.({ 
        type: EventType.EXECUTION_ERROR, 
        execution_id: executionId(executionIdRef.current!),
        error: executionUpdates.error, 
        timestamp: new Date().toISOString() 
      });
      
      // Auto-exit is now handled by useMonitorMode
      // No need to check URL params here
    } else if (executionUpdates.status === ExecutionStatus.ABORTED) {
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
    
    const status = nodeUpdates.status || '';

    if (status === 'RUNNING') {
      handleNodeStart(nodeUpdates.node_id, nodeUpdates.node_type);
    } else if (status === 'COMPLETED' || status === 'MAXITER_REACHED') {
      handleNodeComplete(nodeUpdates.node_id, nodeUpdates.tokens_used || undefined, nodeUpdates.output);
      
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
    } else if (status === 'FAILED') {
      updateNodeState(nodeUpdates.node_id, {
        status: 'error',
        endTime: new Date(),
        error: nodeUpdates.error || 'Unknown error'
      });
      
      executionActions.updateNodeExecution(nodeId(nodeUpdates.node_id), {
        status: NodeExecutionStatus.FAILED,
        timestamp: Date.now(),
        error: nodeUpdates.error ?? undefined
      });
      
      showThrottledToast(`node-error-${nodeUpdates.node_id}`, 'error', `Node ${nodeUpdates.node_id.slice(0, 8)}... failed: ${nodeUpdates.error}`);
      
      onUpdate?.({ 
        type: EventType.EXECUTION_ERROR,
        execution_id: executionId(executionIdRef.current!),
        node_id: nodeId(nodeUpdates.node_id),
        error: nodeUpdates.error || undefined, 
        status: NodeExecutionStatus.FAILED, 
        timestamp: new Date().toISOString() 
      });
    } else if (status === 'SKIPPED') {
      incrementCompletedNodes();
      
      updateNodeState(nodeUpdates.node_id, {
        status: 'skipped',
        endTime: new Date(),
      });
      
      addSkippedNode(nodeUpdates.node_id, 'Skipped');
      executionActions.updateNodeExecution(nodeId(nodeUpdates.node_id), {
        status: NodeExecutionStatus.SKIPPED,
        timestamp: Date.now()
      });
      
      onUpdate?.({ 
        type: EventType.EXECUTION_UPDATE,
        execution_id: executionId(executionIdRef.current!),
        node_id: nodeId(nodeUpdates.node_id),
        status: NodeExecutionStatus.SKIPPED, 
        timestamp: new Date().toISOString() 
      });
    } else if (status === 'PAUSED') {
      updateNodeState(nodeUpdates.node_id, {
        status: 'paused'
      });
      
      onUpdate?.({ 
        type: EventType.NODE_STATUS_CHANGED, 
        execution_id: executionId(executionIdRef.current!),
        node_id: nodeId(nodeUpdates.node_id),
        status: NodeExecutionStatus.PAUSED, 
        timestamp: new Date().toISOString() 
      });
    }
    
    // Handle progress updates
    if (nodeUpdates.progress) {
      updateNodeState(nodeUpdates.node_id, {
        progress: nodeUpdates.progress
      });
      
      onUpdate?.({ 
        type: EventType.NODE_PROGRESS, 
        execution_id: executionId(executionIdRef.current!),
        node_id: nodeId(nodeUpdates.node_id),
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