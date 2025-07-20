#!/usr/bin/env tsx

import { Project, InterfaceDeclaration, PropertySignature, Type } from 'ts-morph';
import { readdir, writeFile, mkdir, readFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import process from 'node:process';

//--- Types
interface FieldConfigOutput {
  name: string;
  type: string;
  label: string;
  required: boolean;
  placeholder?: string;
  defaultValue?: unknown;
  options?: Array<{ value: string; label: string }>;
  min?: number;
  max?: number;
  rows?: number;
}

interface NodeFieldConfigs {
  nodeType: string;
  fields: FieldConfigOutput[];
}

//--- Field Type Mapping
const TYPE_TO_FIELD_TYPE: Record<string, string> = {
  'string': 'text',
  'number': 'number',
  'boolean': 'checkbox',
  'PersonID': 'personSelect',
  'SupportedLanguage': 'select',
  'HttpMethod': 'select',
  'DBBlockSubType': 'select',
  'HookType': 'select',
  'ForgettingMode': 'select',
  'NotionOperation': 'select',
  'HookTriggerMode': 'select',
  'ContentType': 'select'
};

//--- Field Config Generator
class FieldConfigGenerator {
  private project: Project;
  private enumValues = new Map<string, string[]>();
  private nodeDataInterfaces = new Map<string, string>();

  constructor(tsConfigPath: string) {
    this.project = new Project({ tsConfigFilePath: tsConfigPath });
  }

  async generate(srcDir: string, outputDir: string): Promise<void> {
    await mkdir(outputDir, { recursive: true });

    // First pass: collect enums and node type mappings
    await this.collectEnumsAndMappings(srcDir);

    // Second pass: generate field configs for each node type
    const nodeConfigs: NodeFieldConfigs[] = [];
    
    for (const [nodeType, interfaceName] of this.nodeDataInterfaces) {
      const config = await this.generateNodeFieldConfig(nodeType, interfaceName);
      if (config) {
        nodeConfigs.push(config);
      }
    }

    // Write output
    const outputPath = join(outputDir, 'field-configs.json');
    await writeFile(outputPath, JSON.stringify(nodeConfigs, null, 2));

    // Generate TypeScript file with proper imports
    const tsOutput = this.generateTypeScriptOutput(nodeConfigs);
    const tsOutputPath = PATHS.webNodesFields;
    await mkdir(dirname(tsOutputPath), { recursive: true });
    await writeFile(tsOutputPath, tsOutput);

    console.log(`✅ Generated field configs for ${nodeConfigs.length} node types`);
    console.log(`📁 Output: ${outputPath}`);
    console.log(`📁 TypeScript: ${tsOutputPath}`);
  }

  private async collectEnumsAndMappings(srcDir: string): Promise<void> {
    const diagramPath = join(srcDir, 'diagram.ts');
    const sourceFile = this.project.addSourceFileAtPath(diagramPath);

    // Collect enum values
    for (const enumDecl of sourceFile.getEnums()) {
      const name = enumDecl.getName();
      const values = enumDecl.getMembers().map(m => m.getValue()?.toString() ?? m.getName());
      this.enumValues.set(name, values);
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

  private async generateNodeFieldConfig(nodeType: string, interfaceName: string): Promise<NodeFieldConfigs | null> {
    const diagramPath = join(dirname(fileURLToPath(import.meta.url)), '../src/diagram.ts');
    const sourceFile = this.project.getSourceFile(diagramPath) || this.project.addSourceFileAtPath(diagramPath);
    
    const interfaceDecl = sourceFile.getInterface(interfaceName);
    if (!interfaceDecl) {
      console.warn(`⚠️  Interface ${interfaceName} not found`);
      return null;
    }

    const fields = this.extractFields(interfaceDecl);
    
    return {
      nodeType,
      fields
    };
  }

  private extractFields(interfaceDecl: InterfaceDeclaration): FieldConfigOutput[] {
    const fields: FieldConfigOutput[] = [];
    const baseFields = ['label', 'flipped']; // Ignore base fields

    for (const prop of interfaceDecl.getProperties()) {
      const name = prop.getName();
      
      // Skip base fields
      if (baseFields.includes(name)) continue;

      const fieldConfig = this.generateFieldConfig(prop);
      if (fieldConfig) {
        fields.push(fieldConfig);
      }
    }

    return fields;
  }

  private generateFieldConfig(prop: PropertySignature): FieldConfigOutput | null {
    const name = prop.getName();
    const type = prop.getType();
    const typeText = type.getText();
    const isOptional = prop.hasQuestionToken();

    // Generate human-readable label
    const label = this.generateLabel(name);

    // Determine field type
    const fieldType = this.getFieldType(name, typeText);

    const config: FieldConfigOutput = {
      name,
      type: fieldType,
      label,
      required: !isOptional
    };

    // Add type-specific properties
    this.addTypeSpecificProperties(config, name, typeText);

    return config;
  }

  private generateLabel(name: string): string {
    // Convert snake_case to Title Case
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  private getFieldType(name: string, typeText: string): string {
    // Special handling for specific field names
    if (name.includes('prompt') || name === 'code' || name === 'expression' || name === 'query') {
      return 'variableTextArea';
    }
    
    if (name === 'max_iteration') {
      return 'maxIteration';
    }

    if (name === 'person') {
      return 'personSelect';
    }

    // Check type mapping
    const cleanType = typeText.replace(/\s*\|\s*null|\s*\|\s*undefined/g, '').trim();
    
    // Check for branded types (e.g., PersonID)
    if (cleanType.includes('PersonID')) {
      return 'personSelect';
    }
    
    if (TYPE_TO_FIELD_TYPE[cleanType]) {
      return TYPE_TO_FIELD_TYPE[cleanType];
    }

    // Handle Record types
    if (typeText.includes('Record<')) {
      return 'textarea'; // JSON editor
    }

    // Handle arrays
    if (typeText.includes('[]')) {
      return 'textarea'; // JSON array editor
    }

    // Default to text
    return 'text';
  }

  private addTypeSpecificProperties(config: FieldConfigOutput, name: string, typeText: string): void {
    // Add placeholders
    if (name.includes('prompt')) {
      config.placeholder = 'Enter prompt. Use {{variable_name}} for variables.';
      config.rows = 6;
    } else if (name === 'code') {
      config.placeholder = 'Enter code here';
      config.rows = 10;
    } else if (name === 'url') {
      config.placeholder = 'https://api.example.com/endpoint';
    } else if (name === 'timeout') {
      config.placeholder = 'Timeout in seconds';
      config.min = 0;
      config.max = 600;
    }

    // Add select options for enums
    const cleanType = typeText.replace(/\s*\|\s*null|\s*\|\s*undefined/g, '');
    if (this.enumValues.has(cleanType)) {
      const values = this.enumValues.get(cleanType)!;
      config.options = values.map(value => ({
        value,
        label: this.generateLabel(value)
      }));
    }

    // Add defaults
    if (typeText === 'number') {
      if (name === 'max_iteration') {
        config.defaultValue = 1;
        config.min = 1;
        config.max = 100;
      } else if (name === 'timeout') {
        config.defaultValue = 30;
      }
    } else if (typeText === 'boolean') {
      config.defaultValue = false;
    }
  }

  private generateTypeScriptOutput(nodeConfigs: NodeFieldConfigs[]): string {
    let output = `/**
 * GENERATED FILE - DO NOT EDIT
 * Generated by generate-field-configs.ts
 * 
 * This file contains base field configurations generated from domain models.
 * To customize fields, use the override system in each node's config file.
 */

import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export interface GeneratedFieldConfigs {
  [nodeType: string]: UnifiedFieldDefinition[];
}

export const GENERATED_FIELD_CONFIGS: GeneratedFieldConfigs = {
`;

    for (const config of nodeConfigs) {
      output += `  '${config.nodeType}': [\n`;
      
      for (const field of config.fields) {
        output += `    {\n`;
        output += `      name: '${field.name}',\n`;
        output += `      type: '${field.type}',\n`;
        output += `      label: '${field.label}',\n`;
        output += `      required: ${field.required},\n`;
        
        if (field.placeholder) {
          output += `      placeholder: '${field.placeholder}',\n`;
        }
        if (field.defaultValue !== undefined) {
          output += `      defaultValue: ${JSON.stringify(field.defaultValue)},\n`;
        }
        if (field.min !== undefined) {
          output += `      min: ${field.min},\n`;
        }
        if (field.max !== undefined) {
          output += `      max: ${field.max},\n`;
        }
        if (field.rows !== undefined) {
          output += `      rows: ${field.rows},\n`;
        }
        if (field.options) {
          output += `      options: ${JSON.stringify(field.options, null, 8).split('\n').join('\n      ')},\n`;
        }
        
        output += `    },\n`;
      }
      
      output += `  ],\n`;
    }

    output += `};\n\n`;

    // Add helper function
    output += `/**
 * Get generated field configurations for a node type
 */
export function getGeneratedFields(nodeType: string): UnifiedFieldDefinition[] {
  return GENERATED_FIELD_CONFIGS[nodeType] || [];
}\n`;

    return output;
  }
}

//--- Entry Point
export async function generateFieldConfigs() {
  const __dirname = dirname(fileURLToPath(import.meta.url));
  const tsConfig = join(__dirname, '../tsconfig.json');
  const srcDir = join(__dirname, '../src');
  const outputDir = join(__dirname, '../__generated__');

  const generator = new FieldConfigGenerator(tsConfig);
  await generator.generate(srcDir, outputDir);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  generateFieldConfigs().catch(err => {
    console.error('❌ Failed to generate field configs:', err);
    process.exit(1);
  });
}