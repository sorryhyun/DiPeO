import * as fs from 'fs';
import * as path from 'path';
import { Project } from 'ts-morph';

const GRAPHQL_SCALAR_MAPPINGS: Record<string, string> = {
  string: 'String',
  number: 'Float',
  boolean: 'Boolean',
  Date: 'DateTime',
  DateTime: 'DateTime',
  any: 'JSONScalar',
  object: 'JSONScalar',
  'Record<string, any>': 'JSONScalar',
  'NodeID': 'NodeID',
  'DiagramID': 'DiagramID',
  'ExecutionID': 'ExecutionID',
  'PersonID': 'PersonID',
  'ApiKeyID': 'ApiKeyID',
  'HandleID': 'HandleID',
  'ArrowID': 'ArrowID',
};

interface TypeInfo {
  name: string;
  fields: Array<{
    name: string;
    type: string;
    optional: boolean;
    description?: string;
  }>;
  description?: string;
}

interface EnumInfo {
  name: string;
  values: string[];
  description?: string;
}

class GraphQLSchemaGenerator {
  private project: Project;
  private types: Map<string, TypeInfo> = new Map();
  private enums: Map<string, EnumInfo> = new Map();
  private scalars = new Set<string>(['NodeID', 'DiagramID', 'ExecutionID', 'PersonID', 'ApiKeyID', 'HandleID', 'ArrowID', 'JSONScalar']);

  constructor() {
    this.project = new Project({
      tsConfigFilePath: path.join(__dirname, '..', 'tsconfig.json'),
    });
  }

  async generate() {
    console.log('Generating GraphQL schema from TypeScript models...');
    
    // Load source files
    const sourceFiles = this.project.getSourceFiles();
    
    // Extract types and enums
    for (const sourceFile of sourceFiles) {
      this.extractTypes(sourceFile);
      this.extractEnums(sourceFile);
    }

    // Generate GraphQL schema
    const schema = this.generateSchema();
    
    // Write to file
    const outputPath = path.join(__dirname, '..', '..', '..', 'apps', 'server', 'src', 'dipeo_server', 'api', 'graphql', 'generated-schema.graphql');
    fs.writeFileSync(outputPath, schema);
    
    console.log(`GraphQL schema generated at: ${outputPath}`);
  }

  private extractTypes(sourceFile: any) {
    const fileName = sourceFile.getFilePath();
    if (!fileName.includes('/src/') || fileName.includes('.test.')) return;

    sourceFile.forEachDescendant((node: any) => {
      if (node.getKindName() === 'InterfaceDeclaration') {
        const typeInfo = this.extractInterface(node);
        if (typeInfo && this.shouldIncludeType(typeInfo.name)) {
          this.types.set(typeInfo.name, typeInfo);
        }
      }
    });
  }

  private extractInterface(node: any): TypeInfo | null {
    const name = node.getName();
    if (!name) return null;

    const fields: TypeInfo['fields'] = [];
    
    node.getProperties().forEach((prop: any) => {
      const fieldName = prop.getName();
      if (!fieldName) return;

      const typeNode = prop.getTypeNode();
      const type = typeNode ? typeNode.getText() : 'unknown';
      const optional = prop.hasQuestionToken();
      
      fields.push({
        name: fieldName,
        type,
        optional,
      });
    });

    return { name, fields };
  }

  private extractEnums(sourceFile: any) {
    sourceFile.forEachDescendant((node: any) => {
      if (node.getKindName() === 'EnumDeclaration') {
        const name = node.getName();
        if (!name) return;

        const values: string[] = [];
        node.getMembers().forEach((member: any) => {
          const memberName = member.getName();
          if (memberName) {
            values.push(memberName);
          }
        });

        if (this.shouldIncludeEnum(name)) {
          this.enums.set(name, { name, values });
        }
      }
    });
  }

  private shouldIncludeType(name: string): boolean {
    // Include domain types and important interfaces
    return name.startsWith('Domain') || 
           name.startsWith('I') || 
           ['Vec2', 'TokenUsage', 'NodeState', 'ExecutionState', 'DiagramMetadata', 'PersonLLMConfig'].includes(name);
  }

  private shouldIncludeEnum(name: string): boolean {
    // Include all enums except internal ones
    return !name.startsWith('_');
  }

  private generateSchema(): string {
    const lines: string[] = [];
    
    // Header
    lines.push('# THIS FILE WAS GENERATED - DO NOT EDIT');
    lines.push('# Generated GraphQL schema from TypeScript models');
    lines.push('# Source: dipeo/models/scripts/generate-graphql-schema.ts');
    lines.push('# Run "make codegen" to regenerate');
    lines.push('');
    
    // Scalar types
    lines.push('# Scalar Types');
    for (const scalar of this.scalars) {
      lines.push(`scalar ${scalar}`);
    }
    lines.push('scalar DateTime');
    lines.push('scalar JSONScalar');
    lines.push('');
    
    // Enums
    lines.push('# Enums');
    for (const [name, enumInfo] of this.enums) {
      lines.push(`enum ${name} {`);
      for (const value of enumInfo.values) {
        lines.push(`  ${value}`);
      }
      lines.push('}');
      lines.push('');
    }
    
    // Types
    lines.push('# Types');
    for (const [name, typeInfo] of this.types) {
      const graphqlName = this.toGraphQLTypeName(name);
      lines.push(`type ${graphqlName} {`);
      
      for (const field of typeInfo.fields) {
        const fieldType = this.toGraphQLType(field.type, field.optional);
        lines.push(`  ${field.name}: ${fieldType}`);
      }
      
      // Add computed fields for specific types
      if (name === 'DomainDiagram') {
        lines.push('  nodeCount: Int!');
        lines.push('  arrowCount: Int!');
        lines.push('  personCount: Int!');
      }
      
      lines.push('}');
      lines.push('');
    }
    
    // Input types
    lines.push('# Input Types');
    this.generateInputTypes(lines);
    
    // Mutation result types
    lines.push('# Result Types');
    this.generateResultTypes(lines);
    
    return lines.join('\n');
  }

