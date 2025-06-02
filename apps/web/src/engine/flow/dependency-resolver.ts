import { ExecutionContext, DiagramArrow, ArrowValidation, NodeType } from '@/shared/types/core';

export class DependencyResolver {
  constructor(private context: ExecutionContext) {}

  /**
   * Validate and return start node IDs
   */
  validateStartNodes(): string[] {
    const startNodes: string[] = [];
    
    for (const [nodeId, node] of Object.entries(this.context.nodesById)) {
      if (!node) continue;
      // Check for both normalized and React Flow node types
      if (node.type === 'start' || node.type === 'startNode') {
        startNodes.push(nodeId);
      }
    }

    if (startNodes.length === 0) {
      console.warn('No start nodes found in diagram');
    }

    return startNodes;
  }

  /**
   * Check if all dependencies for a node are met
   */
  checkDependenciesMet(
    nodeId: string,
    executedNodes: Set<string>,
    conditionValues: Record<string, boolean>
  ): [boolean, DiagramArrow[]] {
    const node = this.context.nodesById[nodeId];
    if (!node) {
      return [false, []];
    }
    console.debug(`\n[Dependency Check] Node ${nodeId} (type: ${node.type})`);

    // Start nodes have no dependencies
    if (this.isStartNode(node)) {
      return [true, []];
    }

    const incomingArrows = this.context.incomingArrows[nodeId] || [];
    console.debug(`[Dependency Check] Incoming arrows: ${incomingArrows.length}`);
    
    if (incomingArrows.length === 0) {
      return [true, []];
    }

    // Validate each incoming arrow
    const arrowValidations = incomingArrows.map(arrow =>
      this.validateArrowDependency(arrow, nodeId, executedNodes, conditionValues)
    );

    const validArrows = arrowValidations.filter(v => v.isValid).map(v => v.arrow);
    const missingDeps = arrowValidations.filter(v => !v.isValid).map(v => v.arrow);

    // Special handling for PersonJob nodes with first-only inputs
    if (this.canExecuteWithFirstOnly(node, nodeId, incomingArrows, executedNodes)) {
      console.debug(`[Dependency Check] PersonJobNode ${nodeId} can execute with first_only input`);
      // Return all first-only arrows that have data available
      const firstOnlyArrows = incomingArrows.filter(arrow => {
        if (this.isHandleFirstOnly(arrow)) {
          const srcId = this.getArrowSource(arrow);
          return srcId && executedNodes.has(srcId);
        }
        return false;
      });
      return [true, firstOnlyArrows as DiagramArrow[]];
    }

    const dependenciesMet = missingDeps.length === 0;
    return [dependenciesMet, validArrows as DiagramArrow[]];
  }

  /**
   * Detect cycles in the graph using DFS
   */
  detectCycles(): string[][] {
    const cycles: string[][] = [];
    const visited = new Set<string>();
    const recStack = new Set<string>();

    const dfs = (nodeId: string, path: string[]): void => {
      visited.add(nodeId);
      recStack.add(nodeId);
      path.push(nodeId);

      const outgoingArrows = this.context.outgoingArrows[nodeId] || [];
      for (const arrow of outgoingArrows) {
        const neighbor = this.getArrowTarget(arrow);
        if (!neighbor) continue;

        if (recStack.has(neighbor)) {
          const cycleStart = path.indexOf(neighbor);
          const cycle = [...path.slice(cycleStart), neighbor];
          cycles.push(cycle);
        } else if (!visited.has(neighbor)) {
          dfs(neighbor, [...path]);
        }
      }

      recStack.delete(nodeId);
    };

    for (const nodeId of Object.keys(this.context.nodesById)) {
      if (!visited.has(nodeId)) {
        dfs(nodeId, []);
      }
    }

    return cycles;
  }

  /**
   * Get the next nodes to execute after a given node
   */
  getNextNodes(nodeId: string, conditionValues: Record<string, boolean>): string[] {
    const outgoing = this.context.outgoingArrows[nodeId] || [];
    const nextNodes: string[] = [];

    console.log(`[DependencyResolver] Getting next nodes for ${nodeId}, outgoing arrows: ${outgoing.length}`);

    for (const arrow of outgoing) {
      const targetId = this.getArrowTarget(arrow);
      if (!targetId) continue;

      // Check condition branches
      const srcNode = this.context.nodesById[nodeId];
      if (srcNode && this.getNodeType(srcNode) === 'condition') {
        const branch = this.extractBranchFromArrow(arrow);
        const condValue = conditionValues[nodeId] || false;
        console.log(`[DependencyResolver] Condition ${nodeId}: branch=${branch}, condValue=${condValue}, target=${targetId}`);
        
        if (branch) {
          const skipArrow = (branch === 'true' && !condValue) || (branch === 'false' && condValue);
          console.log(`[DependencyResolver] Skip arrow check: (${branch} === 'true' && !${condValue}) || (${branch} === 'false' && ${condValue}) = ${skipArrow}`);
          if (skipArrow) {
            console.log(`[DependencyResolver] Skipping arrow to ${targetId} (wrong branch)`);
            continue;
          }
        }
      }

      console.log(`[DependencyResolver] Adding ${targetId} to next nodes`);
      nextNodes.push(targetId);
    }

    console.log(`[DependencyResolver] Next nodes for ${nodeId}: [${nextNodes.join(', ')}]`);
    return nextNodes;
  }

  /**
   * Get direct dependencies for a node
   */
  getDependencies(nodeId: string): string[] {
    const incomingArrows = this.context.incomingArrows[nodeId] || [];
    return incomingArrows
      .map(arrow => this.getArrowSource(arrow))
      .filter((source): source is string => source !== null);
  }

