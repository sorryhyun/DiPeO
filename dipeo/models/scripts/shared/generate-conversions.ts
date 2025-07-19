#!/usr/bin/env tsx
/**
 * Code-generates Python conversion helpers from `conversions.ts`.
 *
 *   yarn tsx scripts/generate-conversions.ts \
 *     --src ../src/conversions.ts \
 *     --out ../../domain/conversions.py
 *
 * All flags are optional; sensible defaults are used.
 */

import { Project, SyntaxKind, PropertyAssignment } from 'ts-morph';
import { readFile, writeFile, mkdir } from 'fs/promises';
import { join, dirname, resolve } from 'path';
import { fileURLToPath } from 'url';
import process from 'node:process';
import { PATHS } from '../paths';

interface CliOpts {
  src: string;
  out: string;
}

function parseArgs(): CliOpts {
  const args = process.argv.slice(2);
  const opts: Partial<CliOpts> = {};
  for (let i = 0; i < args.length; i += 2) {
    const flag = args[i];
    const val = args[i + 1];
    if (!val?.startsWith('-')) {
      if (flag === '--src') opts.src = val;
      if (flag === '--out') opts.out = val;
    }
  }
  return {
    src: opts.src ?? join(PATHS.srcDir, 'conversions.ts'),
    out:
      opts.out ??
      join(PATHS.modelsRoot, 'conversions.py'),
  };
}

/* -------------------------------------------------------------------------- */

function extractNodeTypeEntries(srcPath: string): [string, string][] {
  const project = new Project({ compilerOptions: { allowJs: true } });
  const source = project.addSourceFileAtPath(srcPath);
  const varDecl = source.getVariableDeclarationOrThrow('NODE_TYPE_MAP');
  const obj = varDecl.getInitializerIfKindOrThrow(SyntaxKind.ObjectLiteralExpression);

  return obj.getProperties().flatMap(prop => {
    if (!PropertyAssignment.isPropertyAssignment(prop)) return [];
    const key = prop.getName().replace(/['"`]/g, '');
    const match = prop.getInitializerOrThrow().getText().match(/NodeType\.([A-Z0-9_]+)/);
    if (!match) return [];
    return [[key, match[1]]] as [string, string][];
  });
}

/* -------------------------------------------------------------------------- */

function buildPython(entries: [string, string][]): string {
  const now = new Date().toISOString();
  const mapLines = entries
    .map(([k, v]) => `    "${k}": NodeType.${v},`)
    .join('\n');

  return `"""
Auto-generated ${now}. Do NOT edit by hand.
Source of truth: \`conversions.ts\`
"""

from typing import Dict, Any, TypedDict
from .models import (
    NodeType,
    HandleDirection,
    NodeID,
    HandleID,
)

# ---------------------------------------------------------------------------

NODE_TYPE_MAP: Dict[str, NodeType] = {
${mapLines}
}

NODE_TYPE_REVERSE_MAP: Dict[NodeType, str] = {v: k for k, v in NODE_TYPE_MAP.items()}

def node_kind_to_domain_type(kind: str) -> NodeType:
    try:
        return NODE_TYPE_MAP[kind]
    except KeyError as exc:
        raise ValueError(f"Unknown node kind: {kind}") from exc


def domain_type_to_node_kind(node_type: NodeType) -> str:
    try:
        return NODE_TYPE_REVERSE_MAP[node_type]
    except KeyError as exc:
        raise ValueError(f"Unknown node type: {node_type}") from exc


# ---------------------------------------------------------------------------
# Handle helpers – kept trivial and logic-aligned with TypeScript.
# ---------------------------------------------------------------------------

def normalize_node_id(node_id: str) -> NodeID:  # noqa: D401
    """Return the node ID unchanged (placeholder for future logic)."""
    return node_id  # type: ignore[return-value]


def create_handle_id(
    node_id: NodeID,
    handle_label: str,
    direction: HandleDirection,
) -> HandleID:
    """Compose a handle ID the same way the frontend expects it."""
    return f"{node_id}_{handle_label}_{direction.value}"  # type: ignore[return-value]


class ParsedHandle(TypedDict):
    node_id: NodeID
    handle_label: str
    direction: HandleDirection


def parse_handle_id(handle_id: HandleID) -> ParsedHandle:
    parts = handle_id.split("_")
    if len(parts) != 3:
        raise ValueError(f"Invalid handle ID: {handle_id}")
    node_id, label, dir_str = parts
    try:
        direction = HandleDirection[dir_str.upper()]
    except KeyError as exc:
        raise ValueError(f"Unknown handle direction: {dir_str}") from exc
    return {"node_id": node_id, "handle_label": label, "direction": direction}  # type: ignore[return-value]


__all__ = [
    "NODE_TYPE_MAP",
    "NODE_TYPE_REVERSE_MAP",
    "node_kind_to_domain_type",
    "domain_type_to_node_kind",
    "normalize_node_id",
    "create_handle_id",
    "parse_handle_id",
]
`;
}

/* -------------------------------------------------------------------------- */

export async function generateConversions() {
  const { src, out } = parseArgs();

  try {
    // Validate source file exists (ts-morph would throw later anyway)
    await readFile(src);

    const entries = extractNodeTypeEntries(src);
    if (entries.length === 0) throw new Error('NODE_TYPE_MAP is empty or not found.');

    const pyCode = buildPython(entries);
    await mkdir(dirname(out), { recursive: true });
    await writeFile(out, pyCode);

    console.log(`✅ conversions.py generated at ${out}`);
  } catch (err) {
    console.error('❌ Failed to generate conversions:', err);
    process.exit(1);
  }
}

/* -------------------------------------------------------------------------- */

if (import.meta.url === `file://\${process.argv[1]}`) {
  generateConversions();
}
