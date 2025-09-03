// Generated field configuration for condition
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const conditionFields: UnifiedFieldDefinition[] = [
  {
    name: 'condition_type',
    type: 'select',
    label: 'Condition type',
    required: false,
    defaultValue: "custom",
    description: 'Type of condition to evaluate',
    options: [
      { value: 'detect_max_iterations', label: 'Detect Max Iterations' },
      { value: 'check_nodes_executed', label: 'Check Nodes Executed' },
      { value: 'custom', label: 'Custom Expression' },
      { value: 'llm_decision', label: 'LLM Decision' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'expression',
    type: 'textarea',
    label: 'Expression',
    required: false,
    placeholder: 'e.g., inputs.value > 10',
    description: 'Boolean expression to evaluate',
    rows: 3,
  },
  {
    name: 'node_indices',
    type: 'nodeSelect',
    label: 'Node indices',
    required: false,
    placeholder: 'Select nodes to monitor',
    description: 'Node indices for detect_max_iteration condition',
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'person',
    type: 'personSelect',
    label: 'Person',
    required: false,
    placeholder: 'Select AI agent',
    description: 'AI agent to use for decision making',
  },
  {
    name: 'judge_by',
    type: 'textarea',
    label: 'Judge by',
    required: false,
    placeholder: 'Enter the prompt for LLM to judge (should result in YES/NO)',
    description: 'Prompt for LLM to make a judgment',
    rows: 5,
  },
  {
    name: 'judge_by_file',
    type: 'text',
    label: 'Judge by file',
    required: false,
    placeholder: 'e.g., prompts/quality_check.txt',
    description: 'External prompt file path',
  },
  {
    name: 'memorize_to',
    type: 'text',
    label: 'Memorize to',
    required: false,
    defaultValue: "GOLDFISH",
    placeholder: 'e.g., GOLDFISH',
    description: 'Memory control strategy (e.g., GOLDFISH for fresh evaluation)',
  },
  {
    name: 'at_most',
    type: 'number',
    label: 'At most',
    required: false,
    placeholder: 'e.g., 10',
    description: 'Maximum messages to keep in memory',
  },
  {
    name: 'expose_index_as',
    type: 'text',
    label: 'Expose index as',
    required: false,
    placeholder: 'e.g., current_index, loop_counter',
    description: 'Variable name to expose the condition node\'s execution count (0-based index) to downstream nodes',
  },
  {
    name: 'skippable',
    type: 'checkbox',
    label: 'Skippable',
    required: false,
    defaultValue: false,
    description: 'When true, downstream nodes can execute even if this condition hasn\'t been evaluated yet',
  },
];