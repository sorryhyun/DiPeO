#!/usr/bin/env tsx


import { readFile, writeFile, mkdir } from 'fs/promises';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import process from 'node:process';
import { SchemaDefinition } from './generate-schema';

//--- Hoisted constants & regex patterns
const PY_TYPE_MAP: Record<string, string> = {
  string: 'str',
  number: 'float',
  boolean: 'bool',
  any: 'Any',
  unknown: 'Any',
  null: 'None',
  undefined: 'None',
  object: 'Dict[str, Any]',
  array: 'List[Any]',
  void: 'None'
} as const;

const CLI_TYPES = new Set([
  'DomainNode', 'DomainArrow', 'DomainHandle', 'DomainPerson', 'DomainApiKey',
  'DomainDiagram', 'DiagramMetadata', 'Vec2',
  'StartNodeData', 'PersonJobNodeData', 'ConditionNodeData', 'EndpointNodeData',
  'JobNodeData', 'DBNodeData', 'UserResponseNodeData'
]);

const RE_IMPORT = /import\([^)]+\)\.(\w+)/;
const RE_BRAND = /&\s*\{/;
const RE_ARRAY = /^(.+)\[\]$/;
const RE_RECORD = /^Record</;

//--- String Builder
class SB {
  private buf: string[] = [];
  add(...parts: (string | undefined | null)[]) {
    for (const p of parts) if (p) this.buf.push(p);
    return this;
  }
  nl() { this.buf.push('\n'); return this; }
  toString() { return this.buf.join(''); }
}

//--- Main Generator
class CLIPythonGenerator {
  private imports = new Map<string, Set<string>>();
  private typeCache = new Map<string, string>();
  private schemaMap = new Map<string, SchemaDefinition>();

  constructor(private schemas: SchemaDefinition[]) {
    schemas.forEach(s => this.schemaMap.set(s.name, s));
  }

  private addImport(mod: string, ...items: string[]) {
    const set = this.imports.get(mod) ?? new Set();
    items.forEach(i => set.add(i));
    this.imports.set(mod, set);
  }

  private pyType(ts: string, opt = false): string {
    const key = `${ts}|${opt}`;
    const cached = this.typeCache.get(key);
    if (cached) return cached;

    ts = ts.trim().replace(RE_IMPORT, '$1').replace(RE_BRAND, 'str');

    let result: string;

    // Array types
    const arrMatch = ts.match(RE_ARRAY);
    if (arrMatch) {
      this.addImport('typing', 'List');
      result = `List[${this.pyType(arrMatch[1])}]`;
    }
    // Record/object types
    else if (RE_RECORD.test(ts) || ts === 'object') {
      this.addImport('typing', 'Dict', 'Any');
      result = 'Dict[str, Any]';
    }
    // Union (non-literal)
    else if (ts.includes('|') && !ts.includes('"')) {
      const types = ts.split('|').map(t => t.trim());
      if (types.some(t => t === 'null' || t === 'undefined')) {
        const nonNull = types.find(t => t !== 'null' && t !== 'undefined');
        this.addImport('typing', 'Optional');
        return this.cache(key, `Optional[${this.pyType(nonNull!)}]`);
      }
      this.addImport('typing', 'Union');
      result = `Union[${types.map(t => this.pyType(t)).join(', ')}]`;
    }
    // Literal types -> str for CLI
    else if (ts.includes('"')) {
      result = 'str';
    }
    // Custom type or primitive
    else {
      result = this.schemaMap.has(ts) ? ts : (PY_TYPE_MAP[ts] ?? ts);
      if (result === 'Any') this.addImport('typing', 'Any');
    }

    // Apply optional wrapper
    if (opt) {
      this.addImport('typing', 'Optional');
      result = `Optional[${result}]`;
    }

    return this.cache(key, result);
  }

  private cache(key: string, value: string): string {
    this.typeCache.set(key, value);
    return value;
  }

  private toSnake(name: string): string {
    return name.replace(/([A-Z])/g, '_$1').toLowerCase().replace(/^_/, '');
  }

  private genEnum(s: SchemaDefinition): string {
    if (!s.values) return '';
    this.addImport('enum', 'Enum');

    const sb = new SB();
    sb.add(`class ${s.name}(str, Enum):`).nl();
    sb.add(`    """${s.description || s.name}"""`).nl();

    for (const v of s.values) {
      const key = v.toUpperCase().replace(/[^A-Z0-9_]/g, '_');
      sb.add(`    ${key} = "${v}"`).nl();
    }

    return sb.toString();
  }

  private genClass(s: SchemaDefinition): string {
    if (!s.properties) return '';
    this.addImport('dataclasses', 'dataclass', 'field');

    const sb = new SB();
    sb.add('@dataclass').nl();
    sb.add(`class ${s.name}:`).nl();

    if (s.description) sb.add(`    """${s.description}"""`).nl();

    const props = Object.entries(s.properties);
    if (!props.length) {
      sb.add('    pass').nl();
    } else {
      // Sort properties: required fields first, then optional fields
      const sortedProps = props.sort(([, a], [, b]) => {
        const aHasDefault = a.optional || a.type.includes('List[') || a.type.includes('Dict[');
        const bHasDefault = b.optional || b.type.includes('List[') || b.type.includes('Dict[');
        return Number(aHasDefault) - Number(bHasDefault);
      });

      for (const [name, info] of sortedProps) {
        const pyName = this.toSnake(name);
        const pyType = this.pyType(info.type, info.optional);

        const defaultValue = info.optional ? ' = None'
          : pyType.includes('List[') ? ' = field(default_factory=list)'
          : pyType.includes('Dict[') ? ' = field(default_factory=dict)'
          : '';

        sb.add(`    ${pyName}: ${pyType}${defaultValue}`).nl();
      }
    }

    return sb.toString();
  }

  private sortSchemas(schemas: SchemaDefinition[]): SchemaDefinition[] {
    const sorted: SchemaDefinition[] = [];
    const visited = new Set<string>();

    const visit = (s: SchemaDefinition) => {
      if (visited.has(s.name)) return;
      visited.add(s.name);

      // Visit dependencies first
      if (s.extends) {
        s.extends.forEach(ext => {
          const dep = schemas.find(x => x.name === ext);
          if (dep) visit(dep);
        });
      }

      if (s.properties) {
        Object.values(s.properties).forEach(p => {
          const dep = schemas.find(x => x.name === p.type);
          if (dep) visit(dep);
        });
      }

      sorted.push(s);
    };

    schemas.forEach(visit);
    return sorted;
  }

  generate(): string {
    const sb = new SB();

    // Header
    sb.add('"""').nl();
    sb.add('Auto-generated lightweight Python models for CLI').nl();
    sb.add('DO NOT EDIT THIS FILE DIRECTLY').nl();
    sb.add('Generated by: packages/domain-models/scripts/generate-cli.ts').nl();
    sb.add('"""').nl().nl();

    // Type aliases for branded IDs
    sb.add('# Type aliases for branded IDs').nl();
    sb.add('NodeID = str').nl();
    sb.add('ArrowID = str').nl();
    sb.add('HandleID = str').nl();
    sb.add('PersonID = str').nl();
    sb.add('ApiKeyID = str').nl();
    sb.add('DiagramID = str').nl().nl();

    // Enums
    this.schemas
      .filter(s => s.type === 'enum')
      .forEach(s => sb.add(this.genEnum(s)).nl());

    // Classes (sorted)
    const classes = this.schemas.filter(s =>
      s.type === 'interface' && CLI_TYPES.has(s.name)
    );

    this.sortSchemas(classes).forEach(s =>
      sb.add(this.genClass(s)).nl()
    );

    // Utilities
    sb.add('# Utility functions for CLI').nl().nl();
    sb.add(`def create_node_id() -> str:
    """Generate a new node ID"""
    import uuid
    return f"node_{uuid.uuid4().hex[:8]}"

def create_arrow_id() -> str:
    """Generate a new arrow ID"""
    import uuid
    return f"arrow_{uuid.uuid4().hex[:8]}"

def create_handle_id(node_id: str, handle_name: str) -> str:
    """Generate a handle ID from node ID and handle name"""
    return f"{node_id}:{handle_name}"`);

    // Prepend imports
    const imports = Array.from(this.imports.entries())
      .sort(([a], [b]) => {
        const order = (m: string) =>
          ['typing', 'enum', 'dataclasses'].includes(m) ? 0 : m.startsWith('.') ? 2 : 1;
        return order(a) - order(b);
      })
      .map(([mod, items]) => `from ${mod} import ${[...items].sort().join(', ')}`)
      .join('\n');

    return `${imports  }\n\n${  sb.toString().trim()  }\n`;
  }
}

// //--- Utility Functions Template -------------------------------------
// const UTILITY_FUNCTIONS = `def create_node_id() -> str:
//     """Generate a new node ID"""
//     import uuid
//     return f"node_{uuid.uuid4().hex[:8]}"
//
// def create_arrow_id() -> str:
//     """Generate a new arrow ID"""
//     import uuid
//     return f"arrow_{uuid.uuid4().hex[:8]}"
//
// def create_handle_id(node_id: str, handle_name: str) -> str:
//     """Generate a handle ID from node ID and handle name"""
//     return f"{node_id}:{handle_name}"`;

//--- Main Entry Point -----------------------------------------------
export async function generateCLI() {
  try {
    const __dirname = dirname(fileURLToPath(import.meta.url));
    const schemaData = await readFile(join(__dirname, '../__generated__/schemas.json'), 'utf-8');
    const schemas: SchemaDefinition[] = JSON.parse(schemaData);

    const pythonCode = new CLIPythonGenerator(schemas).generate();

    const outputPath = join(__dirname, '../../../apps/cli/src/dipeo_cli/__generated__/models.py');
    await mkdir(dirname(outputPath), { recursive: true });
    await writeFile(outputPath, pythonCode);

    const initContent = '"""Auto-generated CLI models"""\n\nfrom .models import *\n';
    await writeFile(join(dirname(outputPath), '__init__.py'), initContent);

    console.log(`✅ Generated CLI models: ${outputPath}`);
  } catch (error) {
    console.error('❌ Error generating CLI models:', error);
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  generateCLI();
}