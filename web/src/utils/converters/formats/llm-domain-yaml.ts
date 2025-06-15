/**
 * LLM-friendly YAML format converter wrapper for DiPeO diagrams
 * 
 * This wraps the existing LlmYaml converter to implement the DomainFormatConverter interface
 * The LLM format is fundamentally different from other formats, so it legitimately uses
 * an intermediate representation (ConverterDiagram) for the complex transformation
 */

import { DomainFormatConverter } from '../core/types';
import { DomainDiagram } from '@/types';

export class LLMDomainConverter implements DomainFormatConverter {
  readonly formatName = 'llm-readable';
  readonly fileExtension = '.llm.yaml';

  serialize(_diagram: DomainDiagram): string {
    // TODO: Implement LLM-friendly YAML serialization
    // This format is currently under development
    throw new Error('LLM-friendly YAML format is not yet implemented. Please use another format.');
  }

  deserialize(_yamlString: string): DomainDiagram {
    // TODO: Implement LLM-friendly YAML deserialization
    // This format is currently under development
    throw new Error('LLM-friendly YAML format is not yet implemented. Please use another format.');
  }
}