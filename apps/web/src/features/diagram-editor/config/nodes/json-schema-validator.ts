import { HandleLabel } from '@dipeo/domain-models';
import type { JsonSchemaValidatorNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the JSON Schema Validator node type
 * Combines visual metadata, node structure, and field definitions
 */
export const JsonSchemaValidatorNodeConfig: UnifiedNodeConfig<JsonSchemaValidatorNodeData> = {
  // Visual metadata
  label: 'JSON Schema Validator',
  icon: '✅',
  color: '#10b981',
  nodeType: 'json_schema_validator' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
    output: [
      { id: HandleLabel.DEFAULT, position: 'right' },
      { id: 'error', position: 'right' }
    ]
  },
  
  // Default values
  defaults: { 
    label: 'JSON Schema Validator',
    strict_mode: false,
    error_on_extra: false
  },
  
  // Panel layout configuration
  panelLayout: 'single',
  panelFieldOrder: ['label', 'schema_path', 'schema', 'data_path', 'strict_mode', 'error_on_extra'],
  
  // Field definitions
  customFields: [
    {
      name: 'label',
      type: 'text',
      label: 'Label',
      required: true,
      placeholder: 'Enter validator label'
    },
    {
      name: 'schema_path',
      type: 'text',
      label: 'Schema File Path',
      placeholder: 'Path to JSON schema file (e.g., files/schemas/node.schema.json)',
      conditional: {
        field: 'schema',
        operator: 'empty'
      }
    },
    {
      name: 'schema',
      type: 'code',
      label: 'Inline Schema',
      placeholder: '{\n  "$schema": "http://json-schema.org/draft-07/schema#",\n  "type": "object",\n  "properties": {\n    "name": { "type": "string" }\n  }\n}',
      language: 'json',
      rows: 15,
      conditional: {
        field: 'schema_path',
        operator: 'empty'
      }
    },
    {
      name: 'data_path',
      type: 'text',
      label: 'Data File Path',
      placeholder: 'Path to JSON data file to validate (optional, uses input if not provided)'
    },
    {
      name: 'strict_mode',
      type: 'checkbox',
      label: 'Strict Mode',
      description: 'Collect all validation errors instead of stopping at first'
    },
    {
      name: 'error_on_extra',
      type: 'checkbox',
      label: 'Error on Extra Properties',
      description: 'Fail validation if object contains properties not in schema'
    }
  ]
};