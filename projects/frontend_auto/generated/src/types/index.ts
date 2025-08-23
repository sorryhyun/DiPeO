// src/types/index.ts

/**
 * Centralized TypeScript type definitions for domain models
 * Exposed as named exports for use across services and UI components
 */

// Basic user representation
export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  // Role is kept flexible to accommodate future roles or external systems
  role?: 'admin' | 'member' | 'guest' | string;
  // Optional convenience flag for presence UI
  isOnline?: boolean;
  // Optional arbitrary metadata to allow extensibility without changing core types
  metadata?: Record<string, any>;
}

// Authentication tokens payload
export interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  // ISO date string or epoch timestamp
  expiresAt?: string | number;
}

// Message within a channel or thread
export interface Message {
  id: string;
  channelId: string;
  threadId?: string;
  author: User;
  content: string;
  attachments?: FileItem[];
  reactions?: Reaction[];
  createdAt: string;
  updatedAt?: string;
}

// Channel (room) in which messages are exchanged
export interface Channel {
  id: string;
  name: string;
  description?: string;
  isPrivate?: boolean;
  members: User[];
  createdAt: string;
}

// File attachment representation
export interface FileItem {
  id: string;
  fileName: string;
  url: string;
  size?: number; // in bytes
  mimeType?: string;
  uploadedBy: User;
  createdAt: string;
}

// Reaction to a message
export interface Reaction {
  id: string;
  emoji: string;
  user: User;
  createdAt?: string;
}

// Thread container for a message and its replies
export interface Thread {
  id: string;
  parentMessageId: string;
  messages: Message[];
}

// Presence information for a user
export interface Presence {
  userId: string;
  status: 'online' | 'offline' | 'away' | 'dnd';
  lastActiveAt?: string;
}

// Generic API response wrapper
export interface ApiResponse<T> {
  data: T;
  meta?: Record<string, any>;
}