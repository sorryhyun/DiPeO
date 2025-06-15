import { PersonID, ApiKeyID } from '../branded';

export type LLMService = 'openai' | 'claude' | 'gemini'  | 'grok';

export type ForgettingMode = 'no_forget' | 'on_every_turn' | 'upon_request';

export interface DomainPerson {
  id: PersonID;
  label: string;
  model: string;
  service: LLMService;
  apiKeyId?: ApiKeyID;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
  forgettingMode?: ForgettingMode;
}

export interface PersonMemoryConfig {
  maxMessages?: number;
  ttlSeconds?: number;
  autoCleanup?: boolean;
}

export interface ExtendedPerson extends DomainPerson {
  memoryConfig?: PersonMemoryConfig;
  metadata?: {
    created: string;
    lastUsed?: string;
    totalTokensUsed?: number;
  };
}

export function isDomainPerson(obj: unknown): obj is DomainPerson {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'label' in obj &&
    'model' in obj &&
    'service' in obj
  );
}

export const DEFAULT_PERSON_CONFIG: Partial<DomainPerson> = {
  temperature: 0.7,
  maxTokens: 2000,
  topP: 1.0,
  frequencyPenalty: 0,
  presencePenalty: 0,
  forgettingMode: 'no_forget'
};

export function createPerson(
  id: PersonID,
  label: string,
  model: string,
  service: LLMService,
  overrides?: Partial<DomainPerson>
): DomainPerson {
  return {
    ...DEFAULT_PERSON_CONFIG,
    id,
    label,
    model,
    service,
    ...overrides
  };
}

