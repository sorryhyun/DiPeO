/**
 * Setup and configuration for the converter registry
 * Registers all format converters in a central location
 */

import { converterRegistry } from './registry';
import { 
  NativeDomainConverter,
  LightDomainConverter,
  ReadableDomainConverter,
  LLMDomainConverter
} from '../formats';

/**
 * Initialize the converter registry with all available format converters
 */
export function setupConverterRegistry(): void {
  // Clear any existing registrations
  converterRegistry.clear();

  // Register all format converters
  converterRegistry.register(
    'native',
    new NativeDomainConverter(),
    {
      displayName: 'Native YAML',
      description: 'Full-fidelity YAML format preserving all diagram details'
    }
  );

  converterRegistry.register(
    'light',
    new LightDomainConverter(),
    {
      displayName: 'Light YAML',
      description: 'Simplified YAML format using labels instead of IDs'
    }
  );

  converterRegistry.register(
    'readable',
    new ReadableDomainConverter(),
    {
      displayName: 'Readable Workflow',
      description: 'Human-friendly format with embedded connections'
    }
  );

  converterRegistry.register(
    'llm-readable',
    new LLMDomainConverter(),
    {
      displayName: 'LLM-Friendly YAML',
      description: 'Simplified format optimized for AI understanding'
    }
  );
}

// Auto-initialize on module load
setupConverterRegistry();