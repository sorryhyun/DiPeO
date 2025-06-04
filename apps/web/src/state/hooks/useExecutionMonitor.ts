import { useEffect, useRef, useCallback } from 'react';
import { useExecutionStore, useDiagramStore } from '@/state/stores';
import { toast } from 'sonner';
import { getStreamingUrl, API_ENDPOINTS } from '@/common/utils/apiConfig';

export const useExecutionMonitor = () => {
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingEventsRef = useRef<Array<{ type: string; data: any }>>([]);
  const diagramLoadedRef = useRef<boolean>(false);
  
  const {
    addRunningNode,
    removeRunningNode,
    setCurrentRunningNode,
    setRunContext
  } = useExecutionStore();
  const loadDiagram = useDiagramStore(state => state.loadDiagram);
  const nodes = useDiagramStore(state => state.nodes);

  const processEvent = useCallback((type: string, data: any) => {
    switch (type) {
      case 'node_start': {
        const startNodeId = data.node_id;
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
        const completeNodeId = data.node_id;
        if (completeNodeId) {
          console.log(`[Monitor] Removing running node: ${completeNodeId}`);
          removeRunningNode(completeNodeId);
        }
        break;
      }
      
      case 'node_skipped': {
        const skippedNodeId = data.node_id;
        if (skippedNodeId) {
          console.log(`[Monitor] Removing skipped node: ${skippedNodeId}`);
          removeRunningNode(skippedNodeId);
        }
        break;
      }
    }
  }, [nodes, addRunningNode, removeRunningNode, setCurrentRunningNode]);

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

  useEffect(() => {
    let isComponentMounted = true;

    const attachEventHandlers = (eventSource: EventSource) => {
      eventSource.onopen = () => {
        console.log('SSE connected for execution monitoring');
        // Clear any reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      eventSource.onmessage = async (event) => {
        if (!isComponentMounted) return;

        try {
          const data = JSON.parse(event.data);

          // Process all events that come through the monitor SSE connection
          // These could be from CLI executions or other browser instances
          // The 'from_monitor' flag indicates it came through broadcast_to_monitors
          // We want to process these to show execution progress

          // Debug log for monitor events
          if (data.type && data.type.startsWith('node_')) {
            console.log('[Monitor] Received event:', data.type, data);
          }

          switch (data.type) {
            case 'monitor_connected':
              console.log('Monitor connected:', data.monitor_id);
              break;

            case 'execution_started':
              if (data.from_monitor || data.from_cli) {
                toast.info(`External execution started: ${data.execution_id}`);
                if (data.diagram) {
                  console.log('[Monitor] Loading diagram from execution_started event');
                  // Clear any pending events from previous executions
                  pendingEventsRef.current = [];
                  diagramLoadedRef.current = false;
                  loadDiagram(data.diagram, 'external');
                }
              }
              break;

            case 'node_start': {
              console.log('[Monitor] node_start event received:', data);
              if (!diagramLoadedRef.current) {
                console.log('[Monitor] Diagram not loaded yet, queueing event');
                pendingEventsRef.current.push({ type: data.type, data });
              } else {
                processEvent(data.type, data);
              }
              break;
            }

            case 'node_complete': {
              console.log('[Monitor] node_complete event received:', data);
              processEvent(data.type, data);
              break;
            }
              
            case 'node_skipped': {
              console.log('[Monitor] node_skipped event received:', data);
              processEvent(data.type, data);
              break;
            }

            case 'execution_complete':
              if (data.context) {
                setRunContext(data.context);
              }
              if (data.from_monitor || data.from_cli) {
                toast.success('External execution completed');
              }
              break;

            case 'execution_error':
              if (data.from_monitor || data.from_cli) {
                toast.error(`External execution failed: ${data.error}`);
              }
              break;
          }
        } catch (error) {
          console.error('Failed to parse monitor update:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE monitor connection error:', error);
        eventSource.close();

        // Reconnect after 5 seconds
        if (isComponentMounted) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Reconnecting SSE monitor...');
            connectSSE();
          }, 5000);
        }
      };
    };

    const connectSSE = () => {
      if (!isComponentMounted) return;

      // Check if we have an early SSE connection from index.html
      if (window.__earlySSEConnection && window.__earlySSEConnection.readyState !== EventSource.CLOSED) {
        console.log('[Monitor] Reusing early SSE connection');
        eventSourceRef.current = window.__earlySSEConnection;
        attachEventHandlers(window.__earlySSEConnection);
        return;
      }

      // For SSE, connect directly to backend to avoid proxy issues
      const sseUrl = import.meta.env.DEV 
        ? `http://localhost:8000${API_ENDPOINTS.MONITOR_STREAM}`
        : getStreamingUrl(API_ENDPOINTS.MONITOR_STREAM);
      const eventSource = new EventSource(sseUrl);
      eventSourceRef.current = eventSource;
      attachEventHandlers(eventSource);
    };

    // Initial connection
    connectSSE();

    return () => {
      isComponentMounted = false;
      if (eventSourceRef.current) {
        // Don't close the early connection if we're just unmounting temporarily
        if (eventSourceRef.current !== window.__earlySSEConnection) {
          eventSourceRef.current.close();
        }
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [processEvent, setRunContext, loadDiagram]);

  return null;
};