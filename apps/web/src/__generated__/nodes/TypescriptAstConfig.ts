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
      { id: 'data', label: '', position: 'left' },
    ],
    output: [
      { id: 'result', label: '', position: 'right' },
      { id: 'result', label: '', position: 'right' },
      { id: 'result', label: '', position: 'right' },
      { id: 'result', label: '', position: 'right' },
      { id: 'result', label: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: typescriptAstFields,
};

export default typescriptAstConfig;