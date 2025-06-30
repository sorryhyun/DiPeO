#!/usr/bin/env tsx

import * as fs from 'fs/promises';
import * as path from 'path';
import process from 'node:process';
import { fileURLToPath } from 'url';
import { SchemaDefinition } from './generate-schema';
import { loadSchemas } from './load-schema';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const PY_TYPE_MAP: Record<string, string> = {
  string: 'str',
  number: 'float',
  boolean: 'bool',
  any: 'Any',
  unknown: 'Any',
  null: 'None',
  undefined: 'None',
  object: 'Dict[str, Any]',
  void: 'None',
};

// Fields that should be integers instead of floats
const INTEGER_FIELDS = new Set([
  'maxIteration',
  'sequence',
  'messageCount',
  'timeout',
  'timeoutSeconds',
  'durationSeconds',
  'maxTokens',
  'statusCode',
  'totalTokens',
  'promptTokens',
  'completionTokens',
  // TokenUsage fields
  'input',
  'output',
  'cached',
  'total'
]);
const RE_BRAND   = /&\s*{.*/;                       // "… & { readonly … }"
const RE_IMPORT  = /^import\([^)]+\)\.(.+)$/;     // unwrap import()
const RE_ARRAY   = /^(.*)\[\]$/;                  // T[] syntax
const RE_GENERIC = /^Array<(.+)>$/;                 // Array<T> syntax

// Branded type IDs that need NewType
const BRANDED_IDS = [
  'NodeID',
  'ArrowID',
  'HandleID',
  'PersonID',
  'ApiKeyID',
  'DiagramID',
  'ExecutionID'
];


// Additional fields to add to certain interfaces
const ADDITIONAL_FIELDS: Record<string, Array<{name: string, type: string, optional: boolean}>> = {
  // No additional fields needed - all fields should be defined in TypeScript
};

export class PythonGenerator {
  private typeCache = new Map<string, string>();
  private schemaMap = new Map<string, SchemaDefinition>();
  private imports  = new Map<string, Set<string>>();
  private brandedTypes = new Set<string>();
  private enumNames = new Set<string>();
  
  // Configuration options
  private allowExtraFields = true;  // Set to false for stricter validation

  constructor(private schemas: SchemaDefinition[], options?: { allowExtraFields?: boolean }) {
    // Apply options
    if (options?.allowExtraFields !== undefined) {
      this.allowExtraFields = options.allowExtraFields;
    }
    
    // build custom-type lookup map
    schemas.forEach(s => {
      this.schemaMap.set(s.name, s);
      if (s.type === 'enum') {
        this.enumNames.add(s.name);
      }
    });
  }

  private addImport(from: string, ...items: string[]) {
    let set = this.imports.get(from);
    if (!set) {
      set = new Set<string>();
      this.imports.set(from, set);
    }
    items.forEach(i => set!.add(i));
  }

