import { HandleLabel } from '@dipeo/domain-models';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the Job node type
 * This is a generic job node type that can be extended by specific job types
 */
export const JobNodeConfig: UnifiedNodeConfig<Record<string, unknown>> = {
  // Visual metadata
  label: 'Job',
  icon: '⚙️',
  color: '#6b7280',
  nodeType: 'job' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
    output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    label: 'Job' 
  },
  
  // Panel layout configuration
  panelLayout: 'single',
  panelFieldOrder: ['label'],
  
  // Field definitions
  customFields: [
    {
      name: 'label',
      type: 'text',
      label: 'Label',
      required: true,
      placeholder: 'Enter job label'
    }
  ]
};