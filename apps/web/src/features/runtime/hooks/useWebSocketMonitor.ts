/**
 * Hook for monitoring execution events via WebSocket
 * This is a WebSocket-based alternative to useExecutionMonitor that uses SSE
 */

import { useEffect, useCallback } from 'react';
import { useWebSocket, useWebSocketMessage } from './useWebSocket';
import { useExecutionStore, useDiagramStore } from '@/state/stores';
import { toast } from 'sonner';
import { DiagramState } from '@/common/types';

export const useWebSocketMonitor = (enabled = false) => {
  const { isConnected, connectionState } = useWebSocket({ 
    autoConnect: enabled,
    debug: true 
  });
  
  const {
    addRunningNode,
    removeRunningNode,
    setCurrentRunningNode,
    setRunContext
  } = useExecutionStore();
  
  const loadDiagram = useDiagramStore(state => state.loadDiagram);
  const nodes = useDiagramStore(state => state.nodes);
  
  const processNodeEvent = useCallback((data: Record<string, unknown>) => {
    const nodeId = (data.node_id || data.nodeId) as string;
    if (!nodeId) return;
    
    const nodeExists = nodes.some(n => n.id === nodeId);
    if (!nodeExists) {
      console.warn(`[WebSocket Monitor] Node ${nodeId} not found in diagram`);
      return;
    }
    
    switch (data.type) {
      case 'node_start':
        console.log(`[WebSocket Monitor] Adding running node: ${nodeId}`);
        addRunningNode(nodeId);
        setCurrentRunningNode(nodeId);
        break;
        
      case 'node_complete':
      case 'node_skipped':
        console.log(`[WebSocket Monitor] Removing node: ${nodeId}`);
        removeRunningNode(nodeId);
        break;
    }
  }, [nodes, addRunningNode, removeRunningNode, setCurrentRunningNode]);
  
  // Handle execution started events
  useWebSocketMessage('execution_started', (message: Record<string, unknown>) => {
    console.log('[WebSocket Monitor] Execution started:', message);
    if (message.from_monitor || message.from_cli || message.is_external) {
      toast.info(`External execution started: ${message.execution_id}`);
      if (message.diagram && typeof message.diagram === 'object') {
        console.log('[WebSocket Monitor] Loading diagram from execution_started event');
        loadDiagram(message.diagram as DiagramState, 'external');
      }
    }
  });
  
  // Handle node events
  useWebSocketMessage('node_start', processNodeEvent);
  useWebSocketMessage('node_complete', processNodeEvent);
  useWebSocketMessage('node_skipped', processNodeEvent);
  
  // Handle execution complete
  useWebSocketMessage('execution_complete', (message: Record<string, unknown>) => {
    console.log('[WebSocket Monitor] Execution complete:', message);
    if (message.context && typeof message.context === 'object') {
      setRunContext(message.context as Record<string, unknown>);
    }
    if (message.from_monitor || message.from_cli || message.is_external) {
      toast.success('External execution completed');
    }
  });
  
  // Handle execution errors
  useWebSocketMessage('execution_error', (message: Record<string, unknown>) => {
    console.log('[WebSocket Monitor] Execution error:', message);
    if (message.from_monitor || message.from_cli || message.is_external) {
      toast.error(`External execution failed: ${message.error}`);
    }
  });
  
  // Handle heartbeat (for debugging)
  useWebSocketMessage('heartbeat', (message: Record<string, unknown>) => {
    console.log('[WebSocket Monitor] Heartbeat received:', message.timestamp);
  });
  
  // Log connection state changes
  useEffect(() => {
    if (enabled) {
      console.log(`[WebSocket Monitor] Connection state: ${connectionState}, Connected: ${isConnected}`);
    }
  }, [connectionState, isConnected, enabled]);
  
  return {
    isConnected,
    connectionState
  };
};