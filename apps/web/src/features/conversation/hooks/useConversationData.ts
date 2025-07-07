import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { toast } from 'sonner';
import { GetConversationsDocument } from '@/__generated__/graphql';
import { createEntityQuery } from '@/graphql/hooks';
import type { ConversationFilters, UIConversationMessage, UIPersonMemoryState } from '@/core/types/conversation';
import { type PersonID, type ExecutionID, type NodeID, ExecutionStatus, isExecutionActive } from '@dipeo/domain-models';

const MESSAGES_PER_PAGE = 50;

export interface UseConversationDataOptions {
  filters: ConversationFilters;
  personId?: PersonID | null;
  enableRealtimeUpdates?: boolean;
  executionStatus?: string | null; // Pass execution status to control polling
}

export const useConversationData = (options: UseConversationDataOptions | ConversationFilters) => {
  // Support both old and new API for backward compatibility
  const { filters, personId = null, enableRealtimeUpdates = true, executionStatus = null } = 
    'filters' in options ? options : { filters: options, personId: null, enableRealtimeUpdates: true, executionStatus: null };
  
  const [conversationData, setConversationData] = useState<Record<string, UIPersonMemoryState>>({});
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const lastUpdateTime = useRef<string | null>(null);
  const messageCounts = useRef<Record<string, number>>({});

  // Determine if we should poll based on execution status
  const shouldPoll = enableRealtimeUpdates && (!executionStatus || isExecutionActive(executionStatus as ExecutionStatus));
  
  // Create query variables
  const queryVariables = useMemo(() => ({
    person_id: personId || undefined,
    execution_id: filters.executionId || undefined,
    search: filters.searchTerm || undefined,
    show_forgotten: filters.showForgotten || false,
    limit: MESSAGES_PER_PAGE,
    offset: 0,
    since: filters.startTime ? new Date(filters.startTime) : undefined
  }), [personId, filters]);

  // Create the query hook using factory pattern
  const useConversationsQuery = useMemo(
    () => createEntityQuery({
      entityName: 'Conversations',
      document: GetConversationsDocument,
      cacheStrategy: 'cache-and-network',
    }),
    []
  );

  // GraphQL query with automatic loading state
  const { data, loading, error, refetch, fetchMore } = useConversationsQuery(
    queryVariables,
    {
      skip: false,
      // Poll for updates only when realtime updates are enabled AND execution is active
      pollInterval: shouldPoll ? 5000 : 0,
    }
  );

  // Transform function for conversation data
  const transformConversationsData = useCallback((conversationsData: {
    conversations?: Array<{
      id?: string;
      personId: PersonID;
      nodeId: NodeID;
      userPrompt?: string;
      assistantResponse?: string;
      timestamp: string;
      executionId?: ExecutionID;
      forgotten?: boolean;
      tokenUsage?: { total?: number };
    }>;
    has_more?: boolean;
  }) => {
    const transformed: Record<string, UIPersonMemoryState> = {};
    
    // Group conversations by personId
    const groupedByPerson: Record<string, typeof conversationsData.conversations> = {};
    conversationsData.conversations?.forEach((conv) => {
      const pid = conv.personId;
      if (!groupedByPerson[pid]) {
        groupedByPerson[pid] = [];
      }
      groupedByPerson[pid].push(conv);
    });
    
    // Transform to UIPersonMemoryState format
    Object.entries(groupedByPerson).forEach(([pid, convs]) => {
      if (!convs) return;
      transformed[pid as PersonID] = {
        messages: convs.map((conv) => ({
          id: conv.id || `${conv.nodeId}-${conv.timestamp}`,
          role: 'assistant' as const,
          personId: pid as PersonID,
          content: conv.assistantResponse || '',
          timestamp: conv.timestamp,
          tokenCount: conv.tokenUsage?.total || 0,
          // Additional fields for internal use
          nodeId: conv.nodeId,
          userPrompt: conv.userPrompt,
          executionId: conv.executionId,
          forgotten: conv.forgotten || false
        })),
        visibleMessages: convs.filter((c) => !c.forgotten).length,
        hasMore: conversationsData.has_more || false,
        config: {
          forgetMode: 'no_forget',
          maxMessages: 20
        }
      };
      
      // Update message counts
      messageCounts.current[pid] = convs?.length || 0;
      
      // Update last fetch time
      if (convs && convs.length > 0) {
        lastUpdateTime.current = convs[convs.length - 1]!.timestamp;
      }
    });
    
    return transformed;
  }, []);

  // Transform GraphQL response to match expected format
  useEffect(() => {
    if (data?.conversations) {
      const transformed = transformConversationsData(data.conversations);
      setConversationData(transformed);
    }
  }, [data, transformConversationsData]);

  // Add new message to conversation data
  const addMessage = useCallback((personId: PersonID, message: UIConversationMessage) => {
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
  const refresh = useCallback(async (personId?: PersonID) => {
    try {
      const result = await refetch({
        person_id: personId || undefined,
        execution_id: filters.executionId || undefined,
        search: filters.searchTerm || undefined,
        show_forgotten: filters.showForgotten || false,
        limit: MESSAGES_PER_PAGE,
        offset: 0,
        since: filters.startTime ? new Date(filters.startTime) : undefined
      });
      if (result.data?.conversations) {
        const transformed = transformConversationsData(result.data.conversations);
        setConversationData(transformed);
      }
      return result;
    } catch (error) {
      // Error is handled by the query factory
      console.error('Failed to refresh conversations:', error);
      throw error;
    }
  }, [refetch, filters, transformConversationsData]);

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
          
          const newData = fetchMoreResult.conversations as {
            conversations?: Array<unknown>;
            has_more?: boolean;
          };
          const prevData = prev.conversations as {
            conversations?: Array<unknown>;
            has_more?: boolean;
          };
          
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
        const newMessages = ((result.data.conversations as {
          conversations?: Array<unknown>;
          has_more?: boolean;
        }).conversations || []) as Array<unknown>;
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
          const message = data.message as UIConversationMessage;
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