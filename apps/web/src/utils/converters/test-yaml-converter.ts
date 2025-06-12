#!/usr/bin/env tsx
/**
 * Test script for YAML converter functionality
 * Run with: pnpm tsx apps/web/src/utils/converters/test-yaml-converter.ts
 */

import { readFileSync, writeFileSync } from 'fs';
import { JsonConverter } from './formats/json';
import { YamlConverter } from './formats/yaml';

function testYamlConversion() {
  console.log('🧪 Testing YAML Converter...\n');

  // 1. Load the JSON diagram
  console.log('1. Loading JSON diagram...');
  const jsonContent = readFileSync('files/diagrams/diagram.json', 'utf-8');
  const jsonConverter = new JsonConverter();
  
  let diagram;
  try {
    diagram = jsonConverter.deserialize(jsonContent);
    console.log('✓ JSON parsed successfully');
    console.log(`  - Nodes: ${diagram.nodes.length}`);
    console.log(`  - Arrows: ${diagram.arrows.length}`);
    console.log(`  - Persons: ${diagram.persons.length}`);
    console.log(`  - API Keys: ${diagram.apiKeys.length}`);
  } catch (error) {
    console.error('✗ Error parsing JSON:', error);
    return;
  }

  // 2. Convert to YAML
  console.log('\n2. Converting to YAML...');
  const yamlConverter = new YamlConverter();
  
  let yamlContent;
  try {
    yamlContent = yamlConverter.serialize(diagram);
    console.log('✓ Converted to YAML successfully');
    
    // Save YAML
    writeFileSync('files/diagrams/diagram_test.yaml', yamlContent);
    console.log('  Saved to: files/diagrams/diagram_test.yaml');
    
    // Show preview
    const lines = yamlContent.split('\n');
    console.log('  Preview:');
    lines.slice(0, 20).forEach(line => console.log(`    ${line}`));
    if (lines.length > 20) {
      console.log('    ...');
    }
  } catch (error) {
    console.error('✗ Error converting to YAML:', error);
    console.error(error instanceof Error ? error.stack : '');
    return;
  }

  // 3. Convert back from YAML
  console.log('\n3. Converting back from YAML...');
  let diagramFromYaml;
  try {
    diagramFromYaml = yamlConverter.deserialize(yamlContent);
    console.log('✓ YAML parsed successfully');
    console.log(`  - Nodes: ${diagramFromYaml.nodes.length}`);
    console.log(`  - Arrows: ${diagramFromYaml.arrows.length}`);
    console.log(`  - Persons: ${diagramFromYaml.persons.length}`);
    console.log(`  - API Keys: ${diagramFromYaml.apiKeys.length}`);
  } catch (error) {
    console.error('✗ Error parsing YAML:', error);
    console.error(error instanceof Error ? error.stack : '');
    return;
  }

  // 4. Convert back to JSON for comparison
  console.log('\n4. Converting back to JSON...');
  let jsonFromYaml;
  try {
    jsonFromYaml = jsonConverter.serialize(diagramFromYaml);
    writeFileSync('files/diagrams/diagram_from_yaml.json', jsonFromYaml);
    console.log('✓ Saved to: files/diagrams/diagram_from_yaml.json');
  } catch (error) {
    console.error('✗ Error converting to JSON:', error);
    return;
  }

  // 5. Compare structures
  console.log('\n5. Comparing structures...');
  
  // Compare node types
  const originalNodeTypes = diagram.nodes.map(n => n.type).sort();
  const yamlNodeTypes = diagramFromYaml.nodes.map(n => n.type).sort();
  
  console.log(`  Original node types: ${originalNodeTypes.join(', ')}`);
  console.log(`  YAML roundtrip types: ${yamlNodeTypes.join(', ')}`);
  console.log(`  Node types match: ${JSON.stringify(originalNodeTypes) === JSON.stringify(yamlNodeTypes) ? '✓' : '✗'}`);
  
  // Compare arrow counts
  console.log(`\n  Original arrows: ${diagram.arrows.length}`);
  console.log(`  YAML roundtrip arrows: ${diagramFromYaml.arrows.length}`);
  console.log(`  Arrow count matches: ${diagram.arrows.length === diagramFromYaml.arrows.length ? '✓' : '✗'}`);
  
  // Check for data preservation
  console.log('\n6. Checking data preservation...');
  
  // Check a person_job node
  const originalPersonJob = diagram.nodes.find(n => n.type === 'person_job');
  const yamlPersonJob = diagramFromYaml.nodes.find(n => n.type === 'person_job');
  
  if (originalPersonJob && yamlPersonJob) {
    console.log('  Person Job node data:');
    console.log(`    Original prompt: ${originalPersonJob.data.defaultPrompt}`);
    console.log(`    YAML roundtrip prompt: ${yamlPersonJob.data.defaultPrompt}`);
    console.log(`    Prompts match: ${originalPersonJob.data.defaultPrompt === yamlPersonJob.data.defaultPrompt ? '✓' : '✗'}`);
  }

  console.log('\n✓ Test completed!');
}

// Run the test
testYamlConversion();