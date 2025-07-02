#!/usr/bin/env tsx
import fs from 'fs/promises';
import path from 'path';
import process from 'node:process';
import { fileURLToPath } from 'url';
import { SchemaDefinition } from './generate-schema';
import { loadSchemas } from './load-schema';

const __dirname = path.dirname(fileURLToPath(import.meta.url));


//  Static mappings & regex helpers

const PY_TYPE_MAP: Record<string, string> = {
  string: 'str', number: 'float', boolean: 'bool', any: 'Any', unknown: 'Any',
  null: 'None', undefined: 'None', object: 'Dict[str, Any]', void: 'None'
};

const INTEGER_FIELDS = new Set([
  'maxIteration', 'sequence', 'messageCount', 'timeout', 'timeoutSeconds',
  'durationSeconds', 'maxTokens', 'statusCode', 'totalTokens', 'promptTokens',
  'completionTokens', 'input', 'output', 'cached', 'total'
]);

const RE = {
  BRAND: /&\s*{.*/,                                  // "… & { readonly … }"
  IMPORT: /^import\([^)]+\)\.(.+)$/,                // unwrap import()
  ARRAY: /^(.*)\[\]$/,                              // T[] syntax
  GENERIC: /^Array<(.+)>$/                           // Array<T> syntax
};

const BRANDED_IDS = [
  'NodeID', 'ArrowID', 'HandleID', 'PersonID', 'ApiKeyID', 'DiagramID', 'ExecutionID'
] as const;

type TsType = string;

const ADDITIONAL_FIELDS: Record<string, Array<{ name: string; type: string; optional: boolean }>> = {};


//  Generator class

class PythonGenerator {
  private cache   = new Map<string, string>();
  private schemas = new Map<string, SchemaDefinition>();
  private imports = new Map<string, Set<string>>();
  private branded = new Set<string>();

  constructor(private all: SchemaDefinition[], private allowExtra = true) {
    all.forEach(s => this.schemas.set(s.name, s));
  }

  // ─────────────── helpers ────────────────

  private add(from: string, ...items: string[]) {
    const set = this.imports.get(from) || this.imports.set(from, new Set()).get(from)!;
    items.forEach(i => set.add(i));
  }

  private optional(t: string) { this.add('typing', 'Optional'); return `Optional[${t}]`; }