  private pyType(ts: string, opt = false, fieldName?: string): string {
    const key = `${ts}|${opt}|${fieldName || ''}`;
    const hit = this.typeCache.get(key);
    if (hit) return hit;

    const cache = (v: string) => (this.typeCache.set(key, v), v);
    const optional = (v: string) => {
      this.addImport('typing', 'Optional');
      return `Optional[${v}]`;
    };

    ts = ts.trim()
           .replace(RE_IMPORT, '$1')
           .replace(RE_BRAND, '')
           .trim();

    // Check for branded types
    if (BRANDED_IDS.includes(ts)) {
      this.brandedTypes.add(ts);
      this.addImport('typing', 'NewType');
      return cache(opt ? optional(ts) : ts);
    }

    // Arrays
    const arr = ts.match(RE_ARRAY);
    if (arr) {
      const inner = this.pyType(arr[1]);
      this.addImport('typing', 'List');
      const listType = `List[${inner}]`;
      return cache(opt ? optional(listType) : listType);
    }
    
    // Special case for Array<Record<...>>
    if (ts.startsWith('Array<Record<')) {
      this.addImport('typing', 'List', 'Dict', 'Any');
      const listType = 'List[Dict[str, Any]]';
      return cache(opt ? optional(listType) : listType);
    }
    const gen = ts.match(RE_GENERIC);
    if (gen) {
      const innerRaw = gen[1].trim();
      if (innerRaw.startsWith('{')) {
        this.addImport('typing', 'Dict', 'Any', 'List');
        const py = 'List[Dict[str, Any]]';
        return cache(opt ? optional(py) : py);
      }
      const inner = this.pyType(innerRaw);
      this.addImport('typing', 'List');
      const listType = `List[${inner}]`;
      return cache(opt ? optional(listType) : listType);
    }

    // Record
    if (ts.startsWith('Record<')) {
      const match = ts.match(/^Record<([^,]+),\s*(.+)>$/);
      if (match) {
        const keyType = match[1].trim();
        const valueType = match[2].trim();
        
        // Convert key type
        let pyKeyType = 'str';  // Default to str for branded types like NodeID
        if (keyType !== 'string' && !BRANDED_IDS.includes(keyType)) {
          pyKeyType = this.pyType(keyType);
        }
        
        // Convert value type
        const pyValueType = this.pyType(valueType);
        
        this.addImport('typing', 'Dict');
        const py = `Dict[${pyKeyType}, ${pyValueType}]`;
        return cache(opt ? optional(py) : py);
      }
      // Fallback for malformed Record types
      this.addImport('typing', 'Dict', 'Any');
      const py = 'Dict[str, Any]';
      return cache(opt ? optional(py) : py);
    }

    // Check if this is a literal union type (all values are quoted strings)
    // e.g., "foo" | "bar" or 'foo' | 'bar'
    // First check if the entire string contains | within quotes
    if (ts.includes('|') && (ts.includes('"') || ts.includes("'"))) {
      // Check if all parts are quoted strings
      const parts = ts.split('|').map(p => p.trim());
      const allQuoted = parts.every(part => 
        (part.startsWith('"') && part.endsWith('"')) || 
        (part.startsWith("'") && part.endsWith("'"))
      );
      
      if (allQuoted) {
        this.addImport('typing', 'Literal');
        // Join the parts as-is (they already have quotes)
        const py = `Literal[${parts.join(', ')}]`;
        return cache(opt ? optional(py) : py);
      }
    }

    // Single literal string (e.g., 'person', "value")
    if ((ts.startsWith("'") && ts.endsWith("'")) || (ts.startsWith('"') && ts.endsWith('"'))) {
      this.addImport('typing', 'Literal');
      const py = `Literal[${ts}]`;
      return cache(opt ? optional(py) : py);
    }

    // Union types (including mixed literal/non-literal)
    if (ts.includes('|')) {
      const branches = ts.split('|').map(x => x.trim());
      
      // Separate literal values from other types
      const literals: string[] = [];
      const nonLiterals: string[] = [];
      
      for (const branch of branches) {
        if (branch.includes('"') || branch.includes("'")) {
          // It's a literal string
          literals.push(branch);
        } else if (!['undefined', 'null'].includes(branch)) {
          // It's a non-literal type
          nonLiterals.push(branch);
        }
      }
      
      // Process non-literal types
      const processedNonLiterals = nonLiterals.map(x => this.pyType(x));
      
      // Build the final type
      const types: string[] = [];
      
      // Add literal type if we have any literals
      if (literals.length > 0) {
        this.addImport('typing', 'Literal');
        // If we only have literals and no other types, create a single Literal type
        if (nonLiterals.length === 0) {
          return cache(opt ? optional(`Literal[${literals.join(', ')}]`) : `Literal[${literals.join(', ')}]`);
        }
        types.push(`Literal[${literals.join(', ')}]`);
      }
      
      // Add non-literal types
      types.push(...processedNonLiterals);
      
      // Handle special cases
      const uniqTypes = [...new Set(types)];
      
      // Optional alias (T | None => Optional[T])
      if (uniqTypes.length === 2 && uniqTypes.includes('None')) {
        const base = uniqTypes.find(x => x !== 'None')!;
        return cache(optional(base));
      }
      
      // Single type after processing
      if (uniqTypes.length === 1) {
        return cache(opt ? optional(uniqTypes[0]) : uniqTypes[0]);
      }
      
      // Multiple types => Union
      this.addImport('typing', 'Union');
      const py = `Union[${uniqTypes.join(', ')}]`;
      return cache(opt ? optional(py) : py);
    }

    // Custom schema
    if (this.schemaMap.has(ts)) {
      return cache(opt ? optional(ts) : ts);
    }

    // Primitive / fallback
    let mapped = PY_TYPE_MAP[ts] ?? ts;
    
    // Special handling for number type - check if it should be int
    if (ts === 'number' && fieldName && INTEGER_FIELDS.has(fieldName)) {
      mapped = 'int';
    }
    
    if (mapped === 'Any') this.addImport('typing', 'Any');
    return cache(opt ? optional(mapped) : mapped);
  }

