// Person-related types
import { ApiKey } from './api';

export interface PersonDefinition {
  id: string;
  label: string;
  service?: ApiKey['service'];
  apiKeyId?: ApiKey['id'];
  modelName?: string;
  systemPrompt?: string;
}

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata: Record<string, unknown>;
}

export interface PersonMemory {
  personId: string;
  messages: ConversationMessage[];
  context: Record<string, unknown>;
  lastUpdated: Date;
}