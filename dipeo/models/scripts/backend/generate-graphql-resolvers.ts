/**
 * GraphQL Resolver Generator - Fixed Version
 * Generates Python GraphQL resolvers from entity definitions following DiPeO server patterns
 */

import { EntityDefinition, CreateOperationConfig, UpdateOperationConfig } from '../../src/entity-config';
import * as fs from 'fs/promises';
import * as path from 'path';

/**
 * Helper function to properly indent multi-line custom logic
 */
function indentCustomLogic(logic: string, baseIndent: string): string {
  // Handle empty or undefined logic
  if (!logic || logic.trim() === '') return '';
  
  // Split into lines but don't trim the overall logic yet
  const lines = logic.split('\n');
  
  // Remove leading and trailing empty lines
  while (lines.length > 0 && lines[0]?.trim() === '') {
    lines.shift();
  }
  while (lines.length > 0 && lines[lines.length - 1]?.trim() === '') {
    lines.pop();
  }
  
  if (lines.length === 0) return '';
  
  // Find the minimum indentation level (excluding empty lines)
  let minIndent = Infinity;
  for (const line of lines) {
    // Skip empty lines
    if (line.trim() === '') continue;
    
    // Count leading spaces
    const match = line.match(/^( *)/);
    const spaces = match && match[1] ? match[1].length : 0;
    minIndent = Math.min(minIndent, spaces);
  }
  
  // If no indentation found, use 0
  if (minIndent === Infinity) minIndent = 0;
  
  // Remove the minimum indentation and apply base indentation
  return lines.map(line => {
    // For empty lines, return empty string
    if (line.trim() === '') return '';
    
    // Remove the common indentation and add base indentation
    return baseIndent + line.substring(minIndent);
  }).join('\n');
}

/**
 * Extract service names from custom logic
 */
