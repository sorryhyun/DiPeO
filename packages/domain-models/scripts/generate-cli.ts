#!/usr/bin/env tsx

/**
 * Generate lightweight Python dataclasses for CLI from TypeScript interfaces
 * These are simpler than the Pydantic models and don't require heavy dependencies
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { SchemaDefinition } from './generate-schema';

class CLIPythonGenerator {
  private imports: Map<string, Set<string>> = new Map();
  private generatedEnums: Set<string> = new Set();
  private generatedClasses: Set<string> = new Set();

  constructor(private schemas: SchemaDefinition[]) {}

  addImport(module: string, ...items: string[]) {
    if (!this.imports.has(module)) {
      this.imports.set(module, new Set());
    }
    const imp = this.imports.get(module)!;
    items.forEach(item => imp.add(item));
  }

  generatePythonType(tsType: string, isOptional: boolean = false): string {
    // Clean up the type string
    tsType = tsType.trim();
    
    // Remove import(...) wrapping if present
    if (tsType.startsWith('import(')) {
      const match = tsType.match(/import\([^)]+\)\.(\w+)/);
      if (match) {
        tsType = match[1];
      }
    }
    
    // Handle branded types
    if (tsType.includes('& {')) {
      tsType = 'str'; // Branded types are just strings in CLI
      return isOptional ? `Optional[${tsType}]` : tsType;
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
      
      // If it's just type | null or type | undefined, use Optional
      if (types.includes('null') || types.includes('undefined')) {
        const nonNullType = types.find(t => t !== 'null' && t !== 'undefined');
        if (nonNullType) {
          this.addImport('typing', 'Optional');
          return `Optional[${this.generatePythonType(nonNullType)}]`;
        }
      }
      
      this.addImport('typing', 'Union');
      const pythonTypes = types.map(t => this.generatePythonType(t));
      const unionType = `Union[${pythonTypes.join(', ')}]`;
      return isOptional ? `Optional[${unionType}]` : unionType;
    }

    // Handle literal types
    if (tsType.includes('"')) {
      // For CLI, just use str for literal types
      return isOptional ? 'Optional[str]' : 'str';
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
    
    lines.push(`class ${schema.name}(str, Enum):`);
    lines.push(`    """${schema.description || schema.name}"""`);
    
    for (const value of schema.values) {
      const key = value.toUpperCase().replace(/[^A-Z0-9_]/g, '_');
      lines.push(`    ${key} = "${value}"`);
    }
    
    return lines.join('\n');
  }

  generateDataclass(schema: SchemaDefinition): string {
    if (!schema.properties) return '';
    
    this.addImport('dataclasses', 'dataclass', 'field');
    this.generatedClasses.add(schema.name);

    const lines: string[] = [];
    
    lines.push('@dataclass');
    lines.push(`class ${schema.name}:`);
    
    if (schema.description) {
      lines.push(`    """${schema.description}"""`);
    }
    
    // Generate properties
    const properties = Object.entries(schema.properties);
    
    if (properties.length === 0) {
      lines.push('    pass');
    } else {
      for (const [propName, propInfo] of properties) {
        const pythonName = this.toPythonName(propName);
        const pythonType = this.generatePythonType(propInfo.type, propInfo.optional);
        
        let defaultValue = '';
        if (propInfo.optional) {
          defaultValue = ' = None';
        } else if (pythonType.includes('List[')) {
          defaultValue = ' = field(default_factory=list)';
        } else if (pythonType.includes('Dict[')) {
          defaultValue = ' = field(default_factory=dict)';
        }
        
        lines.push(`    ${pythonName}: ${pythonType}${defaultValue}`);
      }
    }
    
    return lines.join('\n');
  }

  toPythonName(name: string): string {
    // Convert camelCase to snake_case
    return name.replace(/([A-Z])/g, '_$1').toLowerCase().replace(/^_/, '');
  }

  generateImports(): string {
    const lines: string[] = [];
    
    // Sort imports by module
    const sortedImports = Array.from(this.imports.entries()).sort((a, b) => {
      // Standard library first
      const getPriority = (mod: string) => {
        if (['typing', 'enum', 'dataclasses'].includes(mod)) return 0;
        if (mod.startsWith('.')) return 2;
        return 1;
      };
      return getPriority(a[0]) - getPriority(b[0]);
    });
    
    for (const [module, items] of sortedImports) {
      const itemList = Array.from(items).sort();
      lines.push(`from ${module} import ${itemList.join(', ')}`);
    }
    
    return lines.join('\n');
  }

  generate(): string {
    const sections: string[] = [];
    
    // Add header
    sections.push('"""');
    sections.push('Auto-generated lightweight Python models for CLI');
    sections.push('DO NOT EDIT THIS FILE DIRECTLY');
    sections.push('Generated by: packages/domain-models/scripts/generate-cli.ts');
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
    
    // Generate key dataclasses for CLI
    const cliRelevantTypes = [
      'DomainNode', 'DomainArrow', 'DomainHandle', 'DomainPerson', 'DomainApiKey',
      'DiagramArrayFormat', 'DiagramMetadata', 'Vec2',
      'StartNodeData', 'PersonJobNodeData', 'ConditionNodeData', 'EndpointNodeData',
      'JobNodeData', 'DBNodeData', 'UserResponseNodeData'
    ];
    
    const interfaces = this.schemas.filter(s => 
      s.type === 'interface' && cliRelevantTypes.includes(s.name)
    );
    
    // Sort interfaces to handle dependencies
    const sortedInterfaces = this.topologicalSort(interfaces);
    
    for (const intSchema of sortedInterfaces) {
      const classCode = this.generateDataclass(intSchema);
      if (classCode) {
        sections.push(classCode);
        sections.push('');
      }
    }
    
    // Add utility functions
    sections.push('# Utility functions for CLI');
    sections.push('');
    sections.push('def create_node_id() -> str:');
    sections.push('    """Generate a new node ID"""');
    sections.push('    import uuid');
    sections.push('    return f"node_{uuid.uuid4().hex[:8]}"');
    sections.push('');
    sections.push('def create_arrow_id() -> str:');
    sections.push('    """Generate a new arrow ID"""');
    sections.push('    import uuid');
    sections.push('    return f"arrow_{uuid.uuid4().hex[:8]}"');
    sections.push('');
    sections.push('def create_handle_id(node_id: str, handle_name: str) -> str:');
    sections.push('    """Generate a handle ID from node ID and handle name"""');
    sections.push('    return f"{node_id}:{handle_name}"');
    
    // Prepend imports
    const imports = this.generateImports();
    const fullCode = imports + '\n\n' + sections.join('\n');
    
    return fullCode.trim() + '\n';
  }

  topologicalSort(interfaces: SchemaDefinition[]): SchemaDefinition[] {
    // Simple topological sort to handle interface dependencies
    const sorted: SchemaDefinition[] = [];
    const visited = new Set<string>();
    
    const visit = (schema: SchemaDefinition) => {
      if (visited.has(schema.name)) return;
      visited.add(schema.name);
      
      // Visit dependencies first
      if (schema.extends) {
        for (const ext of schema.extends) {
          const dep = interfaces.find(s => s.name === ext);
          if (dep) visit(dep);
        }
      }
      
      // Also check property types for dependencies
      if (schema.properties) {
        for (const propInfo of Object.values(schema.properties)) {
          const propType = propInfo.type;
          const dep = interfaces.find(s => s.name === propType);
          if (dep) visit(dep);
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

async function generateCLI() {
  try {
    // Read schemas
    const schemaPath = path.join(__dirname, '..', '__generated__', 'schemas.json');
    const schemaData = await fs.readFile(schemaPath, 'utf-8');
    const schemas: SchemaDefinition[] = JSON.parse(schemaData);
    
    // Generate CLI Python code
    const generator = new CLIPythonGenerator(schemas);
    const pythonCode = generator.generate();
    
    // Write to CLI package
    const outputPath = path.join(__dirname, '..', '..', '..', 'cli', 'dipeo_cli', '__generated__', 'models.py');
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, pythonCode);
    
    console.log(`Generated CLI models: ${outputPath}`);
    
    // Also generate __init__.py
    const initContent = '"""Auto-generated CLI models"""\n\nfrom .models import *\n';
    await fs.writeFile(path.join(path.dirname(outputPath), '__init__.py'), initContent);
    
  } catch (error) {
    console.error('Error generating CLI models:', error);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  generateCLI().catch(console.error);
}

export { generateCLI };