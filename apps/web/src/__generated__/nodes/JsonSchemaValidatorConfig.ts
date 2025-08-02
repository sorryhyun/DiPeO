







// Auto-generated node configuration for json_schema_validator
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/domain-models';
import { jsonSchemaValidatorFields } from '../fields/JsonSchemaValidatorFields';

export const jsonSchemaValidatorConfig: UnifiedNodeConfig = {
  label: 'JSON Schema Validator',
  icon: '✓',
  color: '#8BC34A',
  nodeType: NodeType.JSON_SCHEMA_VALIDATOR,
  category: 'validation',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
    ],
    output: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: jsonSchemaValidatorFields,
  primaryDisplayField: 'schema_name',
};

export default jsonSchemaValidatorConfig;