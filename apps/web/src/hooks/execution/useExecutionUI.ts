/**
 * useExecutionUI - UI concerns and formatting for execution
 * 
 * This hook handles all UI-related aspects of execution including
 * toast notifications, formatting, and user-friendly messages.
 */

import { useCallback, useState, useEffect } from 'react';
import { toast } from 'sonner';
import type { NodeStateV2 } from './useExecutionState';
import type { InteractivePromptData } from '@/types';

export interface UseExecutionUIOptions {
  showToasts?: boolean;
  formatDuration?: boolean;
}

export interface UseExecutionUIReturn {
  // UI State
  interactivePrompt: InteractivePromptData | null;
  executionProgress: number;
  executionDuration: string;
  currentNodeName: string | null;
  
  // UI Actions
  showExecutionStart: (executionId: string, totalNodes: number) => void;
  showExecutionComplete: (executionId: string, duration: number, totalTokens?: number) => void;
  showExecutionError: (error: string) => void;
  showNodeStart: (nodeId: string, nodeType: string) => void;
  showNodeComplete: (nodeId: string, nodeType: string) => void;
  showNodeError: (nodeId: string, error: string) => void;
  showNodeSkipped: (nodeId: string, reason?: string) => void;
  setInteractivePrompt: (prompt: InteractivePromptData | null) => void;
  clearInteractivePrompt: () => void;
  
  // Formatters
  formatExecutionTime: (startTime: Date | null, endTime: Date | null) => string;
  formatTokenCount: (tokens: number) => string;
  formatProgress: (completed: number, total: number) => string;
  getNodeStatusIcon: (status: NodeStateV2['status']) => string;
  getNodeStatusColor: (status: NodeStateV2['status']) => string;
}

export function useExecutionUI(options: UseExecutionUIOptions = {}): UseExecutionUIReturn {
  const { showToasts = true, formatDuration = true } = options;
  
  const [interactivePrompt, setInteractivePrompt] = useState<InteractivePromptData | null>(null);
  const [executionProgress, setExecutionProgress] = useState(0);
  const [executionDuration, setExecutionDuration] = useState('0s');
  const [currentNodeName, setCurrentNodeName] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<Date | null>(null);

  // Update duration every second during execution
  useEffect(() => {
    if (!startTime) return;

    const interval = setInterval(() => {
      const duration = formatExecutionTime(startTime, null);
      setExecutionDuration(duration);
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  // UI Actions
  const showExecutionStart = useCallback((_executionId: string, totalNodes: number) => {
    setStartTime(new Date());
    setExecutionProgress(0);
    if (showToasts) {
      toast.info(`Execution started with ${totalNodes} nodes`);
    }
  }, [showToasts]);

  const showExecutionComplete = useCallback((_executionId: string, duration: number, totalTokens?: number) => {
    setStartTime(null);
    setExecutionProgress(100);
    if (showToasts) {
      const message = totalTokens 
        ? `Execution completed in ${duration}s (${formatTokenCount(totalTokens)} tokens)`
        : `Execution completed in ${duration}s`;
      toast.success(message);
    }
  }, [showToasts]);

  const showExecutionError = useCallback((error: string) => {
    setStartTime(null);
    if (showToasts) {
      toast.error(`Execution failed: ${error}`);
    }
  }, [showToasts]);

  const showNodeStart = useCallback((nodeId: string, nodeType: string) => {
    setCurrentNodeName(`${nodeType} (${nodeId.slice(0, 8)}...)`);
    if (showToasts && nodeType === 'user_response') {
      toast.info('Waiting for user input...');
    }
  }, [showToasts]);

  const showNodeComplete = useCallback((nodeId: string, _nodeType: string) => {
    if (currentNodeName?.includes(nodeId.slice(0, 8))) {
      setCurrentNodeName(null);
    }
  }, [currentNodeName]);

  const showNodeError = useCallback((nodeId: string, error: string) => {
    if (showToasts) {
      toast.error(`Node ${nodeId.slice(0, 8)}... failed: ${error}`);
    }
  }, [showToasts]);

  const showNodeSkipped = useCallback((nodeId: string, reason?: string) => {
    if (showToasts && reason) {
      toast.warning(`Node ${nodeId.slice(0, 8)}... skipped: ${reason}`);
    }
  }, [showToasts]);

  const clearInteractivePrompt = useCallback(() => {
    setInteractivePrompt(null);
  }, []);

  // Formatters
  const formatExecutionTime = useCallback((startTime: Date | null, endTime: Date | null): string => {
    if (!startTime) return '0s';
    
    const end = endTime || new Date();
    const duration = Math.floor((end.getTime() - startTime.getTime()) / 1000);
    
    if (!formatDuration) return `${duration}s`;
    
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = duration % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  }, [formatDuration]);

  const formatTokenCount = useCallback((tokens: number): string => {
    if (tokens < 1000) return `${tokens}`;
    if (tokens < 1000000) return `${(tokens / 1000).toFixed(1)}k`;
    return `${(tokens / 1000000).toFixed(2)}M`;
  }, []);

  const formatProgress = useCallback((completed: number, total: number): string => {
    if (total === 0) return '0%';
    const percentage = Math.round((completed / total) * 100);
    return `${percentage}%`;
  }, []);

  const getNodeStatusIcon = useCallback((status: NodeStateV2['status']): string => {
    switch (status) {
      case 'pending': return '⏳';
      case 'running': return '🔄';
      case 'completed': return '✅';
      case 'skipped': return '⏭️';
      case 'error': return '❌';
      case 'paused': return '⏸️';
      default: return '❓';
    }
  }, []);

  const getNodeStatusColor = useCallback((status: NodeStateV2['status']): string => {
    switch (status) {
      case 'pending': return 'text-gray-500';
      case 'running': return 'text-blue-500';
      case 'completed': return 'text-green-500';
      case 'skipped': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      case 'paused': return 'text-orange-500';
      default: return 'text-gray-400';
    }
  }, []);

  return {
    // UI State
    interactivePrompt,
    executionProgress,
    executionDuration,
    currentNodeName,
    
    // UI Actions
    showExecutionStart,
    showExecutionComplete,
    showExecutionError,
    showNodeStart,
    showNodeComplete,
    showNodeError,
    showNodeSkipped,
    setInteractivePrompt,
    clearInteractivePrompt,
    
    // Formatters
    formatExecutionTime,
    formatTokenCount,
    formatProgress,
    getNodeStatusIcon,
    getNodeStatusColor
  };
}