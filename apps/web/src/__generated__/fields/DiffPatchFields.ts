// Generated field configuration for diff_patch
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const diffPatchFields: UnifiedFieldDefinition[] = [
  {
    name: 'target_path',
    type: 'text',
    label: '"Target path"',
    required: true,
    placeholder: '"/path/to/file.txt"',
    description: '"Path to the file to patch"',
  },
  {
    name: 'diff',
    type: 'text',
    label: '"Diff"',
    required: true,
    placeholder: '"--- a/file.txt\n+++ b/file.txt\n@@ -1,3 +1,3 @@\n line1\n-old line\n+new line\n line3"',
    description: '"Unified diff content to apply"',
    rows: 15,
  },
  {
    name: 'format',
    type: 'text',
    label: '"Format"',
    required: false,
    description: '"Diff format type"',
    options: [
      { value: '"unified"', label: '"Unified"' },
      { value: '"git"', label: '"Git"' },
      { value: '"context"', label: '"Context"' },
      { value: '"ed"', label: '"Ed Script"' },
      { value: '"normal"', label: '"Normal"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'apply_mode',
    type: 'text',
    label: '"Apply mode"',
    required: false,
    description: '"How to apply the patch"',
    options: [
      { value: '"normal"', label: '"Normal"' },
      { value: '"force"', label: '"Force"' },
      { value: '"dry_run"', label: '"Dry Run"' },
      { value: '"reverse"', label: '"Reverse"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'backup',
    type: 'checkbox',
    label: '"Backup"',
    required: false,
    description: '"Create backup before patching"',
  },
  {
    name: 'validate_patch',
    type: 'text',
    label: '"Validate patch"',
    required: false,
    description: '"Validate patch before applying"',
  },
  {
    name: 'backup_dir',
    type: 'text',
    label: '"Backup dir"',
    required: false,
    placeholder: '"/tmp/backups"',
    description: '"Directory for backup files"',
  },
  {
    name: 'strip_level',
    type: 'number',
    label: '"Strip level"',
    required: false,
    description: '"Strip N leading path components (like patch -pN)"',
    min: 0,
    max: 10,
    validate: (value: unknown) => {
      if (typeof value === 'number' && value < 0) {
        return { isValid: false, error: 'Value must be at least 0' };
      }
      if (typeof value === 'number' && value > 10) {
        return { isValid: false, error: 'Value must be at most 10' };
      }
      return { isValid: true };
    },
  },
  {
    name: 'fuzz_factor',
    type: 'number',
    label: '"Fuzz factor"',
    required: false,
    description: '"Number of lines that can be ignored when matching context"',
    min: 0,
    max: 100,
    validate: (value: unknown) => {
      if (typeof value === 'number' && value < 0) {
        return { isValid: false, error: 'Value must be at least 0' };
      }
      if (typeof value === 'number' && value > 100) {
        return { isValid: false, error: 'Value must be at most 100' };
      }
      return { isValid: true };
    },
  },
  {
    name: 'reject_file',
    type: 'text',
    label: '"Reject file"',
    required: false,
    placeholder: '"/tmp/patch.reject"',
    description: '"Path to save rejected hunks"',
  },
  {
    name: 'ignore_whitespace',
    type: 'checkbox',
    label: '"Ignore whitespace"',
    required: false,
    description: '"Ignore whitespace changes when matching"',
  },
  {
    name: 'create_missing',
    type: 'checkbox',
    label: '"Create missing"',
    required: false,
    description: '"Create target file if it doesn\'t exist"',
  },
];
