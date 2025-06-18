// Auto-generated from domain models - DO NOT EDIT
// Run 'pnpm generate:node-kinds' to update

import type { NodeType } from '@dipeo/domain-models';

export type NodeKind = 'start' | 'person_job' | 'condition' | 'job' | 'endpoint' | 'db' | 'user_response' | 'notion' | 'person_batch_job';

export const NODE_KINDS = ['start', 'person_job', 'condition', 'job', 'endpoint', 'db', 'user_response', 'notion', 'person_batch_job'] as const;

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
