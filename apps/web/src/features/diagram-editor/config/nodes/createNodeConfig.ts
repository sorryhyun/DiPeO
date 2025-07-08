import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import type { NodeTypeKey } from '@/core/types/type-factories';
import type { NodeConfigItem } from '@/features/diagram-editor/types';
import { mergeFieldConfigs } from './fieldOverrides';

export interface NodeConfigOptions<T extends Record<string, unknown>> {
  nodeType: NodeTypeKey;
  label: string;
  icon: string;
  color: string;
  handles: NodeConfigItem['handles'];
  defaults: Record<string, unknown>;
  panelLayout?: 'single' | 'twoColumn';
  panelFieldOrder?: Array<keyof T | string>;
}

/**
 * Create a node configuration with automatically generated and merged field configs
 * This ensures new domain fields automatically appear in the UI with sensible defaults
 */
export function createNodeConfig<T extends Record<string, unknown>>(
  options: NodeConfigOptions<T>
): UnifiedNodeConfig<T> {
  const { nodeType, ...rest } = options;
  
  // Get merged field configs (generated + overrides)
  const customFields = mergeFieldConfigs(nodeType);
  
  return {
    nodeType,
    customFields,
    ...rest
  };
}

/**
 * Create a basic node configuration without field generation
 * Use this for simple nodes that don't need field configs
 */
export function createBasicNodeConfig<T extends Record<string, unknown>>(
  options: NodeConfigOptions<T> & {
    customFields?: UnifiedNodeConfig<T>['customFields'];
  }
): UnifiedNodeConfig<T> {
  return options as UnifiedNodeConfig<T>;
}