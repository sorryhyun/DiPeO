// Generated field configuration for code_job
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const codeJobFields: UnifiedFieldDefinition[] = [

  {
    name: 'filePath',
    type: 'text',
    label: 'File Path',
    required: true,
    
    
    placeholder: '/path/to/file',
    
    
    description: 'Filepath configuration',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'functionName',
    type: 'text',
    label: 'Function Name',
    required: false,
    
    
    
    description: 'Functionname configuration',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'language',
    type: 'select',
    label: 'Language',
    required: true,
    
    
    
    description: 'Language configuration',
    
    
    
      
      
      
      
      
      
      
    options: [
        
      { value: 'python', label: 'Python' },
        
      { value: 'typescript', label: 'TypeScript' },
        
      { value: 'bash', label: 'Bash' },
        
      { value: 'shell', label: 'Shell' },
        
    ],
      
    
    
    
    validate: (value: unknown) => {
      
      
      
      return { isValid: true };
    },
    
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

];