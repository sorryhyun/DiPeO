// Generated field configuration for person_batch_job
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const personBatchJobFields: UnifiedFieldDefinition[] = [

  {
    name: 'batch_key',
    type: 'text',
    label: 'Batch Key',
    required: true,
    
    
    placeholder: 'Key containing the array to iterate over',
    
    
    description: 'Key containing the array to iterate over',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'person',
    type: 'text',
    label: 'Person',
    required: false,
    
    
    placeholder: 'Select a person',
    
    
    description: 'Person configuration for AI model',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'prompt',
    type: 'textarea',
    label: 'Prompt',
    required: true,
    
    
    placeholder: 'Use {{item}} for current batch item, {{variable_name}} for other variables',
    
    
    description: 'Prompt template for each batch item',
    
    
    
      
    rows: 5,
      
      
      
      
      
      
      
    
    
    
    validate: (value: unknown) => {
      
      
      
      return { isValid: true };
    },
    
  },

];