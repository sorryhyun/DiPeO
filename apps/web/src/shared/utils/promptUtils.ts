/**
 * Utility functions for prompt template rendering and variable resolution
 * Migrated from server-side resolve_utils.py
 */

/**
 * Extract a value from an object using dot notation key path
 */
function extractFromObject(obj: unknown, keyPath: string): unknown {
  if (!obj) return null;
  
  const keys = keyPath.split('.');
  let current = obj;
  
  for (const key of keys) {
    if (typeof current === 'object' && current !== null && key in current) {
      current = (current as Record<string, unknown>)[key];
    } else {
      return null;
    }
  }
  
  return current;
}

/**
 * Replace {{var}} with its value. Unknown names are left untouched.
 */
export function renderPrompt(template: string, variables: Record<string, unknown>): string {
  return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    return Object.prototype.hasOwnProperty.call(variables, key) ? String(variables[key]) : match;
  });
}

/**
 * Extract text content from PersonJob output format
 */
function extractPersonJobText(value: unknown): unknown {
  if (typeof value === 'object' && value && '_type' in value) {
    const obj = value as Record<string, unknown>;
    if (obj._type === 'personjob_output') {
      return obj.text || '';
    }
  }
  return value;
}

/**
 * Extract conversation history from PersonJob output format
 */
function extractConversationHistory(value: unknown): Array<{role: string; content: string}> {
  if (typeof value === 'object' && value && '_type' in value) {
    const obj = value as Record<string, unknown>;
    if (obj._type === 'personjob_output') {
      return (obj.conversation_history as Array<{role: string; content: string}>) || [];
    }
  }
  return [];
}

/**
 * Check if a value is PersonJob output format
 */
function isPersonJobOutput(value: unknown): boolean {
  return typeof value === 'object' && value !== null && '_type' in value && 
         (value as Record<string, unknown>)._type === 'personjob_output';
}

export interface ResolvedInputs {
  varsMap: Record<string, unknown>;
  inputs: unknown[];
}

/**
 * Resolve incoming arrow values into vars_map and inputs list
 * This is the main function that processes arrows to prepare variables for execution
 */
export function resolveInputs(
  nodeId: string,
  incoming: Array<{
    source?: string;
    id?: string;
    data?: {
      contentType?: string;
      label?: string;
      objectKeyPath?: string;
      variableName?: string;
    };
  }>,
  context: Record<string, unknown>
): ResolvedInputs {
  const varsMap: Record<string, any> = {};
  const inputs: any[] = [];

  for (const edge of incoming) {
    const srcId = edge.source;
    const value = context[srcId || ''];
    
    // Skip if source is same as current node and value is null
    if (srcId === nodeId && value == null) {
      continue;
    }

    const arrowId = edge.id || '<unknown>';
    const data = edge.data || {};
    const contentType = data.contentType || 'raw_text';
    const label = data.label;

    let processedValue: unknown;
    let varName: string;

    switch (contentType) {
      case 'raw_text': {
        // Extract text content if this is a PersonJob output
        processedValue = extractPersonJobText(value);
        varName = label || `raw_text_${arrowId}`;
        break;
      }

      case 'variable_in_object': {
        const objectKeyPath = data.objectKeyPath;
        if (!objectKeyPath) {
          throw new Error(`Arrow ${arrowId} with type 'variable_in_object' missing 'objectKeyPath'`);
        }
        processedValue = extractFromObject(value, objectKeyPath);
        varName = label || objectKeyPath.split('.').pop() || 'extracted_value';
        break;
      }

      case 'conversation_state': {
        // For conversation_state, provide the conversation history as Messages object
        if (isPersonJobOutput(value)) {
          // Extract conversation history from PersonJob output
          processedValue = extractConversationHistory(value);
        } else if (Array.isArray(value) && 
                   value.every(msg => typeof msg === 'object' && msg && 'role' in msg && 'content' in msg)) {
          // Already properly formatted as Messages object
          processedValue = value;
        } else {
          // Fallback: create a simple message
          processedValue = [{ role: 'user', content: String(value) }];
        }
        varName = label || 'conversation_state';
        break;
      }

      default: {
        varName = label || data.variableName || 'unnamed_variable';
        if (!varName) {
          throw new Error(`Arrow ${arrowId} missing 'label' or 'variableName'`);
        }
        // Handle PersonJob output for default case
        if (isPersonJobOutput(value)) {
          const obj = value as Record<string, unknown>;
          processedValue = obj.text || '';
        } else {
          processedValue = value;
        }
        break;
      }
    }

    varsMap[varName] = processedValue;
    inputs.push(processedValue);
  }

  return { varsMap, inputs };
}