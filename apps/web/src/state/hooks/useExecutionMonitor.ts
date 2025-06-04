import { useEffect, useRef, useCallback } from 'react';
import { useExecutionStore, useDiagramStore } from '@/state/stores';
import { toast } from 'sonner';
import { useWebSocket, useWebSocketMessage } from '@/features/runtime/hooks/useWebSocket';
import { DiagramState } from '@/common/types';

interface MonitorEvent {
  type: string;
  data: Record<string, unknown>;
}

export const useExecutionMonitor = () => {
  const pendingEventsRef = useRef<MonitorEvent[]>([]);
  const diagramLoadedRef = useRef<boolean>(false);
  const subscriptionSentRef = useRef<boolean>(false);
  
  // WebSocket connection with auto-connect
  const { isConnected, send } = useWebSocket({ autoConnect: true });
  
  const {
    addRunningNode,
    removeRunningNode,
    setCurrentRunningNode,
    setRunContext,
    addSkippedNode
  } = useExecutionStore();
  const loadDiagram = useDiagramStore(state => state.loadDiagram);
  const nodes = useDiagramStore(state => state.nodes);

  const processEvent = useCallback((type: string, data: Record<string, unknown>) => {
    switch (type) {
      case 'node_start': {
        const startNodeId = data.node_id as string;
        if (startNodeId) {
          // Check if node exists before updating
          const nodeExists = nodes.some(n => n.id === startNodeId);
          if (nodeExists) {
            console.log(`[Monitor] Adding running node: ${startNodeId}`);
            addRunningNode(startNodeId);
            setCurrentRunningNode(startNodeId);
          } else {
            console.warn(`[Monitor] Node ${startNodeId} not found in diagram, queueing event`);
            pendingEventsRef.current.push({ type, data });
          }
        }
        break;
      }
      
      case 'node_complete': {
        const completeNodeId = data.node_id as string;
        if (completeNodeId) {
          console.log(`[Monitor] Removing running node: ${completeNodeId}`);
          removeRunningNode(completeNodeId);
        }
        break;
      }
      
      case 'node_skipped': {
        const skippedNodeId = data.node_id as string;
        const skipReason = (data.reason as string) || 'No reason provided';
        if (skippedNodeId) {
          console.log(`[Monitor] Node skipped: ${skippedNodeId}, reason: ${skipReason}`);
          removeRunningNode(skippedNodeId);
          addSkippedNode(skippedNodeId, skipReason);
        }
        break;
      }
    }
  }, [nodes, addRunningNode, removeRunningNode, setCurrentRunningNode, addSkippedNode]);

  // Process any pending events when nodes change
  useEffect(() => {
    if (nodes.length > 0 && pendingEventsRef.current.length > 0) {
      console.log(`[Monitor] Processing ${pendingEventsRef.current.length} pending events now that nodes are loaded`);
      const events = [...pendingEventsRef.current];
      pendingEventsRef.current = [];
      
      events.forEach(event => {
        processEvent(event.type, event.data);
      });
    }
    diagramLoadedRef.current = nodes.length > 0;
  }, [nodes, processEvent]);

  // Subscribe to monitor events when connected
  useEffect(() => {
    if (isConnected && !subscriptionSentRef.current) {
      console.log('[Monitor] Subscribing to monitor events via WebSocket');
      send({ type: 'subscribe_monitor' });
      subscriptionSentRef.current = true;
    }
  }, [isConnected, send]);

  // Handle monitor connected event
  useWebSocketMessage('monitor_connected', (data: Record<string, unknown>) => {
    console.log('Monitor connected via WebSocket:', data.monitor_id);
  });

  // Handle execution started event
  useWebSocketMessage('execution_started', (data: Record<string, unknown>) => {
    if (data.from_monitor || data.from_cli) {
      toast.info(`External execution started: ${data.execution_id}`);
      if (data.diagram && typeof data.diagram === 'object') {
        console.log('[Monitor] Loading diagram from execution_started event');
        // Clear any pending events from previous executions
        pendingEventsRef.current = [];
        diagramLoadedRef.current = false;
        loadDiagram(data.diagram as DiagramState, 'external');
      }
    }
  });

  // Handle node start event
  useWebSocketMessage('node_start', (data: Record<string, unknown>) => {
    console.log('[Monitor] node_start event received:', data);
    if (!diagramLoadedRef.current) {
      console.log('[Monitor] Diagram not loaded yet, queueing event');
      pendingEventsRef.current.push({ type: 'node_start', data });
    } else {
      processEvent('node_start', data);
    }
  });

  // Handle node complete event
  useWebSocketMessage('node_complete', (data: Record<string, unknown>) => {
    console.log('[Monitor] node_complete event received:', data);
    processEvent('node_complete', data);
  });

  // Handle node skipped event
  useWebSocketMessage('node_skipped', (data: Record<string, unknown>) => {
    console.log('[Monitor] node_skipped event received:', data);
    processEvent('node_skipped', data);
  });

  // Handle execution complete event
  useWebSocketMessage('execution_complete', (data: Record<string, unknown>) => {
    if (data.context && typeof data.context === 'object') {
      setRunContext(data.context as Record<string, unknown>);
    }
    if (data.from_monitor || data.from_cli) {
      toast.success('External execution completed');
    }
  });

  // Handle execution error event
  useWebSocketMessage('execution_error', (data: Record<string, unknown>) => {
    if (data.from_monitor || data.from_cli) {
      toast.error(`External execution failed: ${data.error}`);
    }
  });
  
  // Handle conversation update event
  useWebSocketMessage('conversation_update', (data: Record<string, unknown>) => {
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
  });

  // Note: SSE fallback has been removed. WebSocket is now the only transport mechanism.

  return null;
};