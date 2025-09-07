// Generated field configuration for template_job
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const templateJobFields: UnifiedFieldDefinition[] = [
  {
    name: 'template_path',
    type: 'text',
    label: 'Template path',
    required: false,
    placeholder: '/path/to/file',
    description: 'Path to template file',
  },
  {
    name: 'template_content',
    type: 'textarea',
    label: 'Template content',
    required: false,
    placeholder: 'Enter template content...',
    description: 'Inline template content',
    rows: 10,
    adjustable: true,
  },
  {
    name: 'output_path',
    type: 'text',
    label: 'Output path',
    required: false,
    placeholder: '/path/to/file',
    description: 'Output file path',
  },
  {
    name: 'variables',
    type: 'code',
    label: 'Variables',
    required: false,
    description: 'Variables configuration',
  },
  {
    name: 'engine',
    type: 'select',
    label: 'Engine',
    required: false,
    defaultValue: "jinja2",
    description: 'Template engine to use',
    options: [
      { value: 'internal', label: 'Internal' },
      { value: 'jinja2', label: 'Jinja2' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'preprocessor',
    type: 'text',
    label: 'Preprocessor',
    required: false,
    description: 'Preprocessor function to apply before templating',
  },
];
