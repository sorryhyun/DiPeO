#!/usr/bin/env tsx


import { Project, InterfaceDeclaration, EnumDeclaration, Type } from 'ts-morph';
import { readdir, writeFile, mkdir } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import process from 'node:process';

//--- Types
export interface SchemaDefinition {
  name: string;
  type: 'interface' | 'enum';
  properties?: Record<string, PropertyInfo>;
  values?: string[];
  extends?: string[];
  description?: string;
}

interface PropertyInfo {
  type: string;
  optional: boolean;
  description?: string;
}

//--- Schema Extractor
class SchemaExtractor {
  private typeCache = new Map<string, string>();

  constructor(private project: Project) {}

  async extractFromFile(filePath: string): Promise<SchemaDefinition[]> {
    const src = this.project.addSourceFileAtPath(filePath);
    return [
      ...src.getInterfaces().map(i => this.extractInterface(i)).filter(Boolean),
      ...src.getEnums().map(e => this.extractEnum(e)).filter(Boolean)
    ] as SchemaDefinition[];
  }

  private extractInterface(decl: InterfaceDeclaration): SchemaDefinition | null {
    const name = decl.getName();
    const extends_ = decl.getExtends().map(e => e.getText());
    const description = this.getJsDoc(decl);

    const properties: Record<string, PropertyInfo> = {};

    for (const prop of decl.getProperties()) {
      properties[prop.getName()] = {
        type: this.getTypeText(prop.getType()),
        optional: prop.hasQuestionToken(),
        description: this.getJsDoc(prop)
      };
    }

    return { name, type: 'interface', properties, extends: extends_.length ? extends_ : undefined, description };
  }

  private extractEnum(decl: EnumDeclaration): SchemaDefinition | null {
    const name = decl.getName();
    const values = decl.getMembers().map(m => m.getValue()?.toString() ?? m.getName());
    const description = this.getJsDoc(decl);

    return { name, type: 'enum', values, description };
  }

  private getJsDoc(node: any): string | undefined {
    const docs = node.getJsDocs?.();
    return docs?.length ? docs[0].getDescription().trim() : undefined;
  }

  private getTypeText(type: Type): string {
    const text = type.getText();
    // Cache type text for repeated types
    if (!this.typeCache.has(text)) {
      this.typeCache.set(text, text);
    }
    return this.typeCache.get(text)!;
  }
}

//--- Main Generator
class SchemaGenerator {
  private project: Project;
  private extractor: SchemaExtractor;

  constructor(tsConfigPath: string) {
    this.project = new Project({ tsConfigFilePath: tsConfigPath });
    this.extractor = new SchemaExtractor(this.project);
  }

  async generate(srcDir: string, outputDir: string): Promise<void> {
    await mkdir(outputDir, { recursive: true });

    const files = await this.collectTsFiles(srcDir);
    const schemas: SchemaDefinition[] = [];

    // Batch process files
    await Promise.all(
      files.map(async file => {
        const extracted = await this.extractor.extractFromFile(file);
        schemas.push(...extracted);
      })
    );

    // Write combined schema
    await writeFile(
      join(outputDir, 'schemas.json'),
      JSON.stringify(schemas, null, 2)
    );

    // Write module schemas (simplified - just use 'diagram' for now)
    const moduleSchemas = this.groupByModule(schemas);
    await Promise.all(
      Object.entries(moduleSchemas).map(([module, moduleSchemas]) =>
        writeFile(
          join(outputDir, `${module}.schema.json`),
          JSON.stringify(moduleSchemas, null, 2)
        )
      )
    );

    console.log(`✅ Generated schemas for ${schemas.length} types`);
    console.log(`📁 Output: ${outputDir}`);
  }

  private async collectTsFiles(dir: string): Promise<string[]> {
    const entries = await readdir(dir, { recursive: true, withFileTypes: true });
    return entries
      .filter(e => e.isFile() && e.name.endsWith('.ts') && !e.name.endsWith('.test.ts'))
      .map(e => join(e.path, e.name));
  }

  private groupByModule(schemas: SchemaDefinition[]): Record<string, SchemaDefinition[]> {
    // Simplified module extraction - enhance as needed
    const modules: Record<string, SchemaDefinition[]> = {};

    for (const schema of schemas) {
      const module = 'diagram'; // Simplified
      (modules[module] ??= []).push(schema);
    }

    return modules;
  }
}

//--- Entry Point
export async function generateSchemas() {
  const __dirname = dirname(fileURLToPath(import.meta.url));
  const tsConfig = join(__dirname, '../tsconfig.json');
  const srcDir = join(__dirname, '../src');
  const outputDir = join(__dirname, '../__generated__');

  const generator = new SchemaGenerator(tsConfig);
  await generator.generate(srcDir, outputDir);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  generateSchemas().catch(err => {
    console.error('❌ Failed to generate schemas:', err);
    process.exit(1);
  });
}
