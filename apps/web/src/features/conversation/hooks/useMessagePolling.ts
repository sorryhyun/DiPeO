import { useEffect } from 'react';
import { ConversationMessage } from '../types';

interface UseMessagePollingProps {
  personId: string | null;
  runContext: Record<string, unknown>;
  lastUpdateTime: string | null;
  onNewMessage: (personId: string, message: ConversationMessage) => void;
  fetchConversationData: (personId?: string, append?: boolean, since?: string) => Promise<void>;
}

export const useMessagePolling = ({
  personId,
  runContext: _runContext, // No longer used - kept for backward compatibility
  lastUpdateTime: _lastUpdateTime, // No longer used - kept for backward compatibility
  onNewMessage,
  fetchConversationData: _fetchConversationData // No longer used - kept for backward compatibility
}: UseMessagePollingProps) => {
  // Subscribe to real-time updates via WebSocket/SSE
  useEffect(() => {
    const handleRealtimeUpdate = (event: CustomEvent) => {
      const { type, data } = event.detail;

      if (type === 'message_added' && data.personId) {
        // Add new message to the current view if it matches the selected person
        if (personId === data.personId || !personId) {
          const message = data.message as ConversationMessage;
          onNewMessage(data.personId, message);
        }
      }
    };

    window.addEventListener('conversation-update', handleRealtimeUpdate as any);
    return () => {
      window.removeEventListener('conversation-update', handleRealtimeUpdate as any);
    };
  }, [personId, onNewMessage]);

  // Return empty functions for backward compatibility
  return {
    startPolling: () => {}, // No-op, we use real-time updates now
    stopPolling: () => {}, // No-op
    isPolling: false // Always false since we don't poll anymore
  };
};