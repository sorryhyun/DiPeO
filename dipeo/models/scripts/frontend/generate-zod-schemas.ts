#!/usr/bin/env tsx

import { Project, InterfaceDeclaration, PropertySignature, Type } from 'ts-morph';
import { readdir, writeFile, mkdir } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import process from 'node:process';
import { PATHS } from '../paths';

//--- Types
interface ZodSchemaOutput {
  nodeType: string;
  interfaceName: string;
  schemaCode: string;
}

//--- Type to Zod mapping
const TYPE_TO_ZOD: Record<string, string> = {
  'string': 'z.string()',
  'number': 'z.number()',
  'boolean': 'z.boolean()',
  'any': 'z.any()',
  'PersonID': 'PersonID',
  'NodeID': 'NodeID',
  'HandleID': 'HandleID',
  'ArrowID': 'ArrowID',
  'SupportedLanguage': 'SupportedLanguage',
  'HttpMethod': 'HttpMethod',
  'DBBlockSubType': 'DBBlockSubType',
  'HookType': 'HookType',
  'ForgettingMode': 'ForgettingMode',
  'NotionOperation': 'NotionOperation',
  'HookTriggerMode': 'HookTriggerMode',
  'ContentType': 'ContentType',
  'NodeType': 'NodeType'
};

//--- Zod Schema Generator
class ZodSchemaGenerator {
  private project: Project;
  private nodeDataInterfaces = new Map<string, string>();
  private enumSchemas = new Map<string, string>();

  constructor(tsConfigPath: string) {
    this.project = new Project({ tsConfigFilePath: tsConfigPath });
  }

  async generate(srcDir: string): Promise<void> {
    // Collect node type mappings and enums
    await this.collectMappings(srcDir);

    // Generate schemas for each node type
    const schemas: ZodSchemaOutput[] = [];
    
    for (const [nodeType, interfaceName] of this.nodeDataInterfaces) {
      const schema = await this.generateNodeSchema(nodeType, interfaceName);
      if (schema) {
        schemas.push(schema);
      }
    }

    // Generate TypeScript file with Zod schemas
    const tsOutput = this.generateTypeScriptOutput(schemas);
    const tsOutputPath = PATHS.webNodesSchemas;
    await mkdir(dirname(tsOutputPath), { recursive: true });
    await writeFile(tsOutputPath, tsOutput);

    console.log(`✅ Generated Zod schemas for ${schemas.length} node types`);
    console.log(`📁 TypeScript: ${tsOutputPath}`);
  }

  private async collectMappings(srcDir: string): Promise<void> {
    const diagramPath = join(srcDir, 'diagram.ts');
    const sourceFile = this.project.addSourceFileAtPath(diagramPath);

    // Collect enum schemas
    for (const enumDecl of sourceFile.getEnums()) {
      const name = enumDecl.getName();
      const values = enumDecl.getMembers().map(m => m.getValue()?.toString() ?? m.getName());
      const enumSchema = `z.enum([${values.map(v => `'${v}'`).join(', ')}])`;
      this.enumSchemas.set(name, enumSchema);
    }

    // Map node types to their data interfaces
    this.nodeDataInterfaces.set('start', 'StartNodeData');
    this.nodeDataInterfaces.set('person_job', 'PersonJobNodeData');
    this.nodeDataInterfaces.set('condition', 'ConditionNodeData');
    this.nodeDataInterfaces.set('endpoint', 'EndpointNodeData');
    this.nodeDataInterfaces.set('db', 'DBNodeData');
    this.nodeDataInterfaces.set('job', 'JobNodeData');
    this.nodeDataInterfaces.set('code_job', 'CodeJobNodeData');
    this.nodeDataInterfaces.set('api_job', 'ApiJobNodeData');
    this.nodeDataInterfaces.set('user_response', 'UserResponseNodeData');
    this.nodeDataInterfaces.set('notion', 'NotionNodeData');
    this.nodeDataInterfaces.set('person_batch_job', 'PersonBatchJobNodeData');
    this.nodeDataInterfaces.set('hook', 'HookNodeData');
  }

  private async generateNodeSchema(nodeType: string, interfaceName: string): Promise<ZodSchemaOutput | null> {
    const diagramPath = join(PATHS.srcDir, 'diagram.ts');
    const sourceFile = this.project.getSourceFile(diagramPath) || this.project.addSourceFileAtPath(diagramPath);
    
    const interfaceDecl = sourceFile.getInterface(interfaceName);
    if (!interfaceDecl) {
      console.warn(`⚠️  Interface ${interfaceName} not found`);
      return null;
    }

    const schemaCode = this.generateInterfaceSchema(interfaceDecl);
    
    return {
      nodeType,
      interfaceName,
      schemaCode
    };
  }

  private generateInterfaceSchema(interfaceDecl: InterfaceDeclaration): string {
    const properties: string[] = [];
    const baseFields = ['label', 'flipped']; // Fields to skip from base interface

    for (const prop of interfaceDecl.getProperties()) {
      const name = prop.getName();
      
      // Skip base fields
      if (baseFields.includes(name)) continue;

      const zodSchema = this.generatePropertySchema(prop);
      if (zodSchema) {
        properties.push(`  ${name}: ${zodSchema}`);
      }
    }

    return `z.object({\n${properties.join(',\n')}\n})`;
  }

