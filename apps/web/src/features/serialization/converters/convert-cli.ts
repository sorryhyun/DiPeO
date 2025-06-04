#!/usr/bin/env tsx
/* eslint-env node */
/* global process */
/**
 * CLI wrapper for diagram conversion that can properly resolve path aliases
 */

import { readFileSync, writeFileSync } from 'fs';
import { resolve } from 'path';
import { parse as parseYaml } from 'yaml';
import { YamlExporter } from './yamlExporter';
import { LLMYamlImporter } from './llmYamlImporter';

// Parse command line arguments
const [, , inputFile, outputFile, format] = process.argv;

// Resolve paths relative to project root (we're in apps/web when running)
const resolvedInputFile = inputFile ? resolve(process.cwd(), '../..', inputFile) : undefined;
const resolvedOutputFile = outputFile ? resolve(process.cwd(), '../..', outputFile) : undefined;

if (!resolvedInputFile || !resolvedOutputFile) {
  console.error('Usage: node convert-cli.js <input> <output> [format]');
  console.error('Formats: json, yaml, llm-yaml');
  process.exit(1);
}

try {
  // Read input file
  const inputContent = readFileSync(resolvedInputFile, 'utf8');
  let diagram;

  // Parse input based on extension
  if (resolvedInputFile.endsWith('.json')) {
    diagram = JSON.parse(inputContent);
  } else if (resolvedInputFile.endsWith('.yaml') || resolvedInputFile.endsWith('.yml') || resolvedInputFile.endsWith('.llm-yaml')) {
    const yamlData = parseYaml(inputContent);
    
    // Detect if this is LLM YAML format
    if (yamlData.flow && (yamlData.prompts || yamlData.agents)) {
      // LLM YAML format - convert to DiagramState
      diagram = LLMYamlImporter.fromLLMYAML(inputContent);
    } else {
      // Enhanced YAML format - convert to DiagramState  
      diagram = YamlExporter.fromYAML(inputContent);
    }
  } else {
    throw new Error(`Unsupported input format: ${resolvedInputFile}`);
  }

  // Convert to output format
  let outputContent;
  const targetFormat = format || resolvedOutputFile.split('.').pop();

  switch (targetFormat) {
    case 'json':
      outputContent = JSON.stringify(diagram, null, 2);
      break;
      
    case 'yaml':
    case 'yml':
      outputContent = YamlExporter.toYAML(diagram);
      break;
      
    case 'llm-yaml':
      outputContent = LLMYamlImporter.toLLMYAML(diagram);
      break;
      
    default:
      throw new Error(`Unsupported output format: ${targetFormat}`);
  }

  // Write output file
  writeFileSync(resolvedOutputFile, outputContent);
  console.log(`✓ Converted: ${inputFile} → ${outputFile} (${targetFormat})`);

} catch (error) {
  console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
  process.exit(1);
}