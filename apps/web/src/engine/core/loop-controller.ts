/**
 * Loop controller for managing explicit loop execution state.
 * 
 * Manages loop execution state for both individual nodes and global loops.
 */
export class LoopController {
  private iterationCounts: Map<string, number> = new Map();

  constructor(
    private maxIterations: number,
    private loopNodes: string[]
  ) {}

  /**
   * Check if loop should continue executing.
   * 
   * @returns True if more iterations are allowed, False otherwise
   */
  shouldContinueLoop(nodeId: string, maxIterations?: number): boolean {
    const currentIteration = this.getIterationCount(nodeId);
    const limit = maxIterations || this.maxIterations;
    return currentIteration < limit;
  }

  /**
   * Increment iteration count for a specific node.
   * 
   * @param nodeId - The node to increment iteration for
   */
  incrementIteration(nodeId: string): void {
    const current = this.iterationCounts.get(nodeId) || 0;
    this.iterationCounts.set(nodeId, current + 1);
  }

  /**
   * Reset iterations for a specific node.
   * 
   * @param nodeId - The node to reset iterations for
   */
  resetIterations(nodeId: string): void {
    this.iterationCounts.set(nodeId, 0);
  }

  /**
   * Get current iteration number for a node (0-based).
   * 
   * @param nodeId - The node to get iteration count for
   * @returns Current iteration count
   */
  getIterationCount(nodeId: string): number {
    return this.iterationCounts.get(nodeId) || 0;
  }

  /**
   * Get number of remaining iterations for a node.
   * 
   * @param nodeId - The node to check
   * @param maxIterations - Optional max iterations override
   * @returns Number of remaining iterations
   */
  getRemainingIterations(nodeId: string, maxIterations?: number): number {
    const current = this.getIterationCount(nodeId);
    const limit = maxIterations || this.maxIterations;
    return Math.max(0, limit - current);
  }

  /**
   * Check if a node is part of this loop.
   * 
   * @param nodeId - ID of node to check
   * @returns True if node is part of the loop, False otherwise
   */
  isNodeInLoop(nodeId: string): boolean {
    return this.loopNodes.includes(nodeId);
  }

  /**
   * Reset loop controller to initial state.
   */
  reset(): void {
    this.iterationCounts.clear();
  }

  /**
   * Check if any node in the loop has reached max iterations.
   * 
   * @returns True if any loop node has reached max iterations
   */
  hasAnyNodeReachedMaxIterations(): boolean {
    for (const nodeId of this.loopNodes) {
      const current = this.getIterationCount(nodeId);
      if (current >= this.maxIterations) {
        return true;
      }
    }
    return false;
  }

  /**
   * Get all nodes that have reached their maximum iterations.
   * 
   * @returns Array of node IDs that have reached max iterations
   */
  getNodesAtMaxIterations(): string[] {
    const result: string[] = [];
    for (const nodeId of this.loopNodes) {
      const current = this.getIterationCount(nodeId);
      if (current >= this.maxIterations) {
        result.push(nodeId);
      }
    }
    return result;
  }

  /**
   * Get iteration statistics for all loop nodes.
   * 
   * @returns Object with iteration stats
   */
  getIterationStats(): {
    totalIterations: number;
    maxIterationsReached: boolean;
    nodeIterations: Record<string, number>;
    averageIterations: number;
  } {
    const nodeIterations: Record<string, number> = {};
    let totalIterations = 0;

    for (const nodeId of this.loopNodes) {
      const count = this.getIterationCount(nodeId);
      nodeIterations[nodeId] = count;
      totalIterations += count;
    }

    return {
      totalIterations,
      maxIterationsReached: this.hasAnyNodeReachedMaxIterations(),
      nodeIterations,
      averageIterations: this.loopNodes.length > 0 ? totalIterations / this.loopNodes.length : 0
    };
  }

  /**
   * Check if a specific node should continue looping based on its iteration count.
   * 
   * @param nodeId - The node to check
   * @param nodeMaxIterations - Optional node-specific max iterations
   * @returns True if the node should continue looping
   */
  shouldNodeContinueLooping(nodeId: string, nodeMaxIterations?: number): boolean {
    if (!this.isNodeInLoop(nodeId)) {
      return false;
    }

    const current = this.getIterationCount(nodeId);
    const limit = nodeMaxIterations || this.maxIterations;
    return current < limit;
  }

  /**
   * Mark that a node has completed an iteration and check if it should continue.
   * 
   * @param nodeId - The node that completed an iteration
   * @param nodeMaxIterations - Optional node-specific max iterations
   * @returns True if the node should continue looping
   */
  markIterationComplete(nodeId: string, nodeMaxIterations?: number): boolean {
    this.incrementIteration(nodeId);
    return this.shouldNodeContinueLooping(nodeId, nodeMaxIterations);
  }

  /**
   * Create a new LoopController for a subset of nodes.
   * 
   * @param nodeIds - The nodes to include in the new controller
   * @param maxIterations - Max iterations for the new controller
   * @returns New LoopController instance
   */
  createSubController(nodeIds: string[], maxIterations?: number): LoopController {
    const subController = new LoopController(
      maxIterations || this.maxIterations,
      nodeIds
    );
    
    // Copy existing iteration counts for these nodes
    for (const nodeId of nodeIds) {
      const count = this.getIterationCount(nodeId);
      if (count > 0) {
        subController.iterationCounts.set(nodeId, count);
      }
    }
    
    return subController;
  }
}