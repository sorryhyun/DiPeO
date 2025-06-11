#!/usr/bin/env tsx
/* eslint-env node */
/* global process */
/**
 * CLI wrapper for diagram conversion that can properly resolve path aliases
 */

import { readFile, writeFile } from 'fs/promises';
import { resolve } from 'path';
import { parse as parseYaml } from 'yaml';
import { Yaml } from '../formats/yaml';
import { LlmYaml } from '../formats/llm-yaml';

// Main async function
async function main() {
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
    // Read input file asynchronously
    const inputContent = await readFile(resolvedInputFile, 'utf8');
    let diagram;

    // Parse input based on extension
    if (resolvedInputFile.endsWith('.json')) {
      diagram = JSON.parse(inputContent);
    } else if (resolvedInputFile.endsWith('.yaml') || resolvedInputFile.endsWith('.yml') || resolvedInputFile.endsWith('.llm-yaml')) {
      const yamlData = parseYaml(inputContent);
      
      // Detect if this is LLM YAML format
      if (yamlData.flow && (yamlData.prompts || yamlData.persons)) {
        // LLM YAML format - convert to DiagramState
        diagram = LlmYaml.fromLLMYAML(inputContent);
      } else {
        // Enhanced YAML format - convert to DiagramState  
        diagram = Yaml.fromYAML(inputContent);
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
        outputContent = Yaml.toYAML(diagram);
        break;
        
      case 'llm-yaml':
        outputContent = LlmYaml.toLLMYAML(diagram);
        break;
        
      default:
        throw new Error(`Unsupported output format: ${targetFormat}`);
    }

    // Write output file asynchronously
    await writeFile(resolvedOutputFile, outputContent);
    console.log(`✓ Converted: ${inputFile} → ${outputFile} (${targetFormat})`);

  } catch (error) {
    console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

// Run the async main function
main().catch(error => {
  console.error('Unexpected error:', error);
  process.exit(1);
});