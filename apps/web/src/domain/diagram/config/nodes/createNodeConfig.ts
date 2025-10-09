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

export function createNodeConfig<T extends Record<string, unknown>>(
  options: NodeConfigOptions<T>
): UnifiedNodeConfig<T> {
  const { nodeType, ...rest } = options;

  const customFields = mergeFieldConfigs(nodeType);

  return {
    nodeType,
    customFields,
    ...rest
  };
}

export async function createNodeConfigAsync<T extends Record<string, unknown>>(
  options: NodeConfigOptions<T>
): Promise<UnifiedNodeConfig<T>> {
  const { nodeType, ...rest } = options;

  const customFields = await getBestFieldConfig(nodeType) as UnifiedFieldDefinition<T>[];

  return {
    nodeType,
    customFields,
    ...rest
  };
}

export function createBasicNodeConfig<T extends Record<string, unknown>>(
  options: NodeConfigOptions<T> & {
    customFields?: UnifiedNodeConfig<T>['customFields'];
  }
): UnifiedNodeConfig<T> {
  return options as UnifiedNodeConfig<T>;
}
