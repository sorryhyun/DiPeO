import type { NodeConfigItem } from '../types';

export const dbNodeConfig: NodeConfigItem = {
  label: 'Database',
  icon: '💾',
  color: 'yellow',
  handles: {
    input: [{ id: 'default', position: 'bottom', offset: { x: -20, y: 0 } }],
    output: [{ id: 'default', position: 'bottom', offset: { x: 20, y: 0 } }]
  },
  fields: [
    { 
      name: 'operation', 
      type: 'select', 
      label: 'Operation', 
      required: true,
      options: [
        { value: 'read', label: 'Read File' },
        { value: 'write', label: 'Write File' },
        { value: 'query', label: 'Query Database' }
      ]
    },
    { name: 'path', type: 'string', label: 'File Path', required: true, placeholder: 'data/file.json' },
    { 
      name: 'format', 
      type: 'select', 
      label: 'Format', 
      required: true,
      options: [
        { value: 'json', label: 'JSON' },
        { value: 'csv', label: 'CSV' },
        { value: 'text', label: 'Text' }
      ]
    }
  ],
  defaults: { operation: 'read', path: '', format: 'json' }
};