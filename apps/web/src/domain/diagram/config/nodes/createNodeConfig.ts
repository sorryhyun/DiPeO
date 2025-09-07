import type { UnifiedNodeConfig, UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';
import type { NodeTypeKey } from '@/infrastructure/types/type-factories';
import type { NodeConfigItem } from '@/domain/diagram/types/config';
import { mergeFieldConfigs } from './fieldOverrides';
import { getBestFieldConfig, hasSpecFields } from './field-utils';

export interface NodeConfigOptions<T extends Record<string, unknown>> {
  nodeType: NodeTypeKey;
  label: string;
  icon: string;
  color: string;
  handles: NodeConfigItem['handles'];
  defaults: Record<string, unknown>;
  panelLayout?: 'single' | 'twoColumn';
  panelFieldOrder?: Array<keyof T | string>;
  category?: string;
}

/**
 * Create a node configuration with automatically generated and merged field configs
 * This ensures new domain fields automatically appear in the UI with sensible defaults
 */
export function createNodeConfig<T extends Record<string, unknown>>(
  options: NodeConfigOptions<T>
): UnifiedNodeConfig<T> {
  const { nodeType, ...rest } = options;

  // For now, use domain model fields synchronously
  // TODO: Update to use async getBestFieldConfig when the app supports it
  const customFields = mergeFieldConfigs(nodeType);

  return {
    nodeType,
    customFields,
    ...rest
  };
}

/**
 * Create a node configuration with async field loading
 * Use this when you can handle async configuration
 */
export async function createNodeConfigAsync<T extends Record<string, unknown>>(
  options: NodeConfigOptions<T>
): Promise<UnifiedNodeConfig<T>> {
  const { nodeType, ...rest } = options;

  // Get best available fields (spec-based or domain model)
  const customFields = await getBestFieldConfig(nodeType) as UnifiedFieldDefinition<T>[];

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
