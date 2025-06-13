import { DomainDiagram } from '@/types';
import type { UnifiedStore } from '@/stores/unifiedStore.types';

// Base converter interface for all format converters
export interface DomainFormatConverter<T = string> {
  // Domain to format
  serialize(diagram: DomainDiagram): T;
  
  // Format to domain
  deserialize(data: T): DomainDiagram;
  
  // Format metadata
  readonly formatName: string;
  readonly fileExtension: string;
}

// Store to domain converter (single source of truth)
export interface StoreDomainConverter {
  // Store state to domain model
  storeToDomain(store: Pick<UnifiedStore, 'nodes' | 'arrows' | 'handles' | 'persons' | 'apiKeys'>): DomainDiagram;
  
  // Domain model to store state
  domainToStore(diagram: DomainDiagram): Pick<UnifiedStore, 'nodes' | 'arrows' | 'handles' | 'persons' | 'apiKeys'>;
}

// Re-export for convenience
export type { UnifiedStore } from '@/stores/unifiedStore.types';

// Supported format types
export type SupportedFormat = 'native' | 'light' | 'readable' | 'llm-readable';

// Format metadata
export interface FormatMetadata {
  name: string;
  displayName: string;
  extension: string;
  description: string;
}