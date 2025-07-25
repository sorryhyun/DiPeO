// Generated field configuration for sub_diagram
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const subDiagramFields: UnifiedFieldDefinition[] = [

  {
    name: 'diagram_data',
    type: 'code',
    label: 'Diagram Data',
    required: false,
    
    
    
    description: 'Inline diagram data (alternative to diagram_name)',
    
    
    
      
      
      
      
      
    language: 'json',
      
      
      
    
    
    
  },

  {
    name: 'diagram_name',
    type: 'select',
    label: 'Diagram Name',
    required: false,
    
    
    placeholder: 'Select diagram...',
    
    
    description: 'Name of the diagram to execute (e.g., \'workflow/process\')',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'input_mapping',
    type: 'code',
    label: 'Input Mapping',
    required: false,
    
    
    placeholder: '{ \"targetVar\": \"sourceInput\" }',
    
    
    description: 'Map node inputs to sub-diagram variables',
    
    
    
      
      
      
      
      
    language: 'json',
      
      
      
    
    
    
  },

  {
    name: 'isolate_conversation',
    type: 'checkbox',
    label: 'Isolate Conversation',
    required: false,
    
    defaultValue: false,
    
    
    
    description: 'Create isolated conversation context for sub-diagram',
    
    
    
    
    
  },

  {
    name: 'output_mapping',
    type: 'code',
    label: 'Output Mapping',
    required: false,
    
    
    placeholder: '{ \"outputKey\": \"nodeId.field\" }',
    
    
    description: 'Map sub-diagram outputs to node outputs',
    
    
    
      
      
      
      
      
    language: 'json',
      
      
      
    
    
    
  },

  {
    name: 'timeout',
    type: 'number',
    label: 'Timeout',
    required: false,
    
    
    
    description: 'Execution timeout in seconds',
    
    
    
    
    
    validate: (value: unknown) => {
      
      
      if (typeof value === 'number' && value < 1) {
        return { isValid: false, error: 'Value must be at least 1' };
      }
      
      
      if (typeof value === 'number' && value > 3600) {
        return { isValid: false, error: 'Value must be at most 3600' };
      }
      
      return { isValid: true };
    },
    
  },

  {
    name: 'wait_for_completion',
    type: 'checkbox',
    label: 'Wait For Completion',
    required: false,
    
    defaultValue: true,
    
    
    
    description: 'Whether to wait for sub-diagram completion',
    
    
    
    
    
  },

];