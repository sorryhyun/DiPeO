#!/usr/bin/env tsx


import { readFile, writeFile } from 'fs/promises';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';
import process from 'node:process';
import { SchemaDefinition } from './generate-schema';

const TYPE_MAP: Record<string, string> = {
  string: 'String',
  number: 'Float',
  float: 'Float',
  boolean: 'Boolean',
  any: 'JSON',
  unknown: 'JSON',
  null: 'null',
  undefined: 'null',
  void: 'null',
} as const;

const IMPORT_RE = /import\([^)]+\)\.(\w+)/;
const BRAND_RE = /&\s*\{/;
const UNION_RE = /\|/;

/** Minimal string builder to reduce memory churn */
class SB {
  private buf: string[] = [];
  push(...parts: (string | undefined | null)[]) {
    for (const p of parts) if (p) this.buf.push(p);
  }
  toString() { return this.buf.join(''); }
}

class GraphQLGenerator {
  private cache = new Map<string, string>();

  constructor(private schemas: SchemaDefinition[]) {}

  private type(ts: string, nonNull = true): string {
    const key = ts + (nonNull ? '!' : '');
    if (this.cache.has(key)) return this.cache.get(key)!;

    let clean = ts.trim();
    if (clean.startsWith('import(')) clean = clean.replace(IMPORT_RE, '$1');
    if (BRAND_RE.test(clean)) clean = 'string';
    
    // Handle string literal types (e.g., 'person' -> String)
    if (clean.startsWith('"') || clean.startsWith("'")) {
      clean = 'string';
    }

    const result =
      clean.endsWith('[]')
        ? `[${this.type(clean.slice(0, -2))}]${nonNull ? '!' : ''}`
      : clean.startsWith('Record<') || clean === 'object'
        ? `JSON${nonNull ? '!' : ''}`
      : UNION_RE.test(clean)
        ? (() => {
            // Handle union types
            const types = clean.split('|').map(t => t.trim());
            const hasNull = types.includes('null') || types.includes('undefined');
            const nonNullTypes = types.filter(t => t !== 'null' && t !== 'undefined');
            
            // Check if all non-null types are string literals
            const allStringLiterals = nonNullTypes.every(t => 
              t.startsWith('"') || t.startsWith("'")
            );
            
            if (allStringLiterals) {
              return `String${!hasNull && nonNull ? '!' : ''}`;
            }
            
            if (nonNullTypes.length === 1) {
              return this.type(nonNullTypes[0], !hasNull && nonNull);
            }
            // For multiple non-null types, just use the first one for GraphQL
            return this.type(nonNullTypes[0], !hasNull && nonNull);
          })()
        : (TYPE_MAP[clean as keyof typeof TYPE_MAP] ?? clean) + (nonNull ? '!' : '');

    this.cache.set(key, result);
    return result;
  }

  private fieldName(name: string) {
    return name.replace(/([A-Z])/g, '_$1').toLowerCase();
  }

  private genType(s: SchemaDefinition): string {
    if (!s.properties) return '';

    const sb = new SB();
    if (s.description) sb.push(`"""${s.description}"""\n`);
    sb.push(`type ${s.name} {\n`);
    for (const [k, v] of Object.entries(s.properties)) {
      if (v.description) sb.push(`  """${v.description}"""\n`);
      sb.push(`  ${this.fieldName(k)}: ${this.type(v.type, !v.optional)}\n`);
    }
    sb.push('}\n\n');
    return sb.toString();
  }

  private genEnum(s: SchemaDefinition): string {
    const sb = new SB();
    if (s.description) sb.push(`"""${s.description}"""\n`);
    sb.push(`enum ${s.name} {\n`);
    for (const v of s.values ?? []) sb.push(`  ${v}\n`);
    sb.push('}\n\n');
    return sb.toString();
  }

  generate(): string {
    const sb = new SB();
    
    // Add GraphQL schema header comment
    sb.push('# Generated GraphQL schema from TypeScript domain models\n');
    sb.push('# This file is auto-generated - DO NOT EDIT\n\n');
    
    // Generate enums (skip descriptions that look like file-level comments)
    for (const s of this.schemas.filter(x => x.type === 'enum')) {
      // Skip file-level descriptions that were incorrectly attached to enums
      if (s.description?.includes('source of truth')) {
        const enumWithoutDesc = { ...s, description: undefined };
        sb.push(this.genEnum(enumWithoutDesc));
      } else {
        sb.push(this.genEnum(s));
      }
    }
    
    // Generate types
    for (const s of this.schemas.filter(x => x.type === 'interface')) sb.push(this.genType(s));
    
    // Add root types
    sb.push(ROOT_TYPES);
    return sb.toString();
  }
}

const ROOT_TYPES = /* GraphQL */`
# Custom Scalar Types
scalar JSON
scalar NodeID
scalar DiagramID
scalar ExecutionID
scalar PersonID
scalar ApiKeyID
scalar HandleID
scalar ArrowID
scalar DateTime

# Basic Input Types
input DomainDiagramInput {
  nodes: [JSON!]!
  handles: [JSON!]!
  arrows: [JSON!]!
  persons: [JSON!]!
  apiKeys: [JSON!]!
  metadata: JSON
}

input ExecutionOptionsInput {
  mode: String
  timeout: Float
  variables: JSON
  debug: Boolean
}

# Root Query Type (to be extended by server)
type Query {
  """Get a diagram by ID"""
  diagram(id: String!): DomainDiagram
  """List all diagrams"""
  diagrams: [DiagramMetadata!]!
  """Get execution state by ID"""
  execution(id: String!): ExecutionState
}

# Root Mutation Type (to be extended by server)
type Mutation {
  """Create a diagram"""
  createDiagram(input: DomainDiagramInput!): DomainDiagram!
  """Update an existing diagram"""
  updateDiagram(id: String!, input: DomainDiagramInput!): DomainDiagram!
  """Delete a diagram"""
  deleteDiagram(id: String!): Boolean!
  """Execute a diagram"""
  executeDiagram(diagramId: String!, options: ExecutionOptionsInput): ExecutionState!
  """Stop an execution"""
  stopExecution(executionId: String!): ExecutionState!
}

# Root Subscription Type (to be extended by server)
type Subscription {
  """Real-time execution updates"""
  executionUpdates(executionId: ID!): ExecutionState!
}
`;

export async function generateGraphQL() {
  try {
    const __dirname = dirname(fileURLToPath(import.meta.url));
    const schema = JSON.parse(await readFile(resolve(__dirname, '../__generated__/schemas.json'), 'utf8')) as SchemaDefinition[];
    const sdl = new GraphQLGenerator(schema).generate();
    const output = resolve(__dirname, '../schema.graphql');
    await writeFile(output, sdl);
    console.log('✅  GraphQL schema generated at', output);
  } catch (err) {
    console.error('❌  Failed to generate schema:', err);
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  generateGraphQL();
}