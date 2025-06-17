// Auto-generated from GraphQL schema - DO NOT EDIT
// Run 'pnpm generate:node-kinds' to update

import type { NodeType } from '@/__generated__/graphql';

export type NodeKind = 'condition' | 'db' | 'endpoint' | 'job' | 'notion' | 'person_batch_job' | 'person_job' | 'start' | 'user_response';

export const NODE_KINDS = ['condition', 'db', 'endpoint', 'job', 'notion', 'person_batch_job', 'person_job', 'start', 'user_response'] as const;

export function isNodeKind(value: string): value is NodeKind {
  return NODE_KINDS.includes(value as NodeKind);
}

export function toNodeKind(type: NodeType): NodeKind {
  return type.toLowerCase() as NodeKind;
}

export function fromNodeKind(kind: NodeKind): NodeType {
  return kind.toUpperCase() as NodeType;
}
