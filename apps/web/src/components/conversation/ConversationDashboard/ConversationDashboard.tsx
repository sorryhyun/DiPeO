import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  User, MessageSquare,
  Search, Filter, Download, DollarSign
} from 'lucide-react';
import { Button, Input, Select } from '@/components/ui';
import { useFileOperations } from '@/hooks/useFileOperations';
import { toast } from 'sonner';
import { useCanvasOperations } from '@/hooks';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import { useConversationData } from '@/hooks/useConversationData';
import { MessageList } from '../MessageList';
import {ConversationFilters, ConversationMessage, PersonID, executionId, personId} from '@/types';
import { debounce, throttle } from '@/utils/math';

const ConversationDashboard: React.FC = () => {
  const [dashboardSelectedPerson, setDashboardSelectedPerson] = useState<PersonID | 'whole' | null>(null);
  const [filters, setFilters] = useState<ConversationFilters>({
    searchTerm: '',
    executionId: executionId(''),
    showForgotten: false,
  });
  const [showFilters, setShowFilters] = useState(false);
  
  // Create a debounced search handler
  const debouncedSetSearchTerm = React.useMemo(
    () => debounce((searchTerm: string) => {
      setFilters(prev => ({ ...prev, searchTerm }));
    }, 300),
    []
  );

  const canvas = useCanvasOperations();
  const store = useUnifiedStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Get persons from canvas with proper memoization
  const persons = React.useMemo(
    () => canvas.persons.map(id => canvas.getPersonById(id)).filter(Boolean),
    [canvas]
  );
  
  // Get selected person ID if a person is selected
  const selectedPersonId = React.useMemo(() => {
    if (!store.selectedId) return null;
    // Check if the selected ID is a person
    const person = store.persons.get(store.selectedId as PersonID);
    return person ? store.selectedId as PersonID : null;
  }, [store.selectedId, store.persons]);
  

  // Use consolidated conversation data hook with real-time updates
  const {
    conversationData,
    isLoading,
    isLoadingMore,
    fetchConversationData,
    fetchMore
  } = useConversationData({
    filters,
    personId: dashboardSelectedPerson && dashboardSelectedPerson !== 'whole' ? dashboardSelectedPerson : undefined,
    enableRealtimeUpdates: true
  });

  // Debounced auto-scroll handler
  const scrollToBottom = React.useMemo(
    () => debounce(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 300),
    []
  );
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    const handleMessageAdded = () => {
      scrollToBottom();
    };

    window.addEventListener('conversation-update', handleMessageAdded);
    return () => {
      window.removeEventListener('conversation-update', handleMessageAdded);
    };
  }, [scrollToBottom]);

  // Initial load - only run once on mount
  useEffect(() => {
    void fetchConversationData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array to run only once

  // Handle person selection from sidebar
  useEffect(() => {
    if (selectedPersonId && selectedPersonId !== dashboardSelectedPerson) {
      setDashboardSelectedPerson(personId(selectedPersonId));
      if (!conversationData[selectedPersonId]) {
        void fetchConversationData(personId(selectedPersonId));
      }
    }
  }, [selectedPersonId, dashboardSelectedPerson, conversationData, fetchConversationData]);

  // Handle infinite scroll with throttling
  const handleScrollInternal = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const element = e.currentTarget;
    const threshold = 100;

    if (
      element.scrollTop + element.clientHeight >= element.scrollHeight - threshold &&
      dashboardSelectedPerson && dashboardSelectedPerson !== 'whole' &&
      conversationData[dashboardSelectedPerson]?.hasMore &&
      !isLoadingMore
    ) {
      void fetchMore(dashboardSelectedPerson);
    }
  }, [dashboardSelectedPerson, conversationData, isLoadingMore, fetchMore]);
  
  // Throttled scroll handler to prevent excessive calls
  const handleScroll = React.useMemo(
    () => throttle(handleScrollInternal, 150),
    [handleScrollInternal]
  );

  // Export conversations
  const { downloadJSON } = useFileOperations();
  
  const exportConversations = async () => {
    if (!dashboardSelectedPerson || !conversationData[dashboardSelectedPerson]) return;

    const data = conversationData[dashboardSelectedPerson];
    const person = dashboardSelectedPerson !== 'whole' ? persons.find(p => p.id === dashboardSelectedPerson) : null;

    const exportData = {
      person: person?.name,
      personId: dashboardSelectedPerson,
      exportDate: new Date().toISOString(),
      messages: data.messages,
      stats: {
        visible: data.visibleMessages,
      }
    };

    void downloadJSON(exportData, `conversation-${person?.name || dashboardSelectedPerson}-${new Date().toISOString()}.json`);
    toast.success('Conversation exported');
  };

  // Calculate total tokens for selected person
  const calculateTotalTokens = useCallback(() => {
    if (!dashboardSelectedPerson || !conversationData[dashboardSelectedPerson]) return 0;

    return conversationData[dashboardSelectedPerson].messages
      .reduce((sum, msg) => sum + (msg.tokenCount || 0), 0);
  }, [dashboardSelectedPerson, conversationData]);

  // Memoize whole conversation data with stable dependency
  const conversationDataKeys = Object.keys(conversationData).sort().join(',');
  const wholeConversationData = useMemo(() => {
    if (dashboardSelectedPerson !== 'whole') {
      return { allMessages: [], totalTokens: 0 };
    }

    const messages: ConversationMessage[] = [];
    Object.entries(conversationData).forEach(([key, personData]) => {
      // Add personId to each message
      const messagesWithPersonId = personData.messages.map(msg => ({
        ...msg,
        personId: personId(key)
      } as ConversationMessage));
      messages.push(...messagesWithPersonId);
    });
    
    // Sort messages by timestamp
    messages.sort((a, b) => {
      const aTime = a.timestamp ? new Date(a.timestamp).getTime() : 0;
      const bTime = b.timestamp ? new Date(b.timestamp).getTime() : 0;
      return aTime - bTime;
    });
    
    const tokens = messages.reduce((sum, msg) => sum + (msg.tokenCount || 0), 0);
    return { allMessages: messages, totalTokens: tokens };
  }, [dashboardSelectedPerson, conversationDataKeys]); // Use stable dependency

  // Handle whole conversation button click
  const handleWholeConversation = () => {
    setDashboardSelectedPerson('whole');
    void fetchConversationData(); // Fetch all conversations
  };

  // Memoize selected person for render functions
  const selectedPersonForRender = React.useMemo(
    () => dashboardSelectedPerson && dashboardSelectedPerson !== 'whole' 
      ? persons.find(p => p.id === dashboardSelectedPerson) 
      : null,
    [dashboardSelectedPerson, persons]
  );
  
  // Render person status bar
  const renderPersonBar = () => {
    const selectedPerson = selectedPersonForRender;
    
    return (
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b">
        <div className="flex items-center space-x-4">
          <Button
            variant={dashboardSelectedPerson === 'whole' ? 'default' : 'outline'}
            size="sm"
            onClick={handleWholeConversation}
            className="flex items-center space-x-2"
          >
            <MessageSquare className="h-4 w-4" />
            <span>Whole Conversation</span>
          </Button>
          
          {selectedPerson && (
            <div className="flex items-center space-x-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-md">
              <User className="h-4 w-4" />
              <span className="text-sm font-medium">{selectedPerson.name}</span>
              {conversationData[selectedPerson.id] && (
                <div className="flex items-center space-x-1 text-xs">
                  <span className="opacity-70">•</span>
                  <span>{conversationData[selectedPerson.id]?.visibleMessages} messages</span>
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className={showFilters ? 'bg-gray-200' : ''}
          >
            <Filter className="h-4 w-4" />
          </Button>
          {dashboardSelectedPerson && (
            <Button
              variant="ghost"
              size="sm"
              onClick={exportConversations}
            >
              <Download className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    );
  };

  // Render filters
  const renderFilters = () => (
    <div className="px-4 py-2 bg-gray-50 border-b flex items-center space-x-4">
      <div className="flex items-center space-x-2 flex-1">
        <Search className="h-4 w-4 text-gray-400" />
        <Input
          type="text"
          placeholder="Search messages..."
          value={filters.searchTerm}
          onChange={(e) => debouncedSetSearchTerm(e.target.value)}
          className="flex-1 h-8"
        />
      </div>
      <Select
        value={filters.executionId}
        onValueChange={(value) => setFilters(prev => ({ ...prev, executionId: executionId(value) }))}
      >
        <option value="">All Executions</option>
      </Select>
      <label className="flex items-center space-x-2 text-sm">
        <input
          type="checkbox"
          checked={filters.showForgotten}
          onChange={(e) => setFilters(prev => ({ ...prev, showForgotten: e.target.checked }))}
          className="rounded"
        />
        <span>Show Forgotten</span>
      </label>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => void fetchConversationData(dashboardSelectedPerson && dashboardSelectedPerson !== 'whole' ? dashboardSelectedPerson : undefined)}
      >
        Apply
      </Button>
    </div>
  );

  // Render conversation with extracted MessageList component
  const renderConversation = () => {
    if (!dashboardSelectedPerson) return null;

    // Handle whole conversation view
    if (dashboardSelectedPerson === 'whole') {
      return (
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="px-4 py-2 bg-gray-50 border-b flex items-center justify-between">
            <h3 className="font-medium text-sm text-gray-700">
              Whole Conversation Timeline
            </h3>
            <div className="flex items-center space-x-4 text-xs text-gray-600">
              <span>{wholeConversationData.allMessages.length} messages</span>
              {wholeConversationData.totalTokens > 0 && (
                <span className="flex items-center">
                  <DollarSign className="h-3 w-3 mr-1" />
                  Total Tokens: {wholeConversationData.totalTokens.toFixed(2)}
                </span>
              )}
            </div>
          </div>

          <MessageList
            messages={wholeConversationData.allMessages}
            currentPersonId={dashboardSelectedPerson}
            persons={persons}
            messagesEndRef={messagesEndRef}
          />
        </div>
      );
    }

    // Handle individual person view
    if (dashboardSelectedPerson === 'whole' || !conversationData[dashboardSelectedPerson]) return null;
    
    const personMemory = conversationData[dashboardSelectedPerson];
    const totalTokens = calculateTotalTokens();

    return (
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-4 py-2 bg-gray-50 border-b flex items-center justify-between">
          <h3 className="font-medium text-sm text-gray-700">
            Conversation for {selectedPersonForRender?.name}
          </h3>
          <div className="flex items-center space-x-4 text-xs text-gray-600">
            <span>{personMemory.visibleMessages} messages</span>
            {totalTokens > 0 && (
              <span className="flex items-center">
                <DollarSign className="h-3 w-3 mr-1" />
                Total Tokens: {totalTokens.toFixed(2)}
              </span>
            )}
          </div>
        </div>

        <MessageList
          messages={personMemory.messages.map(msg => ({
            ...msg,
            personId: dashboardSelectedPerson
          }))}
          currentPersonId={dashboardSelectedPerson}
          persons={persons}
          onScroll={handleScroll}
          messagesEndRef={messagesEndRef}
          isLoadingMore={isLoadingMore}
        />
      </div>
    );
  };

  const isEmbedded = true; // Always embedded since we don't have routing
  
  if (isEmbedded) {
    // Embedded view - no expansion controls or person bar
    return (
      <div className="h-full flex flex-col">
        {renderPersonBar()}
        {showFilters && renderFilters()}
        <div className="flex-1 flex overflow-hidden">
          {isLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <span className="text-gray-500">Loading conversations...</span>
            </div>
          ) : dashboardSelectedPerson ? (
            renderConversation()
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Select a person from the left sidebar or click &quot;Whole Conversation&quot;</p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }
};

export default React.memo(ConversationDashboard);