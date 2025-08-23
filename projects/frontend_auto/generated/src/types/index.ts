// src/types/index.ts

/**
 * Central domain type definitions for the app.
 * These interfaces describe the standard shape of core entities used across services
 * and UI components (Users, Messages, Channels, Files, Reactions, Threads, Presence, etc.).
 */

// User representation
export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  role?: 'admin' | 'member' | 'guest';
  createdAt?: string;
  updatedAt?: string;
}

// Authentication tokens
export interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: string; // ISO date string
}

// File representation (upload/download)
export interface FileItem {
  id: string;
  fileName: string;
  url: string;
  size?: number; // in bytes
  mimeType?: string;
  uploadedBy: User;
  createdAt?: string;
}

// Reactions to messages
export interface Reaction {
  id: string;
  emoji: string;
  user: User;
  createdAt?: string;
}

// A single thread of messages under a parent message
export interface Thread {
  id: string;
  parentMessageId: string;
  messages: Message[];
  createdAt?: string;
  updatedAt?: string;
}

// Message entity
export interface Message {
  id: string;
  channelId: string;
  threadId?: string;
  author: User;
  content: string;
  attachments?: FileItem[];
  reactions?: Reaction[];
  createdAt?: string;
  editedAt?: string;
  replyToMessageId?: string;
}

// Channel entity
export interface Channel {
  id: string;
  name: string;
  description?: string;
  isPrivate?: boolean;
  members: User[];
  createdAt?: string;
  updatedAt?: string;
}

// Presence information for a user
export type PresenceStatus = 'online' | 'offline' | 'away' | 'dnd';
export interface Presence {
  userId: string;
  status: PresenceStatus;
  lastActiveAt?: string;
}

// Generic API response wrapper
export interface ApiResponse<T> {
  data: T;
  meta?: Record<string, any>;
}