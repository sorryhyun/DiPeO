#!/usr/bin/env node
/**
 * CLI Runner - Entry point for Node.js execution
 * This file is bundled by esbuild to create execution_runner.cjs
 */

/* eslint-env node */

import fs from 'fs';
import { StandardExecutionOrchestrator } from './execution-orchestrator';
import type { Diagram } from '@/shared/types/core';

declare const process: NodeJS.Process;
declare function require(id: string): any;
declare const module: any;

// Polyfill fetch for Node.js environment
if (typeof globalThis.fetch === 'undefined') {
  // eslint-disable-next-line @typescript-eslint/no-var-requires, @typescript-eslint/no-require-imports
  globalThis.fetch = require('node-fetch');
}

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length < 1) {
    console.log('Usage: node execution_runner.cjs <diagram.json>');
    process.exit(1);
  }
  
  const diagramPath = args[0];
  if (!diagramPath) {
    throw new Error('No diagram path provided');
  }
  
  try {
    // Load diagram
    const diagramData = JSON.parse(fs.readFileSync(diagramPath, 'utf8')) as Diagram;
    console.log(`📂 Loaded diagram from ${diagramPath}`);
    
    // Create orchestrator
    const orchestrator = new StandardExecutionOrchestrator();
    
    // Execute diagram
    console.log('🚀 Starting execution...\n');
    const result = await orchestrator.execute(diagramData);
    
    // Display summary
    console.log('\n📊 Execution Summary:');
    console.log(`  Success: ${result.success}`);
    console.log(`  Total Cost: $${result.metadata.totalCost.toFixed(4)}`);
    console.log(`  Execution Time: ${Date.now() - result.metadata.startTime}ms`);
    
    if (result.errors && result.errors.length > 0) {
      console.log(`  Errors: ${result.errors.map(e => e.message).join(', ')}`);
    }
    
    // Save results
    const resultsPath = 'results.json';
    fs.writeFileSync(resultsPath, JSON.stringify(result, null, 2));
    console.log(`  Results saved to: ${resultsPath}`);
    
    // Exit with appropriate code
    process.exit(result.success ? 0 : 1);
    
  } catch (error) {
    console.error('Failed to execute diagram:', error);
    process.exit(1);
  }
}

// Run if called directly
// @ts-expect-error - CommonJS module check
if (typeof require !== 'undefined' && require.main === module) {
  main().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}

// Export for testing
export { main };