#!/usr/bin/env tsx
/**
 * Diagram conversion script using TypeScript serialization logic
 * Bridges Python CLI tool with sophisticated TypeScript converters
 */

import { readFileSync, writeFileSync } from 'fs';
import { parse as parseYaml } from 'yaml';
import { YamlExporter } from '../apps/web/src/serialization/converters/yamlExporter';
import { LLMYamlImporter } from '../apps/web/src/serialization/converters/llmYamlImporter';

// Parse command line arguments
const [, , inputFile, outputFile, format] = process.argv;

if (!inputFile || !outputFile) {
  console.error('Usage: node convert-diagram.js <input> <output> [format]');
  console.error('Formats: json, yaml, llm-yaml');
  process.exit(1);
}

try {
  // Read input file
  const inputContent = readFileSync(inputFile, 'utf8');
  let diagram;

  // Parse input based on extension
  if (inputFile.endsWith('.json')) {
    diagram = JSON.parse(inputContent);
  } else if (inputFile.endsWith('.yaml') || inputFile.endsWith('.yml')) {
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
    throw new Error(`Unsupported input format: ${inputFile}`);
  }

  // Convert to output format
  let outputContent;
  const targetFormat = format || outputFile.split('.').pop();

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
  writeFileSync(outputFile, outputContent);
  console.log(`✓ Converted: ${inputFile} → ${outputFile} (${targetFormat})`);

} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}