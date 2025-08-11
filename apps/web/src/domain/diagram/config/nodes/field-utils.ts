import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';
import { getGeneratedFields as getDomainFields } from '@/__generated__/fields';
import { NODE_FIELD_OVERRIDES, mergeFieldConfigs } from './fieldOverrides';

// Import all spec-based field configs
// These are dynamically imported to avoid circular dependencies
const specFieldImports: Record<string, () => Promise<{ default?: UnifiedFieldDefinition[] } | UnifiedFieldDefinition[]>> = {
  'api_job': () => import('@/__generated__/fields/ApiJobFields').then(m => m.apiJobFields),
  'code_job': () => import('@/__generated__/fields/CodeJobFields').then(m => m.codeJobFields),
  'condition': () => import('@/__generated__/fields/ConditionFields').then(m => m.conditionFields),
  'db': () => import('@/__generated__/fields/DbFields').then(m => m.dbFields),
  'endpoint': () => import('@/__generated__/fields/EndpointFields').then(m => m.endpointFields),
  'hook': () => import('@/__generated__/fields/HookFields').then(m => m.hookFields),
  'json_schema_validator': () => import('@/__generated__/fields/JsonSchemaValidatorFields').then(m => m.jsonSchemaValidatorFields),
  'person_batch_job': () => import('@/__generated__/fields/PersonBatchJobFields').then(m => m.personBatchJobFields),
  'person_job': () => import('@/__generated__/fields/PersonJobFields').then(m => m.personJobFields),
  'start': () => import('@/__generated__/fields/StartFields').then(m => m.startFields),
  'sub_diagram': () => import('@/__generated__/fields/SubDiagramFields').then(m => m.subDiagramFields),
  'template_job': () => import('@/__generated__/fields/TemplateJobFields').then(m => m.templateJobFields),
  'typescript_ast': () => import('@/__generated__/fields/TypescriptAstFields').then(m => m.typescriptAstFields),
  'user_response': () => import('@/__generated__/fields/UserResponseFields').then(m => m.userResponseFields),
};

/**
 * Get the best available field configuration for a node type
 * Priority order:
 * 1. Spec-based fields (from node specifications) - richer, includes UI config
 * 2. Domain model fields (from TypeScript interfaces) - basic, structural
 * 
 * Both are then enhanced with manual overrides from fieldOverrides.ts
 */
export async function getBestFieldConfig(nodeType: string): Promise<UnifiedFieldDefinition[]> {
  // Try to get spec-based fields first
  const specFieldImport = specFieldImports[nodeType];
  if (specFieldImport) {
    try {
      const fields = await specFieldImport();
      // Apply overrides to spec fields
      return applyFieldOverrides(nodeType, Array.isArray(fields) ? fields : []);
    } catch (error) {
      console.warn(`Failed to load spec fields for ${nodeType}, falling back to domain fields:`, error);
    }
  }
  
  // Fall back to domain model fields with overrides
  return mergeFieldConfigs(nodeType);
}

/**
 * Apply field overrides to a set of fields
 */
function applyFieldOverrides(
  nodeType: string, 
  fields: UnifiedFieldDefinition[]
): UnifiedFieldDefinition[] {
  const overrides = NODE_FIELD_OVERRIDES[nodeType];
  
  if (!overrides) {
    return fields;
  }
  
  let result = [...fields];
  
  // Remove excluded fields
  if (overrides.excludeFields) {
    result = result.filter(field => !overrides.excludeFields!.includes(field.name));
  }
  
  // Apply field overrides
  if (overrides.fieldOverrides) {
    result = result.map(field => {
      const fieldOverride = overrides.fieldOverrides![field.name];
      if (fieldOverride) {
        return { ...field, ...fieldOverride };
      }
      return field;
    });
  }
  
  // Add additional fields
  if (overrides.additionalFields) {
    result = [...result, ...overrides.additionalFields];
  }
  
  // Apply custom field order if specified
  if (overrides.fieldOrder) {
    const orderedFields: UnifiedFieldDefinition[] = [];
    const fieldMap = new Map(result.map(f => [f.name, f]));
    
    // Add fields in specified order
    for (const fieldName of overrides.fieldOrder) {
      const field = fieldMap.get(fieldName);
      if (field) {
        orderedFields.push(field);
        fieldMap.delete(fieldName);
      }
    }
    
    // Add any remaining fields not in the order
    orderedFields.push(...fieldMap.values());
    
    return orderedFields;
  }
  
  return result;
}

/**
 * Check if spec-based fields exist for a node type
 */
export function hasSpecFields(nodeType: string): boolean {
  return nodeType in specFieldImports;
}