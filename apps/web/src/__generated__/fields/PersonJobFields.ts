// Generated field configuration for person_job
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const personJobFields: UnifiedFieldDefinition[] = [

  {
    name: 'default_prompt',
    type: 'textarea',
    label: 'Default Prompt',
    required: false,
    
    
    placeholder: 'Enter prompt template...',
    
    
    description: 'Default Prompt configuration',
    
    
    
      
    rows: 10,
      
      
    column: 2,
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'first_only_prompt',
    type: 'textarea',
    label: 'First Only Prompt',
    required: true,
    
    
    placeholder: 'Enter prompt template...',
    
    
    description: 'First Only Prompt configuration',
    
    
    
      
    rows: 10,
      
      
    column: 2,
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'max_iteration',
    type: 'number',
    label: 'Max Iteration',
    required: true,
    
    
    
    description: 'Max Iteration configuration',
    
    
    
      
      
      
    min: 1,
      
      
      
      
      
    
    
    
  },

  {
    name: 'memory_config',
    type: 'code',
    label: 'Memory Config',
    required: false,
    
    
    
    description: 'Memory Config configuration',
    
    
    
      
      
      
      
      
    language: 'json',
      
      
      
    
    
    
  },

  {
    name: 'memory_settings',
    type: 'group',
    label: 'Memory Settings',
    required: false,
    
    
    
    description: 'Memory Settings configuration',
    
    
    
      
      
      
      
      
      
      
    
    
    nestedFields: [
      
      {
        name: 'view',
        type: 'select',
        label: 'View',
        required: false,
        
        description: 'Memory view mode',
        
        
          
        inputType: 'select',
          
          
        options: [
          
          { value: 'all_involved', label: 'All Involved - Messages where person is sender or recipient' },
          
          { value: 'sent_by_me', label: 'Sent By Me - Messages I sent' },
          
          { value: 'sent_to_me', label: 'Sent To Me - Messages sent to me' },
          
          { value: 'system_and_me', label: 'System and Me - System messages and my interactions' },
          
          { value: 'conversation_pairs', label: 'Conversation Pairs - Request/response pairs' },
          
          { value: 'all_messages', label: 'All Messages - All messages in conversation' },
          
        ],
          
          
        
      },
      
      {
        name: 'max_messages',
        type: 'number',
        label: 'Max Messages',
        required: false,
        
        description: 'Maximum number of messages to include',
        
        
          
        inputType: 'number',
          
          
          
        min: 1,
          
        
      },
      
      {
        name: 'preserve_system',
        type: 'checkbox',
        label: 'Preserve System',
        required: false,
        
        description: 'Preserve system messages',
        
        
          
        inputType: 'checkbox',
          
          
          
        
      },
      
    ],
    
    
  },

  {
    name: 'person',
    type: 'personSelect',
    label: 'Person',
    required: false,
    
    
    
    description: 'Person configuration',
    
    
    
      
      
      
      
      
      
      
    
    
    
  },

  {
    name: 'tools',
    type: 'code',
    label: 'Tools',
    required: false,
    
    
    
    description: 'Tools configuration',
    
    
    
      
      
      
      
      
    language: 'json',
      
      
      
    
    
    
    validate: (value: unknown) => {
      
      
      
      return { isValid: true };
    },
    
  },

];