import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  User, MessageSquare,
  Search, Filter, Download, DollarSign, Hash
} from 'lucide-react';
import { useConsolidatedDiagramStore, useExecutionStore, useConsolidatedUIStore } from '@/stores';
import { Button, Input, Select, SelectItem } from '@repo/ui-kit';
import { downloadJson } from '@/utils/downloadUtils';
import { toast } from 'sonner';
import { API_ENDPOINTS, getApiUrl } from '@/utils/apiConfig';
import { createErrorHandlerFactory } from '@repo/core-model';

interface ConversationMessage {
  id: string;
  role: 'assistant' | 'user';
  content: string;
  timestamp: string;
  sender_person_id: string;
  execution_id: string;
  node_id?: string;
  node_label?: string;
  token_count?: number;
  cost?: number;
}

interface PersonMemoryState {
  person_id: string;
  messages: ConversationMessage[];
  total_messages: number;
  visible_messages: number;
  forgotten_messages: number;
  has_more: boolean;
}

interface ConversationFilters {
  searchTerm: string;
  executionId: string;
  showForgotten: boolean;
  startTime?: string;
  endTime?: string;
}

const MESSAGES_PER_PAGE = 50;

const ConversationDashboard: React.FC = () => {
  const [conversationData, setConversationData] = useState<Record<string, PersonMemoryState>>({});
  const [dashboardSelectedPerson, setDashboardSelectedPerson] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [filters, setFilters] = useState<ConversationFilters>({
    searchTerm: '',
    executionId: '',
    showForgotten: false,
  });
  const [showFilters, setShowFilters] = useState(false);
  const createErrorHandler = createErrorHandlerFactory(toast);

  const { persons } = useConsolidatedDiagramStore();
  const { runContext } = useExecutionStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastUpdateTime = useRef<string | null>(null);
  const messageCounts = useRef<Record<string, number>>({});
  const fetchConversationDataRef = useRef<typeof fetchConversationData | null>(null);

  // Subscribe to real-time updates
  useEffect(() => {
    const handleRealtimeUpdate = (event: CustomEvent) => {
      const { type, data } = event.detail;

      if (type === 'message_added' && dashboardSelectedPerson) {
        // Add new message to the current view
        const message = data.message as ConversationMessage;
        setConversationData(prev => {
          const personData = prev[dashboardSelectedPerson];
          if (!personData) return prev;

          return {
            ...prev,
            [dashboardSelectedPerson]: {
              ...personData,
              messages: [...personData.messages, message],
              visible_messages: personData.visible_messages + 1,
            }
          };
        });

        // Auto-scroll to bottom
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    };

    window.addEventListener('conversation-update', handleRealtimeUpdate as EventListener);
    return () => {
      window.removeEventListener('conversation-update', handleRealtimeUpdate as EventListener);
    };
  }, [dashboardSelectedPerson]);

  // Fetch conversation data
  const fetchConversationData = useCallback(async (
    personId?: string,
    append: boolean = false,
    since?: string
  ) => {
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

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
        if (data.persons[personId!]?.messages.length > 0) {
          const lastMsg = data.persons[personId!].messages[data.persons[personId!].messages.length - 1];
          lastUpdateTime.current = lastMsg.timestamp;
        }
      }
    } catch (error) {
      console.error('Failed to fetch conversation data:', error);
      createErrorHandler('Failed to load conversations')(error as Error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [filters]);

  // Update the ref whenever fetchConversationData changes
  useEffect(() => {
    fetchConversationDataRef.current = fetchConversationData;
  }, [fetchConversationData]);

  // Initial load when runContext changes
  useEffect(() => {
    if (Object.keys(runContext).length > 0) {
      fetchConversationData();
    }
  }, [runContext, fetchConversationData]);

  // Separate polling logic with stable interval
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    const hasRunContext = Object.keys(runContext).length > 0;

    // Only start polling if we have a selected person and runContext
    if (dashboardSelectedPerson && hasRunContext) {
      interval = setInterval(() => {
        // Check if we still have a selected person and last update time
        if (dashboardSelectedPerson && lastUpdateTime.current && fetchConversationDataRef.current) {
          fetchConversationDataRef.current(dashboardSelectedPerson, false, lastUpdateTime.current);
        }
      }, 5000); // Poll every 5 seconds
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [dashboardSelectedPerson, runContext]); // Stable dependencies

  // Handle person selection from sidebar
  const { selectedPersonId } = useConsolidatedUIStore();
  
  useEffect(() => {
    if (selectedPersonId && selectedPersonId !== dashboardSelectedPerson) {
      setDashboardSelectedPerson(selectedPersonId);
      if (!conversationData[selectedPersonId]) {
        fetchConversationData(selectedPersonId);
      }
    }
  }, [selectedPersonId]);

  // Handle infinite scroll
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const element = e.currentTarget;
    const threshold = 100;

    if (
      element.scrollTop + element.clientHeight >= element.scrollHeight - threshold &&
      dashboardSelectedPerson &&
      conversationData[dashboardSelectedPerson]?.has_more &&
      !loadingMore
    ) {
      fetchConversationData(dashboardSelectedPerson, true);
    }
  }, [dashboardSelectedPerson, conversationData, loadingMore, fetchConversationData]);

  // Export conversations
  const exportConversations = () => {
    if (!dashboardSelectedPerson || !conversationData[dashboardSelectedPerson]) return;

    const data = conversationData[dashboardSelectedPerson];
    const person = persons.find(p => p.id === dashboardSelectedPerson);

    const exportData = {
      person: person?.label,
      personId: dashboardSelectedPerson,
      exportDate: new Date().toISOString(),
      messages: data.messages,
      stats: {
        total: data.total_messages,
        visible: data.visible_messages,
        forgotten: data.forgotten_messages,
      }
    };

    downloadJson(exportData, `conversation-${person?.label || dashboardSelectedPerson}-${new Date().toISOString()}.json`);

    toast.success('Conversation exported');
  };

  // Calculate total cost for selected person
  const calculateTotalCost = () => {
    if (!dashboardSelectedPerson || !conversationData[dashboardSelectedPerson]) return 0;

    return conversationData[dashboardSelectedPerson].messages
      .reduce((sum, msg) => sum + (msg.cost || 0), 0);
  };

  // Handle whole conversation button click
  const handleWholeConversation = () => {
    setDashboardSelectedPerson('whole');
    fetchConversationData(); // Fetch all conversations
  };

  // Render person status bar
  const renderPersonBar = () => {
    const selectedPerson = dashboardSelectedPerson && dashboardSelectedPerson !== 'whole' 
      ? persons.find(p => p.id === dashboardSelectedPerson) 
      : null;
    
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
                  <span>{conversationData[selectedPerson.id].visible_messages} messages</span>
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
          onChange={(e) => setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
          className="flex-1 h-8"
        />
      </div>
      <Select
        value={filters.executionId}
        onValueChange={(value) => setFilters(prev => ({ ...prev, executionId: value }))}
      >
        <SelectItem value="">All Executions</SelectItem>
        {/* Add execution options dynamically */}
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
        onClick={() => fetchConversationData(dashboardSelectedPerson || undefined)}
      >
        Apply
      </Button>
    </div>
  );

  // Render single message
  const renderMessage = (message: ConversationMessage) => {
    const isFromSelectedPerson = message.sender_person_id === dashboardSelectedPerson;
    const senderPerson = persons.find(p => p.id === message.sender_person_id);

    return (
      <div
        key={message.id}
        className={`flex ${isFromSelectedPerson ? 'justify-end' : 'justify-start'} px-4 py-2`}
      >
        <div
          className={`
            max-w-2xl p-3 rounded-lg
            ${isFromSelectedPerson 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-800'
            }
          `}
        >
          <div className="flex items-center justify-between mb-1">
            <div className="text-xs opacity-75">
              {isFromSelectedPerson ? 'Wrote' : `Read from ${senderPerson?.label || 'Unknown'}`}
              {message.node_label && (
                <span className="ml-2">• {message.node_label}</span>
              )}
            </div>
            <div className="flex items-center space-x-2 text-xs opacity-60">
              {message.token_count && (
                <span className="flex items-center">
                  <Hash className="h-3 w-3 mr-1" />
                  {message.token_count}
                </span>
              )}
              {message.cost && (
                <span className="flex items-center">
                  <DollarSign className="h-3 w-3" />
                  {message.cost.toFixed(4)}
                </span>
              )}
            </div>
          </div>
          <div className="text-sm whitespace-pre-wrap break-words">{message.content}</div>
          <div className="text-xs opacity-50 mt-1">
            {new Date(message.timestamp).toLocaleString()}
          </div>
        </div>
      </div>
    );
  };

  // Render conversation with virtual scrolling
  const renderConversation = () => {
    if (!dashboardSelectedPerson) return null;

    // Handle whole conversation view
    if (dashboardSelectedPerson === 'whole') {
      const allMessages: ConversationMessage[] = [];
      Object.values(conversationData).forEach(personData => {
        allMessages.push(...personData.messages);
      });
      
      // Sort messages by timestamp
      allMessages.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
      
      const totalCost = allMessages.reduce((sum, msg) => sum + (msg.cost || 0), 0);
      
      return (
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="px-4 py-2 bg-gray-50 border-b flex items-center justify-between">
            <h3 className="font-medium text-sm text-gray-700">
              Whole Conversation Timeline
            </h3>
            <div className="flex items-center space-x-4 text-xs text-gray-600">
              <span>{allMessages.length} messages</span>
              {totalCost > 0 && (
                <span className="flex items-center">
                  <DollarSign className="h-3 w-3 mr-1" />
                  Total: ${totalCost.toFixed(4)}
                </span>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {allMessages.map((message) => renderMessage(message))}
            <div ref={messagesEndRef} />
          </div>
        </div>
      );
    }

    // Handle individual person view
    if (!conversationData[dashboardSelectedPerson]) return null;
    
    const personMemory = conversationData[dashboardSelectedPerson];
    const totalCost = calculateTotalCost();

    return (
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-4 py-2 bg-gray-50 border-b flex items-center justify-between">
          <h3 className="font-medium text-sm text-gray-700">
            Conversation for {persons.find(p => p.id === dashboardSelectedPerson)?.label}
          </h3>
          <div className="flex items-center space-x-4 text-xs text-gray-600">
            <span>{personMemory.visible_messages} messages</span>
            {totalCost > 0 && (
              <span className="flex items-center">
                <DollarSign className="h-3 w-3 mr-1" />
                Total: ${totalCost.toFixed(4)}
              </span>
            )}
          </div>
        </div>

        <div
          className="flex-1 overflow-y-auto"
          onScroll={handleScroll}
        >
          {personMemory.messages.map((message) => renderMessage(message))}
          {loadingMore && (
            <div className="text-center py-4">
              <span className="text-sm text-gray-500">Loading more messages...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
    );
  };

  // Check if we're embedded in IntegratedDashboard
  const isEmbedded = true; // Always embedded since we don't have routing
  
  if (isEmbedded) {
    // Embedded view - no expansion controls or person bar
    return (
      <div className="h-full flex flex-col">
        {renderPersonBar()}
        {showFilters && renderFilters()}
        <div className="flex-1 flex overflow-hidden">
          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <span className="text-gray-500">Loading conversations...</span>
            </div>
          ) : dashboardSelectedPerson ? (
            renderConversation()
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Select a person from the left sidebar or click "Whole Conversation"</p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }
};

export default ConversationDashboard;