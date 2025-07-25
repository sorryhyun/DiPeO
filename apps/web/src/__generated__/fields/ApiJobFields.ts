// Generated field configuration for api_job
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const apiJobFields: UnifiedFieldDefinition[] = [

  {
    name: 'auth_config',
    type: 'code',
    label: 'Auth Config',
    required: false,
    
    
    
    description: 'Auth Config configuration',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'auth_type',
    type: 'select',
    label: 'Auth Type',
    required: false,
    
    
    
    description: 'Auth Type configuration',
    
    
    
      
      
      
      
      
      
      
    options: [
        
      { value: 'none', label: 'None' },
        
      { value: 'bearer', label: 'Bearer Token' },
        
      { value: 'basic', label: 'Basic Auth' },
        
      { value: 'api_key', label: 'API Key' },
        
    ],
      
    
    
    
    validate: (value: unknown) => {
      
      
      
      return { isValid: true };
    },
    
  },

  {
    name: 'body',
    type: 'code',
    label: 'Body',
    required: false,
    
    
    
    description: 'Body configuration',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'headers',
    type: 'code',
    label: 'Headers',
    required: false,
    
    
    
    description: 'Headers configuration',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'method',
    type: 'select',
    label: 'Method',
    required: true,
    
    
    
    description: 'Method configuration',
    
    
    
      
      
      
      
      
      
      
    options: [
        
      { value: 'GET', label: 'GET' },
        
      { value: 'POST', label: 'POST' },
        
      { value: 'PUT', label: 'PUT' },
        
      { value: 'DELETE', label: 'DELETE' },
        
      { value: 'PATCH', label: 'PATCH' },
        
    ],
      
    
    
    
    validate: (value: unknown) => {
      
      
      
      return { isValid: true };
    },
    
  },

  {
    name: 'params',
    type: 'code',
    label: 'Params',
    required: false,
    
    
    
    description: 'Params configuration',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'timeout',
    type: 'number',
    label: 'Timeout',
    required: false,
    
    
    
    description: 'Timeout configuration',
    
    
    
      
      
      
    min: 0,
      
      
    max: 3600,
      
      
      
      
    
    
    
  },

  {
    name: 'url',
    type: 'text',
    label: 'Url',
    required: true,
    
    
    placeholder: 'https://example.com',
    
    
    description: 'Url configuration',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

];