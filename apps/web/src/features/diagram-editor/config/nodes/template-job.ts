import { HandleLabel } from '@dipeo/domain-models';
import type { TemplateJobNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the Template Job node type
 * Combines visual metadata, node structure, and field definitions
 */
export const TemplateJobNodeConfig: UnifiedNodeConfig<TemplateJobNodeData> = {
  // Visual metadata
  label: 'Template Job',
  icon: '📝',
  color: '#8b5cf6',
  nodeType: 'template_job' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
    output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    label: 'Template Job',
    engine: 'internal'
  },
  
  // Panel layout configuration
  panelLayout: 'single',
  panelFieldOrder: ['label', 'engine', 'template_path', 'template_content', 'output_path', 'variables'],
  
  // Field definitions
  customFields: [
    {
      name: 'label',
      type: 'text',
      label: 'Label',
      required: true,
      placeholder: 'Enter template job label'
    },
    {
      name: 'engine',
      type: 'select',
      label: 'Template Engine',
      required: true,
      options: [
        { value: 'internal', label: 'Internal (Handlebars-style)' },
        { value: 'jinja2', label: 'Jinja2' },
        { value: 'handlebars', label: 'Handlebars' }
      ]
    },
    {
      name: 'template_path',
      type: 'text',
      label: 'Template File Path',
      placeholder: 'Path to template file (e.g., files/codegen/templates/backend/example.j2)',
      conditional: {
        field: 'template_content',
        operator: 'equals',
        values: ['', null, undefined]
      }
    },
    {
      name: 'template_content',
      type: 'variableTextArea',
      label: 'Inline Template',
      placeholder: 'Enter template content directly\n{{variable}} for variable substitution',
      rows: 10,
      conditional: {
        field: 'template_path',
        operator: 'equals',
        values: ['', null, undefined]
      }
    },
    {
      name: 'output_path',
      type: 'text',
      label: 'Output File Path',
      placeholder: 'Path to write rendered output (optional)'
    },
    {
      name: 'variables',
      type: 'textarea',
      label: 'Template Variables',
      placeholder: '{\n  "name": "value",\n  "items": ["item1", "item2"]\n}',
      required: false
    }
  ]
};