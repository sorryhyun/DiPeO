// Auto-generated node configuration for typescript_ast
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { typescriptAstFields } from '../fields/TypescriptAstFields';

export const typescriptAstConfig: UnifiedNodeConfig = {
  label: 'TypeScript AST Parser',
  icon: '🔍',
  color: '#3178c6',
  nodeType: NodeType.TYPESCRIPT_AST,
  category: 'codegen',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
    ],
    output: [
      { label: HandleLabel.RESULTS, displayLabel: '', position: 'right' },
      { label: HandleLabel.ERROR, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
    extract_patterns: ["interface", "type", "enum"],
    include_jsdoc: false,
    parse_mode: 'module',
    transform_enums: false,
    flatten_output: false,
    output_format: 'standard',
    batch: false,
    batch_input_key: 'sources',
  },
  customFields: typescriptAstFields,
  primaryDisplayField: 'parse_mode',
};

export default typescriptAstConfig;
