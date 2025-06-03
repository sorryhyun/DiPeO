import { useEffect, useRef } from 'react';
import { useExecutionStore, useMonitorStore } from '@/global/stores';
import { toast } from 'sonner';
import { getStreamingUrl, API_ENDPOINTS } from '@/shared/utils/apiConfig';

export const useExecutionMonitor = () => {
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const {
    addRunningNode,
    removeRunningNode,
    setCurrentRunningNode,
    setRunContext
  } = useExecutionStore();
  const { loadMonitorDiagram } = useMonitorStore();

  useEffect(() => {
    let isComponentMounted = true;

    const connectSSE = () => {
      if (!isComponentMounted) return;

      const eventSource = new EventSource(getStreamingUrl(API_ENDPOINTS.MONITOR_STREAM));
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('SSE connected for execution monitoring');
        // Clear any reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      eventSource.onmessage = (event) => {
        if (!isComponentMounted) return;

        try {
          const data = JSON.parse(event.data);

          // Skip if this is from our own execution (not external)
          if (data.from_monitor && !data.is_external) {
            // You might want to check execution_id against current execution
            return;
          }

          switch (data.type) {
            case 'monitor_connected':
              console.log('Monitor connected:', data.monitor_id);
              break;

            case 'execution_started':
              if (data.from_monitor) {
                toast.info(`External execution started: ${data.execution_id}`);
                if (data.diagram) {
                  loadMonitorDiagram(data.diagram);
                }
              }
              break;

            case 'node_start':
              if (data.nodeId) {
                addRunningNode(data.nodeId);
                setCurrentRunningNode(data.nodeId);
              }
              break;

            case 'node_complete':
              if (data.nodeId) {
                removeRunningNode(data.nodeId);
              }
              break;

            case 'execution_complete':
              if (data.context) {
                setRunContext(data.context);
              }
              if (data.from_monitor) {
                toast.success('External execution completed');
              }
              break;

            case 'execution_error':
              if (data.from_monitor) {
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
  }, [addRunningNode, removeRunningNode, setCurrentRunningNode, setRunContext, loadMonitorDiagram]);

  return null;
};