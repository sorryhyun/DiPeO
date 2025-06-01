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
import { DiagramNode, DiagramArrow, ExecutionContext } from '@/shared/types/core';

export function createExecutionContext(nodes: DiagramNode[], arrows: DiagramArrow[]): ExecutionContext {
  const nodesById: Record<string, DiagramNode> = {};
  const incomingArrows: Record<string, DiagramArrow[]> = {};
  const outgoingArrows: Record<string, DiagramArrow[]> = {};

  // Build nodes_by_id
  for (const node of nodes) {
    nodesById[node.id] = node;
  }

  // Initialize arrow maps
  for (const node of nodes) {
    incomingArrows[node.id] = [];
    outgoingArrows[node.id] = [];
  }

  // Build arrow maps
  for (const arrow of arrows) {
    if (arrow.source && arrow.target) {
      outgoingArrows[arrow.source] = outgoingArrows[arrow.source] || [];
      incomingArrows[arrow.target] = incomingArrows[arrow.target] || [];
      
      outgoingArrows[arrow.source]?.push(arrow);
      incomingArrows[arrow.target]?.push(arrow);
    }
  }

  return {
    nodesById,
    incomingArrows,
    outgoingArrows
  };
}