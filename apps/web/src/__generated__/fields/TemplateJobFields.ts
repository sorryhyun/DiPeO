// Generated field configuration for template_job
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const templateJobFields: UnifiedFieldDefinition[] = [
  {
    name: 'template_content',
    type: 'textarea',
    label: '"Template content"',
    required: false,
    placeholder: '"Enter template content..."',
    description: '"Inline template content"',
    rows: 10,
    adjustable: true,
  },
  {
    name: 'variables',
    type: 'textarea',
    label: '"Variables"',
    required: false,
    description: '"Variables configuration"',
  },
  {
    name: 'engine',
    type: 'text',
    label: '"Engine"',
    required: false,
    description: '"Template engine to use"',
    options: [
      { value: '"internal"', label: '"Internal"' },
      { value: '"jinja2"', label: '"Jinja2"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'preprocessor',
    type: 'text',
    label: '"Preprocessor"',
    required: false,
    description: '"Preprocessor function to apply before templating"',
  },
];
