#!/usr/bin/env tsx

/**
 * Generate JSON schemas from TypeScript interfaces
 * These schemas will be used as the source for generating code in other languages
 */

import { Project, Node, InterfaceDeclaration, EnumDeclaration } from 'ts-morph';
import * as fs from 'fs/promises';
import * as path from 'path';

interface SchemaDefinition {
  name: string;
  type: 'interface' | 'enum';
  properties?: Record<string, any>;
  values?: string[];
  extends?: string[];
  description?: string;
}

async function extractTypesFromFile(filePath: string, project: Project): Promise<SchemaDefinition[]> {
  const sourceFile = project.addSourceFileAtPath(filePath);
  const schemas: SchemaDefinition[] = [];

  // Extract interfaces
  const interfaces = sourceFile.getInterfaces();
  for (const int of interfaces) {
    const schema = extractInterface(int);
    if (schema) {
      schemas.push(schema);
    }
  }

  // Extract enums
  const enums = sourceFile.getEnums();
  for (const enumDecl of enums) {
    const schema = extractEnum(enumDecl);
    if (schema) {
      schemas.push(schema);
    }
  }

  return schemas;
}

function extractInterface(int: InterfaceDeclaration): SchemaDefinition | null {
  const name = int.getName();
  const properties: Record<string, any> = {};
  
  // Get extends clauses
  const extendsTypes = int.getExtends().map(ext => ext.getText());
  
  // Get JSDoc comment
  const jsDocs = int.getJsDocs();
  const description = jsDocs.length > 0 ? jsDocs[0].getDescription().trim() : undefined;

  // Extract properties
  for (const prop of int.getProperties()) {
    const propName = prop.getName();
    const propType = prop.getType();
    const isOptional = prop.hasQuestionToken();
    const propJsDocs = prop.getJsDocs();
    const propDescription = propJsDocs.length > 0 ? propJsDocs[0].getDescription().trim() : undefined;

    properties[propName] = {
      type: getSimplifiedType(propType.getText()),
      optional: isOptional,
      description: propDescription
    };
  }

  return {
    name,
    type: 'interface',
    properties,
    extends: extendsTypes.length > 0 ? extendsTypes : undefined,
    description
  };
}

function extractEnum(enumDecl: EnumDeclaration): SchemaDefinition | null {
  const name = enumDecl.getName();
  const values = enumDecl.getMembers().map(member => member.getValue()?.toString() || member.getName());
  
  // Get JSDoc comment
  const jsDocs = enumDecl.getJsDocs();
  const description = jsDocs.length > 0 ? jsDocs[0].getDescription().trim() : undefined;

  return {
    name,
    type: 'enum',
    values,
    description
  };
}

function getSimplifiedType(typeText: string): string {
  // Keep the full type text for better generation
  return typeText;
}

async function generateSchemas() {
  const project = new Project({
    tsConfigFilePath: path.join(__dirname, '..', 'tsconfig.json')
  });

  const srcDir = path.join(__dirname, '..', 'src');
  const outputDir = path.join(__dirname, '..', '__generated__');
  
  // Ensure output directory exists
  await fs.mkdir(outputDir, { recursive: true });

  const allSchemas: SchemaDefinition[] = [];

  // Process all TypeScript files
  const files = await fs.readdir(srcDir, { recursive: true });
  for (const file of files) {
    if (typeof file === 'string' && file.endsWith('.ts') && !file.endsWith('.test.ts')) {
      const filePath = path.join(srcDir, file);
      const schemas = await extractTypesFromFile(filePath, project);
      allSchemas.push(...schemas);
    }
  }

  // Group schemas by module
  const schemasByModule: Record<string, SchemaDefinition[]> = {};
  
  // For now, we'll group by extracting module name from file path
  // This is a simplified approach - you might want to enhance this
  for (const schema of allSchemas) {
    const module = 'diagram'; // Simplified - you'd extract this from the actual file path
    if (!schemasByModule[module]) {
      schemasByModule[module] = [];
    }
    schemasByModule[module].push(schema);
  }

  // Write schemas to files
  await fs.writeFile(
    path.join(outputDir, 'schemas.json'),
    JSON.stringify(allSchemas, null, 2)
  );

  // Write module-specific schemas
  for (const [module, schemas] of Object.entries(schemasByModule)) {
    await fs.writeFile(
      path.join(outputDir, `${module}.schema.json`),
      JSON.stringify(schemas, null, 2)
    );
  }

  console.log(`Generated schemas for ${allSchemas.length} types`);
  console.log(`Output written to ${outputDir}`);
}

// Run if executed directly
if (require.main === module) {
  generateSchemas().catch(console.error);
}

export { generateSchemas, SchemaDefinition };