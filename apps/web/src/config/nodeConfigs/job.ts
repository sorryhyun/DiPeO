import type { NodeConfigItem } from '@/types/config';

export const jobNodeConfig: NodeConfigItem = {
  label: 'Job',
  icon: '⚙️',
  color: 'blue',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { 
      name: 'subType', 
      type: 'select', 
      label: 'Language', 
      required: true,
      options: [
        { value: 'python', label: 'Python' },
        { value: 'javascript', label: 'JavaScript' },
        { value: 'bash', label: 'Bash' }
      ]
    },
    { name: 'code', type: 'textarea', label: 'Code', required: true, placeholder: 'Enter your code here...' }
  ],
  defaults: { subType: 'python', code: '' }
};