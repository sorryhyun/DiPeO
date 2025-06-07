import { useState, useEffect, useCallback, useRef } from 'react';
import { Client, getWebSocketClient } from '@/utils/websocket';
import { createWebSocketExecutionClient } from '@/utils/websocket/execution-client';
import { toast } from 'sonner';
import { DiagramState, WSMessage, PersonDefinition, InteractivePromptData } from '@/types';
import { DiagramData, ExecutionUpdate } from '@/types/api';
import { API_ENDPOINTS, getApiUrl } from '@/utils/api';
import { isApiKey, parseApiArrayResponse } from '@/utils/types';
import { 
  useCanvasSelectors, 
  useExecutionSelectors,
  loadDiagram as loadDiagramAction,
  exportDiagramState
} from './useStoreSelectors';
import { useExecutionStore } from '@/stores/executionStore';

export interface UseExecutionOptions {
  autoConnect?: boolean;
  enableMonitoring?: boolean;
  debug?: boolean;
  mode?: 'realtime' | 'simple'; // For backward compatibility
}

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

type RunStatus = 'idle' | 'running' | 'success' | 'fail';

export const useExecution = (options: UseExecutionOptions = {}) => {
  const { 
    autoConnect = true, 
    enableMonitoring = false, 
    debug = false,
    mode = 'realtime' 
  } = options;

  // Store selectors
  const { nodes } = useCanvasSelectors();
  const execution = useExecutionSelectors();
  const {
    runningNodes,
    currentRunningNode,
    nodeRunningStates,
    skippedNodes: storeSkippedNodes,
  } = execution;
  // Store actions directly from execution store
  const executionStore = useExecutionStore();
  const {
    addRunningNode,
    removeRunningNode,
    setCurrentRunningNode,
    setRunContext,
    addSkippedNode
  } = executionStore;
  
  // Helper functions to match old behavior
  const clearRunContext = () => setRunContext({});
  const clearRunningNodes = () => {
    executionStore.runningNodes.forEach(nodeId => removeRunningNode(nodeId));
  };

  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'reconnecting'>('disconnected');
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);

  // Execution state (comprehensive)
  const [executionState, setExecutionState] = useState<ExecutionState>({
    isRunning: false,
    executionId: null,
    totalNodes: 0,
    completedNodes: 0,
    currentNode: null,
    startTime: null,
    endTime: null,
    error: null
  });
  const [nodeStates, setNodeStates] = useState<Record<string, NodeState>>({});

  // Simple state (for backward compatibility)
  const [runStatus, setRunStatus] = useState<RunStatus>('idle');
  const [runError, setRunError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [interactivePrompt, setInteractivePrompt] = useState<InteractivePromptData | null>(null);

  // Refs
  const clientRef = useRef<Client | null>(null);
  const executionClientRef = useRef<ReturnType<typeof createWebSocketExecutionClient> | null>(null);
  const pendingEventsRef = useRef<Array<{ type: string; data: Record<string, unknown> }>>([]);
  const subscriptionSentRef = useRef<boolean>(false);
  const isComponentMountedRef = useRef(true);

  // =====================
  // WEBSOCKET CONNECTION
  // =====================

  useEffect(() => {
    const client = getWebSocketClient({ debug });
    clientRef.current = client;
    
    // Create execution client wrapper
    executionClientRef.current = createWebSocketExecutionClient(client);
    
    // Set up interactive prompt handler
    if ('setInteractivePromptHandler' in executionClientRef.current) {
      executionClientRef.current.setInteractivePromptHandler((prompt: InteractivePromptData) => {
        setInteractivePrompt(prompt);
      });
    }
    
    // Set up event handlers
    const handleConnected = () => {
      setIsConnected(true);
      setConnectionState('connected');
      if (debug) console.log('[useExecution] Connected to WebSocket');
    };
    
    const handleDisconnected = () => {
      setIsConnected(false);
      setConnectionState('disconnected');
      subscriptionSentRef.current = false;
      if (debug) console.log('[useExecution] Disconnected from WebSocket');
    };
    
    const handleMessage = (event: Event) => {
      const customEvent = event as CustomEvent<WSMessage>;
      const message = customEvent.detail;
      setLastMessage(message);
      
      if (debug) {
        console.log('[useExecution] Received message:', message);
      }
      
      handleWebSocketMessage(message);
    };
    
    const handleError = (event: Event) => {
      const customEvent = event as CustomEvent;
      console.error('[useExecution] Error:', customEvent.detail);
    };
    
    const handleReconnectFailed = () => {
      setConnectionState('disconnected');
      console.error('[useExecution] Failed to reconnect after maximum attempts');
    };
    
    // Subscribe to events
    client.addEventListener('connected', handleConnected);
    client.addEventListener('disconnected', handleDisconnected);
    client.addEventListener('message', handleMessage);
    client.addEventListener('error', handleError);
    client.addEventListener('reconnectFailed', handleReconnectFailed);
    
    // Auto-connect if enabled
    if (autoConnect && !client.isConnected()) {
      setConnectionState('connecting');
      client.connect();
    }
    
    // Cleanup
    return () => {
      isComponentMountedRef.current = false;
      client.removeEventListener('connected', handleConnected);
      client.removeEventListener('disconnected', handleDisconnected);
      client.removeEventListener('message', handleMessage);
      client.removeEventListener('error', handleError);
      client.removeEventListener('reconnectFailed', handleReconnectFailed);
      if (executionClientRef.current) {
        executionClientRef.current.abort();
      }
    };
  }, [autoConnect, debug]);

  // Subscribe to monitor events when connected and monitoring is enabled
  useEffect(() => {
    if (isConnected && enableMonitoring && !subscriptionSentRef.current) {
      console.log('[useExecution] Subscribing to monitor events');
      send({ type: 'subscribe_monitor' });
      subscriptionSentRef.current = true;
    }
  }, [isConnected, enableMonitoring]);

  // =====================
  // MESSAGE HANDLING
  // =====================

  const handleWebSocketMessage = useCallback((message: WSMessage) => {
    const { type, ...data } = message;

    // Update simple status based on execution events
    switch (type) {
      case 'execution_started':
        handleExecutionStarted(data);
        setRunStatus('running');
        setRunError(null);
        break;

      case 'execution_complete':
        handleExecutionComplete(data);
        setRunStatus('success');
        break;

      case 'execution_error':
        handleExecutionError(data);
        setRunStatus('fail');
        setRunError(data.error as string);
        break;

      case 'execution_aborted':
        handleExecutionAborted(data);
        setRunStatus('idle');
        break;

      // Node events
      case 'node_start':
        handleNodeStart(data);
        break;

      case 'node_progress':
        handleNodeProgress(data);
        break;

      case 'node_complete':
        handleNodeComplete(data);
        break;

      case 'node_skipped':
        handleNodeSkipped(data);
        break;

      case 'node_error':
        handleNodeError(data);
        break;

      // Control events
      case 'node_paused':
        handleNodePaused(data);
        break;

      case 'node_resumed':
        handleNodeResumed(data);
        break;

      // Interactive events
      case 'interactive_prompt':
        handleInteractivePrompt(data);
        break;

      case 'interactive_response_received':
        handleInteractiveResponseReceived(data);
        break;

      case 'interactive_prompt_timeout':
        handleInteractivePromptTimeout(data);
        break;

      // Conversation events
      case 'conversation_update':
        handleConversationUpdate(data);
        break;

      default:
        if (debug) {
          console.log('[useExecution] Unhandled message type:', type, data);
        }
    }
  }, [debug]);

  // =====================
  // EVENT HANDLERS
  // =====================

  const handleExecutionStarted = useCallback((data: Record<string, unknown>) => {
    const executionId = data.execution_id as string;
    const totalNodes = (data.total_nodes as number) || 0;
    
    setExecutionState(prev => ({
      ...prev,
      isRunning: true,
      executionId,
      totalNodes,
      completedNodes: 0,
      currentNode: null,
      startTime: new Date(),
      endTime: null,
      error: null
    }));

    // Clear previous states
    setNodeStates({});
    clearRunContext();
    clearRunningNodes();

    // Handle external executions
    if ((data.from_monitor || data.from_cli) && data.diagram) {
      toast.info(`External execution started: ${executionId}`);
      console.log('[useExecution] Loading diagram from external execution');
      loadDiagramAction(data.diagram as DiagramState);
      pendingEventsRef.current = [];
    }

    console.log('[useExecution] Execution started:', executionId);
  }, [setRunContext, removeRunningNode, executionStore.runningNodes]);

  const handleExecutionComplete = useCallback((data: Record<string, unknown>) => {
    const totalTokenCount = data.total_token_count as number;
    const duration = data.duration as number;

    setExecutionState(prev => ({
      ...prev,
      isRunning: false,
      endTime: new Date(),
      currentNode: null
    }));

    if (data.context) {
      setRunContext(data.context as Record<string, unknown>);
    }

    clearRunningNodes();

    // Show execution summary
    const skipCount = Object.keys(storeSkippedNodes).length;
    let summaryMessage = 'Execution completed successfully';
    
    if (totalTokenCount && totalTokenCount > 0) {
      summaryMessage = `Execution completed. Total tokens: ${totalTokenCount.toFixed(2)}`;
    }
    
    if (skipCount > 0) {
      summaryMessage += ` • ${skipCount} node${skipCount > 1 ? 's' : ''} skipped`;
    }

    if (data.from_monitor || data.from_cli) {
      toast.success('External execution completed');
    } else {
      toast.success(summaryMessage);
    }

    console.log('[useExecution] Execution completed. Token count:', totalTokenCount, 'Duration:', duration);
  }, [setRunContext, clearRunningNodes, storeSkippedNodes]);

  const handleExecutionError = useCallback((data: Record<string, unknown>) => {
    const error = data.error as string;

    setExecutionState(prev => ({
      ...prev,
      isRunning: false,
      endTime: new Date(),
      error
    }));

    clearRunningNodes();

    if (data.from_monitor || data.from_cli) {
      toast.error(`External execution failed: ${error}`);
    } else {
      toast.error(`Diagram Execution: ${error}`);
    }

    console.error('[useExecution] Execution error:', error);
  }, [removeRunningNode, executionStore.runningNodes]);

  const handleExecutionAborted = useCallback((data: Record<string, unknown>) => {
    setExecutionState(prev => ({
      ...prev,
      isRunning: false,
      endTime: new Date(),
      error: 'Execution aborted'
    }));

    clearRunningNodes();
    console.log('[useExecution] Execution aborted:', data.execution_id);
  }, [removeRunningNode, executionStore.runningNodes]);

  const handleNodeStart = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    if (!nodeId) return;

    // Check if node exists in current diagram
    const nodeExists = nodes.some(n => n.id === nodeId);
    if (!nodeExists) {
      console.warn(`[useExecution] Node ${nodeId} not found, queueing event`);
      pendingEventsRef.current.push({ type: 'node_start', data });
      return;
    }

    addRunningNode(nodeId);
    setCurrentRunningNode(nodeId);

    setNodeStates(prev => ({
      ...prev,
      [nodeId]: {
        status: 'running',
        startTime: new Date(),
        endTime: null
      }
    }));

    setExecutionState(prev => ({
      ...prev,
      currentNode: nodeId
    }));

    console.log('[useExecution] Node started:', nodeId);
  }, [nodes, addRunningNode, setCurrentRunningNode]);

  const handleNodeProgress = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    const message = data.message as string;

    if (nodeId) {
      setNodeStates(prev => ({
        ...prev,
        [nodeId]: {
          status: prev[nodeId]?.status || 'running',
          startTime: prev[nodeId]?.startTime || null,
          endTime: prev[nodeId]?.endTime || null,
          progress: message,
          error: prev[nodeId]?.error,
          tokenCount: prev[nodeId]?.tokenCount,
          skipReason: prev[nodeId]?.skipReason
        }
      }));
    }
  }, []);

  const handleNodeComplete = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    const tokenCount = data.token_count as number;

    if (nodeId) {
      removeRunningNode(nodeId);

      setNodeStates(prev => ({
        ...prev,
        [nodeId]: {
          status: 'completed' as const,
          startTime: prev[nodeId]?.startTime || null,
          endTime: new Date(),
          tokenCount,
          progress: prev[nodeId]?.progress,
          error: undefined,
          skipReason: undefined
        }
      }));

      setExecutionState(prev => ({
        ...prev,
        completedNodes: prev.completedNodes + 1
      }));

      console.log('[useExecution] Node completed:', nodeId, 'Token count:', tokenCount);
    }
  }, [removeRunningNode]);

  const handleNodeSkipped = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    const reason = data.reason as string;

    if (nodeId) {
      removeRunningNode(nodeId);
      addSkippedNode(nodeId, reason);

      setNodeStates(prev => ({
        ...prev,
        [nodeId]: {
          status: 'skipped' as const,
          startTime: prev[nodeId]?.startTime || null,
          endTime: new Date(),
          skipReason: reason,
          progress: prev[nodeId]?.progress,
          error: undefined,
          tokenCount: undefined
        }
      }));

      console.log('[useExecution] Node skipped:', nodeId, 'Reason:', reason);
    }
  }, [removeRunningNode, addSkippedNode]);

  const handleNodeError = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    const error = data.error as string;

    if (nodeId) {
      removeRunningNode(nodeId);

      setNodeStates(prev => ({
        ...prev,
        [nodeId]: {
          status: 'error' as const,
          startTime: prev[nodeId]?.startTime || null,
          endTime: new Date(),
          error,
          progress: prev[nodeId]?.progress,
          tokenCount: undefined,
          skipReason: undefined
        }
      }));

      console.error('[useExecution] Node error:', nodeId, error);
    }
  }, [removeRunningNode]);

  const handleNodePaused = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    if (nodeId) {
      setNodeStates(prev => ({
        ...prev,
        [nodeId]: {
          status: 'paused' as const,
          startTime: prev[nodeId]?.startTime || null,
          endTime: prev[nodeId]?.endTime || null,
          progress: prev[nodeId]?.progress,
          error: prev[nodeId]?.error,
          tokenCount: prev[nodeId]?.tokenCount,
          skipReason: prev[nodeId]?.skipReason
        }
      }));
    }
    console.log('[useExecution] Node paused:', nodeId);
  }, []);

  const handleNodeResumed = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    if (nodeId) {
      setNodeStates(prev => ({
        ...prev,
        [nodeId]: {
          status: 'running' as const,
          startTime: prev[nodeId]?.startTime || null,
          endTime: prev[nodeId]?.endTime || null,
          progress: prev[nodeId]?.progress,
          error: prev[nodeId]?.error,
          tokenCount: prev[nodeId]?.tokenCount,
          skipReason: prev[nodeId]?.skipReason
        }
      }));
    }
    console.log('[useExecution] Node resumed:', nodeId);
  }, []);

  const handleInteractivePrompt = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    const prompt = data.prompt as string;
    const timeout = data.timeout as number;

    // Set interactive prompt for UI
    setInteractivePrompt({
      nodeId,
      executionId: executionState.executionId || '',
      prompt,
      timeout
    });

    // Dispatch custom event for UI components
    window.dispatchEvent(new CustomEvent('interactive-prompt', {
      detail: { nodeId, prompt, timeout }
    }));

    console.log('[useExecution] Interactive prompt:', nodeId, prompt);
  }, []);

  const handleInteractiveResponseReceived = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    setInteractivePrompt(null);
    console.log('[useExecution] Interactive response received:', nodeId);
  }, []);

  const handleInteractivePromptTimeout = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    setInteractivePrompt(null);
    console.log('[useExecution] Interactive prompt timeout:', nodeId);
  }, []);

  const handleConversationUpdate = useCallback((data: Record<string, unknown>) => {
    // Dispatch custom event for conversation components
    window.dispatchEvent(new CustomEvent('conversation-update', {
      detail: {
        type: 'message_added',
        data: {
          personId: data.person_id,
          message: data.message,
          conversationId: data.conversation_id
        }
      }
    }));
  }, []);

  // Process pending events when nodes change
  useEffect(() => {
    if (nodes.length > 0 && pendingEventsRef.current.length > 0) {
      console.log(`[useExecution] Processing ${pendingEventsRef.current.length} pending events`);
      const events = [...pendingEventsRef.current];
      pendingEventsRef.current = [];
      
      events.forEach(event => {
        if (event.type === 'node_start') {
          handleNodeStart(event.data);
        }
      });
    }
  }, [nodes, handleNodeStart]);

  // =====================
  // PUBLIC API
  // =====================

  const connect = useCallback(() => {
    if (clientRef.current && !clientRef.current.isConnected()) {
      setConnectionState('connecting');
      clientRef.current.connect();
    }
  }, []);

  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
    }
  }, []);

  const send = useCallback((message: WSMessage) => {
    if (clientRef.current) {
      clientRef.current.send(message);
    }
  }, []);

  // Unified execution function with API key validation
  const executeDiagram = useCallback(async (diagram?: DiagramState) => {
    // Clear previous state
    clearRunContext();
    clearRunningNodes();
    setCurrentRunningNode(null);
    setRunStatus('running');
    setRunError(null);
    setRetryCount(0);

    try {
      const diagramData = diagram || exportDiagramState();
      
      // Validate API keys (from useDiagramRunner)
      try {
        const keysRes = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS));
        if (keysRes.ok) {
          const response = await keysRes.json();
          const apiKeysData = response.apiKeys || response;
          const apiKeys = parseApiArrayResponse(apiKeysData, isApiKey);
          const validIds = new Set(apiKeys.map(k => k.id));

          // Validate person API keys
          if (apiKeys.length > 0) {
            (diagramData.persons || []).forEach((person: PersonDefinition) => {
              if (person.apiKeyId && !validIds.has(person.apiKeyId)) {
                const fallback = apiKeys.find(k => k.service === person.service);
                if (fallback) {
                  console.warn(
                    `Replaced invalid apiKeyId ${person.apiKeyId} → ${fallback.id}`
                  );
                  person.apiKeyId = fallback.id;
                }
              }
            });
          }
        } else {
          console.warn('Failed to fetch API keys', keysRes.status);
        }
      } catch (keyError) {
        console.warn('API key validation failed:', keyError);
      }

      // Execute via WebSocket
      if (mode === 'simple' && executionClientRef.current) {
        // Use execution client wrapper for simpler interface
        const result = await executionClientRef.current.execute(
          diagramData as DiagramData,
          {
            continueOnError: false,
            allowPartial: false,
            debugMode: false
          },
          (update: ExecutionUpdate) => {
            // Updates are already handled by WebSocket message handler
            if (debug) console.log('[useExecution] Execution update:', update);
          }
        );
        
        if (result.context) {
          setRunContext(result.context);
        }
        
        return result;
      } else {
        // Direct WebSocket execution
        send({
          type: 'execute_diagram',
          diagram: diagramData,
          options: {
            from_browser: true
          }
        });
      }
    } catch (error) {
      if (isComponentMountedRef.current) {
        clearRunningNodes();
        setCurrentRunningNode(null);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setRunError(errorMessage);
        console.error('Execution Error:', errorMessage);
        toast.error(`Diagram Execution: ${errorMessage}`);
        setRunStatus('fail');
      }
      throw error;
    }
  }, [mode, send, setRunContext, removeRunningNode, executionStore.runningNodes, setCurrentRunningNode, debug]);

  // Backward compatibility - wrapper for executeDiagram
  const onRunDiagram = useCallback(async () => {
    return executeDiagram();
  }, [executeDiagram]);

  // Control functions
  const pauseNode = useCallback((nodeId: string) => {
    send({ type: 'pause_node', nodeId });
  }, [send]);

  const resumeNode = useCallback((nodeId: string) => {
    send({ type: 'resume_node', nodeId });
  }, [send]);

  const skipNode = useCallback((nodeId: string) => {
    send({ type: 'skip_node', nodeId });
  }, [send]);

  const abort = useCallback(() => {
    if (executionState.executionId) {
      send({ type: 'abort_execution', executionId: executionState.executionId });
    }
  }, [executionState.executionId, send]);

  const stopExecution = useCallback(() => {
    console.log('[useExecution] Manual stop requested');
    abort();
    clearRunningNodes();
    setCurrentRunningNode(null);
    setRunStatus('idle');
    setRunError(null);
  }, [abort, removeRunningNode, executionStore.runningNodes, setCurrentRunningNode]);

  const respondToPrompt = useCallback((nodeId: string, response: string) => {
    send({ type: 'interactive_response', nodeId, response });
    setInteractivePrompt(null);
  }, [send]);

  const sendInteractiveResponse = respondToPrompt; // Alias for backward compatibility

  const cancelInteractivePrompt = useCallback(() => {
    setInteractivePrompt(null);
    if (interactivePrompt) {
      send({ type: 'interactive_response', nodeId: interactivePrompt.nodeId, response: '' });
    }
  }, [interactivePrompt, send]);

  return {
    // Connection state
    isConnected,
    connectionState,
    lastMessage,
    
    // Comprehensive execution state
    executionState,
    nodeStates,
    isRunning: executionState.isRunning,
    currentNode: executionState.currentNode,
    
    // Simple state (backward compatibility)
    runStatus,
    runError,
    retryCount,
    
    // Store state
    runningNodes,
    currentRunningNode,
    nodeRunningStates,
    skippedNodes: storeSkippedNodes,
    
    // Connection control
    connect,
    disconnect,
    send,
    
    // Execution control
    executeDiagram,
    onRunDiagram, // Backward compatibility
    pauseNode,
    resumeNode,
    skipNode,
    abort,
    stopExecution,
    respondToPrompt,
    
    // Interactive prompts
    interactivePrompt,
    sendInteractiveResponse,
    cancelInteractivePrompt,
    
    // Settings
    isMonitoring: enableMonitoring,
  };
};

export const useDiagramRunner = () => {
  // Use simple mode for backward compatibility with useDiagramRunner behavior
  const execution = useExecution({ mode: 'simple', autoConnect: true });

  // Return interface matching original useDiagramRunner
  return {
    runStatus: execution.runStatus,
    runError: execution.runError,
    retryCount: execution.retryCount,
    onRunDiagram: execution.onRunDiagram,
    stopExecution: execution.stopExecution,
    pauseNode: execution.pauseNode,
    resumeNode: execution.resumeNode,
    skipNode: execution.skipNode,
    interactivePrompt: execution.interactivePrompt,
    sendInteractiveResponse: execution.sendInteractiveResponse,
    cancelInteractivePrompt: execution.cancelInteractivePrompt,
  };
};