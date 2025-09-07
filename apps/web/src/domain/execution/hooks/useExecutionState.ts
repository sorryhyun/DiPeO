import { useState, useRef, useCallback } from 'react';
import type { InteractivePromptData } from '@/domain/execution/types/execution';

export interface HookExecutionState {
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

const initialExecutionState: HookExecutionState = {
  isRunning: false,
  executionId: null,
  totalNodes: 0,
  completedNodes: 0,
  currentNode: null,
  startTime: null,
  endTime: null,
  error: null,
};

export function useExecutionState() {
  const [execution, setExecution] = useState<HookExecutionState>(initialExecutionState);
  const [nodeStates, setNodeStates] = useState<Record<string, NodeState>>({});
  const [interactivePrompt, setInteractivePrompt] = useState<InteractivePromptData | null>(null);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState('0s');

  // Refs for internal state
  const executionIdRef = useRef<string | null>(null);
  const durationInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<Date | null>(null);
  const runContextRef = useRef<Record<string, unknown>>({});
  const skippedNodesRef = useRef<Array<{ nodeId: string; reason: string }>>([]);
  const currentRunningNodeRef = useRef<string | null>(null);

  // State management functions
  const startExecution = useCallback((executionIdStr: string, totalNodes: number, formatDuration: boolean = true) => {
    const now = new Date();
    startTimeRef.current = now;
    executionIdRef.current = executionIdStr;

    setExecution({
      isRunning: true,
      executionId: executionIdStr,
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
  }, []);

  const completeExecution = useCallback(() => {
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
  }, []);

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
  }, []);

  const updateNodeState = useCallback((nodeIdStr: string, update: Partial<NodeState>) => {
    setNodeStates(prev => ({
      ...prev,
      [nodeIdStr]: {
        ...(prev[nodeIdStr] || { startTime: null, endTime: null, status: 'pending' }),
        ...update
      } as NodeState
    }));
  }, []);

  const setCurrentNode = useCallback((nodeIdStr: string | null) => {
    setExecution(prev => ({
      ...prev,
      currentNode: nodeIdStr,
    }));
    currentRunningNodeRef.current = nodeIdStr;
  }, []);

  const incrementCompletedNodes = useCallback(() => {
    setExecution(prev => ({
      ...prev,
      completedNodes: prev.completedNodes + 1,
    }));
  }, []);

  const updateProgress = useCallback((totalNodes: number, completedNodes: number) => {
    if (totalNodes > 0) {
      setProgress(Math.round(((completedNodes + 1) / totalNodes) * 100));
    }
  }, []);

  const resetState = useCallback(() => {
    setExecution(initialExecutionState);
    setNodeStates({});
    setInteractivePrompt(null);
    setProgress(0);
    setDuration('0s');
    runContextRef.current = {};
    skippedNodesRef.current = [];
    currentRunningNodeRef.current = null;
    executionIdRef.current = null;

    if (durationInterval.current) {
      clearInterval(durationInterval.current);
      durationInterval.current = null;
    }
  }, []);

  const addToRunContext = useCallback((data: unknown) => {
    if (data && typeof data === 'object') {
      runContextRef.current = { ...runContextRef.current, ...data };
    }
  }, []);

  const addSkippedNode = useCallback((nodeIdStr: string, reason: string) => {
    skippedNodesRef.current.push({ nodeId: nodeIdStr, reason });
  }, []);

  const connectToExecution = useCallback((executionIdStr: string, totalNodes: number = 0) => {
    executionIdRef.current = executionIdStr;

    setExecution({
      isRunning: true,
      executionId: executionIdStr,
      totalNodes,
      completedNodes: 0,
      currentNode: null,
      startTime: new Date(), // We'll update this from the actual execution data
      endTime: null,
      error: null,
    });

    // Clear any existing node states when connecting to a new execution
    setNodeStates({});
  }, []);

  return {
    // State
    execution,
    nodeStates,
    interactivePrompt,
    progress,
    duration,

    // Refs
    executionIdRef,
    currentRunningNodeRef,
    runContextRef,
    skippedNodesRef,
    durationInterval,

    // Actions
    startExecution,
    connectToExecution,
    completeExecution,
    errorExecution,
    updateNodeState,
    setCurrentNode,
    incrementCompletedNodes,
    updateProgress,
    resetState,
    setInteractivePrompt,
    addToRunContext,
    addSkippedNode,
  };
}
