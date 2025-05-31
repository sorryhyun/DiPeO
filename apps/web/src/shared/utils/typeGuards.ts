import { 
  DiagramNodeData,
  StartBlockData,
  PersonJobBlockData,
  PersonBatchJobBlockData,
  JobBlockData,
  DBBlockData,
  ConditionBlockData,
  EndpointBlockData,
  ApiKey,
  ArrowData,
  PersonDefinition
} from '@/shared/types';

// Node type guards
export function isStartBlockData(data: DiagramNodeData): data is StartBlockData {
  return data.type === 'start';
}

export function isPersonJobBlockData(data: DiagramNodeData): data is PersonJobBlockData {
  return data.type === 'person_job';
}

export function isPersonBatchJobBlockData(data: DiagramNodeData): data is PersonBatchJobBlockData {
  return data.type === 'person_batch_job';
}

export function isJobBlockData(data: DiagramNodeData): data is JobBlockData {
  return data.type === 'job';
}

export function isDBBlockData(data: DiagramNodeData): data is DBBlockData {
  return data.type === 'db';
}

export function isConditionBlockData(data: DiagramNodeData): data is ConditionBlockData {
  return data.type === 'condition';
}

export function isEndpointBlockData(data: DiagramNodeData): data is EndpointBlockData {
  return data.type === 'endpoint';
}

// API key type guard
export function isApiKey(value: unknown): value is ApiKey {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'name' in value &&
    'service' in value &&
    typeof (value as any).id === 'string' &&
    typeof (value as any).name === 'string' &&
    ['claude', 'chatgpt', 'grok', 'gemini', 'custom'].includes((value as any).service)
  );
}

// Arrow data type guard
export function isArrowData(value: unknown): value is ArrowData {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'sourceBlockId' in value &&
    'targetBlockId' in value &&
    typeof (value as any).id === 'string' &&
    typeof (value as any).sourceBlockId === 'string' &&
    typeof (value as any).targetBlockId === 'string'
  );
}

// Person definition type guard
export function isPersonDefinition(value: unknown): value is PersonDefinition {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'label' in value &&
    typeof (value as any).id === 'string' &&
    typeof (value as any).label === 'string'
  );
}

// Generic array type guard helper
export function isArrayOfType<T>(
  value: unknown,
  typeGuard: (item: unknown) => item is T
): value is T[] {
  return Array.isArray(value) && value.every(typeGuard);
}

// Helper for API responses
export function parseApiResponse<T>(
  data: unknown,
  typeGuard: (item: unknown) => item is T
): T | null {
  if (typeGuard(data)) {
    return data;
  }
  return null;
}

export function parseApiArrayResponse<T>(
  data: unknown,
  typeGuard: (item: unknown) => item is T
): T[] {
  if (isArrayOfType(data, typeGuard)) {
    return data;
  }
  if (Array.isArray(data)) {
    return data.filter(typeGuard);
  }
  return [];
}