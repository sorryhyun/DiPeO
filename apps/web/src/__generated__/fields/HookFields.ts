// Generated field configuration for hook
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const hookFields: UnifiedFieldDefinition[] = [

  {
    name: 'command',
    type: 'text',
    label: 'Command',
    required: false,
    
    
    placeholder: 'Command to execute',
    
    
    description: 'Shell command to run (for shell hooks)',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'hook_type',
    type: 'select',
    label: 'Hook Type',
    required: true,
    
    defaultValue: "shell",
    
    
    
    description: 'Type of hook to execute',
    
    
    options: [
      
      { value: 'shell', label: 'Shell' },
      
      { value: 'http', label: 'Http' },
      
      { value: 'python', label: 'Python' },
      
      { value: 'file', label: 'File' },
      
    ],
    
    
    
    
  },

  {
    name: 'retry_count',
    type: 'number',
    label: 'Retry Count',
    required: false,
    
    defaultValue: 0,
    
    
    
    description: 'Number of retries on failure',
    
    
    
    
    
    validate: (value: unknown) => {
      
      
      if (typeof value === 'number' && value < 0) {
        return { isValid: false, error: 'Value must be at least 0' };
      }
      
      
      if (typeof value === 'number' && value > 5) {
        return { isValid: false, error: 'Value must be at most 5' };
      }
      
      return { isValid: true };
    },
    
  },

  {
    name: 'timeout',
    type: 'number',
    label: 'Timeout',
    required: false,
    
    defaultValue: 60,
    
    
    
    description: 'Execution timeout in seconds',
    
    
    
    
    
    validate: (value: unknown) => {
      
      
      if (typeof value === 'number' && value < 1) {
        return { isValid: false, error: 'Value must be at least 1' };
      }
      
      
      if (typeof value === 'number' && value > 300) {
        return { isValid: false, error: 'Value must be at most 300' };
      }
      
      return { isValid: true };
    },
    
  },

  {
    name: 'url',
    type: 'text',
    label: 'Url',
    required: false,
    
    
    placeholder: 'https://api.example.com/webhook',
    
    
    description: 'Webhook URL (for HTTP hooks)',
    
    
    
    
    
    validate: (value: unknown) => {
      
      if (typeof value === 'string' && !new RegExp('^https?://').test(value)) {
        return { isValid: false, error: 'Invalid format' };
      }
      
      
      
      return { isValid: true };
    },
    
  },

];