function extractServicesFromLogic(logic: string): Set<string> {
  const services = new Set<string>();
  
  // Match patterns like: service_name.method(), await service_name.method()
  const servicePattern = /(?:await\s+)?(\w+_service)\.\w+\(/g;
  let match;
  while ((match = servicePattern.exec(logic)) !== null) {
    if (match[1]) {
      services.add(match[1]);
    }
  }
  
  return services;
}

/**
 * Generate service retrieval code for custom logic
 */
function generateServiceRetrievals(entity: EntityDefinition, customLogic: string | undefined, indent: string): string {
  const services = customLogic ? extractServicesFromLogic(customLogic) : new Set<string>();
  const lines: string[] = [];
  
  // Check if using CRUD adapter
  if (entity.service?.useCrudAdapter) {
    // Get CRUD adapter registry and adapter
    lines.push(`${indent}# Get CRUD adapter for standardized interface`);
    lines.push(`${indent}crud_registry = context.get_service("crud_registry")`);
    lines.push(`${indent}if not crud_registry:`);
    lines.push(`${indent}    from dipeo.application.services import create_crud_registry`);
    lines.push(`${indent}    crud_registry = create_crud_registry(context.service_registry)`);
    lines.push(`${indent}${entity.service.name} = crud_registry.get_adapter("${entity.service.name}")`);    
    lines.push(`${indent}if not ${entity.service.name}:`);
    lines.push(`${indent}    raise ValueError("CRUD adapter for ${entity.service.name} not found")`);    
  } else {
    // Always include the entity's main service
    const mainService = entity.service?.name || `${entity.name.toLowerCase()}_service`;
    lines.push(`${indent}${mainService} = context.get_service("${mainService}")`);    
  }
  
  // Add other services found in custom logic
  const definedService = entity.service?.name || `${entity.name.toLowerCase()}_service`;
  for (const service of services) {
    if (service !== definedService) {
      lines.push(`${indent}${service} = context.get_service("${service}")`);
    }
  }
  
  return lines.join('\n');
}

/**
 * Generate complete GraphQL mutation class for an entity
 */
export async function generateMutations(entity: EntityDefinition): Promise<string> {
  const imports = generateImports(entity);
  const className = `${entity.name}Mutations`;
  const mutations: string[] = [];
  
  // Generate CRUD operations
  if (entity.operations.create) {
    mutations.push(generateCreateMutation(entity));
  }
  
  if (entity.operations.update) {
    mutations.push(generateUpdateMutation(entity));
  }
  
  if (entity.operations.delete) {
    mutations.push(generateDeleteMutation(entity));
  }
  
  // Generate custom operations
  if (entity.operations.custom) {
    for (const [key, config] of Object.entries(entity.operations.custom)) {
      if (config.type === 'mutation') {
        mutations.push(generateCustomMutation(entity, key, config));
      }
    }
  }
  
  return `"""GraphQL mutations for ${entity.name} management - Auto-generated."""

${imports}

logger = logging.getLogger(__name__)


@strawberry.type
class ${className}:
    """Handles ${entity.name} CRUD operations."""
    
${mutations.join('\n\n')}
`;
}

/**
 * Generate imports based on entity configuration
 */
function generateImports(entity: EntityDefinition): string {
  const imports = [
    'import logging',
    'import uuid',
    'from typing import Optional',
  ];
  
  // Check if datetime is needed
  const hasDateField = Object.values(entity.fields).some(field => field.type === 'Date');
  if (hasDateField) {
    imports.push('from datetime import datetime');
  }
  
  // Collect all ID types used in fields
  const idTypes = new Set<string>();
  idTypes.add(`${entity.name}ID`); // Always include the entity's own ID
  
  Object.values(entity.fields).forEach(field => {
    if (field.type.endsWith('ID')) {
      idTypes.add(field.type);
    }
  });
  
  imports.push(
    '',
    'import strawberry',
    `from dipeo.models import ${entity.name}`,
  );
  
  // Don't import ID types from dipeo.models - they'll come from generated_types
  
  imports.push(
    '',
    'from ..context import GraphQLContext',
    'from ..generated_types import (',
    `    Create${entity.name}Input,`,
    `    Update${entity.name}Input,`,
    `    ${entity.name}Result,`,
    `    ${entity.name}ID,`, // Import from generated_types for GraphQL arguments
    '    DeleteResult,',
    '    JSONScalar,',
    '    MutationResult,',
  );
  
  // Import other ID types from generated_types if needed
  const otherIdTypes = Array.from(idTypes).filter(id => id !== `${entity.name}ID`);
  if (otherIdTypes.length > 0) {
    otherIdTypes.forEach(idType => {
      imports.push(`    ${idType},`);
    });
  }
  
  // Add entity type
  imports.push(`    ${entity.name}Type,`);
  
  imports.push(')');
  
  return imports.join('\n');
}

/**
 * Generate GraphQL types for an entity
 */
export async function generateTypes(entity: EntityDefinition): Promise<string> {
  const types: string[] = [];
  
  // Generate input types
  types.push(generateCreateInput(entity));
  types.push(generateUpdateInput(entity));
  
  // Generate result type
  types.push(generateResultType(entity));
  
  // Generate the entity type itself
  types.push(generateEntityType(entity));
  
  return types.join('\n\n');
}

/**
 * Generate create input type
 */
function generateCreateInput(entity: EntityDefinition): string {
  const config = typeof entity.operations.create === 'object' 
    ? entity.operations.create 
    : { input: [] } as CreateOperationConfig;
    
  const fields = config.input.map(field => {
    const fieldDef = entity.fields[field];
    if (!fieldDef) return `    ${field}: JSONScalar`;
    
    let fieldType = mapFieldTypeToGraphQL(fieldDef.type);
    if (!fieldDef.required && !fieldDef.nullable) {
      fieldType = `${fieldType} | None = None`;
    }
    
    return `    ${field}: ${fieldType}`;
  });
  
  return `@strawberry.input
class Create${entity.name}Input:
${fields.join('\n')}`;
}

/**
 * Generate update input type
 */
function generateUpdateInput(entity: EntityDefinition): string {
  const config = typeof entity.operations.update === 'object' 
    ? entity.operations.update 
    : { input: [], partial: true } as UpdateOperationConfig;
    
  const fields = [`    id: ${entity.name}ID`];
  
  config.input.forEach(field => {
    const fieldDef = entity.fields[field];
    if (!fieldDef) {
      fields.push(`    ${field}: JSONScalar | None = None`);
      return;
    }
    
    let fieldType = mapFieldTypeToGraphQL(fieldDef.type);
    // Update operations are usually partial
    if (config.partial) {
      fieldType = `${fieldType} | None = None`;
    }
    
    fields.push(`    ${field}: ${fieldType}`);
  });
  
  return `@strawberry.input
class Update${entity.name}Input:
${fields.join('\n')}`;
}

/**
 * Generate result type
 */
function generateResultType(entity: EntityDefinition): string {
  // Convert entity name to snake_case field name
  const fieldName = entity.name === 'ApiKey' ? 'api_key' : entity.name.toLowerCase();
  
  return `@strawberry.type
class ${entity.name}Result(MutationResult):
    ${fieldName}: ${entity.name}Type | None = None`;
}

/**
 * Generate entity GraphQL type
 */
function generateEntityType(entity: EntityDefinition): string {
  const fields = Object.entries(entity.fields).map(([name, def]) => {
    let fieldType = mapFieldTypeToGraphQL(def.type);
    if (def.nullable) {
      fieldType = `${fieldType} | None`;
    }
    return `    ${name}: ${fieldType}`;
  });
  
  return `@strawberry.type
class ${entity.name}Type:
${fields.join('\n')}`;
}

/**
 * Map field types to GraphQL types
 */
function mapFieldTypeToGraphQL(type: string): string {
  const typeMap: Record<string, string> = {
    'string': 'str',
    'number': 'float',
    'boolean': 'bool',
    'Date': 'datetime',
    'JSON': 'JSONScalar',
  };
  
  // Handle arrays
  if (type.endsWith('[]')) {
    const baseType = type.slice(0, -2);
    const mappedType = typeMap[baseType] || baseType;
    return `list[${mappedType}]`;
  }
  
  // Handle branded types (IDs)
  if (type.endsWith('ID')) {
    return type;
  }
  
  return typeMap[type] || type;
}

/**
 * Generate create mutation
 */
function generateCreateMutation(entity: EntityDefinition): string {
  const config = typeof entity.operations.create === 'object' 
    ? entity.operations.create 
    : { input: [], returnEntity: true } as CreateOperationConfig;
    
  const methodName = `create_${entity.name.toLowerCase()}`;
  const inputParam = `Create${entity.name}Input`;
  const returnType = `${entity.name}Result`;
  
  // Convert field names from camelCase to snake_case
  const fieldMappings = config.input.map(field => {
    const snakeCase = camelToSnake(field);
    return `                "${snakeCase}": getattr(${entity.name.toLowerCase()}_input, "${field}", None),`;
  }).join('\n');
  
  return `    @strawberry.mutation
    async def ${methodName}(
        self,
        ${entity.name.toLowerCase()}_input: ${inputParam},
        info: strawberry.Info[GraphQLContext],
    ) -> ${returnType}:
        """Create a new ${entity.name}."""
        try:
            context: GraphQLContext = info.context
${generateServiceRetrievals(entity, config.customLogic, '            ')}
            
            # Extract fields from input
            data = {
${fieldMappings}
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Validate required fields
            required_fields = [${config.input.filter(f => entity.fields[f]?.required).map(f => `"${camelToSnake(f)}"`).join(', ')}]
            missing = [f for f in required_fields if f not in data or data[f] is None]
            if missing:
                return ${returnType}(
                    success=False,
                    error=f"Missing required fields: {', '.join(missing)}"
                )
            
            # Create the entity
            entity_id = f"${entity.name.toLowerCase()}_{str(uuid.uuid4())[:8]}"
            
            # Build domain model
            ${entity.name.toLowerCase()}_data = ${entity.name}(
                id=${entity.name}ID(entity_id),
                **data
            )
            
            # Save through service
            ${entity.service?.useCrudAdapter ? 
              `saved_entity = await ${entity.service.name}.create(data)` :
              entity.service?.operations?.create ? 
                `saved_entity = await ${entity.service.name}.${entity.service.operations.create}(${generateCreateArgs(entity, config)})` :
                `saved_entity = await ${entity.service?.name || entity.name.toLowerCase() + '_service'}.create(${entity.name.toLowerCase()}_data)`
            }
            
${config.customLogic ? `
            # Custom logic
            entity = saved_entity
${indentCustomLogic(config.customLogic, '            ')}` : ''}
            
            # Convert to GraphQL type if needed
            ${entity.name === 'Execution' ? `${entity.name.toLowerCase()}_graphql = ${entity.name}Type.from_pydantic(saved_entity)` : `${entity.name.toLowerCase()}_graphql = saved_entity`}
            
            return ${returnType}(
                success=True,
                ${entity.name === 'ApiKey' ? 'api_key' : entity.name.toLowerCase()}=${entity.name === 'Execution' ? `${entity.name.toLowerCase()}_graphql` : 'saved_entity'},
                message=f"${entity.name} created successfully with ID: {entity_id}"
            )
            
        except ValueError as e:
            logger.error(f"Validation error creating ${entity.name}: {e}")
            return ${returnType}(
                success=False, 
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create ${entity.name}: {e}", exc_info=True)
            return ${returnType}(
                success=False, 
                error=f"Failed to create ${entity.name}: {str(e)}"
            )`;
}

/**
 * Generate update mutation
 */
function generateUpdateMutation(entity: EntityDefinition): string {
  const config = typeof entity.operations.update === 'object' 
    ? entity.operations.update 
    : { input: [], partial: true } as UpdateOperationConfig;
    
  const methodName = `update_${entity.name.toLowerCase()}`;
  const inputParam = `Update${entity.name}Input`;
  const returnType = `${entity.name}Result`;
  
  // Convert field names from camelCase to snake_case
  const fieldUpdates = config.input.map(field => {
    const snakeCase = camelToSnake(field);
    return `            if ${entity.name.toLowerCase()}_input.${field} is not None:
                updates["${snakeCase}"] = ${entity.name.toLowerCase()}_input.${field}`;
  }).join('\n');
  
  return `    @strawberry.mutation
    async def ${methodName}(
        self,
        ${entity.name.toLowerCase()}_input: ${inputParam},
        info: strawberry.Info[GraphQLContext],
    ) -> ${returnType}:
        """Update an existing ${entity.name}."""
        try:
            context: GraphQLContext = info.context
${generateServiceRetrievals(entity, config.customLogic, '            ')}
            
            # Get existing entity
            existing = await ${entity.service?.name || entity.name.toLowerCase() + '_service'}.get(${entity.name.toLowerCase()}_input.id)
            if not existing:
                return ${returnType}(
                    success=False,
                    error=f"${entity.name} with ID {${entity.name.toLowerCase()}_input.id} not found"
                )
            
            # Build updates
            updates = {}
${fieldUpdates}
            
            if not updates:
                return ${returnType}(
                    success=False,
                    error="No fields to update"
                )
            
${config.customLogic ? `
            # Custom logic
            entity = existing
${indentCustomLogic(config.customLogic, '            ')}` : ''}
            
            # Apply updates
            ${entity.service?.useCrudAdapter ? 
              `updated_entity = await ${entity.service.name}.update(${entity.name.toLowerCase()}_input.id, updates)` :
              entity.service?.operations?.update ? 
                `updated_entity = await ${entity.service.name}.${entity.service.operations.update}(${generateUpdateArgs(entity, config)})` :
                `updated_entity = await ${entity.service?.name || entity.name.toLowerCase() + '_service'}.update(${entity.name.toLowerCase()}_input.id, updates)`
            }
            
            # Convert to GraphQL type if needed
            ${entity.name === 'Execution' ? `${entity.name.toLowerCase()}_graphql = ${entity.name}Type.from_pydantic(updated_entity)` : `${entity.name.toLowerCase()}_graphql = updated_entity`}
            
            return ${returnType}(
                success=True,
                ${entity.name === 'ApiKey' ? 'api_key' : entity.name.toLowerCase()}=${entity.name === 'Execution' ? `${entity.name.toLowerCase()}_graphql` : 'updated_entity'},
                message=f"${entity.name} updated successfully"
            )
            
        except ValueError as e:
            logger.error(f"Validation error updating ${entity.name}: {e}")
            return ${returnType}(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to update ${entity.name}: {e}", exc_info=True)
            return ${returnType}(
                success=False,
                error=f"Failed to update ${entity.name}: {str(e)}"
            )`;
}

/**
 * Generate delete mutation
 */
function generateDeleteMutation(entity: EntityDefinition): string {
  const config = typeof entity.operations.delete === 'object' 
    ? entity.operations.delete 
    : { soft: false };
    
  const methodName = `delete_${entity.name.toLowerCase()}`;
  
  return `    @strawberry.mutation
    async def ${methodName}(
        self,
        ${entity.name.toLowerCase()}_id: ${entity.name}ID,
        info: strawberry.Info[GraphQLContext],
    ) -> DeleteResult:
        """Delete a ${entity.name}${config.soft ? ' (soft delete)' : ''}."""
        try:
            context: GraphQLContext = info.context
${generateServiceRetrievals(entity, config.customLogic, '            ')}
            
            # Check if exists
            ${entity.service?.useCrudAdapter ?
              `existing = await ${entity.service.name}.get(${entity.name.toLowerCase()}_id)` :
              entity.service?.operations?.get ?
                `existing = await ${entity.service.name}.${entity.service.operations.get}(${entity.name.toLowerCase()}_id)` :
                `existing = await ${entity.service?.name || entity.name.toLowerCase() + '_service'}.get(${entity.name.toLowerCase()}_id)`
            }
            if not existing:
                return DeleteResult(
                    success=False,
                    error=f"${entity.name} with ID {${entity.name.toLowerCase()}_id} not found"
                )
            
${config.customLogic ? `
            # Pre-delete validation
            entity = existing
            id = ${entity.name.toLowerCase()}_id
${indentCustomLogic(config.customLogic, '            ')}` : ''}
            
            # Delete the entity
            ${entity.service?.useCrudAdapter ?
              `await ${entity.service.name}.delete(${entity.name.toLowerCase()}_id)` :
              entity.service?.operations?.delete ?
                `await ${entity.service.name}.${entity.service.operations.delete}(${entity.name.toLowerCase()}_id)` :
                config.soft ? 
                  `await ${entity.service?.name || entity.name.toLowerCase() + '_service'}.soft_delete(${entity.name.toLowerCase()}_id)` : 
                  `await ${entity.service?.name || entity.name.toLowerCase() + '_service'}.delete(${entity.name.toLowerCase()}_id)`
            }
            
            return DeleteResult(
                success=True,
                deleted_id=str(${entity.name.toLowerCase()}_id),
                message=f"${entity.name} deleted successfully"
            )
            
        except ValueError as e:
            logger.error(f"Validation error deleting ${entity.name}: {e}")
            return DeleteResult(
                success=False,
                error=f"Cannot delete: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to delete ${entity.name}: {e}", exc_info=True)
            return DeleteResult(
                success=False,
                error=f"Failed to delete ${entity.name}: {str(e)}"
            )`;
}

/**
 * Generate custom mutation
 */
function generateCustomMutation(entity: EntityDefinition, key: string, config: any): string {
  const params = config.input?.map((field: string) => 
    `        ${camelToSnake(field)}: ${field.endsWith('Id') ? field.slice(0, -2) + 'ID' : 'str'},`
  ).join('\n') || '';
  
  return `    @strawberry.mutation
    async def ${config.name}(
        self,
${params}
        info: strawberry.Info[GraphQLContext],
    ) -> ${config.returns}:
        """${config.name} - Custom mutation for ${entity.name}."""
        try:
            context: GraphQLContext = info.context
${generateServiceRetrievals(entity, config.implementation, '            ')}
            
            # Custom implementation
${indentCustomLogic(config.implementation, '            ')}
            
        except ValueError as e:
            logger.error(f"Validation error in ${config.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to execute ${config.name}: {e}", exc_info=True)
            raise`;
}

/**
 * Generate queries for an entity
 */
export async function generateQueries(entity: EntityDefinition): Promise<string> {
  const queries: string[] = [];
  
  if (entity.operations.get) {
    queries.push(generateGetQuery(entity));
  }
  
  if (entity.operations.list) {
    queries.push(generateListQuery(entity));
  }
  
  // Generate custom queries
  if (entity.operations.custom) {
    for (const [key, config] of Object.entries(entity.operations.custom)) {
      if (config.type === 'query') {
        queries.push(generateCustomQuery(entity, key, config));
      }
    }
  }
  
  const hasFilters = entity.operations.list && 
                    typeof entity.operations.list === 'object' && 
                    entity.operations.list.filters && 
                    entity.operations.list.filters.length > 0;
  
  const imports = `"""GraphQL queries for ${entity.name} - Auto-generated."""

import strawberry
from typing import Optional

from dipeo_server.api.graphql.context import GraphQLContext
from dipeo_server.api.graphql.generated_types import (
    ${entity.name}ID,
    ${entity.name}Type,${hasFilters ? `
    ${entity.name}FilterInput,` : ''}
    JSONScalar,
)`;
  
  return `${imports}


${queries.join('\n\n')}`;
}

/**
 * Generate get query
 */
function generateGetQuery(entity: EntityDefinition): string {
  const config = typeof entity.operations.get === 'object' 
    ? entity.operations.get 
    : { throwIfNotFound: true };
    
  return `@strawberry.field
async def ${entity.name.toLowerCase()}(
    self,
    id: ${entity.name}ID,
    info: strawberry.Info[GraphQLContext]
) -> ${entity.name}Type | None:
    """Get a single ${entity.name} by ID."""
    context: GraphQLContext = info.context
    service = context.get_service("${entity.service?.name || entity.name.toLowerCase() + '_service'}")
    
    entity = await service.get(id)
    
    if not entity:
${config.throwIfNotFound ? 
        `        raise ValueError(f"${entity.name} with ID {id} not found")` : 
        `        return None`}
    
    return entity`;
}

/**
 * Generate list query
 */
function generateListQuery(entity: EntityDefinition): string {
  const config = typeof entity.operations.list === 'object' 
    ? entity.operations.list 
    : { pagination: true };
    
  const params: string[] = ['    self', '    info: strawberry.Info[GraphQLContext]'];
  
  if (config.filters && config.filters.length > 0) {
    params.push(`    filter: ${entity.name}FilterInput | None = None`);
  }
  
  if (config.pagination) {
    params.push(`    limit: int = ${config.defaultPageSize || 20}`);
    params.push('    offset: int = 0');
  }
  
  if (config.sortable) {
    params.push('    sort_by: str | None = None');
    params.push('    sort_order: str = "asc"');
  }
  
  return `@strawberry.field
async def ${entity.plural}(
${params.join(',\n')}
) -> list[${entity.name}Type]:
    """List ${entity.plural} with optional filtering and pagination."""
    context: GraphQLContext = info.context
    service = context.get_service("${entity.service?.name || entity.name.toLowerCase() + '_service'}")
    
    # Build query parameters
    query_params = {}
    
${config.filters ? `    if filter:
        # Convert filter input to service parameters
        if hasattr(filter, 'name_contains') and filter.name_contains:
            query_params['name_contains'] = filter.name_contains
${config.filters.map(f => `        if hasattr(filter, '${f}') and filter.${f} is not None:
            query_params['${camelToSnake(f)}'] = filter.${f}`).join('\n')}
` : ''}
    
    # Get entities from service
    entities = await service.list(
        **query_params,
${config.pagination ? `        limit=min(limit, ${config.maxPageSize || 100}),
        offset=offset,` : ''}
${config.sortable ? `        sort_by=sort_by,
        sort_order=sort_order,` : ''}
    )
    
    return entities`;
}

/**
 * Generate custom query
 */
function generateCustomQuery(entity: EntityDefinition, key: string, config: any): string {
  const params = ['self', 'info: strawberry.Info[GraphQLContext]'];
  
  if (config.input) {
    params.push(...config.input.map((field: string) => 
      `${camelToSnake(field)}: ${field.endsWith('Id') ? field.slice(0, -2) + 'ID' : 'str'}`
    ));
  }
  
  return `@strawberry.field
async def ${config.name}(
    ${params.join(',\n    ')}
) -> ${config.returns}:
    """${config.name} - Custom query for ${entity.name}."""
    context: GraphQLContext = info.context
${generateServiceRetrievals(entity, config.implementation, '    ')}
    
    # Custom implementation
${indentCustomLogic(config.implementation, '    ')}`;
}

/**
 * Generate create method arguments based on service configuration
 */
function generateCreateArgs(entity: EntityDefinition, config: CreateOperationConfig): string {
  // If using specific method mapping, generate appropriate args
  if (entity.service?.operations?.create && typeof entity.service.operations.create === 'string') {
    // For methods like create_api_key(label, service, key)
    if (entity.name === 'ApiKey') {
      return `label=data['label'], service=data['service'], key=data['key']`;
    }
  }
  // Default to passing the entity data object
  return `${entity.name.toLowerCase()}_data`;
}

/**
 * Generate update method arguments based on service configuration
 */
function generateUpdateArgs(entity: EntityDefinition, config: any): string {
  // If using specific method mapping, generate appropriate args
  if (entity.service?.operations?.update && typeof entity.service.operations.update === 'string') {
    // For methods like update_api_key(key_id, label, service, key)
    if (entity.name === 'ApiKey') {
      return `key_id=${entity.name.toLowerCase()}_input.id, **updates`;
    }
  }
  // Default pattern
  return `${entity.name.toLowerCase()}_input.id, updates`;
}

/**
 * Convert camelCase to snake_case
 */
function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`).replace(/^_/, '');
}

/**
 * Generate type additions to be added to generated_types.py
 */
export async function generateTypeAdditions(entity: EntityDefinition): Promise<string> {
  const additions: string[] = [];
  
  // Add the entity ID type
  additions.push(`${entity.name}ID = strawberry.scalar(
    NewType("${entity.name}ID", str),
    description="Unique identifier for a ${entity.name.toLowerCase()}",
    serialize=lambda v: str(v),
    parse_value=lambda v: str(v) if v else None,
)`);
  
  // Add filter input if list operation exists
  if (entity.operations.list) {
    const config = typeof entity.operations.list === 'object' ? entity.operations.list : {};
    
    if (config.filters && config.filters.length > 0) {
      const filterFields = ['    name_contains: str | None = None'];
      
      config.filters.forEach(filter => {
        const fieldDef = entity.fields[filter];
        if (fieldDef) {
          const fieldType = mapFieldTypeToGraphQL(fieldDef.type);
          filterFields.push(`    ${filter}: ${fieldType} | None = None`);
        }
      });
      
      additions.push(`@strawberry.input
class ${entity.name}FilterInput:
${filterFields.join('\n')}`);
    }
  }
  
  // Add the types generated earlier
  additions.push(await generateTypes(entity));
  
  return additions.join('\n\n');
}