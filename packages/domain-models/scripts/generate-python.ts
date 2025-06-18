#!/usr/bin/env tsx

/**
 * Generate Python Pydantic models from TypeScript interfaces
 * This creates the Python domain models that match our TypeScript definitions
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { SchemaDefinition } from './generate-schema';

interface PythonImport {
  from: string;
  imports: Set<string>;
}

class PythonGenerator {
  private imports: Map<string, PythonImport> = new Map();
  private generatedEnums: Set<string> = new Set();
  private generatedClasses: Set<string> = new Set();

  constructor(private schemas: SchemaDefinition[]) {}

  addImport(from: string, ...items: string[]) {
    if (!this.imports.has(from)) {
      this.imports.set(from, { from, imports: new Set() });
    }
    const imp = this.imports.get(from)!;
    items.forEach(item => imp.imports.add(item));
  }

  generatePythonType(tsType: string, isOptional: boolean = false): string {
    // Clean up the type string
    tsType = tsType.trim();
    
    // Remove import(...) wrapping if present
    if (tsType.startsWith('import(')) {
      const match = tsType.match(/import\([^)]+\)\.(.+)/);
      if (match) {
        tsType = match[1];
      }
    }
    
    // Handle branded types (e.g., "string & { readonly __brand: 'NodeID' }")
    if (tsType.includes('& {')) {
      tsType = tsType.split('&')[0].trim();
    }

    // Type mapping
    const typeMap: Record<string, string> = {
      'string': 'str',
      'number': 'float',
      'boolean': 'bool',
      'any': 'Any',
      'unknown': 'Any',
      'null': 'None',
      'undefined': 'None',
      'object': 'Dict[str, Any]',
      'array': 'List[Any]',
      'void': 'None'
    };

    // Handle array types
    if (tsType.endsWith('[]')) {
      const innerType = tsType.slice(0, -2);
      const pythonInnerType = this.generatePythonType(innerType);
      this.addImport('typing', 'List');
      return isOptional ? `Optional[List[${pythonInnerType}]]` : `List[${pythonInnerType}]`;
    }

    // Handle Record types
    if (tsType.startsWith('Record<')) {
      this.addImport('typing', 'Dict', 'Any');
      return isOptional ? 'Optional[Dict[str, Any]]' : 'Dict[str, Any]';
    }

    // Handle union types
    if (tsType.includes('|') && !tsType.includes('"')) {
      const types = tsType.split('|').map(t => t.trim());
      const pythonTypes = types.map(t => this.generatePythonType(t));
      
      // Remove duplicate None values
      const uniqueTypes = Array.from(new Set(pythonTypes));
      
      // If it's just type | null or type | undefined, use Optional
      if (uniqueTypes.length === 2 && uniqueTypes.includes('None')) {
        const nonNoneType = uniqueTypes.find(t => t !== 'None');
        this.addImport('typing', 'Optional');
        return `Optional[${nonNoneType}]`;
      }
      
      // If only None remains after deduplication, just return None
      if (uniqueTypes.length === 1 && uniqueTypes[0] === 'None') {
        return 'None';
      }
      
      this.addImport('typing', 'Union');
      const unionType = `Union[${uniqueTypes.join(', ')}]`;
      return isOptional ? `Optional[${unionType}]` : unionType;
    }

    // Handle literal types (e.g., "system" | "user" | "assistant")
    if (tsType.includes('"')) {
      this.addImport('typing', 'Literal');
      const literals = tsType.split('|')
        .map(t => t.trim())
        .filter(t => t !== 'undefined' && t !== 'null'); // Filter out undefined and null
      
      if (literals.length === 0) {
        return 'None';
      }
      
      return isOptional ? `Optional[Literal[${literals.join(', ')}]]` : `Literal[${literals.join(', ')}]`;
    }

    // Check if it's a custom type (enum or interface)
    const customType = this.schemas.find(s => s.name === tsType);
    if (customType) {
      if (isOptional) {
        this.addImport('typing', 'Optional');
        return `Optional[${tsType}]`;
      }
      return tsType;
    }

    // Map basic types
    const pythonType = typeMap[tsType] || tsType;
    
    // Handle Any type
    if (pythonType === 'Any') {
      this.addImport('typing', 'Any');
    }

    if (isOptional) {
      this.addImport('typing', 'Optional');
      return `Optional[${pythonType}]`;
    }

    return pythonType;
  }

  generateEnum(schema: SchemaDefinition): string {
    if (!schema.values) return '';
    
    this.addImport('enum', 'Enum');
    this.generatedEnums.add(schema.name);

    const lines: string[] = [];
    
    if (schema.description) {
      lines.push(`"""${schema.description}"""`);
    }
    
    lines.push(`class ${schema.name}(str, Enum):`);
    
    for (const value of schema.values) {
      const key = value.toUpperCase().replace(/[^A-Z0-9_]/g, '_');
      lines.push(`    ${key} = "${value}"`);
    }
    
    return lines.join('\n');
  }

  generateInterface(schema: SchemaDefinition): string {
    if (!schema.properties) return '';
    
    this.addImport('pydantic', 'BaseModel', 'Field', 'ConfigDict');
    this.generatedClasses.add(schema.name);

    const lines: string[] = [];
    
    if (schema.description) {
      lines.push(`"""${schema.description}"""`);
    }
    
    // Determine base class
    let baseClass = 'BaseModel';
    if (schema.extends && schema.extends.length > 0) {
      baseClass = schema.extends[0]; // For now, just use first extend
    }
    
    lines.push(`class ${schema.name}(${baseClass}):`);
    
    // Add model config for better compatibility
    lines.push(`    model_config = ConfigDict(extra='allow', populate_by_name=True)`);
    lines.push('');
    
    // Generate properties
    for (const [propName, propInfo] of Object.entries(schema.properties)) {
      const pythonName = this.toPythonName(propName);
      const pythonType = this.generatePythonType(propInfo.type, propInfo.optional);
      
      let fieldDef = '';
      const fieldArgs: string[] = [];
      
      // Add alias if Python name differs from TypeScript name
      if (pythonName !== propName) {
        fieldArgs.push(`alias="${propName}"`);
      }
      
      // Add description if available
      if (propInfo.description) {
        fieldArgs.push(`description="${propInfo.description}"`);
      }
      
      // Handle optional fields
      if (propInfo.optional) {
        fieldArgs.push('default=None');
      }
      
      if (fieldArgs.length > 0) {
        fieldDef = ` = Field(${fieldArgs.join(', ')})`;
      }
      
      lines.push(`    ${pythonName}: ${pythonType}${fieldDef}`);
    }
    
    // If no properties, add pass
    if (Object.keys(schema.properties).length === 0) {
      lines.push('    pass');
    }
    
    return lines.join('\n');
  }

  generateBrandedTypes(): string {
    const lines: string[] = [];
    
    // Generate NewType for branded types
    const brandedTypes = [
      'NodeID', 'ArrowID', 'HandleID', 'PersonID', 'ApiKeyID', 'DiagramID'
    ];
    
    this.addImport('typing', 'NewType');
    
    lines.push('# Branded types');
    for (const typeName of brandedTypes) {
      lines.push(`${typeName} = NewType('${typeName}', str)`);
    }
    
    return lines.join('\n');
  }

  toPythonName(name: string): string {
    // Convert camelCase to snake_case
    return name.replace(/([A-Z])/g, '_$1').toLowerCase().replace(/^_/, '');
  }

  generateImports(): string {
    const lines: string[] = [];
    
    // Always add __future__ import first for forward references
    lines.push('from __future__ import annotations');
    
    // Sort imports by module
    const sortedImports = Array.from(this.imports.values()).sort((a, b) => {
      // Standard library first, then third party, then local
      const getPriority = (mod: string) => {
        if (['typing', 'enum', 'datetime'].includes(mod)) return 0;
        if (mod.startsWith('.')) return 2;
        return 1;
      };
      return getPriority(a.from) - getPriority(b.from);
    });
    
    for (const imp of sortedImports) {
      const items = Array.from(imp.imports).sort();
      lines.push(`from ${imp.from} import ${items.join(', ')}`);
    }
    
    return lines.join('\n');
  }

  generate(): string {
    const sections: string[] = [];
    
    // Add header
    sections.push('"""');
    sections.push('Auto-generated Python models from TypeScript definitions');
    sections.push('DO NOT EDIT THIS FILE DIRECTLY');
    sections.push('Generated by: packages/domain-models/scripts/generate-python.ts');
    sections.push('"""');
    sections.push('');
    
    // Generate enums first
    const enums = this.schemas.filter(s => s.type === 'enum');
    for (const enumSchema of enums) {
      const enumCode = this.generateEnum(enumSchema);
      if (enumCode) {
        sections.push(enumCode);
        sections.push('');
      }
    }
    
    // Generate branded types
    sections.push(this.generateBrandedTypes());
    sections.push('');
    
    // Generate interfaces
    const interfaces = this.schemas.filter(s => s.type === 'interface');
    
    // Sort interfaces to handle dependencies
    const sortedInterfaces = this.topologicalSort(interfaces);
    
    for (const intSchema of sortedInterfaces) {
      const intCode = this.generateInterface(intSchema);
      if (intCode) {
        sections.push(intCode);
        sections.push('');
      }
    }
    
    // Prepend imports
    const imports = this.generateImports();
    const fullCode = imports + '\n\n' + sections.join('\n');
    
    return fullCode.trim() + '\n';
  }

  topologicalSort(interfaces: SchemaDefinition[]): SchemaDefinition[] {
    // Topological sort to handle interface dependencies and property type dependencies
    const sorted: SchemaDefinition[] = [];
    const visited = new Set<string>();
    
    // Extract custom type names from a type string
    const extractCustomTypes = (typeStr: string): string[] => {
      const customTypes: string[] = [];
      
      // Clean up the type string
      typeStr = typeStr.replace(/import\([^)]+\)\./g, '');
      
      // Find array types like List[CustomType]
      const arrayMatches = typeStr.matchAll(/List\[([A-Z][a-zA-Z0-9]*)\]/g);
      for (const match of arrayMatches) {
        customTypes.push(match[1]);
      }
      
      // Find optional types like Optional[CustomType]
      const optionalMatches = typeStr.matchAll(/Optional\[([A-Z][a-zA-Z0-9]*)\]/g);
      for (const match of optionalMatches) {
        customTypes.push(match[1]);
      }
      
      // Find direct custom types (start with uppercase)
      const directMatches = typeStr.match(/^[A-Z][a-zA-Z0-9]*$/);
      if (directMatches) {
        customTypes.push(directMatches[0]);
      }
      
      return customTypes;
    };
    
    const visit = (schema: SchemaDefinition) => {
      if (visited.has(schema.name)) return;
      visited.add(schema.name);
      
      // Visit parent class dependencies first
      if (schema.extends) {
        for (const ext of schema.extends) {
          const dep = interfaces.find(s => s.name === ext);
          if (dep) visit(dep);
        }
      }
      
      // Visit property type dependencies
      for (const propInfo of Object.values(schema.properties)) {
        const customTypes = extractCustomTypes(propInfo.type);
        for (const typeName of customTypes) {
          const dep = interfaces.find(s => s.name === typeName);
          if (dep && dep.name !== schema.name) {
            visit(dep);
          }
        }
      }
      
      sorted.push(schema);
    };
    
    for (const schema of interfaces) {
      visit(schema);
    }
    
    return sorted;
  }
}

async function generatePython() {
  try {
    // Read schemas
    const schemaPath = path.join(__dirname, '..', '__generated__', 'schemas.json');
    const schemaData = await fs.readFile(schemaPath, 'utf-8');
    const schemas: SchemaDefinition[] = JSON.parse(schemaData);
    
    // Generate Python code
    const generator = new PythonGenerator(schemas);
    const pythonCode = generator.generate();
    
    // Write to server
    const outputPath = path.join(__dirname, '..', '..', '..', 'server', 'src', '__generated__', 'models.py');
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, pythonCode);
    
    console.log(`Generated Python models: ${outputPath}`);
    
    // Also generate __init__.py
    const initContent = '"""Auto-generated models package"""\n\nfrom .models import *\n';
    await fs.writeFile(path.join(path.dirname(outputPath), '__init__.py'), initContent);
    
  } catch (error) {
    console.error('Error generating Python models:', error);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  generatePython().catch(console.error);
}

export { generatePython };