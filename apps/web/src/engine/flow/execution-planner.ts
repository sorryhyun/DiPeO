import { ExecutionContext, ExecutionPlan, DiagramArrow } from '@/types/shared';
import { DependencyResolver } from './dependency-resolver';

export class ExecutionPlanner {
  constructor(
    private context: ExecutionContext,
    private dependencyResolver: DependencyResolver
  ) {}

  /**
   * Create execution plan with validation and metadata
   */
  createExecutionPlan(): ExecutionPlan {
    const startNodes = this.dependencyResolver.validateStartNodes();
    const cycles = this.dependencyResolver.detectCycles();

    return {
      start_nodes: startNodes,
      has_cycles: cycles.length > 0,
      cycle_nodes: cycles,
      total_nodes: Object.keys(this.context.nodes_by_id).length,
      total_arrows: this.getAllArrows().length,
      node_types: Object.fromEntries(
        Object.entries(this.context.nodes_by_id).map(([nodeId, node]) => [
          nodeId,
          node.type || 'unknown'
        ])
      )
    };
  }

  /**
   * Get all start nodes in the diagram
   */
  getStartNodes(): string[] {
    return Object.entries(this.context.nodes_by_id)
      .filter(([_, node]) => node.type === 'startNode')
      .map(([nodeId, _]) => nodeId);
  }

  /**
   * Get the next nodes to execute based on current node output
   */
  getNextNodes(nodeId: string, output?: unknown): string[] {
    const nextNodes: string[] = [];
    const outgoing = this.context.outgoing_arrows[nodeId] || [];

    for (const arrow of outgoing) {
      const targetId = this.getArrowTarget(arrow);
      if (!targetId) continue;

      // Handle conditional arrows
      if (this.isConditionalArrow(arrow) && typeof output === 'boolean') {
        const arrowLabel = this.getArrowLabel(arrow);
        if ((arrowLabel === 'true' && output) || (arrowLabel === 'false' && !output)) {
          nextNodes.push(targetId);
        }
      } else {
        // Non-conditional arrow
        nextNodes.push(targetId);
      }
    }

    return nextNodes;
  }

  /**
   * Identify nodes that can be executed in parallel
   */
  detectParallelExecutionOpportunities(): Set<string>[] {
    const parallelGroups: Set<string>[] = [];
    const processed = new Set<string>();

    while (processed.size < Object.keys(this.context.nodes_by_id).length) {
      // Find nodes with no unprocessed dependencies
      const readyNodes = new Set<string>();

      for (const nodeId of Object.keys(this.context.nodes_by_id)) {
        if (processed.has(nodeId)) continue;

        // Check if all dependencies are processed
        const deps = new Set(this.dependencyResolver.getDependencies(nodeId));
        if (this.isSubset(deps, processed)) {
          readyNodes.add(nodeId);
        }
      }

      if (readyNodes.size === 0) {
        // Handle cycles or disconnected nodes
        const remaining = new Set(Object.keys(this.context.nodes_by_id));
        for (const processed_node of processed) {
          remaining.delete(processed_node);
        }
        if (remaining.size > 0) {
          const firstRemaining = remaining.values().next().value;
          if (firstRemaining) {
            readyNodes.add(firstRemaining);
          }
        }
      }

      if (readyNodes.size > 0) {
        parallelGroups.push(readyNodes);
        for (const node of readyNodes) {
          processed.add(node);
        }
      }
    }

    return parallelGroups;
  }

  /**
   * Validate if an execution path is valid
   */
  validateExecutionPath(path: string[]): { is_valid: boolean; errors: string[]; warnings: string[] } {
    const validationResult = {
      is_valid: true,
      errors: [] as string[],
      warnings: [] as string[]
    };

    const executed = new Set<string>();

    for (let i = 0; i < path.length; i++) {
      const nodeId = path[i];
      
      if (!nodeId || !(nodeId in this.context.nodes_by_id)) {
        validationResult.is_valid = false;
        validationResult.errors.push(`Node ${nodeId} not found in diagram`);
        continue;
      }

      // Check dependencies
      if (nodeId) {
        const deps = new Set(this.dependencyResolver.getDependencies(nodeId));
        const missingDeps = new Set([...deps].filter(dep => !executed.has(dep)));

        if (missingDeps.size > 0) {
          validationResult.is_valid = false;
          validationResult.errors.push(
            `Node ${nodeId} at position ${i} has unmet dependencies: ${Array.from(missingDeps).join(', ')}`
          );
        }

        executed.add(nodeId);
      }
    }

    return validationResult;
  }

  /**
   * Determine optimal execution order using topological sort
   */
  determineExecutionOrder(): string[] {
    return this.dependencyResolver.topologicalSort();
  }

  // Private helper methods

  private isConditionalArrow(arrow: DiagramArrow): boolean {
    const label = this.getArrowLabel(arrow);
    return label === 'true' || label === 'false';
  }

  private getArrowLabel(arrow: DiagramArrow): string {
    // Check multiple possible locations for the label
    let label = arrow.label || '';
    if (!label) {
      // Check sourceHandle for condition output patterns
      const sourceHandle = arrow.sourceHandle || '';
      if (sourceHandle.endsWith('-output-true')) {
        label = 'true';
      } else if (sourceHandle.endsWith('-output-false')) {
        label = 'false';
      } else {
        // Check arrow data
        label = arrow.data?.label || '';
      }
    }

    return label.toLowerCase();
  }

  private getAllArrows(): DiagramArrow[] {
    const allArrows: DiagramArrow[] = [];
    for (const arrows of Object.values(this.context.outgoing_arrows)) {
      allArrows.push(...arrows);
    }
    return allArrows;
  }

  private getArrowTarget(arrow: DiagramArrow): string | null {
    return arrow.target || null;
  }

  private isSubset<T>(subset: Set<T>, superset: Set<T>): boolean {
    for (const elem of subset) {
      if (!superset.has(elem)) {
        return false;
      }
    }
    return true;
  }
}