  private generatePropertySchema(prop: PropertySignature): string | null {
    const type = prop.getType();
    const typeText = type.getText();
    const isOptional = prop.hasQuestionToken();

    // Handle union types with null/undefined
    const cleanType = typeText.replace(/\s*\|\s*null|\s*\|\s*undefined/g, '').trim();
    
    let zodSchema = this.getZodType(cleanType);

    // Handle arrays
    if (cleanType.endsWith('[]')) {
      const elementType = cleanType.slice(0, -2);
      const elementZod = this.getZodType(elementType);
      zodSchema = `z.array(${elementZod})`;
    }
    
    // Handle Record types
    if (cleanType.startsWith('Record<')) {
      const match = cleanType.match(/Record<(.+),\s*(.+)>/);
      if (match) {
        const valueType = match[2].trim();
        const valueZod = this.getZodType(valueType);
        zodSchema = `z.record(z.string(), ${valueZod})`;
      }
    }

    // Handle optional
    if (isOptional) {
      zodSchema = `${zodSchema}.optional()`;
    }

    // Handle nullable
    if (typeText.includes('| null')) {
      zodSchema = `${zodSchema}.nullable()`;
    }

    return zodSchema;
  }

  private getZodType(typeText: string): string {
    // Check for enum schemas
    if (this.enumSchemas.has(typeText)) {
      return this.enumSchemas.get(typeText)!;
    }

    // Check for type mapping
    if (TYPE_TO_ZOD[typeText]) {
      const zodType = TYPE_TO_ZOD[typeText];
      // For branded types and enums, we'll reference them directly
      if (zodType === typeText) {
        return zodType;
      }
      return zodType;
    }

    // Default to z.any() for unknown types
    return 'z.any()';
  }

  private generateTypeScriptOutput(schemas: ZodSchemaOutput[]): string {
    let output = `/**
 * GENERATED FILE - DO NOT EDIT
 * Generated by generate-zod-schemas.ts
 * 
 * This file contains Zod validation schemas generated from domain models.
 * To customize validation, use the validation functions in each node's config file.
 */

import { z } from 'zod';
import { 
  PersonID, 
  NodeID, 
  HandleID, 
  ArrowID,
  NodeType,
  SupportedLanguage,
  HttpMethod,
  DBBlockSubType,
  HookType,
  ForgettingMode,
  NotionOperation,
  HookTriggerMode,
  ContentType
} from '@dipeo/domain-models';

// Re-export enum schemas for validation
`;

    // Add enum schemas
    for (const [enumName, schema] of this.enumSchemas) {
      if (!TYPE_TO_ZOD[enumName] || TYPE_TO_ZOD[enumName] !== enumName) {
        output += `export const ${enumName}Schema = ${schema};\n`;
      }
    }

    output += `
// Node data schemas
export const NODE_DATA_SCHEMAS = {
`;

    for (const schema of schemas) {
      output += `  '${schema.nodeType}': ${schema.schemaCode.split('\n').join('\n  ')},\n`;
    }

    output += `} as const;\n\n`;

    // Add type exports
    output += `// Type exports\n`;
    for (const schema of schemas) {
      output += `export type ${schema.interfaceName}Schema = z.infer<typeof NODE_DATA_SCHEMAS['${schema.nodeType}']>;\n`;
    }

    // Add validation helper functions
    output += `
/**
 * Get validation schema for a node type
 */
export function getNodeDataSchema(nodeType: string) {
  return NODE_DATA_SCHEMAS[nodeType as keyof typeof NODE_DATA_SCHEMAS];
}

/**
 * Validate node data using the generated schema
 */
export function validateNodeData<T = unknown>(nodeType: string, data: T): { 
  success: boolean; 
  data?: T; 
  error?: z.ZodError;
} {
  const schema = getNodeDataSchema(nodeType);
  if (!schema) {
    return { success: false, error: new z.ZodError([]) };
  }
  
  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, data: result.data as T };
  } else {
    return { success: false, error: result.error };
  }
}

/**
 * Create a field validator function that uses Zod schema
 */
export function createZodFieldValidator(nodeType: string, fieldName: string) {
  return (value: unknown, formData: unknown) => {
    const schema = getNodeDataSchema(nodeType);
    if (!schema) {
      return { isValid: true }; // No schema, assume valid
    }
    
    // Type cast to access shape property
    const schemaShape = (schema as z.ZodObject<any>).shape;
    const fieldSchema = schemaShape?.[fieldName];
    
    if (!fieldSchema) {
      return { isValid: true }; // No field schema, assume valid
    }
    
    const result = fieldSchema.safeParse(value);
    
    if (result.success) {
      return { isValid: true };
    } else {
      const error = result.error.errors[0];
      return { 
        isValid: false, 
        error: error?.message || 'Invalid value'
      };
    }
  };
}
`;

    return output;
  }
}

//--- Entry Point
export async function generateZodSchemas() {
  const tsConfig = PATHS.tsConfig;
  const srcDir = PATHS.srcDir;

  const generator = new ZodSchemaGenerator(tsConfig);
  await generator.generate(srcDir);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  generateZodSchemas().catch(err => {
    console.error('❌ Failed to generate Zod schemas:', err);
    process.exit(1);
  });
}