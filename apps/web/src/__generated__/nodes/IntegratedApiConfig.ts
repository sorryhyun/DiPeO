







// Auto-generated node configuration for integrated_api
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { integratedApiFields } from '../fields/IntegratedApiFields';
import { mergeFieldConfigs } from '@/domain/diagram/config/nodes/fieldOverrides';

// Apply field overrides to get dynamic options
const fieldsWithOverrides = mergeFieldConfigs('integrated_api');

export const integratedApiConfig: UnifiedNodeConfig = {
  label: 'Integrated API',
  icon: '🔌',
  color: '#8b5cf6',
  nodeType: NodeType.INTEGRATED_API,
  category: 'integration',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
    ],
    output: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'right' },
      { label: HandleLabel.ERROR, displayLabel: 'Error', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: fieldsWithOverrides,
  primaryDisplayField: 'provider',
};

export default integratedApiConfig;