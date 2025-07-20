import { HandleLabel, NodeType } from '@dipeo/domain-models';
import type { CodeJobNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the Code Job node type
 * Executes code from files instead of inline code
 * 
 * Examples:
 * - Python: files/code_examples/example_python.py (calls main() function)
 * - TypeScript: files/code_examples/example_typescript.ts (calls exported main function)
 * - Bash: files/code_examples/example_bash.sh (accesses inputs via INPUT_* env vars)
 * 
 * Input data flows through connection labels as keys in the input object/env vars
 */
export const CodeJobNodeConfig: UnifiedNodeConfig<CodeJobNodeData> = {
  // Visual metadata
  label: 'Code Job',
  icon: '💻',
  color: '#4ade80',
  nodeType: 'code_job' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
    output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    label: 'Code Job', 
    language: 'python', 
    filePath: '',
    functionName: 'main'
  },
  
  // Panel layout configuration
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'language', 'filePath', 'functionName'],
  
  // Field definitions
  customFields: [
    {
      name: 'label',
      type: 'text',
      label: 'Label',
      required: true,
      placeholder: 'Enter code job label'
    },
    {
      name: 'language',
      type: 'select',
      label: 'Language',
      required: true,
      options: [
        { value: 'python', label: 'Python' },
        { value: 'typescript', label: 'TypeScript' },
        { value: 'bash', label: 'Bash' },
        { value: 'shell', label: 'Shell' }
      ],
      column: 1,
      helpText: 'Select the programming language of your code file'
    },
    {
      name: 'filePath',
      type: 'text',
      label: 'File Path',
      required: true,
      placeholder: 'e.g., files/code_examples/my_script.py',
      column: 2,
      helpText: 'Path to the code file (relative to project root or absolute)',
      validate: (value: unknown) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'File path is required' };
        }
        // Basic file path validation
        const trimmed = value.trim();
        if (trimmed.includes('..')) {
          return { isValid: false, error: 'File path cannot contain ".."' };
        }
        return { isValid: true };
      }
    },
    {
      name: 'functionName',
      type: 'text',
      label: 'Function Name',
      required: false,
      placeholder: 'main',
      column: 2,
      helpText: 'Name of the function to call (Python/TypeScript only, defaults to "main")',
      visible: (data: any) => data.language === 'python' || data.language === 'typescript'
    }
  ]
};