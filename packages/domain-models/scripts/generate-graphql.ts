#!/usr/bin/env tsx

/**
 * Generate GraphQL schema from TypeScript interfaces
 * This creates the GraphQL SDL that matches our TypeScript definitions
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { SchemaDefinition } from './generate-schema';

class GraphQLGenerator {
  private generatedTypes: Set<string> = new Set();
  private enumTypes: Map<string, SchemaDefinition> = new Map();
  private interfaceTypes: Map<string, SchemaDefinition> = new Map();

  constructor(private schemas: SchemaDefinition[]) {
    // Separate enums and interfaces for easier lookup
    for (const schema of schemas) {
      if (schema.type === 'enum') {
        this.enumTypes.set(schema.name, schema);
      } else if (schema.type === 'interface') {
        this.interfaceTypes.set(schema.name, schema);
      }
    }
  }

  generateGraphQLType(tsType: string, isNonNull: boolean = true): string {
    // Clean up the type string
    tsType = tsType.trim();
    
    // Remove import(...) wrapping if present
    if (tsType.startsWith('import(')) {
      const match = tsType.match(/import\([^)]+\)\.(\w+)/);
      if (match) {
        tsType = match[1];
      }
    }
    
    // Handle branded types (e.g., "string & { readonly __brand: 'NodeID' }")
    if (tsType.includes('& {')) {
      tsType = 'String'; // Branded types are strings in GraphQL
      return isNonNull ? `${tsType}!` : tsType;
    }

    // Type mapping
    const typeMap: Record<string, string> = {
      'string': 'String',
      'number': 'Float',
      'float': 'Float',
      'boolean': 'Boolean',
      'any': 'JSON',
      'unknown': 'JSON',
      'null': 'null',
      'undefined': 'null',
      'void': 'null'
    };

    // Handle array types
    if (tsType.endsWith('[]')) {
      const innerType = tsType.slice(0, -2);
      const graphqlInnerType = this.generateGraphQLType(innerType, true);
      const arrayType = `[${graphqlInnerType}]`;
      return isNonNull ? `${arrayType}!` : arrayType;
    }

    // Handle Record types and objects
    if (tsType.startsWith('Record<') || tsType === 'object' || tsType.includes('Dict[str, Any]')) {
      return isNonNull ? 'JSON!' : 'JSON';
    }

    // Handle union types (excluding literal unions)
    if (tsType.includes('|') && !tsType.includes('"')) {
      const types = tsType.split('|').map(t => t.trim());
      
      // If it's just type | null or type | undefined, make it nullable
      if (types.includes('null') || types.includes('undefined')) {
        const nonNullType = types.find(t => t !== 'null' && t !== 'undefined');
        if (nonNullType) {
          return this.generateGraphQLType(nonNullType, false);
        }
      }
      
      // For other unions, use JSON
      return isNonNull ? 'JSON!' : 'JSON';
    }

    // Handle literal types - create enum if not exists
    if (tsType.includes('"')) {
      // For inline literals, use String
      return isNonNull ? 'String!' : 'String';
    }

    // Check if it's a custom type (enum or interface)
    if (this.enumTypes.has(tsType) || this.interfaceTypes.has(tsType)) {
      return isNonNull ? `${tsType}!` : tsType;
    }

    // Map basic types
    const graphqlType = typeMap[tsType] || tsType;
    
    return isNonNull ? `${graphqlType}!` : graphqlType;
  }

  generateEnum(schema: SchemaDefinition): string {
    if (!schema.values) return '';
    
    this.generatedTypes.add(schema.name);

    const lines: string[] = [];
    
    if (schema.description) {
      lines.push(`"""${schema.description}"""`);
    }
    
    lines.push(`enum ${schema.name} {`);
    
    for (const value of schema.values) {
      const key = value.toUpperCase().replace(/[^A-Z0-9_]/g, '_');
      lines.push(`  ${key}`);
    }
    
    lines.push('}');
    
    return lines.join('\n');
  }

  generateType(schema: SchemaDefinition): string {
    if (!schema.properties) return '';
    
    this.generatedTypes.add(schema.name);

    const lines: string[] = [];
    
    if (schema.description) {
      lines.push(`"""${schema.description}"""`);
    }
    
    lines.push(`type ${schema.name} {`);
    
    // Generate fields
    for (const [propName, propInfo] of Object.entries(schema.properties)) {
      const fieldName = this.toGraphQLFieldName(propName);
      const fieldType = this.generateGraphQLType(propInfo.type, !propInfo.optional);
      
      if (propInfo.description) {
        lines.push(`  """${propInfo.description}"""`);
      }
      
      lines.push(`  ${fieldName}: ${fieldType}`);
    }
    
    lines.push('}');
    
    return lines.join('\n');
  }

  generateInput(schema: SchemaDefinition): string {
    if (!schema.properties) return '';
    
    const inputName = `${schema.name}Input`;
    
    const lines: string[] = [];
    
    if (schema.description) {
      lines.push(`"""Input type for ${schema.description}"""`);
    }
    
    lines.push(`input ${inputName} {`);
    
    // Generate fields
    for (const [propName, propInfo] of Object.entries(schema.properties)) {
      const fieldName = this.toGraphQLFieldName(propName);
      
      // Skip ID fields in input types
      if (propName === 'id' || propName.endsWith('Id')) {
        continue;
      }
      
      // Skip computed fields
      if (propName === 'displayName' || propName === 'maskedKey' || propName === 'maskedApiKey') {
        continue;
      }
      
      const fieldType = this.generateGraphQLType(propInfo.type, !propInfo.optional);
      
      if (propInfo.description) {
        lines.push(`  """${propInfo.description}"""`);
      }
      
      lines.push(`  ${fieldName}: ${fieldType}`);
    }
    
    lines.push('}');
    
    return lines.join('\n');
  }

  toGraphQLFieldName(name: string): string {
    // GraphQL uses camelCase field names
    return name;
  }

  generate(): string {
    const sections: string[] = [];
    
    // Add header
    sections.push('"""');
    sections.push('Auto-generated GraphQL schema from TypeScript definitions');
    sections.push('DO NOT EDIT THIS FILE DIRECTLY');
    sections.push('Generated by: packages/domain-models/scripts/generate-graphql.ts');
    sections.push('"""');
    sections.push('');
    
    // Add scalar types
    sections.push('scalar JSON');
    sections.push('scalar DateTime');
    sections.push('');
    
    // Generate enums
    const enums = this.schemas.filter(s => s.type === 'enum');
    for (const enumSchema of enums) {
      const enumCode = this.generateEnum(enumSchema);
      if (enumCode) {
        sections.push(enumCode);
        sections.push('');
      }
    }
    
    // Generate types
    const interfaces = this.schemas.filter(s => s.type === 'interface');
    
    // Generate main types
    for (const intSchema of interfaces) {
      // Skip certain internal types
      if (intSchema.name.includes('Internal') || intSchema.name.includes('Config')) {
        continue;
      }
      
      const typeCode = this.generateType(intSchema);
      if (typeCode) {
        sections.push(typeCode);
        sections.push('');
      }
    }
    
    // Generate input types for mutations
    const inputCandidates = [
      'DomainNode', 'DomainArrow', 'DomainHandle', 'DomainPerson', 'DomainApiKey'
    ];
    
    for (const typeName of inputCandidates) {
      const schema = this.interfaceTypes.get(typeName);
      if (schema) {
        const inputCode = this.generateInput(schema);
        if (inputCode) {
          sections.push(inputCode);
          sections.push('');
        }
      }
    }
    
    // Add basic Query and Mutation types
    sections.push('type Query {');
    sections.push('  """Get a diagram by ID"""');
    sections.push('  diagram(id: String!): DiagramArrayFormat');
    sections.push('  ');
    sections.push('  """List all diagrams"""');
    sections.push('  diagrams: [DiagramMetadata!]!');
    sections.push('  ');
    sections.push('  """Get execution state by ID"""');
    sections.push('  execution(id: String!): ExecutionState');
    sections.push('  ');
    sections.push('  """List active executions"""');
    sections.push('  activeExecutions: [ExecutionState!]!');
    sections.push('}');
    sections.push('');
    
    sections.push('type Mutation {');
    sections.push('  """Create a new diagram"""');
    sections.push('  createDiagram(input: DiagramArrayFormatInput!): DiagramArrayFormat!');
    sections.push('  ');
    sections.push('  """Update an existing diagram"""');
    sections.push('  updateDiagram(id: String!, input: DiagramArrayFormatInput!): DiagramArrayFormat!');
    sections.push('  ');
    sections.push('  """Delete a diagram"""');
    sections.push('  deleteDiagram(id: String!): Boolean!');
    sections.push('  ');
    sections.push('  """Execute a diagram"""');
    sections.push('  executeDiagram(diagramId: String!, options: ExecutionOptionsInput): ExecutionState!');
    sections.push('  ');
    sections.push('  """Stop an execution"""');
    sections.push('  stopExecution(executionId: String!): ExecutionState!');
    sections.push('}');
    sections.push('');
    
    sections.push('type Subscription {');
    sections.push('  """Subscribe to execution updates"""');
    sections.push('  executionUpdates(executionId: String!): ExecutionUpdate!');
    sections.push('}');
    
    return sections.join('\n').trim() + '\n';
  }
}

async function generateGraphQL() {
  try {
    // Read schemas
    const schemaPath = path.join(__dirname, '..', '__generated__', 'schemas.json');
    const schemaData = await fs.readFile(schemaPath, 'utf-8');
    const schemas: SchemaDefinition[] = JSON.parse(schemaData);
    
    // Generate GraphQL schema
    const generator = new GraphQLGenerator(schemas);
    const graphqlSchema = generator.generate();
    
    // Write to server
    const outputPath = path.join(__dirname, '..', '..', '..', 'server', 'src', '__generated__', 'schema.graphql');
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, graphqlSchema);
    
    console.log(`Generated GraphQL schema: ${outputPath}`);
    
  } catch (error) {
    console.error('Error generating GraphQL schema:', error);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  generateGraphQL().catch(console.error);
}

export { generateGraphQL };