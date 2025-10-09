// Auto-generated node configuration for ir_builder
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { irBuilderFields } from '../fields/IrBuilderFields';

export const irBuilderConfig: UnifiedNodeConfig = {
  label: 'IR Builder',
  icon: '🏗️',
  color: '#FF5722',
  nodeType: NodeType.IR_BUILDER,
  category: 'codegen',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
    ],
    output: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
    cache_enabled: false,
    validate_output: false,
  },
  customFields: irBuilderFields,
  primaryDisplayField: 'builder_type',
};

export default irBuilderConfig;
