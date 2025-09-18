import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';

export const diffPatchSpec: NodeSpecification = {
  nodeType: NodeType.DIFF_PATCH,
  displayName: "Diff/Patch",
  category: "utility",
  icon: "🔧",
  color: "#9C27B0",
  description: "Apply unified diffs to files with safety controls",

  fields: [
    {
      name: "target_path",
      type: "string",
      required: true,
      description: "Path to the file to patch",
      uiConfig: {
        inputType: "text",
        placeholder: "/path/to/file.txt"
      }
    },
    {
      name: "diff",
      type: "string",
      required: true,
      description: "Unified diff content to apply",
      uiConfig: {
        inputType: "code",
        collapsible: true,
        rows: 15,
        placeholder: "--- a/file.txt\n+++ b/file.txt\n@@ -1,3 +1,3 @@\n line1\n-old line\n+new line\n line3"
      }
    },
    {
      name: "format",
      type: "enum",
      required: false,
      description: "Diff format type",
      defaultValue: "unified",
      validation: {
        allowedValues: ["unified", "git", "context", "ed", "normal"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "unified", label: "Unified" },
          { value: "git", label: "Git" },
          { value: "context", label: "Context" },
          { value: "ed", label: "Ed Script" },
          { value: "normal", label: "Normal" }
        ]
      }
    },
    {
      name: "apply_mode",
      type: "enum",
      required: false,
      description: "How to apply the patch",
      defaultValue: "normal",
      validation: {
        allowedValues: ["normal", "force", "dry_run", "reverse"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "normal", label: "Normal" },
          { value: "force", label: "Force" },
          { value: "dry_run", label: "Dry Run" },
          { value: "reverse", label: "Reverse" }
        ]
      }
    },
    {
      name: "backup",
      type: "boolean",
      required: false,
      description: "Create backup before patching",
      defaultValue: true,
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "validate",
      type: "boolean",
      required: false,
      description: "Validate patch before applying",
      defaultValue: true,
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "backup_dir",
      type: "string",
      required: false,
      description: "Directory for backup files",
      conditional: {
        field: "backup",
        values: [true],
        operator: "equals"
      },
      uiConfig: {
        inputType: "text",
        placeholder: "/tmp/backups"
      }
    },
    {
      name: "strip_level",
      type: "number",
      required: false,
      description: "Strip N leading path components (like patch -pN)",
      defaultValue: 1,
      validation: {
        min: 0,
        max: 10
      },
      uiConfig: {
        inputType: "number",
        min: 0,
        max: 10
      }
    },
    {
      name: "fuzz_factor",
      type: "number",
      required: false,
      description: "Number of lines that can be ignored when matching context",
      defaultValue: 2,
      validation: {
        min: 0,
        max: 100
      },
      uiConfig: {
        inputType: "number",
        min: 0,
        max: 100
      }
    },
    {
      name: "reject_file",
      type: "string",
      required: false,
      description: "Path to save rejected hunks",
      uiConfig: {
        inputType: "text",
        placeholder: "/tmp/patch.reject"
      }
    },
    {
      name: "ignore_whitespace",
      type: "boolean",
      required: false,
      description: "Ignore whitespace changes when matching",
      defaultValue: false,
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "create_missing",
      type: "boolean",
      required: false,
      description: "Create target file if it doesn't exist",
      defaultValue: false,
      uiConfig: {
        inputType: "checkbox"
      }
    }
  ],

  handles: {
    inputs: ["default"],
    outputs: ["success", "failure"]
  },

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

  examples: [
    {
      name: "Simple file patch",
      description: "Apply a basic unified diff to a file",
      configuration: {
        target_path: "/src/main.py",
        diff: "--- a/main.py\n+++ b/main.py\n@@ -10,3 +10,4 @@\n def main():\n     print('Hello')\n+    print('World')\n     return 0",
        format: "unified",
        apply_mode: "normal",
        backup: true
      }
    },
    {
      name: "Dry run validation",
      description: "Test if a patch can be applied without making changes",
      configuration: {
        target_path: "/config/settings.json",
        diff: "...",
        apply_mode: "dry_run",
        validate: true
      }
    }
  ]
};