  private convertPropNameToSnakeCase(name: string): string {
    // Special case for fields starting with underscore
    if (name.startsWith('_')) {
      return name;
    }
    // Convert camelCase to snake_case
    return name.replace(/([A-Z])/g, '_$1').toLowerCase().replace(/^_/, '');
  }

  private generateClass(schema: SchemaDefinition): string[] {
    const lines: string[] = [];
    
    if (schema.type === 'enum') {
      // Generate enum class
      this.addImport('enum', 'Enum');
      lines.push(`class ${schema.name}(str, Enum):`);
      if (schema.values && schema.values.length > 0) {
        schema.values.forEach(value => {
          // Use the value as-is for the attribute name to match GraphQL expectations
          const enumKey = value.replace(/-/g, '_');
          lines.push(`    ${enumKey} = "${value}"`);
        });
      } else {
        lines.push('    pass');
      }
    } else {
      // Generate Pydantic model
      // Check if this class extends another class
      let baseClass = 'BaseModel';
      if (schema.extends && schema.extends.length > 0) {
        baseClass = schema.extends[0]; // Take the first parent class
      }
      
      lines.push(`class ${schema.name}(${baseClass}):`);
      const extraConfig = this.allowExtraFields ? 'allow' : 'forbid';
      lines.push(`    model_config = ConfigDict(extra='${extraConfig}', populate_by_name=True)`);
      lines.push('');
      
      const allProperties = { ...schema.properties };
      
      // Add any additional fields for this interface
      const additionalFields = ADDITIONAL_FIELDS[schema.name];
      if (additionalFields) {
        for (const field of additionalFields) {
          allProperties[field.name] = {
            type: field.type,
            optional: field.optional
          };
        }
      }
      
      if (!allProperties || Object.keys(allProperties).length === 0) {
        lines.push('    pass');
      } else {
        for (const [propName, propInfo] of Object.entries(allProperties)) {
          const pyT = this.pyType(propInfo.type, propInfo.optional, propName);
          const snakeName = this.convertPropNameToSnakeCase(propName);
          
          // Check if we need Field with alias
          if (snakeName !== propName) {
            this.addImport('pydantic', 'Field');
            if (propInfo.optional) {
              lines.push(`    ${snakeName}: ${pyT} = Field(alias="${propName}", default=None)`);
            } else {
              lines.push(`    ${snakeName}: ${pyT} = Field(alias="${propName}")`);
            }
          } else {
            if (propInfo.optional) {
              lines.push(`    ${propName}: ${pyT} = Field(default=None)`);
            } else {
              lines.push(`    ${propName}: ${pyT}`);
            }
          }
        }
      }
    }
    
    return lines;
  }