  /**
   * Perform topological sort
   */
  topologicalSort(): string[] {
    const visited = new Set<string>();
    const stack: string[] = [];

    const dfs = (nodeId: string): void => {
      visited.add(nodeId);

      const outgoingArrows = this.context.outgoingArrows[nodeId] || [];
      for (const arrow of outgoingArrows) {
        const neighbor = this.getArrowTarget(arrow);
        if (neighbor && !visited.has(neighbor)) {
          dfs(neighbor);
        }
      }

      stack.push(nodeId);
    };

    for (const nodeId of Object.keys(this.context.nodesById)) {
      if (!visited.has(nodeId)) {
        dfs(nodeId);
      }
    }

    return stack.reverse();
  }

  // Private helper methods

  private isStartNode(node: Record<string, any>): boolean {
    return node.type === 'start' || node.type === 'startNode';
  }

  private getNodeType(node: Record<string, any>): NodeType | null {
    try {
      return node.type as NodeType;
    } catch {
      return null;
    }
  }

  private isHandleFirstOnly(arrow: Record<string, any>): boolean {
    const targetHandle = arrow.targetHandle || '';
    if (targetHandle.endsWith('-input-first')) {
      return true;
    }
    return arrow.data?.handleMode === 'first_only';
  }

  private validateArrowDependency(
    arrow: Record<string, any>,
    targetNodeId: string,
    executedNodes: Set<string>,
    conditionValues: Record<string, boolean>
  ): ArrowValidation {
    const srcId = this.getArrowSource(arrow);
    if (!srcId) {
      return { isValid: false, arrow: arrow as DiagramArrow, reason: 'no_source' };
    }

    console.debug(`[Dependency Check] arrow from ${srcId} -> ${targetNodeId}`);

    // Get source node info
    const srcNode = this.context.nodesById[srcId];
    if (!srcNode) {
      return { isValid: false, arrow: arrow as DiagramArrow, reason: 'source_node_not_found' };
    }
    const srcType = this.getNodeType(srcNode);
    const isStartSource = srcType === 'start';
    const isConditionSource = srcType === 'condition';
    const hasData = executedNodes.has(srcId);

    // Handle first-only mode
    if (this.isHandleFirstOnly(arrow)) {
      return this.validateFirstOnlyArrow(arrow, targetNodeId, hasData);
    }

    // Handle regular dependencies
    if (!hasData && srcId !== targetNodeId && !isStartSource) {
      return { isValid: false, arrow: arrow as DiagramArrow, reason: 'missing_data' };
    }

    // Handle condition branches
    if (isConditionSource) {
      return this.validateConditionBranch(arrow, srcId, conditionValues);
    }

    return { isValid: true, arrow: arrow as DiagramArrow };
  }

  private validateFirstOnlyArrow(arrow: Record<string, any>, _targetNodeId: string, hasData: boolean): ArrowValidation {
    // This would need access to execution context state - for now simplified
    if (hasData) {
      return { isValid: true, arrow: arrow as DiagramArrow };
    }
    return { isValid: false, arrow: arrow as DiagramArrow, reason: 'first_only_no_data' };
  }

  private validateConditionBranch(arrow: Record<string, any>, srcId: string, conditionValues: Record<string, boolean>): ArrowValidation {
    const branch = this.extractBranchFromArrow(arrow);
    if (!branch) {
      return { isValid: true, arrow: arrow as DiagramArrow };
    }

    if (!(srcId in conditionValues)) {
      return { isValid: false, arrow: arrow as DiagramArrow, reason: 'condition_not_evaluated' };
    }

    const condValue = conditionValues[srcId];
    if ((branch === 'true' && !condValue) || (branch === 'false' && condValue)) {
      return { isValid: false, arrow: arrow as DiagramArrow, reason: 'wrong_branch' };
    }

    return { isValid: true, arrow: arrow as DiagramArrow };
  }

  private extractBranchFromArrow(arrow: Record<string, any>): string | null {
    // First check if branch is explicitly set in data
    const branch = arrow.data?.branch;
    if (branch) {
      return branch;
    }

    // Check label field
    const label = arrow.data?.label || '';
    if (label.toLowerCase() === 'true' || label.toLowerCase() === 'false') {
      return label.toLowerCase();
    }

    // Extract from sourceHandle (e.g., "conditionNode-WPKS8Q-output-true" -> "true")
    const sourceHandle = arrow.sourceHandle || '';
    if (sourceHandle.endsWith('-output-true')) {
      return 'true';
    } else if (sourceHandle.endsWith('-output-false')) {
      return 'false';
    }

    return null;
  }

  private canExecuteWithFirstOnly(
    node: Record<string, any>,
    _nodeId: string,
    incomingArrows: Record<string, any>[],
    executedNodes: Set<string>
  ): boolean {
    const nodeType = this.getNodeType(node);
    if (nodeType !== 'person_job' && nodeType !== 'job') {
      return false;
    }

    // NOTE: First-only consumption is tracked in the execution engine's TypedExecutionContext
    // The check happens there before marking the node for execution

    // Check if any first-only input has data
    for (const arrow of incomingArrows) {
      if (this.isHandleFirstOnly(arrow)) {
        const srcId = this.getArrowSource(arrow);
        if (srcId && executedNodes.has(srcId)) {
          return true;
        }
      }
    }

    return false;
  }

  private getArrowSource(arrow: Record<string, any>): string | null {
    return arrow.source || null;
  }

  private getArrowTarget(arrow: Record<string, any>): string | null {
    return arrow.target || null;
  }
}