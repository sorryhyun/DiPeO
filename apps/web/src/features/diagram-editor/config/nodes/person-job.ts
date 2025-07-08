import { HandleLabel } from '@dipeo/domain-models';
import type { PersonJobNodeData } from '@/core/types';
import { createNodeConfig } from './createNodeConfig';

/**
 * Complete configuration for the Person Job node type
 * Combines visual metadata, node structure, and field definitions
 * Field configurations are automatically generated from domain models and customized via overrides
 */
export const PersonJobNodeConfig = createNodeConfig<PersonJobNodeData>({
  // Visual metadata
  nodeType: 'person_job' as any,
  label: 'Person Job',
  icon: '🤖',
  color: '#3b82f6',
  
  // Node structure
  handles: {
    input: [
      { id: HandleLabel.FIRST, position: 'left', label: 'first', offset: { x: 0, y: -60 }, color: '#f59e0b' },
      { id: HandleLabel.DEFAULT, position: 'left', label: 'default', offset: { x: 0, y: 60 }, color: '#2563eb' }
    ],
    output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    person: '', 
    max_iteration: 1, 
    first_only_prompt: '', 
    default_prompt: '',
    tools: '',
    memory_config: {
      forget_mode: 'no_forget'
    }
  },
  
  // Panel layout configuration
  panelLayout: 'twoColumn',
  panelFieldOrder: ['labelPersonRow', 'max_iteration', 'tools', 'memory_config.forget_mode', 'default_prompt', 'first_only_prompt']
});