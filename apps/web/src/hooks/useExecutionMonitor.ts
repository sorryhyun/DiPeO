// apps/web/src/hooks/useExecutionMonitor.ts
import { useEffect, useRef } from 'react';
import { useExecutionStore } from '@/stores';
import { toast } from 'sonner';

export const useExecutionMonitor = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const {
    setRunContext,
    addRunningNode,
    removeRunningNode,
    setCurrentRunningNode
  } = useExecutionStore();

  useEffect(() => {
    const clientId = `browser-${Date.now()}`;
    const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

    ws.onopen = () => {
      console.log('WebSocket connected for execution monitoring');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'execution_started':
          toast.info(`External execution started: ${data.execution_id}`);
          // Auto-subscribe to this execution
          ws.send(JSON.stringify({
            type: 'subscribe_execution',
            execution_id: data.execution_id
          }));
          break;

        case 'node_start':
          addRunningNode(data.nodeId);
          setCurrentRunningNode(data.nodeId);
          break;

        case 'node_complete':
          removeRunningNode(data.nodeId);
          break;

        case 'execution_complete':
          setRunContext(data.context);
          toast.success('External execution completed');
          break;
      }
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  return wsRef.current;
};