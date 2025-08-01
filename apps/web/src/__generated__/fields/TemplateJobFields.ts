// Generated field configuration for template_job
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const templateJobFields: UnifiedFieldDefinition[] = [
  {
    name: 'engine',
    type: 'select',
    label: 'Engine',
    required: false,
    description: 'Engine configuration',
    options: [
      { value: 'internal', label: 'Internal' },
      { value: 'jinja2', label: 'Jinja2' },
      { value: 'handlebars', label: 'Handlebars' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'output_path',
    type: 'text',
    label: 'Output Path',
    required: false,
    placeholder: '/path/to/file',
    description: 'Output file path',
  },
  {
    name: 'template_content',
    type: 'text',
    label: 'Template Content',
    required: false,
    description: 'Inline template content',
  },
  {
    name: 'template_path',
    type: 'text',
    label: 'Template Path',
    required: false,
    placeholder: '/path/to/file',
    description: 'Path to template file',
  },
  {
    name: 'variables',
    type: 'code',
    label: 'Variables',
    required: false,
    description: 'Variables configuration',
  },
];