import * as ts from 'typescript';
import * as fs from 'fs';
import * as path from 'path';
import { Project } from 'ts-morph';

interface TypeMapping {
  domainType: string;
  graphqlType: string;
  fields: Array<{
    name: string;
    domainType: string;
    graphqlType: string;
    isEnum?: boolean;
    isArray?: boolean;
    isOptional?: boolean;
  }>;
}

class FrontendMappingsGenerator {
  private project: Project;
  private typeMappings: TypeMapping[] = [];
  private enumMappings = new Map<string, string[]>();
  
  constructor() {
    this.project = new Project({
      tsConfigFilePath: path.join(__dirname, '..', 'tsconfig.json'),
    });
  }

  async generate() {
    console.log('Generating frontend type mappings from TypeScript models...');
    
    // Analyze TypeScript models
    this.analyzeModels();
    
    // Generate mapping functions
    const mappingCode = this.generateMappingCode();
    
    // Write to file
    const outputPath = path.join(
      __dirname, '..', '..', '..',
      'apps', 'web', 'src', 'lib', 'graphql', 'types',
      'generated-mappings.ts'
    );
    
    fs.writeFileSync(outputPath, mappingCode);
    console.log(`Frontend type mappings generated at: ${outputPath}`);
  }
  
  private analyzeModels() {
    const sourceFiles = this.project.getSourceFiles();
    
    // Define mappings between domain types and GraphQL types
    const typeMap = [
      { domain: 'DomainDiagram', graphql: 'Diagram' },
      { domain: 'DomainNode', graphql: 'Node' },
      { domain: 'DomainArrow', graphql: 'Arrow' },
      { domain: 'DomainHandle', graphql: 'Handle' },
      { domain: 'DomainPerson', graphql: 'Person' },
      { domain: 'DomainApiKey', graphql: 'ApiKey' },
      { domain: 'Execution', graphql: 'Execution' },
      { domain: 'NodeState', graphql: 'NodeState' },
      { domain: 'Vec2', graphql: 'Vec2' },
      { domain: 'DiagramMetadata', graphql: 'DiagramMetadata' },
      { domain: 'PersonLLMConfig', graphql: 'PersonLlmConfig' },
    ];
    
    for (const { domain, graphql } of typeMap) {
      const domainInterface = this.findInterface(sourceFiles, domain);
      if (domainInterface) {
        const mapping = this.createTypeMapping(domainInterface, domain, graphql);
        if (mapping) {
          this.typeMappings.push(mapping);
        }
      }
    }
    
    // Extract enums using ts-morph API
    for (const sourceFile of sourceFiles) {
      for (const enumDeclaration of sourceFile.getEnums()) {
        const name = enumDeclaration.getName();
        if (name) {
          const values: string[] = [];
          for (const member of enumDeclaration.getMembers()) {
            values.push(member.getName());
          }
          this.enumMappings.set(name, values);
        }
      }
    }
  }
  
  private findInterface(sourceFiles: any[], name: string): any | null {
    for (const sourceFile of sourceFiles) {
      const interfaceDeclaration = sourceFile.getInterface(name);
      if (interfaceDeclaration) {
        return interfaceDeclaration;
      }
    }
    return null;
  }
  
  private createTypeMapping(
    interfaceNode: any,
    domainType: string,
    graphqlType: string
  ): TypeMapping | null {
    const fields: TypeMapping['fields'] = [];
    
    // Use ts-morph API to get properties
    for (const property of interfaceNode.getProperties()) {
      const fieldName = property.getName();
      if (!fieldName) continue;
      
      const typeNode = property.getTypeNode();
      const type = typeNode ? this.getTypeStringFromNode(typeNode) : 'unknown';
      const isOptional = property.hasQuestionToken();
      const isArray = type.endsWith('[]');
      const isEnum = this.enumMappings.has(type.replace('[]', ''));
      
      fields.push({
        name: fieldName,
        domainType: type,
        graphqlType: this.mapToGraphQLType(type),
        isEnum,
        isArray,
        isOptional,
      });
    }
    
    return { domainType, graphqlType, fields };
  }
  
