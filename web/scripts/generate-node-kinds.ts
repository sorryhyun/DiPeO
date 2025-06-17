// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-expect-error
import { NodeType } from '../src/__generated__/graphql';
import fs from 'fs';
import path from 'path';

// Convert GraphQL enum to string union
const nodeTypes = Object.values(NodeType).map(t => t.toLowerCase());
const unionType = nodeTypes.map(t => `'${t}'`).join(' | ');

const content = `// Auto-generated from GraphQL schema - DO NOT EDIT
// Run 'pnpm generate:node-kinds' to update

import type { NodeType } from '@/__generated__/graphql';

export type NodeKind = ${unionType};

export const NODE_KINDS = [${nodeTypes.map(t => `'${t}'`).join(', ')}] as const;

export function isNodeKind(value: string): value is NodeKind {
  return NODE_KINDS.includes(value as NodeKind);
}

export function toNodeKind(type: NodeType): NodeKind {
  return type.toLowerCase() as NodeKind;
}

export function fromNodeKind(kind: NodeKind): NodeType {
  return kind.toUpperCase() as NodeType;
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