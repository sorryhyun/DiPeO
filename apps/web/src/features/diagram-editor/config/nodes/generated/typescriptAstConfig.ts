import { Position } from '@xyflow/react';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import type { TypescriptAstNodeData } from '@/core/types';
import { typescriptAstFields } from './typescriptAstFields';

export const TypescriptAstNodeConfig: UnifiedNodeConfig<TypescriptAstNodeData> = {
  nodeType: 'typescript_ast' as const,
  label: 'TypeScript AST Parser',
  icon: '🔍',
  color: '#3178c6',
  
  handles: {
    input: [
      { id: 'source', position: Position.Left },
    ],
    output: [
      { id: 'ast', position: Position.Right },
      { id: 'interfaces', position: Position.Right },
      { id: 'types', position: Position.Right },
      { id: 'enums', position: Position.Right },
      { id: 'error', position: Position.Right },
    ]
  },
  
  defaults: {
    label: 'TypeScript AST Parser',
    extractPatterns: ["interface", "type", "enum"],
    parseMode: 'module',
  },
  
  customFields: typescriptAstFields
};