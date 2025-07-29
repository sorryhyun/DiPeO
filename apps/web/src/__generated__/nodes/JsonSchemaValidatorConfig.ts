// Auto-generated node configuration for json_schema_validator
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { jsonSchemaValidatorFields } from '../fields/JsonSchemaValidatorFields';

export const jsonSchemaValidatorConfig: UnifiedNodeConfig = {
  label: 'JSON Schema Validator',
  icon: '✓',
  color: '#8BC34A',
  nodeType: 'json_schema_validator',
  category: 'validation',
  handles: {
    input: [
      { id: 'data', label: '', position: 'left' },
    ],
    output: [
      { id: 'result', label: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: jsonSchemaValidatorFields,
};

export default jsonSchemaValidatorConfig;