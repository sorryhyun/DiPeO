import { NodeType } from '../core/enums/node-types.js';
import { DiffFormat, PatchMode } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';
import { textField, contentField, booleanField } from '../core/field-presets.js';
import { validatedEnumField, validatedNumberField } from '../core/validation-utils.js';

export const diffPatchSpec: NodeSpecification = {
  nodeType: NodeType.DIFF_PATCH,
  displayName: "Diff/Patch",
  category: "utility",
  icon: "🔧",
  color: "#9C27B0",
  description: "Apply unified diffs to files with safety controls",

  fields: [
    textField({
      name: "target_path",
      description: "Path to the file to patch",
      placeholder: "/path/to/file.txt",
      required: true
    }),
    contentField({
      name: "diff",
      description: "Unified diff content to apply",
      inputType: "code",
      rows: 15,
      placeholder: "--- a/file.txt\n+++ b/file.txt\n@@ -1,3 +1,3 @@\n line1\n-old line\n+new line\n line3",
      required: true
    }),
    validatedEnumField({
      name: "format",
      description: "Diff format type",
      options: [
        { value: DiffFormat.UNIFIED, label: "Unified" },
        { value: DiffFormat.GIT, label: "Git" },
        { value: DiffFormat.CONTEXT, label: "Context" },
        { value: DiffFormat.ED, label: "Ed Script" },
        { value: DiffFormat.NORMAL, label: "Normal" }
      ],
      defaultValue: DiffFormat.UNIFIED,
      required: false
    }),
    validatedEnumField({
      name: "apply_mode",
      description: "How to apply the patch",
      options: [
        { value: PatchMode.NORMAL, label: "Normal" },
        { value: PatchMode.FORCE, label: "Force" },
        { value: PatchMode.DRY_RUN, label: "Dry Run" },
        { value: PatchMode.REVERSE, label: "Reverse" }
      ],
      defaultValue: PatchMode.NORMAL,
      required: false
    }),
    booleanField({
      name: "backup",
      description: "Create backup before patching",
      defaultValue: true
    }),
    booleanField({
      name: "validate_patch",
      description: "Validate patch before applying",
      defaultValue: true
    }),
    {
      ...textField({
        name: "backup_dir",
        description: "Directory for backup files",
        placeholder: "/tmp/backups"
      }),
      conditional: {
        field: "backup",
        values: [true],
        operator: "equals"
      }
    },
    validatedNumberField({
      name: "strip_level",
      description: "Strip N leading path components (like patch -pN)",
      min: 0,
      max: 10,
      defaultValue: 1
    }),
    validatedNumberField({
      name: "fuzz_factor",
      description: "Number of lines that can be ignored when matching context",
      min: 0,
      max: 100,
      defaultValue: 2
    }),
    textField({
      name: "reject_file",
      description: "Path to save rejected hunks",
      placeholder: "/tmp/patch.reject"
    }),
    booleanField({
      name: "ignore_whitespace",
      description: "Ignore whitespace changes when matching",
      defaultValue: false
    }),
    booleanField({
      name: "create_missing",
      description: "Create target file if it doesn't exist",
      defaultValue: false
    })
  ],

  handles: {
    inputs: ["default"],
    outputs: ["success", "error"]
  },

  inputPorts: [
    {
      name: "default",
      contentType: "object",
      required: false,
      description: "Input data containing diff content, target path, or patch configuration"
    }
  ],

  outputs: {
    result: {
      type: "any",
      description: "Patch application result with status, modified files, and rejected hunks"
    },
    backup_path: {
      type: "any",
      description: "Path to backup file if created"
    },
    rejected_hunks: {
      type: "any",
      description: "List of hunks that couldn't be applied"
    },
    file_hash: {
      type: "any",
      description: "Hash of the patched file for verification"
    }
  },

  execution: {
    timeout: 60,
    retryable: true,
    maxRetries: 2
  },

  primaryDisplayField: "target_path",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.diff_patch",
    className: "DiffPatchHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["FILE_SYSTEM", "STATE_STORE"]
  },

  examples: [
    {
      name: "Simple file patch",
      description: "Apply a basic unified diff to a file",
      configuration: {
        target_path: "/src/main.py",
        diff: "--- a/main.py\n+++ b/main.py\n@@ -10,3 +10,4 @@\n def main():\n     print('Hello')\n+    print('World')\n     return 0",
        format: DiffFormat.UNIFIED,
        apply_mode: PatchMode.NORMAL,
        backup: true
      }
    },
    {
      name: "Dry run validation",
      description: "Test if a patch can be applied without making changes",
      configuration: {
        target_path: "/config/settings.json",
        diff: "...",
        apply_mode: PatchMode.DRY_RUN,
        validate_patch: true
      }
    }
  ]
};
