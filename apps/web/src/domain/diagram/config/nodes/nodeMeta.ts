import { NodeType } from '@dipeo/models';
import { getNodeConfig, getAllNodeConfigs } from '../nodeRegistry';

/**
 * Build node metadata from dynamic registry
 */
function buildNodeMetadata() {
  const icons: Partial<Record<NodeType, string>> = {};
  const colors: Partial<Record<NodeType, string>> = {};
  const labels: Partial<Record<NodeType, string>> = {};

  // Get all available node types from the registry
  const allConfigs = getAllNodeConfigs();

  for (const [nodeType, config] of allConfigs) {
    if (config) {
      icons[nodeType as NodeType] = config.icon;
      colors[nodeType as NodeType] = config.color;
      labels[nodeType as NodeType] = config.label;
    }
  }

  // Add defaults for any missing node types
  for (const nodeType of Object.values(NodeType)) {
    if (!icons[nodeType]) {
      icons[nodeType] = '📦'; // Default icon
    }
    if (!colors[nodeType]) {
      colors[nodeType] = '#94a3b8'; // Default color (slate-400)
    }
    if (!labels[nodeType]) {
      // Convert enum to title case
      labels[nodeType] = nodeType.split('_').map(word =>
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
      ).join(' ');
    }
  }

  return {
    icons: icons as Record<NodeType, string>,
    colors: colors as Record<NodeType, string>,
    labels: labels as Record<NodeType, string>,
  };
}

// Cache the metadata to avoid rebuilding on every access
let cachedMetadata: ReturnType<typeof buildNodeMetadata> | null = null;

/**
 * Get node metadata from the dynamic registry
 */
function getNodeMetadata() {
  if (!cachedMetadata) {
    cachedMetadata = buildNodeMetadata();
  }
  return cachedMetadata;
}

/**
 * Node visual metadata extracted from configurations
 */
export const NODE_ICONS: Record<NodeType, string> = new Proxy({} as Record<NodeType, string>, {
  get(target, prop) {
    return getNodeMetadata().icons[prop as NodeType];
  }
});

export const NODE_COLORS: Record<NodeType, string> = new Proxy({} as Record<NodeType, string>, {
  get(target, prop) {
    return getNodeMetadata().colors[prop as NodeType];
  }
});

export const NODE_LABELS: Record<NodeType, string> = new Proxy({} as Record<NodeType, string>, {
  get(target, prop) {
    return getNodeMetadata().labels[prop as NodeType];
  }
});

/**
 * Generate a default label for a node
 */
export function generateNodeLabel(type: NodeType, id: string): string {
  const label = NODE_LABELS[type] || 'Node';
  const suffix = id.slice(-4).toUpperCase();
  return `${label} ${suffix}`;
}

/**
 * Force refresh cached metadata (useful after dynamic config updates)
 */
export function refreshNodeMetadata() {
  cachedMetadata = null;
}
