import React, { useMemo } from 'react';
import { Hash } from 'lucide-react';
import { DomainPerson } from '@/core/types';
import { UIConversationMessage } from '@/core/types/conversation';

interface MessageListProps {
  messages: UIConversationMessage[];
  currentPersonId: string | null;
  persons: DomainPerson[];
  onScroll?: (e: React.UIEvent<HTMLDivElement>) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  isLoadingMore?: boolean;
}

interface MessageItemProps {
  message: UIConversationMessage;
  isFromSelectedPerson: boolean;
  senderPerson: DomainPerson | undefined;
}

// Memoized message item component
const MessageItem = React.memo<MessageItemProps>(({
  message,
  isFromSelectedPerson,
  senderPerson
}) => {
  return (
    <div
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
}, (prevProps, nextProps) => {
  // Custom comparison to prevent unnecessary re-renders
  return (
    prevProps.message.id === nextProps.message.id &&
    prevProps.isFromSelectedPerson === nextProps.isFromSelectedPerson &&
    prevProps.senderPerson?.id === nextProps.senderPerson?.id
  );
});

MessageItem.displayName = 'MessageItem';

export const MessageList = React.memo<MessageListProps>(({
  messages,
  currentPersonId,
  persons,
  onScroll,
  messagesEndRef,
  isLoadingMore = false
}) => {
  // Create a person lookup map for efficient lookups
  const personMap = useMemo(() => {
    const map = new Map<string, DomainPerson>();
    persons.forEach(person => map.set(person.id, person));
    return map;
  }, [persons]);

  return (
    <div
      className="flex-1 overflow-y-auto"
      onScroll={onScroll}
    >
      {messages.map((message) => {
        const isFromSelectedPerson = message.personId === currentPersonId;
        const senderPerson = personMap.get(message.personId);
        
        return (
          <MessageItem
            key={message.id}
            message={message}
            isFromSelectedPerson={isFromSelectedPerson}
            senderPerson={senderPerson}
          />
        );
      })}
      {isLoadingMore && (
        <div className="text-center py-4">
          <span className="text-sm text-gray-500">Loading more messages...</span>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function for React.memo
  return (
    prevProps.messages.length === nextProps.messages.length &&
    prevProps.currentPersonId === nextProps.currentPersonId &&
    prevProps.persons.length === nextProps.persons.length &&
    prevProps.isLoadingMore === nextProps.isLoadingMore &&
    // Check if messages array reference is the same or content is identical
    (prevProps.messages === nextProps.messages || 
     prevProps.messages.every((msg, idx) => msg.id === nextProps.messages[idx]?.id))
  );
});