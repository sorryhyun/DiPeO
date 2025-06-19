/**
 * GraphQL Schema Exporter
 * Generates GraphQL SDL from diagram state
 */

import { NodeType, HandleDirection } from '@dipeo/domain-models';
import type { DomainNode, DomainArrow, DomainHandle } from '@/core/types';

interface GraphQLField {
  name: string;
  type: string;
  description?: string;
  args?: GraphQLArgument[];
}

interface GraphQLArgument {
  name: string;
  type: string;
  description?: string;
  defaultValue?: string;
}

interface GraphQLType {
  name: string;
  fields: GraphQLField[];
  description?: string;
}

/**
 * Maps diagram data types to GraphQL types
 */
function mapDataTypeToGraphQL(dataType: string): string {
  switch (dataType) {
    case 'STRING':
      return 'String';
    case 'NUMBER':
      return 'Float';
    case 'BOOLEAN':
      return 'Boolean';
    case 'OBJECT':
      return 'JSON';
    case 'ARRAY':
      return '[JSON]';
    default:
      return 'JSON';
  }
}

/**
 * Generate field name from handle label
 */
function generateFieldName(label: string): string {
  // Convert to camelCase and remove special characters
  return label
    .replace(/[^a-zA-Z0-9]/g, ' ')
    .split(' ')
    .map((word, index) => 
      index === 0 
        ? word.toLowerCase() 
        : word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    )
    .join('');
}

/**
 * Extract GraphQL operations from diagram nodes
 */
function extractOperations(
  nodes: Map<string, DomainNode>,
  handles: Map<string, DomainHandle>,
  arrows: Map<string, DomainArrow>
): { queries: GraphQLField[]; mutations: GraphQLField[] } {
  const queries: GraphQLField[] = [];
  const mutations: GraphQLField[] = [];
  
  nodes.forEach((node) => {
    if (node.type === NodeType.ENDPOINT) {
      const nodeHandles = Array.from(handles.values()).filter(h => h.nodeId === node.id);
      const inputHandles = nodeHandles.filter(h => h.direction === HandleDirection.INPUT);
      const outputHandles = nodeHandles.filter(h => h.direction === HandleDirection.OUTPUT);
      
      // Determine if it's a query or mutation based on node data
      const method = node.data?.method || 'GET';
      const isQuery = method === 'GET';
      
      // Create field name from node label
      const fieldName = generateFieldName(node.data?.label || 'operation');
      
      // Build arguments from input handles
      const args: GraphQLArgument[] = inputHandles.map(handle => ({
        name: generateFieldName(handle.label),
        type: mapDataTypeToGraphQL(handle.dataType),
        description: handle.label
      }));
      
      // Determine return type from output handles
      let returnType = 'JSON';
      if (outputHandles.length === 1 && outputHandles[0]) {
        returnType = mapDataTypeToGraphQL(outputHandles[0].dataType);
      } else if (outputHandles.length > 1) {
        // Create a custom type for multiple outputs
        returnType = `${fieldName}Result`;
      }
      
      const field: GraphQLField = {
        name: fieldName,
        type: returnType,
        description: node.data?.description || node.data?.label,
        args
      };
      
      if (isQuery) {
        queries.push(field);
      } else {
        mutations.push(field);
      }
    }
  });
  
  return { queries, mutations };
}

/**
 * Extract custom types from diagram structure
 */
function extractCustomTypes(
  nodes: Map<string, DomainNode>,
  handles: Map<string, DomainHandle>
): GraphQLType[] {
  const types: GraphQLType[] = [];
  const processedTypes = new Set<string>();
  
  nodes.forEach((node) => {
    if (node.type === NodeType.ENDPOINT) {
      const nodeHandles = Array.from(handles.values()).filter(h => h.nodeId === node.id);
      const outputHandles = nodeHandles.filter(h => h.direction === HandleDirection.OUTPUT);
      
      if (outputHandles.length > 1) {
        const typeName = `${generateFieldName(node.data?.label || 'operation')}Result`;
        
        if (!processedTypes.has(typeName)) {
          processedTypes.add(typeName);
          
          const fields: GraphQLField[] = outputHandles.map(handle => ({
            name: generateFieldName(handle.label),
            type: mapDataTypeToGraphQL(handle.dataType),
            description: handle.label
          }));
          
          types.push({
            name: typeName,
            fields,
            description: `Result type for ${node.data?.label || 'operation'}`
          });
        }
      }
    }
  });
  
  return types;
}

/**
 * Generate field definition
 */
function generateFieldDefinition(field: GraphQLField, indent: string = ''): string {
  let def = `${indent}${field.name}`;
  
  if (field.args && field.args.length > 0) {
    const argsStr = field.args
      .map(arg => `${arg.name}: ${arg.type}`)
      .join(', ');
    def += `(${argsStr})`;
  }
  
  def += `: ${field.type}`;
  
  if (field.description) {
    def = `${indent}# ${field.description}\n${def}`;
  }
  
  return def;
}

/**
 * Export diagram as GraphQL schema
 */
export function exportDiagramAsGraphQLSchema(diagram: {
  nodes: DomainNode[];
  arrows: DomainArrow[];
  handles: DomainHandle[];
}): string {
  // Convert arrays to maps for easier lookup
  const nodesMap = new Map(diagram.nodes.map(n => [n.id, n]));
  const handlesMap = new Map(diagram.handles.map(h => [h.id, h]));
  const arrowsMap = new Map(diagram.arrows.map(a => [a.id, a]));
  
  // Extract operations and types
  const { queries, mutations } = extractOperations(nodesMap, handlesMap, arrowsMap);
  const customTypes = extractCustomTypes(nodesMap, handlesMap);
  
  // Build schema
  let schema = '';
  
  // Add header comment
  schema += `# GraphQL Schema generated from DiPeO diagram\n`;
  schema += `# Generated at: ${new Date().toISOString()}\n\n`;
  
  // Add scalar types if needed
  const usesJSON = queries.some(q => q.type.includes('JSON')) || 
                   mutations.some(m => m.type.includes('JSON')) ||
                   customTypes.some(t => t.fields.some(f => f.type.includes('JSON')));
  
  if (usesJSON) {
    schema += `# Custom scalar for arbitrary JSON data\n`;
    schema += `scalar JSON\n\n`;
  }
  
  // Add custom types
  customTypes.forEach(type => {
    if (type.description) {
      schema += `# ${type.description}\n`;
    }
    schema += `type ${type.name} {\n`;
    type.fields.forEach(field => {
      schema += generateFieldDefinition(field, '  ') + '\n';
    });
    schema += `}\n\n`;
  });
  
  // Add Query type
  if (queries.length > 0) {
    schema += `type Query {\n`;
    queries.forEach(query => {
      schema += generateFieldDefinition(query, '  ') + '\n';
    });
    schema += `}\n\n`;
  }
  
  // Add Mutation type
  if (mutations.length > 0) {
    schema += `type Mutation {\n`;
    mutations.forEach(mutation => {
      schema += generateFieldDefinition(mutation, '  ') + '\n';
    });
    schema += `}\n\n`;
  }
  
  // Add schema definition
  if (queries.length > 0 || mutations.length > 0) {
    schema += `schema {\n`;
    if (queries.length > 0) {
      schema += `  query: Query\n`;
    }
    if (mutations.length > 0) {
      schema += `  mutation: Mutation\n`;
    }
    schema += `}\n`;
  }
  
  return schema;
}