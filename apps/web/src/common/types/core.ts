// Core domain types - Essential entities and their relationships

export interface Node {
  id: string;
  type: 'start' | 'job' | 'person_job' | 'condition' | 'endpoint' | 'db' | 'notion' | 'person_batch_job' | 'user_response';
  position: { x: number; y: number };
  data: Record<string, any>; // Flexible data storage - stop over-typing
}

export interface Arrow {
  id: string;
  source: string;
  target: string;
  type?: string;
  sourceHandle?: string;
  targetHandle?: string;
  data?: Record<string, any>;
}

export interface Person {
  id: string;
  label: string;
  apiKeyId?: string;
  modelName?: string;
  service?: string;
  systemPrompt?: string;
  memory?: ConversationMessage[];
  options?: Record<string, any>;
}

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ApiKey {
  id: string;
  name: string;
  service: 'openai' | 'anthropic' | 'google' | 'groq' | 'notion';
}

export interface Diagram {
  nodes: Node[];
  arrows: Arrow[];
  persons: Person[];
  apiKeys: ApiKey[];
  metadata?: {
    id?: string;
    name?: string;
    description?: string;
    created?: string;
    modified?: string;
  };
}