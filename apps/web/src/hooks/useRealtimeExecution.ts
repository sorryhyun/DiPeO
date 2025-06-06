import { useState, useEffect, useCallback, useRef } from 'react';
import { Client, getWebSocketClient } from '@/utils/websocket';
import { toast } from 'sonner';
import { DiagramState, WSMessage } from '@/types';
import { 
  useCanvasSelectors, 
  useExecutionSelectors,
  useAddRunningNode,
  useRemoveRunningNode,
  useSetCurrentRunningNode,
  useSetRunContext,
  useAddSkippedNode,
  useClearRunContext,
  useClearRunningNodes,
  loadDiagram as loadDiagramAction,
  exportDiagramState
} from './useStoreSelectors';

export interface UseRealtimeExecutionOptions {
  autoConnect?: boolean;
  enableMonitoring?: boolean;
  debug?: boolean;
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
  status: 'pending' | 'running' | 'completed' | 'skipped' | 'error';
  startTime: Date | null;
  endTime: Date | null;
  progress?: string;
  error?: string;
  cost?: number;
  skipReason?: string;
}

export const useRealtimeExecution = (options: UseRealtimeExecutionOptions = {}) => {
  const { 
    autoConnect = true, 
    enableMonitoring = false, 
    debug = false 
  } = options;

  // Store selectors
  const { nodes } = useCanvasSelectors();
  const execution = useExecutionSelectors();
  const {
    runningNodes,
    currentRunningNode,
    nodeRunningStates,
    skippedNodes,
  } = execution;

  // Store actions
  const addRunningNode = useAddRunningNode();
  const removeRunningNode = useRemoveRunningNode();
  const setCurrentRunningNode = useSetCurrentRunningNode();
  const setRunContext = useSetRunContext();
  const addSkippedNode = useAddSkippedNode();
  const clearRunContext = useClearRunContext();
  const clearRunningNodes = useClearRunningNodes();

  // Local state
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'reconnecting'>('disconnected');
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
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

  // Refs
  const clientRef = useRef<Client | null>(null);
  const pendingEventsRef = useRef<Array<{ type: string; data: Record<string, unknown> }>>([]);
  const subscriptionSentRef = useRef<boolean>(false);

  // =====================
  // WEBSOCKET CONNECTION
  // =====================

  useEffect(() => {
    // Get or create WebSocket client
    const client = getWebSocketClient({ debug });
    clientRef.current = client;
    
    // Set up event handlers
    const handleConnected = () => {
      setIsConnected(true);
      setConnectionState('connected');
      console.log('[useRealtimeExecution] Connected to WebSocket');
    };
    
    const handleDisconnected = () => {
      setIsConnected(false);
      setConnectionState('disconnected');
      subscriptionSentRef.current = false;
      console.log('[useRealtimeExecution] Disconnected from WebSocket');
    };
    
    const handleMessage = (event: Event) => {
      const customEvent = event as CustomEvent<WSMessage>;
      const message = customEvent.detail;
      setLastMessage(message);
      
      if (debug) {
        console.log('[useRealtimeExecution] Received message:', message);
      }
      
      handleWebSocketMessage(message);
    };
    
    const handleError = (event: Event) => {
      const customEvent = event as CustomEvent;
      console.error('[useRealtimeExecution] Error:', customEvent.detail);
    };
    
    const handleReconnectFailed = () => {
      setConnectionState('disconnected');
      console.error('[useRealtimeExecution] Failed to reconnect after maximum attempts');
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
      client.removeEventListener('connected', handleConnected);
      client.removeEventListener('disconnected', handleDisconnected);
      client.removeEventListener('message', handleMessage);
      client.removeEventListener('error', handleError);
      client.removeEventListener('reconnectFailed', handleReconnectFailed);
    };
  }, [autoConnect, debug]);

  // Subscribe to monitor events when connected and monitoring is enabled
  useEffect(() => {
    if (isConnected && enableMonitoring && !subscriptionSentRef.current) {
      console.log('[useRealtimeExecution] Subscribing to monitor events');
      send({ type: 'subscribe_monitor' });
      subscriptionSentRef.current = true;
    }
  }, [isConnected, enableMonitoring]);

  // =====================
  // MESSAGE HANDLING
  // =====================

  const handleWebSocketMessage = useCallback((message: WSMessage) => {
    const { type, ...data } = message;

    switch (type) {
      // Connection events
      case 'monitor_connected':
        console.log('[useRealtimeExecution] Monitor connected:', data.monitor_id);
        break;

      case 'heartbeat':
        if (debug) {
          console.log('[useRealtimeExecution] Heartbeat received:', data.timestamp);
        }
        break;

      // Execution lifecycle events
      case 'execution_started':
        handleExecutionStarted(data);
        break;

      case 'execution_complete':
        handleExecutionComplete(data);
        break;

      case 'execution_error':
        handleExecutionError(data);
        break;

      case 'execution_aborted':
        handleExecutionAborted(data);
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
          console.log('[useRealtimeExecution] Unhandled message type:', type, data);
        }
    }
  }, [debug, nodes]);

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

    // Clear previous node states
    setNodeStates({});
    clearRunContext();
    clearRunningNodes();

    // If this is an external execution (from monitor or CLI), load the diagram
    if ((data.from_monitor || data.from_cli) && data.diagram) {
      toast.info(`External execution started: ${executionId}`);
      console.log('[useRealtimeExecution] Loading diagram from external execution');
      loadDiagramAction(data.diagram as DiagramState);
      pendingEventsRef.current = [];
    }

    console.log('[useRealtimeExecution] Execution started:', executionId);
  }, [loadDiagramAction, clearRunContext, clearRunningNodes]);

  const handleExecutionComplete = useCallback((data: Record<string, unknown>) => {
    const totalCost = data.total_cost as number;
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

    if (data.from_monitor || data.from_cli) {
      toast.success('External execution completed');
    }

    console.log('[useRealtimeExecution] Execution completed. Cost:', totalCost, 'Duration:', duration);
  }, [setRunContext, clearRunningNodes]);

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
    }

    console.error('[useRealtimeExecution] Execution error:', error);
  }, [clearRunningNodes]);

  const handleExecutionAborted = useCallback((data: Record<string, unknown>) => {
    setExecutionState(prev => ({
      ...prev,
      isRunning: false,
      endTime: new Date(),
      error: 'Execution aborted'
    }));

    clearRunningNodes();
    console.log('[useRealtimeExecution] Execution aborted:', data.execution_id);
  }, [clearRunningNodes]);

  const handleNodeStart = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    if (!nodeId) return;

    // Check if node exists in current diagram
    const nodeExists = nodes.some(n => n.id === nodeId);
    if (!nodeExists) {
      console.warn(`[useRealtimeExecution] Node ${nodeId} not found, queueing event`);
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

    console.log('[useRealtimeExecution] Node started:', nodeId);
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
          progress: message
        }
      }));
    }
  }, []);

  const handleNodeComplete = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    const cost = data.cost as number;

    if (nodeId) {
      removeRunningNode(nodeId);

      setNodeStates(prev => ({
        ...prev,
        [nodeId]: {
          status: 'completed' as const,
          startTime: prev[nodeId]?.startTime || null,
          endTime: new Date(),
          cost
        }
      }));

      setExecutionState(prev => ({
        ...prev,
        completedNodes: prev.completedNodes + 1
      }));

      console.log('[useRealtimeExecution] Node completed:', nodeId, 'Cost:', cost);
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
          skipReason: reason
        }
      }));

      console.log('[useRealtimeExecution] Node skipped:', nodeId, 'Reason:', reason);
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
          error
        }
      }));

      console.error('[useRealtimeExecution] Node error:', nodeId, error);
    }
  }, [removeRunningNode]);

  const handleNodePaused = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    console.log('[useRealtimeExecution] Node paused:', nodeId);
  }, []);

  const handleNodeResumed = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    console.log('[useRealtimeExecution] Node resumed:', nodeId);
  }, []);

  const handleInteractivePrompt = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    const prompt = data.prompt as string;
    const timeout = data.timeout as number;

    // Dispatch custom event for UI components to handle
    window.dispatchEvent(new CustomEvent('interactive-prompt', {
      detail: { nodeId, prompt, timeout }
    }));

    console.log('[useRealtimeExecution] Interactive prompt:', nodeId, prompt);
  }, []);

  const handleInteractiveResponseReceived = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    console.log('[useRealtimeExecution] Interactive response received:', nodeId);
  }, []);

  const handleInteractivePromptTimeout = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    console.log('[useRealtimeExecution] Interactive prompt timeout:', nodeId);
  }, []);

  const handleConversationUpdate = useCallback((data: Record<string, unknown>) => {
    // Dispatch custom event for conversation components to handle
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
      console.log(`[useRealtimeExecution] Processing ${pendingEventsRef.current.length} pending events`);
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

  // Execution control
  const executeDiagram = useCallback(async (diagram?: DiagramState) => {
    const diagramToExecute = diagram || exportDiagramState();
    
    send({
      type: 'execute_diagram',
      diagram: diagramToExecute,
      options: {
        from_browser: true
      }
    });
  }, [send]);

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

  const respondToPrompt = useCallback((nodeId: string, response: string) => {
    send({ type: 'interactive_response', nodeId, response });
  }, [send]);

  return {
    // Connection state
    isConnected,
    connectionState,
    lastMessage,
    
    // Execution state
    executionState,
    nodeStates,
    isRunning: executionState.isRunning,
    currentNode: executionState.currentNode,
    
    // Store state (for convenience)
    runningNodes,
    currentRunningNode,
    nodeRunningStates,
    skippedNodes,
    
    // Connection control
    connect,
    disconnect,
    send,
    
    // Execution control
    executeDiagram,
    pauseNode,
    resumeNode,
    skipNode,
    abort,
    respondToPrompt,
    
    // Settings
    isMonitoring: enableMonitoring,
  };
};