  private getTypeStringFromNode(typeNode: any): string {
    const text = typeNode.getText();
    
    // Handle array types
    if (text.endsWith('[]')) {
      return text;
    }
    
    // Handle Array<T> syntax
    const arrayMatch = text.match(/^Array<(.+)>$/);
    if (arrayMatch) {
      return `${arrayMatch[1]}[]`;
    }
    
    // Handle union types
    if (text.includes(' | ')) {
      return text;
    }
    
    return text;
  }
  
  private mapToGraphQLType(domainType: string): string {
    // Handle arrays
    if (domainType.endsWith('[]')) {
      const elementType = domainType.slice(0, -2);
      return `${this.mapToGraphQLType(elementType)}[]`;
    }
    
    // Handle branded types
    const brandedTypes: Record<string, string> = {
      'NodeID': 'string',
      'DiagramID': 'string',
      'ExecutionID': 'string',
      'PersonID': 'string',
      'ApiKeyID': 'string',
      'HandleID': 'string',
      'ArrowID': 'string',
    };
    
    if (brandedTypes[domainType]) {
      return brandedTypes[domainType];
    }
    
    // Handle domain types
    const domainToGraphQL: Record<string, string> = {
      'DomainNode': 'Node',
      'DomainArrow': 'Arrow',
      'DomainHandle': 'Handle',
      'DomainPerson': 'Person',
      'DomainApiKey': 'ApiKey',
      'PersonLLMConfig': 'PersonLlmConfig',
    };
    
    return domainToGraphQL[domainType] || domainType;
  }
  
  private generateMappingCode(): string {
    const lines: string[] = [];
    
    // Header
    lines.push('/**');
    lines.push(' * THIS FILE WAS GENERATED - DO NOT EDIT');
    lines.push(' * Generated GraphQL to Domain type mappings');
    lines.push(' * Source: dipeo/models/scripts/generate-frontend-mappings.ts');
    lines.push(' * Run "make codegen" to regenerate');
    lines.push(' */');
    lines.push('');
    
    // Imports
    lines.push("import type { TypedDocumentNode } from '@apollo/client';");
    lines.push("import type * as Domain from '@dipeo/domain-models';");
    lines.push("import type * as GraphQL from '@/__generated__/graphql';");
    lines.push('');
    
    // Enum mappings
    lines.push('// Enum Mappings');
    this.generateEnumMappings(lines);
    lines.push('');
    
    // Type conversion functions
    lines.push('// Type Conversion Functions');
    
    for (const mapping of this.typeMappings) {
      this.generateConversionFunction(lines, mapping);
    }
    
    // Helper functions
    lines.push('// Helper Functions');
    this.generateHelperFunctions(lines);
    
    // Export all functions
    lines.push('// Exports');
    lines.push('export {');
    for (const mapping of this.typeMappings) {
      lines.push(`  convertGraphQL${mapping.graphqlType}ToDomain,`);
      lines.push(`  convertDomain${mapping.domainType}ToGraphQL,`);
    }
    lines.push('  // Enum mappings');
    for (const [enumName] of Array.from(this.enumMappings)) {
      lines.push(`  graphQL${enumName}ToDomain,`);
      lines.push(`  domain${enumName}ToGraphQL,`);
    }
    lines.push('  // Helper functions');
    lines.push('  convertNullable,');
    lines.push('  convertArray,');
    lines.push('};');
    
    return lines.join('\n');
  }
  
  private generateEnumMappings(lines: string[]) {
    for (const [enumName] of Array.from(this.enumMappings)) {
      // GraphQL to Domain
      lines.push(`export function graphQL${enumName}ToDomain(value: GraphQL.${enumName}): Domain.${enumName} {`);
      lines.push(`  return value as Domain.${enumName};`);
      lines.push('}');
      lines.push('');
      
      // Domain to GraphQL
      lines.push(`export function domain${enumName}ToGraphQL(value: Domain.${enumName}): GraphQL.${enumName} {`);
      lines.push(`  return value as GraphQL.${enumName};`);
      lines.push('}');
      lines.push('');
    }
  }
  
