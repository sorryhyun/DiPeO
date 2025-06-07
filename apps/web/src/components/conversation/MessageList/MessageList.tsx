import React from 'react';
import { Hash } from 'lucide-react';
import { PersonDefinition, ConversationMessage } from '@/types';

interface MessageListProps {
  messages: ConversationMessage[];
  currentPersonId: string | null;
  persons: PersonDefinition[];
  onScroll?: (e: React.UIEvent<HTMLDivElement>) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  isLoadingMore?: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  currentPersonId,
  persons,
  onScroll,
  messagesEndRef,
  isLoadingMore = false
}) => {
  // Render single message
  const renderMessage = (message: ConversationMessage) => {
    const isFromSelectedPerson = message.personId === currentPersonId;
    const senderPerson = persons.find(p => p.id === message.personId);

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
              {message.nodeLabel && (
                <span className="ml-2">• {message.nodeLabel}</span>
              )}
            </div>
            <div className="flex items-center space-x-2 text-xs opacity-60">
              {message.tokenCount && (
                <span className="flex items-center">
                  <Hash className="h-3 w-3 mr-1" />
                  {message.tokenCount}
                </span>
              )}
            </div>
          </div>
          <div className="text-sm whitespace-pre-wrap break-words">{message.content}</div>
          <div className="text-xs opacity-50 mt-1">
            {message.timestamp ? new Date(message.timestamp).toLocaleString() : 'No timestamp'}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div
      className="flex-1 overflow-y-auto"
      onScroll={onScroll}
    >
      {messages.map((message) => renderMessage(message))}
      {isLoadingMore && (
        <div className="text-center py-4">
          <span className="text-sm text-gray-500">Loading more messages...</span>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};