  /** Convert a TS type string → Python */
  private py(ts: TsType, opt = false, field = ''): string {
    const key = `${ts}|${opt}|${field}`;
    if (this.cache.has(key)) return this.cache.get(key)!;

    const save = (v: string) => (this.cache.set(key, v), v);

    ts = ts.trim().replace(RE.IMPORT, '$1').replace(RE.BRAND, '').trim();

    // ─── branded ids ────────────────────────────────────────────────
    if (BRANDED_IDS.includes(ts as any)) {
      this.branded.add(ts); this.add('typing', 'NewType');
      return save(opt ? this.optional(ts) : ts);
    }

    // ─── arrays (T[]  /  Array<T>) ─────────────────────────────────
    const arr = ts.match(RE.ARRAY) || ts.match(RE.GENERIC);
    if (arr) {
      const inner = this.py(arr[1]);
      this.add('typing', 'List');
      const T = `List[${inner}]`;
      return save(opt ? this.optional(T) : T);
    }

    // ─── Map<k,v> / Record<k,v> ────────────────────────────────────
    const mapRec = (kw: 'Map' | 'Record') => {
      const m = ts.match(new RegExp(`^${kw}<([^,]+),\s*(.+)>$`));
      if (!m) return;
      const k = BRANDED_IDS.includes(m[1] as any) || m[1] === 'string' ? 'str' : this.py(m[1]);
      const v = this.py(m[2]);
      this.add('typing', 'Dict');
      const T = `Dict[${k}, ${v}]`;
      return save(opt ? this.optional(T) : T);
    };
    if (ts.startsWith('Map<') || ts.startsWith('Record<')) return mapRec(ts.startsWith('Map<') ? 'Map' : 'Record')!;

    // ─── literal unions and literals ───────────────────────────────
    if (/['"]/u.test(ts)) {
      const parts = ts.split('|').map(p => p.trim());
      const allLit = parts.every(p => /^['"][^'"]+['"]$/.test(p));
      if (allLit) {
        this.add('typing', 'Literal');
        const T = `Literal[${parts.join(', ')}]`;
        return save(opt ? this.optional(T) : T);
      }
    }

    if (/^['"][^'"]+['"]$/.test(ts)) {
      this.add('typing', 'Literal');
      const T = `Literal[${ts}]`;
      return save(opt ? this.optional(T) : T);
    }

    // ─── unions ────────────────────────────────────────────────────
    if (ts.includes('|')) {
      const pieces = ts.split('|').map(p => p.trim()).filter(p => !['undefined', 'null'].includes(p));
      const uniq = [...new Set(pieces.map(p => this.py(p)))];
      if (uniq.length === 1) return save(opt ? this.optional(uniq[0]) : uniq[0]);
      this.add('typing', 'Union');
      const T = `Union[${uniq.join(', ')}]`;
      return save(opt ? this.optional(T) : T);
    }

    // ─── custom schema ─────────────────────────────────────────────
    if (this.schemas.has(ts)) return save(opt ? this.optional(ts) : ts);

    // ─── primitives / fallback ─────────────────────────────────────
    let mapped = PY_TYPE_MAP[ts] ?? ts;
    if (ts === 'number' && INTEGER_FIELDS.has(field)) mapped = 'int';
    if (mapped === 'Any') this.add('typing', 'Any');
    return save(opt ? this.optional(mapped) : mapped);
  }

  // ─────────────── class / enum generation ────────────────

  private classLines(s: SchemaDefinition): string[] {
    if (s.type === 'enum') {
      this.add('enum', 'Enum');
      return [
        `class ${s.name}(str, Enum):`,
        ...(s.values?.length ? s.values.map(v => `    ${v.replace(/-/g, '_')} = "${v}"`) : ['    pass'])
      ];
    }

    const base = s.extends?.[0] ?? 'BaseModel';
    const cfg = `    model_config = ConfigDict(extra='${this.allowExtra ? 'allow' : 'forbid'}', populate_by_name=True)`;
    const props: Record<string, any> = { ...s.properties };
    (ADDITIONAL_FIELDS[s.name] || []).forEach(f => props[f.name] = f);

    const lines = [`class ${s.name}(${base}):`, cfg, ''];
    if (!Object.keys(props).length) return [...lines, '    pass'];

    for (const [p, info] of Object.entries(props)) {
      const t = this.py(info.type, info.optional, p);
      lines.push(`    ${p}: ${t}${info.optional ? ' = Field(default=None)' : ''}`);
    }
    return lines;
  }

  // ─────────────── main entry ────────────────

  async generate(dest: string) {
    // reset state for idempotency
    this.imports.clear(); this.cache.clear(); this.branded.clear();

    // base imports
    this.add('__future__', 'annotations');
    this.add('enum', 'Enum');
    this.add('pydantic', 'BaseModel', 'ConfigDict', 'Field');

    // preload imports to fill typing deps
    this.all.filter(s => s.type === 'interface')
      .forEach(s => Object.values(s.properties || {}).forEach(p => this.py(p.type, p.optional)));

    // compose header imports (ordered)
    const std = new Set(['enum', 'typing']);
    const imports = [...this.imports.entries()].sort(([a], [b]) => {
      if (a === '__future__') return -1; if (b === '__future__') return 1;
      const aStd = std.has(a), bStd = std.has(b);
      if (aStd && !bStd) return -1; if (!aStd && bStd) return 1;
      return a.localeCompare(b);
    }).map(([f, i]) => `from ${f} import ${[...i].sort().join(', ')}`);

    const lines: string[] = [
      ...imports, '',
      '"""',
      'Auto‑generated Python models (compact version).',
      'DO NOT EDIT THIS FILE DIRECTLY.',
      '"""',
      ''
    ];

    // enums → interfaces → aliases
    const enums = this.all.filter(s => s.type === 'enum');
    enums.forEach(e => lines.push(...this.classLines(e), ''));

    if (this.branded.size) {
      lines.push('# Branded scalar IDs');
      this.add('typing', 'NewType');
      BRANDED_IDS.filter(b => this.branded.has(b)).forEach(b => lines.push(`${b} = NewType('${b}', str)`));
      lines.push('');
    }

    this.all.filter(s => s.type === 'interface').forEach(i => lines.push(...this.classLines(i), ''));

    this.all.filter(s => s.type === 'type-alias').forEach(a => {
      const m = a.aliasType?.match(/\.([A-Za-z]+)/);
      if (m && [...this.all].some(s => s.name === m[1])) lines.push(`${a.name} = ${m[1]}`, '');
    });

    await fs.mkdir(path.dirname(dest), { recursive: true });
    await fs.writeFile(dest, lines.join('\n'));
  }
}

//  CLI


if (import.meta.url === `file://${process.argv[1]}`) {
  (async () => {
    const schemas = await loadSchemas(path.resolve(__dirname, '../__generated__'));
    const out = path.resolve(process.cwd(), '../python/dipeo_domain/src/dipeo_domain/models.py');
    await new PythonGenerator(schemas, true).generate(out);
    console.log(`Generated models.py → ${out}`);
  })();
}
