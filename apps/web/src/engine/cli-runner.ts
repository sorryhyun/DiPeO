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

/**
 * CLI Stream Manager for broadcasting execution events to monitor
 */
class CLIStreamManager {
  private apiUrl: string;

  constructor(apiUrl = 'http://localhost:8000') {
    this.apiUrl = apiUrl;
  }

  async broadcastEvent(eventData: any) {
    try {
      const response = await fetch(`${this.apiUrl}/api/monitor/broadcast`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventData)
      });
      
      if (!response.ok) {
        console.warn(`Failed to broadcast event: ${response.status}`);
      }
    } catch (error) {
      console.warn('Monitor broadcast failed:', error);
    }
  }

  emit(update: any): void {
    // Debug logging
    console.log('🔄 CLI Stream Manager emit:', update.type, update.nodeId || update.executionId);
    
    // Map execution engine events to monitor events
    const { type, executionId, nodeId, data } = update;
    
    switch (type) {
      case 'execution_started':
        console.log('📡 Broadcasting execution_started...');
        this.broadcastEvent({
          type: 'execution_started',
          execution_id: executionId,
          diagram: data?.diagram
        });
        break;
        
      case 'node_started':
        console.log('📡 Broadcasting node_start for:', nodeId);
        this.broadcastEvent({
          type: 'node_start',
          nodeId: nodeId
        });
        break;
        
      case 'node_completed':
        console.log('📡 Broadcasting node_complete for:', nodeId);
        this.broadcastEvent({
          type: 'node_complete', 
          nodeId: nodeId,
          output_preview: data?.result?.output ? String(data.result.output).substring(0, 100) : undefined
        });
        break;
        
      case 'execution_completed':
        console.log('📡 Broadcasting execution_complete...');
        this.broadcastEvent({
          type: 'execution_complete',
          context: data?.context || {}
        });
        break;
        
      case 'execution_failed':
        console.log('📡 Broadcasting execution_error...');
        this.broadcastEvent({
          type: 'execution_error',
          error: data?.error?.message || 'Execution failed'
        });
        break;
        
      default:
        console.log('⚠️  Unknown stream event type:', type);
    }
  }

  isEnabled(): boolean {
    return true;
  }
}

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
    
    // Load diagram into stores for proper execution
    // This is crucial for PersonJob nodes to find person configurations
    const { useDiagramOperationsStore } = await import('@/core/stores/diagramOperationsStore');
    console.log('🔄 Loading diagram into stores...');
    
    // Convert Diagram to DiagramState (add apiKeys field if missing)
    const diagramState = {
      ...diagramData,
      nodes: diagramData.nodes as any[], // DiagramNode type
      arrows: diagramData.arrows as any[], // Edge<ArrowData> type
      apiKeys: (diagramData as any).apiKeys || [] // Add apiKeys if missing
    };
    
    useDiagramOperationsStore.getState().loadDiagram(diagramState);
    console.log('✅ Diagram loaded into stores');
    
    // Create stream manager for CLI execution monitoring
    const streamManager = new CLIStreamManager();
    console.log('📊 Created CLI stream manager');
    
    // Create orchestrator with stream manager
    const orchestrator = new StandardExecutionOrchestrator(undefined, streamManager);
    console.log('🎭 Created orchestrator with stream manager');
    
    // Execute diagram
    console.log('🚀 Starting execution...\n');
    const result = await orchestrator.execute(diagramData);
    console.log('✅ Execution completed, result:', result.success);
    
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