/**
 * Test component to demonstrate WebSocket operation
 */

import React from 'react';
import { useWebSocketMonitor } from '../hooks/useWebSocketMonitor';
import { Button } from '@/common/components/Button';
import { getWebSocketClient } from '../websocket-client';

interface WebSocketTestProps {
  enabled?: boolean;
}

export const WebSocketTest: React.FC<WebSocketTestProps> = ({ enabled = false }) => {
  const { isConnected, connectionState } = useWebSocketMonitor(enabled);
  
  const sendTestMessage = () => {
    const client = getWebSocketClient();
    client.send({
      type: 'heartbeat',
      timestamp: new Date().toISOString()
    });
  };
  
  const sendMonitorBroadcast = async () => {
    // Test broadcasting through the monitor endpoint
    try {
      const response = await fetch('/api/monitor/broadcast', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'test_broadcast',
          message: 'Hello from WebSocket test!',
          timestamp: new Date().toISOString(),
          source: 'websocket_test_component'
        })
      });
      
      const result = await response.json();
      console.log('Broadcast result:', result);
    } catch (error) {
      console.error('Failed to broadcast:', error);
    }
  };
  
  if (!enabled) {
    return null;
  }
  
  return (
    <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
      <h3 className="text-sm font-semibold mb-2">WebSocket Monitor</h3>
      
      <div className="space-y-2 text-xs">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span>WebSocket: {connectionState}</span>
        </div>
        
        
        <div className="flex gap-2 mt-3">
          <Button
            size="sm"
            variant="outline"
            onClick={sendTestMessage}
            disabled={!isConnected}
          >
            Send Heartbeat
          </Button>
          
          <Button
            size="sm"
            variant="outline"
            onClick={sendMonitorBroadcast}
          >
            Test Broadcast
          </Button>
        </div>
        
        <div className="mt-2 text-gray-500 dark:text-gray-500">
          Open console to see WebSocket activity
        </div>
      </div>
    </div>
  );
};