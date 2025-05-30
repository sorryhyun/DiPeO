import { useEffect, useRef, useCallback } from 'react';
import { ConversationMessage } from '../types';

interface UseMessagePollingProps {
  personId: string | null;
  runContext: Record<string, any>;
  lastUpdateTime: string | null;
  onNewMessage: (personId: string, message: ConversationMessage) => void;
  fetchConversationData: (personId?: string, append?: boolean, since?: string) => Promise<void>;
}

export const useMessagePolling = ({
  personId,
  runContext,
  lastUpdateTime,
  onNewMessage,
  fetchConversationData
}: UseMessagePollingProps) => {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fetchConversationDataRef = useRef(fetchConversationData);

  // Update the ref whenever fetchConversationData changes
  useEffect(() => {
    fetchConversationDataRef.current = fetchConversationData;
  }, [fetchConversationData]);

  // Subscribe to real-time updates
  useEffect(() => {
    const handleRealtimeUpdate = (event: CustomEvent) => {
      const { type, data } = event.detail;

      if (type === 'message_added' && personId) {
        // Add new message to the current view
        const message = data.message as ConversationMessage;
        onNewMessage(personId, message);
      }
    };

    window.addEventListener('conversation-update', handleRealtimeUpdate as EventListener);
    return () => {
      window.removeEventListener('conversation-update', handleRealtimeUpdate as EventListener);
    };
  }, [personId, onNewMessage]);

  // Start polling
  const startPolling = useCallback(() => {
    if (intervalRef.current) return; // Already polling

    intervalRef.current = setInterval(() => {
      // Check if we still have a selected person and last update time
      if (personId && lastUpdateTime && fetchConversationDataRef.current) {
        fetchConversationDataRef.current(personId, false, lastUpdateTime);
      }
    }, 5000); // Poll every 5 seconds
  }, [personId, lastUpdateTime]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Auto-start/stop polling based on conditions
  useEffect(() => {
    const hasRunContext = Object.keys(runContext).length > 0;

    // Only start polling if we have a selected person and runContext
    if (personId && hasRunContext) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [personId, runContext, startPolling, stopPolling]);

  return {
    startPolling,
    stopPolling,
    isPolling: intervalRef.current !== null
  };
};