  private generateConversionFunction(lines: string[], mapping: TypeMapping) {
    // GraphQL to Domain conversion
    lines.push(`export function convertGraphQL${mapping.graphqlType}ToDomain(`);
    lines.push(`  graphql: GraphQL.${mapping.graphqlType}`);
    lines.push(`): Domain.${mapping.domainType} {`);
    lines.push('  return {');
    
    for (const field of mapping.fields) {
      const conversion = this.getFieldConversion(field, 'graphql', 'toDomain');
      lines.push(`    ${field.name}: ${conversion},`);
    }
    
    lines.push('  };');
    lines.push('}');
    lines.push('');
    
    // Domain to GraphQL conversion
    lines.push(`export function convertDomain${mapping.domainType}ToGraphQL(`);
    lines.push(`  domain: Domain.${mapping.domainType}`);
    lines.push(`): Partial<GraphQL.${mapping.graphqlType}> {`);
    lines.push('  return {');
    
    for (const field of mapping.fields) {
      const conversion = this.getFieldConversion(field, 'domain', 'toGraphQL');
      lines.push(`    ${field.name}: ${conversion},`);
    }
    
    lines.push('  };');
    lines.push('}');
    lines.push('');
  }
  
  private getFieldConversion(
    field: TypeMapping['fields'][0],
    sourceVar: string,
    direction: 'toDomain' | 'toGraphQL'
  ): string {
    const fieldAccess = `${sourceVar}.${field.name}`;
    
    // Handle optional fields
    if (field.isOptional) {
      const conversion = this.getRequiredFieldConversion(field, fieldAccess, direction);
      return `${fieldAccess} != null ? ${conversion} : undefined`;
    }
    
    return this.getRequiredFieldConversion(field, fieldAccess, direction);
  }
  
  private getRequiredFieldConversion(
    field: TypeMapping['fields'][0],
    fieldAccess: string,
    direction: 'toDomain' | 'toGraphQL'
  ): string {
    // Handle arrays
    if (field.isArray) {
      const elementType = field.domainType.replace('[]', '');
      const isComplexType = this.isComplexType(elementType);
      
      if (isComplexType) {
        const conversionFunc = direction === 'toDomain' 
          ? `convertGraphQL${this.mapToGraphQLType(elementType)}ToDomain`
          : `convertDomain${elementType}ToGraphQL`;
        return `${fieldAccess}.map(item => ${conversionFunc}(item))`;
      }
      
      if (field.isEnum) {
        const enumFunc = direction === 'toDomain'
          ? `graphQL${elementType}ToDomain`
          : `domain${elementType}ToGraphQL`;
        return `${fieldAccess}.map(item => ${enumFunc}(item))`;
      }
      
      return fieldAccess;
    }
    
    // Handle enums
    if (field.isEnum) {
      const enumType = field.domainType;
      const enumFunc = direction === 'toDomain'
        ? `graphQL${enumType}ToDomain`
        : `domain${enumType}ToGraphQL`;
      return `${enumFunc}(${fieldAccess})`;
    }
    
    // Handle complex types
    if (this.isComplexType(field.domainType)) {
      const conversionFunc = direction === 'toDomain'
        ? `convertGraphQL${this.mapToGraphQLType(field.domainType)}ToDomain`
        : `convertDomain${field.domainType}ToGraphQL`;
      return `${conversionFunc}(${fieldAccess})`;
    }
    
    // Handle branded types
    if (this.isBrandedType(field.domainType)) {
      if (direction === 'toDomain') {
        return `${fieldAccess} as Domain.${field.domainType}`;
      } else {
        return `String(${fieldAccess})`;
      }
    }
    
    // Simple types pass through
    return fieldAccess;
  }
  
  private isComplexType(type: string): boolean {
    return this.typeMappings.some(m => m.domainType === type);
  }
  
  private isBrandedType(type: string): boolean {
    return ['NodeID', 'DiagramID', 'ExecutionID', 'PersonID', 'ApiKeyID', 'HandleID', 'ArrowID'].includes(type);
  }
  
  private generateHelperFunctions(lines: string[]) {
    // Nullable converter
    lines.push('export function convertNullable<T, R>(');
    lines.push('  value: T | null | undefined,');
    lines.push('  converter: (v: T) => R');
    lines.push('): R | null | undefined {');
    lines.push('  return value != null ? converter(value) : value as null | undefined;');
    lines.push('}');
    lines.push('');
    
    // Array converter
    lines.push('export function convertArray<T, R>(');
    lines.push('  array: T[],');
    lines.push('  converter: (item: T) => R');
    lines.push('): R[] {');
    lines.push('  return array.map(converter);');
    lines.push('}');
    lines.push('');
  }
}

// Run the generator
const generator = new FrontendMappingsGenerator();
generator.generate().catch(console.error);