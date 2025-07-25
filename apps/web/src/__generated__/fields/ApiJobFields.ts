// Generated field configuration for api_job
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const apiJobFields: UnifiedFieldDefinition[] = [

  {
    name: 'auth_config',
    type: 'code',
    label: 'Auth Config',
    required: false,
    
    
    
    description: 'Auth Config configuration',
    
    
    
      
      
      
      
      
    language: 'json',
      
      
      
    
    
    
  },

  {
    name: 'auth_type',
    type: 'select',
    label: 'Auth Type',
    required: false,
    
    
    
    description: 'Auth Type configuration',
    
    
    options: [
      
      { value: 'none', label: 'None' },
      
      { value: 'bearer', label: 'Bearer' },
      
      { value: 'basic', label: 'Basic' },
      
      { value: 'api_key', label: 'Api Key' },
      
    ],
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'body',
    type: 'code',
    label: 'Body',
    required: false,
    
    
    
    description: 'Body configuration',
    
    
    
      
      
      
      
      
    language: 'json',
      
      
      
    
    
    
  },

  {
    name: 'headers',
    type: 'code',
    label: 'Headers',
    required: false,
    
    
    
    description: 'Headers configuration',
    
    
    
      
      
      
      
      
    language: 'json',
      
      
      
    
    
    
  },

  {
    name: 'method',
    type: 'select',
    label: 'Method',
    required: true,
    
    
    
    description: 'Method configuration',
    
    
    options: [
      
      { value: 'GET', label: 'Get' },
      
      { value: 'POST', label: 'Post' },
      
      { value: 'PUT', label: 'Put' },
      
      { value: 'DELETE', label: 'Delete' },
      
      { value: 'PATCH', label: 'Patch' },
      
    ],
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'params',
    type: 'code',
    label: 'Params',
    required: false,
    
    
    
    description: 'Params configuration',
    
    
    
      
      
      
      
      
    language: 'json',
      
      
      
    
    
    
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
    type: 'url',
    label: 'Url',
    required: true,
    
    
    placeholder: 'https://example.com',
    
    
    description: 'Url configuration',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

];