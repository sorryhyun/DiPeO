// Auto-generated node configuration for diff_patch
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { diffPatchFields } from '../fields/DiffPatchFields';

export const diffPatchConfig: UnifiedNodeConfig = {
  label: 'Diff/Patch',
  icon: '🔧',
  color: '#9C27B0',
  nodeType: NodeType.DIFF_PATCH,
  category: 'utility',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
    ],
    output: [
      { label: HandleLabel.SUCCESS, displayLabel: '', position: 'right' },
      { label: HandleLabel.ERROR, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
    format: 'unified',
    apply_mode: 'normal',
    strip_level: 1,
    fuzz_factor: 2,
  },
  customFields: diffPatchFields,
  primaryDisplayField: 'target_path',
};

export default diffPatchConfig;
