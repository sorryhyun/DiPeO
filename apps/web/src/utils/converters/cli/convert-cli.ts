#!/usr/bin/env tsx
/* eslint-env node */
/* global process */
/**
 * CLI wrapper for diagram conversion using the new unified converter system
 */

import { readFile, writeFile } from 'fs/promises';
import { resolve } from 'path';
import { converterRegistry } from '../core/registry';
import { storeDomainConverter } from '../core/storeDomainConverter';
import { setupConverterRegistry } from '../core/setupRegistry';
import { SupportedFormat } from '../core/types';
import type { DomainDiagram } from '@/types';

// Ensure converters are registered
setupConverterRegistry();

// Main async function
async function main() {
  // Parse command line arguments
  const [, , inputFile, outputFile, format] = process.argv;

  // Resolve paths relative to project root (we're in apps/web when running)
  const resolvedInputFile = inputFile ? resolve(process.cwd(), '../..', inputFile) : undefined;
  const resolvedOutputFile = outputFile ? resolve(process.cwd(), '../..', outputFile) : undefined;

  if (!resolvedInputFile || !resolvedOutputFile) {
    console.error('Usage: node convert-cli.js <input> <output> [format]');
    console.error('Available formats:');
    console.error('  json: Native JSON format');
    converterRegistry.getFormats().forEach(format => {
      const metadata = converterRegistry.getMetadata(format);
      console.error(`  ${format}: ${metadata?.description || 'No description'}`);
    });
    process.exit(1);
  }

  try {
    // Read input file
    const inputContent = await readFile(resolvedInputFile, 'utf8');
    let diagram: DomainDiagram;

    // Detect input format and parse
    if (resolvedInputFile.endsWith('.json')) {
      // Assume it's native JSON format
      diagram = JSON.parse(inputContent) as DomainDiagram;
    } else if (resolvedInputFile.endsWith('.yaml') || resolvedInputFile.endsWith('.yml')) {
      // Try to detect which YAML format it is
      const detectedFormat = detectYamlFormat(inputContent);
      const converter = converterRegistry.get(detectedFormat);
      diagram = converter.deserialize(inputContent);
    } else {
      throw new Error(`Unsupported input format: ${resolvedInputFile}`);
    }

    // Determine output format
    const detectedFormat = format || detectFormatFromFilename(resolvedOutputFile);
    
    // Convert to output format
    let outputContent: string;
    
    if (detectedFormat === 'json') {
      // Native JSON format
      outputContent = JSON.stringify(diagram, null, 2);
    } else {
      // Use registered converter
      const targetFormat = detectedFormat as SupportedFormat;
      if (!converterRegistry.has(targetFormat)) {
        throw new Error(`Unsupported output format: ${targetFormat}`);
      }
      const converter = converterRegistry.get(targetFormat);
      outputContent = converter.serialize(diagram);
    }

    // Write output file
    await writeFile(resolvedOutputFile, outputContent);
    console.log(`✓ Converted: ${inputFile} → ${outputFile} (${detectedFormat})`);

  } catch (error) {
    console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

/**
 * Detect YAML format by examining content structure
 */
function detectYamlFormat(content: string): SupportedFormat {
  // Simple heuristic: check for format-specific fields
  if (content.includes('flow:') && (content.includes('prompts:') || content.includes('persons:'))) {
    return 'llm-readable';
  } else if (content.includes('connections:')) {
    // Could be light or readable format
    if (content.includes('steps:')) {
      return 'readable';
    } else {
      return 'light';
    }
  } else {
    // Default to native YAML
    return 'native';
  }
}

/**
 * Detect format from filename extension
 */
function detectFormatFromFilename(filename: string): string {
  if (filename.endsWith('.json')) return 'json';
  if (filename.endsWith('.light.yaml') || filename.endsWith('.light.yml')) return 'light';
  if (filename.endsWith('.readable.yaml') || filename.endsWith('.readable.yml')) return 'readable';
  if (filename.endsWith('.llm.yaml') || filename.endsWith('.llm.yml')) return 'llm-readable';
  if (filename.endsWith('.yaml') || filename.endsWith('.yml')) return 'native';
  return 'json'; // Default
}

// Run the async main function
main().catch(error => {
  console.error('Unexpected error:', error);
  process.exit(1);
});