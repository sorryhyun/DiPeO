/**
 * Conversation Feature - Public API
 * 
 * This feature provides conversation history viewing and management,
 * allowing users to review past LLM interactions, analyze conversation
 * patterns, and export conversation data.
 */

// ============================================
// Main Components
// ============================================

/**
 * ConversationDashboard - Main dashboard for conversation management
 * Displays list of conversations with filtering and search capabilities
 */
export { ConversationDashboard } from '@/ui/components/conversation/ConversationDashboard';

/**
 * ConversationTab - Tab component for conversation viewing
 * Used within the main application to display conversation interface
 */
export { ConversationTab } from '@/ui/components/conversation/ConversationTab';

/**
 * MessageList - Component for displaying conversation messages
 * Renders a thread of messages with proper formatting and metadata
 */
export { MessageList } from '@/ui/components/conversation/MessageList';


// ============================================
// Hooks
// ============================================

/**
 * useConversationData - Hook for accessing conversation data
 * Provides methods to load, filter, and manage conversations
 */
export { useConversationData } from './hooks/useConversationData';

