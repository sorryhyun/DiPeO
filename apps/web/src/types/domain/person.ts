import { PersonID } from '../branded';

/**
 * LLM service types
 */
export type LLMService = 'openai' | 'claude' | 'gemini' | 'groq' | 'grok';

/**
 * Forgetting mode for person memory management
 */
export type ForgettingMode = 'no_forget' | 'on_every_turn' | 'upon_request';

/**
 * Pure domain person - represents a configured LLM instance with memory
 */
export interface DomainPerson {
  id: PersonID;
  name: string;
  model: string;
  service: LLMService;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
  forgettingMode?: ForgettingMode;
}

/**
 * Person memory configuration
 */
export interface PersonMemoryConfig {
  maxMessages?: number;
  ttlSeconds?: number;
  autoCleanup?: boolean;
}

/**
 * Person with extended configuration
 */
export interface ExtendedPerson extends DomainPerson {
  memoryConfig?: PersonMemoryConfig;
  metadata?: {
    created: string;
    lastUsed?: string;
    totalTokensUsed?: number;
  };
}

/**
 * Type guard for domain person
 */
export function isDomainPerson(obj: unknown): obj is DomainPerson {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'name' in obj &&
    'model' in obj &&
    'service' in obj
  );
}

/**
 * Default person configuration
 */
export const DEFAULT_PERSON_CONFIG: Partial<DomainPerson> = {
  temperature: 0.7,
  maxTokens: 2000,
  topP: 1.0,
  frequencyPenalty: 0,
  presencePenalty: 0,
  forgettingMode: 'no_forget'
};

/**
 * Create a new person with defaults
 */
export function createPerson(
  id: PersonID,
  name: string,
  model: string,
  service: LLMService,
  overrides?: Partial<DomainPerson>
): DomainPerson {
  return {
    ...DEFAULT_PERSON_CONFIG,
    id,
    name,
    model,
    service,
    ...overrides
  };
}

