import { useEffect, useMemo, useCallback } from 'react';
import { toast } from 'sonner';
import { NodeExecutionStatus, ExecutionStatus, EventType } from '@dipeo/domain-models';
import { nodeId, executionId } from '@/core/types';
import { throttle } from '../utils/executionHelpers';
import type { ExecutionUpdate } from '@dipeo/domain-models';
import { useExecutionState } from './useExecutionState';

interface UseExecutionUpdatesProps {
  state: ReturnType<typeof useExecutionState>;
  executionActions: any; // Store actions
  showToasts?: boolean;
  onUpdate?: (update: ExecutionUpdate) => void;
  executionUpdates?: any;
  nodeUpdates?: any;
  interactivePrompts?: any;
}

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

  // Handle node start
  const handleNodeStart = useMemo(() => throttle((nodeIdStr: string, nodeType: string) => {
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
      type: EventType.NODE_STARTED, 
      executionId: executionId(executionIdRef.current!), 
      nodeId: nodeId(nodeIdStr), 
      nodeType, 
      status: NodeExecutionStatus.RUNNING, 
      timestamp: new Date().toISOString() 
    });
  }, 50), [setCurrentNode, updateNodeState, executionActions, onUpdate, executionIdRef]);

  // Handle node complete
  const handleNodeComplete = useMemo(() => throttle((nodeIdStr: string, tokenCount?: number, output?: unknown) => {
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
      type: EventType.NODE_COMPLETED, 
      executionId: executionId(executionIdRef.current!), 
      nodeId: nodeId(nodeIdStr), 
      tokens: tokenCount, 
      result: output, 
      status: NodeExecutionStatus.COMPLETED, 
      timestamp: new Date().toISOString() 
    });
  }, 50), [incrementCompletedNodes, setCurrentNode, updateNodeState, executionActions, addToRunContext, onUpdate, executionIdRef, currentRunningNodeRef]);

  // Process execution subscription updates
  useEffect(() => {
    if (!executionUpdates) return;
    
    if (executionUpdates.status === ExecutionStatus.COMPLETED) {
      const totalTokens = executionUpdates.tokenUsage ? 
        (executionUpdates.tokenUsage.input + executionUpdates.tokenUsage.output + (executionUpdates.tokenUsage.cached || 0)) : 
        undefined;
      
      completeExecution();
      executionActions.stopExecution();
      
      if (showToasts) {
        const tokensMsg = totalTokens ? ` (${totalTokens.toLocaleString()} tokens)` : '';
        toast.success(`Execution completed${tokensMsg}`);
      }
      
      onUpdate?.({ 
        type: EventType.EXECUTION_COMPLETED, 
        executionId: executionId(executionIdRef.current!), 
        totalTokens, 
        timestamp: new Date().toISOString() 
      });
    } else if (executionUpdates.status === ExecutionStatus.FAILED && executionUpdates.error) {
      errorExecution(executionUpdates.error);
      executionActions.stopExecution();
      
      if (showToasts) {
        toast.error(`Execution failed: ${executionUpdates.error}`);
      }
      
      onUpdate?.({ 
        type: EventType.EXECUTION_ERROR, 
        executionId: executionId(executionIdRef.current!), 
        error: executionUpdates.error, 
        timestamp: new Date().toISOString() 
      });
    } else if (executionUpdates.status === ExecutionStatus.ABORTED) {
      errorExecution('Execution aborted');
      executionActions.stopExecution();
      
      if (showToasts) {
        toast.error('Execution aborted');
      }
      
      onUpdate?.({ 
        type: EventType.EXECUTION_ABORTED, 
        executionId: executionId(executionIdRef.current!), 
        timestamp: new Date().toISOString() 
      });
    }
  }, [executionUpdates, completeExecution, errorExecution, executionActions, showToasts, onUpdate, executionIdRef]);

  // Process node subscription updates
  useEffect(() => {
    if (!nodeUpdates) return;
    
    const status = (nodeUpdates.status || '').toLowerCase();

    if (status === 'running') {
      handleNodeStart(nodeUpdates.nodeId, nodeUpdates.nodeType);
    } else if (status === 'completed') {
      handleNodeComplete(nodeUpdates.nodeId, nodeUpdates.tokensUsed || undefined, nodeUpdates.output);
    } else if (status === 'failed') {
      updateNodeState(nodeUpdates.nodeId, {
        status: 'error',
        endTime: new Date(),
        error: nodeUpdates.error || 'Unknown error'
      });
      
      executionActions.updateNodeExecution(nodeId(nodeUpdates.nodeId), {
        status: NodeExecutionStatus.FAILED,
        timestamp: Date.now(),
        error: nodeUpdates.error ?? undefined
      });
      
      if (showToasts) {
        toast.error(`Node ${nodeUpdates.nodeId.slice(0, 8)}... failed: ${nodeUpdates.error}`);
      }
      
      onUpdate?.({ 
        type: EventType.NODE_FAILED, 
        executionId: executionId(executionIdRef.current!), 
        nodeId: nodeId(nodeUpdates.nodeId), 
        error: nodeUpdates.error || undefined, 
        status: NodeExecutionStatus.FAILED, 
        timestamp: new Date().toISOString() 
      });
    } else if (status === 'skipped') {
      incrementCompletedNodes();
      
      updateNodeState(nodeUpdates.nodeId, {
        status: 'skipped',
        endTime: new Date(),
      });
      
      addSkippedNode(nodeUpdates.nodeId, 'Skipped');
      executionActions.updateNodeExecution(nodeId(nodeUpdates.nodeId), {
        status: NodeExecutionStatus.SKIPPED,
        timestamp: Date.now()
      });
      
      onUpdate?.({ 
        type: EventType.NODE_SKIPPED, 
        executionId: executionId(executionIdRef.current!), 
        nodeId: nodeId(nodeUpdates.nodeId), 
        status: NodeExecutionStatus.SKIPPED, 
        timestamp: new Date().toISOString() 
      });
    } else if (status === 'paused') {
      updateNodeState(nodeUpdates.nodeId, {
        status: 'paused'
      });
      
      onUpdate?.({ 
        type: EventType.NODE_PAUSED, 
        executionId: executionId(executionIdRef.current!), 
        nodeId: nodeId(nodeUpdates.nodeId), 
        status: NodeExecutionStatus.PAUSED, 
        timestamp: new Date().toISOString() 
      });
    }
    
    // Handle progress updates
    if (nodeUpdates.progress) {
      updateNodeState(nodeUpdates.nodeId, {
        progress: nodeUpdates.progress
      });
      
      onUpdate?.({ 
        type: EventType.NODE_PROGRESS, 
        executionId: executionId(executionIdRef.current!), 
        nodeId: nodeId(nodeUpdates.nodeId), 
        status: NodeExecutionStatus.RUNNING, 
        timestamp: new Date().toISOString() 
      });
    }
  }, [nodeUpdates, handleNodeStart, handleNodeComplete, updateNodeState, incrementCompletedNodes, addSkippedNode, executionActions, showToasts, onUpdate, executionIdRef]);

  // Process interactive prompt updates
  useEffect(() => {
    if (!interactivePrompts) return;
    
    setInteractivePrompt({
      executionId: executionId(interactivePrompts.executionId),
      nodeId: nodeId(interactivePrompts.nodeId),
      prompt: interactivePrompts.prompt,
      timeout: interactivePrompts.timeoutSeconds || undefined,
    });
    
    onUpdate?.({ 
      type: EventType.INTERACTIVE_PROMPT, 
      executionId: executionId(executionIdRef.current!), 
      nodeId: nodeId(interactivePrompts.nodeId), 
      status: NodeExecutionStatus.PAUSED, 
      timestamp: new Date().toISOString() 
    });
  }, [interactivePrompts, setInteractivePrompt, onUpdate, executionIdRef]);
}