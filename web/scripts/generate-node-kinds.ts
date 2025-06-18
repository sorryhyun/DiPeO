import { NodeType } from '@dipeo/domain-models';
import fs from 'fs';
import path from 'path';

// Convert enum to string union
const nodeTypes = Object.values(NodeType);
const unionType = nodeTypes.map(t => `'${t}'`).join(' | ');

const content = `// Auto-generated from domain models - DO NOT EDIT
// Run 'pnpm generate:node-kinds' to update

import type { NodeType } from '@dipeo/domain-models';

export type NodeKind = ${unionType};

export const NODE_KINDS = [${nodeTypes.map(t => `'${t}'`).join(', ')}] as const;

export function isNodeKind(value: string): value is NodeKind {
  return NODE_KINDS.includes(value as NodeKind);
}

export function toNodeKind(type: NodeType): NodeKind {
  // NodeType values are already lowercase, just cast
  return type as unknown as NodeKind;
}

export function fromNodeKind(kind: NodeKind): NodeType {
  // NodeKind values match NodeType values, just cast
  return kind as unknown as NodeType;
}
`;

// Ensure the generated directory exists
// eslint-disable-next-line no-undef
const generatedDir = path.join(__dirname, '../src/features/diagram-editor/types');
if (!fs.existsSync(generatedDir)) {
  fs.mkdirSync(generatedDir, { recursive: true });
}

// Write the generated file
fs.writeFileSync(
  path.join(generatedDir, 'node-kinds.ts'),
  content
);

console.log('✅ NodeKind types generated successfully');