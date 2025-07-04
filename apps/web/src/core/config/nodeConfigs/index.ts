import type { NodeType } from '@dipeo/domain-models';
import type { UnifiedNodeConfig } from '../unifiedConfig';

// Import the factory and generated configs
import { nodeConfigs } from './factory';

// Export the unified node configs from factory
export const UNIFIED_NODE_CONFIGS: Record<NodeType, UnifiedNodeConfig<Record<string, unknown>>> = nodeConfigs;