import type { NodeType } from '@dipeo/domain-models';

export interface NodeMetadata {
  icon: string;
  color: string;
  label: string;
  displayName: string;
}

export const NODE_META: Record<NodeType, NodeMetadata> = {
  start: {
    icon: '🚀',
    color: '#10b981',
    label: 'Start',
    displayName: 'Start'
  },
  person_job: {
    icon: '🤖',
    color: '#3b82f6',
    label: 'Person Job',
    displayName: 'Person Job'
  },
  person_batch_job: {
    icon: '📦',
    color: '#8b5cf6',
    label: 'Person Batch Job',
    displayName: 'Person Batch Job'
  },
  condition: {
    icon: '🔀',
    color: '#f59e0b',
    label: 'Condition',
    displayName: 'Condition'
  },
  db: {
    icon: '💾',
    color: '#6366f1',
    label: 'Database',
    displayName: 'Database'
  },
  endpoint: {
    icon: '🎯',
    color: '#ef4444',
    label: 'Endpoint',
    displayName: 'Endpoint'
  },
  job: {
    icon: '⚙️',
    color: '#6b7280',
    label: 'Job',
    displayName: 'Job'
  },
  user_response: {
    icon: '💬',
    color: '#14b8a6',
    label: 'User Response',
    displayName: 'User Response'
  },
  notion: {
    icon: '📝',
    color: '#ec4899',
    label: 'Notion',
    displayName: 'Notion'
  }
} as const;

export function getNodeMeta(type: NodeType): NodeMetadata {
  return NODE_META[type];
}

export function getNodeKinds(): NodeType[] {
  return Object.keys(NODE_META) as NodeType[];
}

/**
 * Generate a default label for a node
 * @param type - The node type
 * @param id - The node ID (optional, used for unique suffix)
 * @returns A formatted label string
 */
export function generateNodeLabel(type: NodeType, id?: string): string {
  const meta = NODE_META[type];
  if (!id) {
    return meta.label;
  }
  
  // Extract the last part of the ID for a unique suffix
  const suffix = id.split('-').pop();
  return `${meta.label} ${suffix}`;
}

// Export individual collections for backward compatibility
export const NODE_ICONS = Object.fromEntries(
  Object.entries(NODE_META).map(([key, value]) => [key, value.icon])
) as Record<NodeType, string>;

export const NODE_COLORS = Object.fromEntries(
  Object.entries(NODE_META).map(([key, value]) => [key, value.color])
) as Record<NodeType, string>;

export const NODE_LABELS = Object.fromEntries(
  Object.entries(NODE_META).map(([key, value]) => [key, value.label])
) as Record<NodeType, string>;