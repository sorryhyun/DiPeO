// Export execution core classes
export { DependencyResolver } from './flow/dependency-resolver';
export { ExecutionPlanner } from './flow/execution-planner';
export { SkipManager } from './core/skip-manager';
export { LoopController } from './core/loop-controller';
export { ExecutionEngine } from './core/execution-engine';

// Export executor classes and factories
export * from './executors';

// Export execution orchestrator
export * from './execution-orchestrator';

// Export utility functions for creating execution contexts
import { DiagramNode, DiagramArrow, ExecutionContext } from '@/types/shared';

export function createExecutionContext(nodes: DiagramNode[], arrows: DiagramArrow[]): ExecutionContext {
  const nodes_by_id: Record<string, DiagramNode> = {};
  const incoming_arrows: Record<string, DiagramArrow[]> = {};
  const outgoing_arrows: Record<string, DiagramArrow[]> = {};

  // Build nodes_by_id
  for (const node of nodes) {
    nodes_by_id[node.id] = node;
  }

  // Initialize arrow maps
  for (const node of nodes) {
    incoming_arrows[node.id] = [];
    outgoing_arrows[node.id] = [];
  }

  // Build arrow maps
  for (const arrow of arrows) {
    if (arrow.source && arrow.target) {
      outgoing_arrows[arrow.source] = outgoing_arrows[arrow.source] || [];
      incoming_arrows[arrow.target] = incoming_arrows[arrow.target] || [];
      
      outgoing_arrows[arrow.source]?.push(arrow);
      incoming_arrows[arrow.target]?.push(arrow);
    }
  }

  return {
    nodes_by_id,
    incoming_arrows,
    outgoing_arrows
  };
}