  private toGraphQLTypeName(typeName: string): string {
    // Convert TypeScript type names to GraphQL conventions
    if (typeName.startsWith('Domain')) {
      return typeName + 'Type';
    }
    if (typeName.startsWith('I')) {
      return typeName.substring(1) + 'Type';
    }
    return typeName + 'Type';
  }

  private toGraphQLType(tsType: string, optional: boolean): string {
    // Handle arrays
    if (tsType.endsWith('[]')) {
      const elementType = tsType.slice(0, -2);
      const graphqlElementType = this.toGraphQLType(elementType, false);
      return optional ? `[${graphqlElementType}]` : `[${graphqlElementType}]!`;
    }
    
    // Handle union types (simplify for GraphQL)
    if (tsType.includes('|')) {
      const types = tsType.split('|').map(t => t.trim());
      // If it's a nullable type, handle it
      if (types.includes('null') || types.includes('undefined')) {
        const nonNullType = types.find(t => t !== 'null' && t !== 'undefined');
        return this.toGraphQLType(nonNullType || 'String', true);
      }
      // Otherwise, use the first type
      return this.toGraphQLType(types[0] || 'String', optional);
    }
    
    // Map to GraphQL types
    const mapped = GRAPHQL_SCALAR_MAPPINGS[tsType] || tsType;
    
    // Check if it's an enum
    if (this.enums.has(tsType)) {
      return optional ? tsType : `${tsType}!`;
    }
    
    // Check if it's a known type
    if (this.types.has(tsType)) {
      const typeName = this.toGraphQLTypeName(tsType);
      return optional ? typeName : `${typeName}!`;
    }
    
    // Default
    return optional ? mapped : `${mapped}!`;
  }

  private generateInputTypes(lines: string[]) {
    // Generate standard CRUD input types
    const crudEntities = ['Node', 'Diagram', 'Person', 'ApiKey'];
    
    for (const entity of crudEntities) {
      // Create input
      lines.push(`input Create${entity}Input {`);
      const typeInfo = this.types.get(`Domain${entity}`) || this.types.get(`I${entity}`);
      if (typeInfo) {
        for (const field of typeInfo.fields) {
          // Skip auto-generated fields
          if (['id', 'createdAt', 'updatedAt'].includes(field.name)) continue;
          
          const fieldType = this.toGraphQLType(field.type, true);
          lines.push(`  ${field.name}: ${fieldType}`);
        }
      }
      lines.push('}');
      lines.push('');
      
      // Update input
      lines.push(`input Update${entity}Input {`);
      lines.push(`  id: ${entity}ID!`);
      if (typeInfo) {
        for (const field of typeInfo.fields) {
          // Skip immutable fields
          if (['id', 'createdAt', 'updatedAt', 'type'].includes(field.name)) continue;
          
          const fieldType = this.toGraphQLType(field.type, true);
          lines.push(`  ${field.name}: ${fieldType}`);
        }
      }
      lines.push('}');
      lines.push('');
    }
    
    // Additional input types
    lines.push(`input Vec2Input {
  x: Float!
  y: Float!
}

input ExecuteDiagramInput {
  diagram_id: DiagramID
  diagram_data: JSONScalar
  variables: JSONScalar
  debug_mode: Boolean
  max_iterations: Int
  timeout_seconds: Int
}

input DiagramFilterInput {
  name_contains: String
  author: String
  tags: [String]
  created_after: DateTime
  created_before: DateTime
  modified_after: DateTime
}

input ExecutionFilterInput {
  diagram_id: DiagramID
  status: ExecutionStatus
  started_after: DateTime
  started_before: DateTime
  active_only: Boolean
}
`);
  }

  private generateResultTypes(lines: string[]) {
    lines.push(`type MutationResult {
  success: Boolean!
  message: String
  error: String
}
`);
    
    const resultEntities = ['Diagram', 'Node', 'Person', 'ApiKey', 'Execution'];
    
    for (const entity of resultEntities) {
      lines.push(`type ${entity}Result {
  success: Boolean!
  message: String
  error: String
  ${entity.toLowerCase()}: ${this.toGraphQLTypeName(`Domain${entity}`)}
}`);
      lines.push('');
    }
    
    lines.push(`type DeleteResult {
  success: Boolean!
  message: String
  error: String
  deleted_count: Int!
  deleted_id: String
}
`);
  }
}

// Run the generator
const generator = new GraphQLSchemaGenerator();
generator.generate().catch(console.error);