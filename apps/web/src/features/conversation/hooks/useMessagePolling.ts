/* global EventListener */
import { useEffect } from 'react';
import { ConversationMessage } from '../types';

interface UseMessagePollingProps {
  personId: string | null;
  onNewMessage: (personId: string, message: ConversationMessage) => void;
}

export const useMessagePolling = ({
  personId,
  onNewMessage
}: UseMessagePollingProps) => {
  // Subscribe to real-time updates via WebSocket
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

    window.addEventListener('conversation-update', handleRealtimeUpdate as EventListener);
    return () => {
      window.removeEventListener('conversation-update', handleRealtimeUpdate as EventListener);
    };
  }, [personId, onNewMessage]);

  // No return value needed - hook only sets up event listeners
};