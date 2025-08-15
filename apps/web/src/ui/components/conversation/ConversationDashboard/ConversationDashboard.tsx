import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  User, MessageSquare,
  Search, Filter, Download, DollarSign, List, FileText
} from 'lucide-react';
import { Button } from '@/ui/components/common/forms/buttons';
import { Input, Select } from '@/ui/components/common/forms';
import { downloadFile } from '@/lib/utils/file';
import { toast } from 'sonner';
import { useConversationData } from '@/domain/execution/hooks';
import { useUIState } from '@/infrastructure/store/hooks/state';
import { usePersonsData } from '@/domain/diagram/hooks';
import { MessageList } from '../MessageList';
import { ExecutionOrderView, ExecutionLogView } from '@/ui/components/execution';
import { useCanvas } from '@/domain/diagram/contexts';
import { ConversationFilters, UIConversationMessage } from '@/infrastructure/types/conversation';
import { PersonID, executionId, personId } from '@/infrastructure/types';
import { debounce, throttle } from '@/lib/utils/math';
import { stringify } from 'yaml';

const ConversationDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'conversation' | 'execution-order' | 'execution-log'>('execution-log');
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

  const { personsArray, personsMap } = usePersonsData();
  const { selectedId } = useUIState();
  // Get execution from Canvas context to avoid multiple instances
  const { operations } = useCanvas();
  const { execution } = operations.executionOps;
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Use persons directly from the hook
  const persons = personsArray;
  
  // Get selected person ID if a person is selected
  const selectedPersonId = React.useMemo(() => {
    if (!selectedId) return null;
    // Check if the selected ID is a person
    const person = personsMap.get(selectedId as PersonID);
    return person ? selectedId as PersonID : null;
  }, [selectedId, personsMap]);
  

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
    enableRealtimeUpdates: true,
    // Pass execution status to control polling - when execution is not running, we can stop polling
    executionStatus: execution.isRunning ? 'RUNNING' : 'COMPLETED'
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

  // File operations are handled directly with utils
  const exportConversations = async () => {
    if (!dashboardSelectedPerson || !conversationData[dashboardSelectedPerson]) return;

    const data = conversationData[dashboardSelectedPerson];
    const person = dashboardSelectedPerson !== 'whole' ? persons.find(p => p.id === dashboardSelectedPerson) : null;

    const exportData = {
      person: person?.label,
      personId: dashboardSelectedPerson,
      exportDate: new Date().toISOString(),
      messages: data.messages,
      stats: {
        visible: data.visibleMessages,
      }
    };

    const yamlContent = stringify(exportData, { lineWidth: 120, defaultStringType: 'PLAIN' });
    downloadFile(yamlContent, `conversation-${person?.label || dashboardSelectedPerson}-${new Date().toISOString()}.yaml`, 'text/yaml');
    toast.success('Conversation exported as YAML');
  };

  // Calculate total tokens for selected person
  const calculateTotalTokens = useCallback(() => {
    if (!dashboardSelectedPerson || !conversationData[dashboardSelectedPerson]) return 0;

    return conversationData[dashboardSelectedPerson].messages
      .reduce((sum: number, msg) => sum + (msg.tokenCount || 0), 0);
  }, [dashboardSelectedPerson, conversationData]);

  // Memoize whole conversation data
  const wholeConversationData = useMemo(() => {
    if (dashboardSelectedPerson !== 'whole') {
      return { allMessages: [], totalTokens: 0 };
    }

    const messages: UIConversationMessage[] = [];
    Object.entries(conversationData).forEach(([key, personData]) => {
      const messagesWithPersonId = personData.messages.map((msg) => ({
        ...msg,
        personId: personId(key)
      } as UIConversationMessage));
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
  }, [dashboardSelectedPerson, conversationData]);

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
              <span className="text-sm font-medium">{selectedPerson.label}</span>
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
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => debouncedSetSearchTerm(e.target.value)}
          className="flex-1 h-8"
        />
      </div>
      <Select
        value={filters.executionId}
        onValueChange={(value: string) => setFilters(prev => ({ ...prev, executionId: executionId(value) }))}
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
            Conversation for {selectedPersonForRender?.label}
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
          messages={personMemory.messages.map((msg) => ({
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

  // Render tab switcher
  const renderTabSwitcher = () => (
    <div className="flex items-center border-b bg-white px-4">
      <button
        className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
          activeTab === 'conversation'
            ? 'border-blue-500 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700'
        }`}
        onClick={() => setActiveTab('conversation')}
      >
        <MessageSquare className="h-4 w-4" />
        <span>Conversation</span>
      </button>
      <button
        className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
          activeTab === 'execution-order'
            ? 'border-blue-500 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700'
        }`}
        onClick={() => setActiveTab('execution-order')}
      >
        <List className="h-4 w-4" />
        <span>Execution Order</span>
      </button>
      <button
        className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
          activeTab === 'execution-log'
            ? 'border-blue-500 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700'
        }`}
        onClick={() => setActiveTab('execution-log')}
      >
        <FileText className="h-4 w-4" />
        <span>Execution Log</span>
      </button>
    </div>
  );

  const isEmbedded = true; // Always embedded since we don't have routing
  
  if (isEmbedded) {
    // Embedded view - no expansion controls or person bar
    return (
      <div className="h-full flex flex-col overflow-hidden">
        {/* Tab switcher - Fixed at top */}
        <div className="flex-shrink-0">
          {renderTabSwitcher()}
        </div>
        
        {/* Content area - Scrollable */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {activeTab === 'conversation' ? (
            <>
              <div className="flex-shrink-0">
                {renderPersonBar()}
                {showFilters && renderFilters()}
              </div>
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
            </>
          ) : activeTab === 'execution-order' ? (
            <ExecutionOrderView />
          ) : (
            <ExecutionLogView />
          )}
        </div>
      </div>
    );
  }
};

export default React.memo(ConversationDashboard);