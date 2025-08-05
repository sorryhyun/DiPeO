







// Auto-generated node configuration for typescript_ast
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
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
      { label: HandleLabel.RESULTS, displayLabel: 'Results', position: 'right' },
      { label: HandleLabel.ERROR, displayLabel: 'Error', position: 'right' },
    ],
  },
  defaults: {
    extractPatterns: ["interface", "type", "enum"],
    includeJSDoc: false,
    parseMode: 'module',
    transformEnums: false,
    flattenOutput: false,
    outputFormat: 'standard',
  },
  customFields: typescriptAstFields,
  primaryDisplayField: 'parseMode',
};

export default typescriptAstConfig;