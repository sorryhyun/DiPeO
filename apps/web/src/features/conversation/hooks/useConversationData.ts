import { useState, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { API_ENDPOINTS, getApiUrl } from '@/common/utils/apiConfig';
import { createErrorHandlerFactory } from '@/common/types';
import { ConversationMessage, PersonMemoryState, ConversationFilters } from '../types';

const MESSAGES_PER_PAGE = 50;

export const useConversationData = (filters: ConversationFilters) => {
  const [conversationData, setConversationData] = useState<Record<string, PersonMemoryState>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const createErrorHandler = createErrorHandlerFactory(toast);
  const lastUpdateTime = useRef<string | null>(null);
  const messageCounts = useRef<Record<string, number>>({});

  // Main fetch function
  const fetchConversationData = useCallback(async (
    personId?: string,
    append: boolean = false,
    since?: string
  ) => {
    if (append) {
      setIsLoadingMore(true);
    } else {
      setIsLoading(true);
    }
    
    setError(null);

    try {
      // Build params with functional state update to avoid stale closure
      const params = new URLSearchParams({
        limit: MESSAGES_PER_PAGE.toString(),
        ...(personId && { personId }),
        ...(since && { since }),
        ...(filters.searchTerm && { search: filters.searchTerm }),
        ...(filters.executionId && { executionId: filters.executionId }),
        ...(filters.showForgotten && { showForgotten: 'true' }),
        ...(filters.startTime && { startTime: filters.startTime }),
        ...(filters.endTime && { endTime: filters.endTime }),
      });

      // Add offset for pagination
      if (append && personId && messageCounts.current[personId]) {
        params.append('offset', messageCounts.current[personId].toString());
      }

      const res = await fetch(`${getApiUrl(API_ENDPOINTS.CONVERSATIONS)}?${params}`);
      if (res.ok) {
        const data = await res.json();

        if (append && personId) {
          // Append to existing messages using functional update
          setConversationData(prev => {
            const newData = {
              ...prev,
              [personId]: {
                ...data.persons[personId],
                messages: [...(prev[personId]?.messages || []), ...data.persons[personId].messages],
              }
            };
            // Update message counts ref
            messageCounts.current[personId] = newData[personId].messages.length;
            return newData;
          });
        } else {
          // Replace data
          setConversationData(data.persons);
          // Update message counts ref for all persons
          Object.keys(data.persons).forEach(pid => {
            messageCounts.current[pid] = data.persons[pid].messages.length;
          });
        }

        // Update last fetch time
        if (personId && data.persons[personId]?.messages.length > 0) {
          const lastMsg = data.persons[personId].messages[data.persons[personId].messages.length - 1];
          lastUpdateTime.current = lastMsg.timestamp;
        }
      } else {
        throw new Error(`Failed to fetch conversations: ${res.statusText}`);
      }
    } catch (error) {
      console.error('Failed to fetch conversation data:', error);
      const errorMessage = 'Failed to load conversations';
      setError(errorMessage);
      createErrorHandler(errorMessage)(error as Error);
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, [filters]);

  // Add new message to conversation data
  const addMessage = useCallback((personId: string, message: ConversationMessage) => {
    setConversationData(prev => {
      const personData = prev[personId];
      if (!personData) return prev;

      return {
        ...prev,
        [personId]: {
          ...personData,
          messages: [...personData.messages, message],
          visibleMessages: personData.visibleMessages + 1,
        }
      };
    });

    // Update last update time
    lastUpdateTime.current = message.timestamp;
  }, []);

  // Refresh data for a specific person or all
  const refresh = useCallback((personId?: string) => {
    return fetchConversationData(personId);
  }, [fetchConversationData]);

  // Load more messages for pagination
  const fetchMore = useCallback((personId: string) => {
    const personData = conversationData[personId];
    if (personData?.hasMore && !isLoadingMore) {
      return fetchConversationData(personId, true);
    }
  }, [conversationData, isLoadingMore, fetchConversationData]);

  // Apply filters and refresh
  const applyFilters = useCallback(() => {
    return fetchConversationData();
  }, [fetchConversationData]);

  return {
    conversationData,
    isLoading,
    isLoadingMore,
    error,
    lastUpdateTime: lastUpdateTime.current,
    fetchConversationData,
    addMessage,
    refresh,
    fetchMore,
    applyFilters
  };
};