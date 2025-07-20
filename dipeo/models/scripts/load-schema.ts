// ─── loadSchemas ───────────────────────────────────────────────────────────────
import * as fs from 'fs/promises';
import * as path from 'path';
import { SchemaDefinition } from './generate-schema';

const _cache = new Map<string, SchemaDefinition[]>();

/**
 * Load the flattened `schemas.json` that `generateSchemas()` produces.
 *
 * @param dir   Directory that contains the file (default: "./dist")
 * @param file  Override the filename if needed.
 */
export async function loadSchemas(
  dir  = path.resolve('dist'),
  file = 'schemas.json',
): Promise<SchemaDefinition[]> {
  const key = path.join(dir, file);
  if (_cache.has(key)) return _cache.get(key)!;           // instant on 2nd hit

  const raw = await fs.readFile(key, 'utf-8');
  const schemas = JSON.parse(raw) as SchemaDefinition[];

  // Light validation: makes debugging easier if wrong file is supplied
  if (!Array.isArray(schemas) || !schemas.every(s => s?.name)) {
    throw new Error(`File at ${key} does not look like a schema bundle`);
  }

  _cache.set(key, schemas);
  return schemas;
}
