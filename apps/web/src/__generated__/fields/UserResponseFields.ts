// Generated field configuration for user_response
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const userResponseFields: UnifiedFieldDefinition[] = [

  {
    name: 'prompt',
    type: 'textarea',
    label: 'Prompt',
    required: true,
    
    
    placeholder: 'Enter prompt template...',
    
    
    description: 'Prompt configuration',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'timeout',
    type: 'number',
    label: 'Timeout',
    required: true,
    
    
    
    description: 'Timeout configuration',
    
    
    
      
      
      
    min: 0,
      
      
    max: 3600,
      
      
      
      
    
    
    
  },

];