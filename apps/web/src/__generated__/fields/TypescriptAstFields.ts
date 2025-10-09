// Generated field configuration for typescript_ast
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const typescriptAstFields: UnifiedFieldDefinition[] = [
  {
    name: 'extract_patterns',
    type: 'textarea',
    label: '"Extract patterns"',
    required: false,
    description: '"Patterns to extract from the AST"',
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
];
