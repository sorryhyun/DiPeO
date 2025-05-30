import React from 'react';
import { Hash, DollarSign } from 'lucide-react';
import { PersonDefinition } from '@repo/core-model';
import { ConversationMessage } from '../types';

interface MessageListProps {
  messages: ConversationMessage[];
  currentPersonId: string | null;
  persons: PersonDefinition[];
  onScroll?: (e: React.UIEvent<HTMLDivElement>) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  loadingMore?: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  currentPersonId,
  persons,
  onScroll,
  messagesEndRef,
  loadingMore = false
}) => {
  // Render single message
  const renderMessage = (message: ConversationMessage) => {
    const isFromSelectedPerson = message.sender_person_id === currentPersonId;
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

  return (
    <div
      className="flex-1 overflow-y-auto"
      onScroll={onScroll}
    >
      {messages.map((message) => renderMessage(message))}
      {loadingMore && (
        <div className="text-center py-4">
          <span className="text-sm text-gray-500">Loading more messages...</span>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};