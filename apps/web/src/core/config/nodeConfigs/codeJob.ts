import type { CodeJobFormData } from '@/features/diagram-editor/types/panel';
import { createUnifiedConfig } from '../unifiedConfig';

export const codeJobConfig = createUnifiedConfig<CodeJobFormData>({
  // Node configuration
  label: 'Code Job',
  icon: '📝',
  color: 'blue',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { 
      name: 'language', 
      type: 'select', 
      label: 'Language', 
      required: true,
      options: [
        { value: 'python', label: 'Python' },
        { value: 'javascript', label: 'JavaScript' },
        { value: 'bash', label: 'Bash' }
      ]
    },
    { 
      name: 'code', 
      type: 'textarea', 
      label: 'Code', 
      required: true, 
      placeholder: 'Enter your code here',
      rows: 10 
    },
    { 
      name: 'timeout', 
      type: 'number', 
      label: 'Timeout (seconds)', 
      required: false,
      min: 1,
      max: 300,
      placeholder: '30'
    }
  ],
  defaults: { 
    language: 'python', 
    code: '', 
    label: 'Code Execution',
    timeout: 30
  },
  
  // Panel configuration
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'language', 'timeout', 'code'],
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Label',
      placeholder: 'Code Execution',
      column: 1
    }
  ],
  panelFieldOverrides: {
    language: { column: 1 },
    timeout: { column: 1 },
    code: { column: 2 }
  }
});