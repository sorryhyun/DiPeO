







// Auto-generated node configuration for typescript_ast
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { typescriptAstFields } from '../fields/TypescriptAstFields';

export const typescriptAstConfig: UnifiedNodeConfig = {
  label: 'TypeScript AST Parser',
  icon: '🔍',
  color: '#3178c6',
  nodeType: 'typescript_ast',
  category: 'utility',
  handles: {
    input: [
      { label: 'default', displayLabel: '', position: 'left' },
    ],
    output: [
      { label: 'results', displayLabel: 'Results', position: 'right' },
      { label: 'error', displayLabel: 'Error', position: 'right' },
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
  primaryDisplayField: 'operation',
};

export default typescriptAstConfig;