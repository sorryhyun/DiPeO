import { useEffect, useRef } from 'react';
import { useExecutionStore, useDiagramStore } from '@/state/stores';
import { toast } from 'sonner';
import { getStreamingUrl, API_ENDPOINTS } from '@/common/utils/apiConfig';

export const useExecutionMonitor = () => {
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const {
    addRunningNode,
    removeRunningNode,
    setCurrentRunningNode,
    setRunContext
  } = useExecutionStore();
  const loadDiagram = useDiagramStore(state => state.loadDiagram);

  useEffect(() => {
    let isComponentMounted = true;

    const connectSSE = () => {
      if (!isComponentMounted) return;

      // For SSE, connect directly to backend to avoid proxy issues
      const sseUrl = import.meta.env.DEV 
        ? `http://localhost:8000${API_ENDPOINTS.MONITOR_STREAM}`
        : getStreamingUrl(API_ENDPOINTS.MONITOR_STREAM);
      const eventSource = new EventSource(sseUrl);
      eventSourceRef.current = eventSource;

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
                  loadDiagram(data.diagram, 'external');
                  // Small delay to ensure diagram is loaded before processing node events
                  await new Promise(resolve => setTimeout(resolve, 100));
                }
              }
              break;

            case 'node_start': {
              // Backend sends node_id directly
              const startNodeId = data.node_id;
              if (startNodeId) {
                addRunningNode(startNodeId);
                setCurrentRunningNode(startNodeId);
              }
              break;
            }

            case 'node_complete': {
              // Backend sends node_id directly
              const completeNodeId = data.node_id;
              if (completeNodeId) {
                removeRunningNode(completeNodeId);
              }
              break;
            }
              
            case 'node_skipped': {
              // Backend sends node_id directly
              const skippedNodeId = data.node_id;
              if (skippedNodeId) {
                removeRunningNode(skippedNodeId);
              }
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

    // Initial connection
    connectSSE();

    return () => {
      isComponentMounted = false;
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [addRunningNode, removeRunningNode, setCurrentRunningNode, setRunContext, loadDiagram]);

  return null;
};