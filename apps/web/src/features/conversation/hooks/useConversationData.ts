import { useState, useCallback, useRef, useEffect } from 'react';
import { toast } from 'sonner';
import { useGetConversationsQuery } from '@/__generated__/graphql';
import type { ConversationFilters, ConversationMessage, PersonMemoryConfig, PersonMemoryState } from '@/features/execution-monitor/types';
import type { PersonID } from '@dipeo/domain-models';

const MESSAGES_PER_PAGE = 50;

export interface UseConversationDataOptions {
  filters: ConversationFilters;
  personId?: PersonID | null;
  enableRealtimeUpdates?: boolean;
}

export const useConversationData = (options: UseConversationDataOptions | ConversationFilters) => {
  // Support both old and new API for backward compatibility
  const { filters, personId = null, enableRealtimeUpdates = true } = 
    'filters' in options ? options : { filters: options, personId: null, enableRealtimeUpdates: true };
  
  const [conversationData, setConversationData] = useState<Record<string, PersonMemoryState>>({});
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const lastUpdateTime = useRef<string | null>(null);
  const messageCounts = useRef<Record<string, number>>({});

  // GraphQL query with automatic loading state
  const { data, loading, error, refetch, fetchMore } = useGetConversationsQuery({
    variables: {
      personId: personId || undefined,
      executionId: filters.executionId || undefined,
      search: filters.searchTerm || undefined,
      showForgotten: filters.showForgotten || false,
      limit: MESSAGES_PER_PAGE,
      offset: 0,
      since: filters.startTime ? new Date(filters.startTime) : undefined
    },
    skip: false,
    // Poll for updates every 5 seconds when realtime updates are enabled
    pollInterval: enableRealtimeUpdates ? 5000 : 0,
    // Error handling
    onError: (error) => {
      console.error('Failed to fetch conversation data:', error);
      toast.error('Failed to load conversations');
    }
  });

  // Transform GraphQL response to match expected format
  useEffect(() => {
    if (data?.conversations) {
      const conversationsData = data.conversations as any;
      const transformed: Record<string, PersonMemoryState> = {};
      
      // Group conversations by personId
      const groupedByPerson: Record<string, any[]> = {};
      conversationsData.conversations?.forEach((conv: any) => {
        const pid = conv.personId;
        if (!groupedByPerson[pid]) {
          groupedByPerson[pid] = [];
        }
        groupedByPerson[pid].push(conv);
      });
      
      // Transform to PersonMemoryState format
      Object.entries(groupedByPerson).forEach(([pid, convs]) => {
        transformed[pid as PersonID] = {
          personId: pid as PersonID,
          messages: convs.map((conv: any) => ({
            id: conv.id || `${conv.nodeId}-${conv.timestamp}`,
            role: 'assistant' as const,
            content: conv.assistantResponse || '',
            timestamp: conv.timestamp,
            tokenCount: conv.tokenUsage?.total || 0,
            // Additional fields for internal use
            nodeId: conv.nodeId,
            userPrompt: conv.userPrompt,
            executionId: conv.executionId,
            forgotten: conv.forgotten || false
          })),
          visibleMessages: convs.filter((c: any) => !c.forgotten).length,
          hasMore: conversationsData.has_more || false,
          config: {
            forgetMode: 'no_forget',
            maxMessages: 20
          }
        };
        
        // Update message counts
        messageCounts.current[pid] = convs.length;
        
        // Update last fetch time
        if (convs.length > 0) {
          lastUpdateTime.current = convs[convs.length - 1].timestamp;
        }
      });
      
      setConversationData(transformed);
    }
  }, [data]);

  // Add new message to conversation data
  const addMessage = useCallback((personId: PersonID, message: ConversationMessage) => {
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
    lastUpdateTime.current = message.timestamp || null;
  }, []);

  // Refresh data for a specific person or all
  const refresh = useCallback((personId?: PersonID) => {
    return refetch({
      personId: personId || undefined,
      executionId: filters.executionId || undefined,
      search: filters.searchTerm || undefined,
      showForgotten: filters.showForgotten || false,
      limit: MESSAGES_PER_PAGE,
      offset: 0,
      since: filters.startTime ? new Date(filters.startTime) : undefined
    });
  }, [refetch, filters]);

  // Load more messages for pagination
  const loadMoreMessages = useCallback(async (personId: PersonID) => {
    const personData = conversationData[personId];
    if (!personData?.hasMore || isLoadingMore) return;
    
    setIsLoadingMore(true);
    
    try {
      const currentOffset = messageCounts.current[personId] || 0;
      const result = await fetchMore({
        variables: {
          personId,
          offset: currentOffset,
          limit: MESSAGES_PER_PAGE
        },
        updateQuery: (prev, { fetchMoreResult }) => {
          if (!fetchMoreResult) return prev;
          
          const newData = fetchMoreResult.conversations as any;
          const prevData = prev.conversations as any;
          
          return {
            conversations: {
              ...prevData,
              conversations: [
                ...(prevData.conversations || []),
                ...(newData.conversations || [])
              ],
              has_more: newData.has_more
            }
          };
        }
      });
      
      // Update message count
      if (result.data) {
        const newMessages = (result.data.conversations as any).conversations || [];
        messageCounts.current[personId] = currentOffset + newMessages.length;
      }
    } catch (error) {
      console.error('Failed to fetch more messages:', error);
      toast.error('Failed to load more messages');
    } finally {
      setIsLoadingMore(false);
    }
  }, [conversationData, isLoadingMore, fetchMore]);

  // Apply filters and refresh
  const applyFilters = useCallback(() => {
    return refresh();
  }, [refresh]);

  // Real-time message updates via events
  useEffect(() => {
    if (!enableRealtimeUpdates) return;

    const handleRealtimeUpdate = (event: Event) => {
      if (!(event instanceof CustomEvent)) return;
      
      const { type, data } = event.detail;

      if (type === 'message_added' && data.personId) {
        // Add new message to the current view if it matches the selected person
        if (personId === data.personId || !personId) {
          const message = data.message as ConversationMessage;
          addMessage(data.personId, message);
        }
      }
    };

    window.addEventListener('conversation-update', handleRealtimeUpdate);
    return () => {
      window.removeEventListener('conversation-update', handleRealtimeUpdate);
    };
  }, [personId, addMessage, enableRealtimeUpdates]);

  return {
    conversationData,
    isLoading: loading,
    isLoadingMore,
    error: error?.message || null,
    lastUpdateTime: lastUpdateTime.current,
    fetchConversationData: refresh,
    addMessage,
    refresh,
    fetchMore: loadMoreMessages,
    applyFilters,
    enableRealtimeUpdates,
  };
};