  public async generateConsolidated(outputPath: string): Promise<void> {
    // Reset state
    this.imports.clear();
    this.typeCache.clear();
    this.brandedTypes.clear();

    // Add base imports
    this.addImport('__future__', 'annotations');
    this.addImport('enum', 'Enum');
    this.addImport('pydantic', 'BaseModel', 'ConfigDict', 'Field');

    const lines: string[] = [];
    
    // Process all schemas to collect imports
    for (const schema of this.schemas) {
      if (schema.type === 'interface') {
        // Pre-process to collect all imports
        if (schema.properties) {
          for (const [_, propInfo] of Object.entries(schema.properties)) {
            this.pyType(propInfo.type, propInfo.optional);
          }
        }
      }
    }

    // Generate header
    const importLines: string[] = [];
    
    // Sort imports by module
    const sortedImports = [...this.imports.entries()].sort(([a], [b]) => {
      // __future__ always first
      if (a === '__future__') return -1;
      if (b === '__future__') return 1;
      // Then standard library
      const stdLibs = ['enum', 'typing'];
      const aIsStd = stdLibs.includes(a);
      const bIsStd = stdLibs.includes(b);
      if (aIsStd && !bIsStd) return -1;
      if (!aIsStd && bIsStd) return 1;
      // Then alphabetical
      return a.localeCompare(b);
    });

    for (const [from, items] of sortedImports) {
      const sortedItems = [...items].sort();
      importLines.push(`from ${from} import ${sortedItems.join(', ')}`);
    }

    lines.push(...importLines);
    lines.push('');
    lines.push('"""');
    lines.push('Auto-generated Python models from TypeScript definitions');
    lines.push('DO NOT EDIT THIS FILE DIRECTLY');
    lines.push('Generated by: packages/domain-models/scripts/generate-python.ts');
    lines.push('');
    lines.push(`Configuration: extra fields are ${this.allowExtraFields ? 'allowed' : 'forbidden'}`);
    lines.push('To change validation strictness, modify the options in generate-python.ts');
    lines.push('"""');
    lines.push('');

    // Generate enums first
    const enums = this.schemas.filter(s => s.type === 'enum');
    for (const enumSchema of enums) {
      lines.push(...this.generateClass(enumSchema));
      lines.push('');
    }

    // Generate additional enums not in TypeScript
    // Currently no additional enums needed - ADDITIONAL_ENUMS is empty

    // Generate branded types
    if (this.brandedTypes.size > 0) {
      lines.push('# Branded types');
      for (const brandedType of BRANDED_IDS) {
        if (this.brandedTypes.has(brandedType)) {
          lines.push(`${brandedType} = NewType('${brandedType}', str)`);
        }
      }
      lines.push('');
    }

    // Generate interfaces
    const interfaces = this.schemas.filter(s => s.type === 'interface');
    for (const interfaceSchema of interfaces) {
      lines.push(...this.generateClass(interfaceSchema));
      lines.push('');
    }

    // Generate type aliases
    const typeAliases = this.schemas.filter(s => s.type === 'type-alias');
    for (const aliasSchema of typeAliases) {
      if (aliasSchema.aliasType) {
        // Extract the actual type name from import syntax
        const match = aliasSchema.aliasType.match(/\.([A-Za-z]+)$/);
        if (match) {
          const targetType = match[1];
          // Only generate if the target type exists
          if (interfaces.some(i => i.name === targetType) || enums.some(e => e.name === targetType)) {
            lines.push(`# Type alias from TypeScript`);
            lines.push(`${aliasSchema.name} = ${targetType}`);
            lines.push('');
          }
        }
      }
    }


    // Write to file
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, lines.join('\n'));
  }
}

//--- CLI Guard
if (import.meta.url === `file://${process.argv[1]}`) {
  (async () => {
    const schemas = await loadSchemas(path.resolve(__dirname, '../__generated__'));
    
    // Configuration options can be set here
    const options = {
      allowExtraFields: true  // Set to false for stricter validation (forbid unknown fields)
    };
    
    const gen = new PythonGenerator(schemas, options);
    const outputPath = path.resolve(process.cwd(), '../python/dipeo_domain/src/dipeo_domain/models.py');
    await gen.generateConsolidated(outputPath);
    console.log(`Generated consolidated models.py at ${outputPath}`);
  })();
}