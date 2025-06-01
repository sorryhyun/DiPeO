/**
 * Centralized skip decision making for node execution.
 * 
 * This class manages which nodes should be skipped during execution and why,
 * providing a single source of truth for skip decisions across the system.
 */
export class SkipManager {
  private skipReasons: Map<string, string> = new Map();
  private skippedNodes: Set<string> = new Set();

  /**
   * Single source of truth for skip decisions.
   * 
   * @param nodeId - The unique identifier of the node
   * @param executionCount - How many times this node has been executed
   * @param maxIterations - Maximum allowed iterations for the node
   * @returns True if the node should be skipped, False otherwise
   */
  shouldSkip(nodeId: string, executionCount: number, maxIterations?: number): boolean {
    if (maxIterations && executionCount >= maxIterations) {
      this.markSkipped(nodeId, 'max_iterations_reached');
      return true;
    }
    return false;
  }

  /**
   * Evaluate a condition expression and determine if node should be skipped based on result
   * 
   * @param condition - The condition expression to evaluate
   * @param context - Context variables for evaluation
   * @returns Boolean result of the condition
   */
  evaluateCondition(condition: string, context: Record<string, any>): boolean {
    try {
      // Simple expression evaluation - in production this would use a proper expression parser
      // For now, handle basic comparisons and boolean expressions
      
      // Replace variables in the condition with their values
      let evaluatedCondition = condition;
      for (const [key, value] of Object.entries(context)) {
        const regex = new RegExp(`\\b${key}\\b`, 'g');
        const stringValue = typeof value === 'string' ? `"${value}"` : String(value);
        evaluatedCondition = evaluatedCondition.replace(regex, stringValue);
      }

      // Basic evaluation - in production use a proper expression evaluator
      // This is a simplified version for common cases
      return this.evaluateSimpleExpression(evaluatedCondition);
    } catch (error) {
      console.warn(`Failed to evaluate condition "${condition}":`, error);
      return false;
    }
  }

  /**
   * Mark a node as skipped with a reason.
   * 
   * @param nodeId - The unique identifier of the node
   * @param reason - The reason why this node was skipped
   */
  markSkipped(nodeId: string, reason: string): void {
    this.skippedNodes.add(nodeId);
    this.skipReasons.set(nodeId, reason);
  }

  /**
   * Check if a node has been marked as skipped.
   * 
   * @param nodeId - The unique identifier of the node
   * @returns True if the node is marked as skipped
   */
  isSkipped(nodeId: string): boolean {
    return this.skippedNodes.has(nodeId);
  }

  /**
   * Get the reason why a node was skipped.
   * 
   * @param nodeId - The unique identifier of the node
   * @returns The skip reason if node was skipped, undefined otherwise
   */
  getSkipReason(nodeId: string): string | undefined {
    return this.skipReasons.get(nodeId);
  }

  /**
   * Clear all skip information.
   */
  clear(): void {
    this.skipReasons.clear();
    this.skippedNodes.clear();
  }

  /**
   * Get all skipped nodes and their reasons.
   * 
   * @returns Object mapping node_id to skip reason
   */
  getAllSkippedNodes(): Record<string, string> {
    return Object.fromEntries(this.skipReasons);
  }

  /**
   * Check if a node should be skipped based on a condition
   * 
   * @param nodeId - The node ID
   * @param condition - The condition to evaluate
   * @param context - Context for condition evaluation
   * @returns True if the node should be skipped
   */
  shouldSkipBasedOnCondition(nodeId: string, condition: string, context: Record<string, any>): boolean {
    try {
      const result = this.evaluateCondition(condition, context);
      if (!result) {
        this.markSkipped(nodeId, 'condition_not_met');
        return true;
      }
      return false;
    } catch (error) {
      this.markSkipped(nodeId, 'condition_evaluation_error');
      return true;
    }
  }

  /**
   * Simple expression evaluator for basic conditions
   * This is a simplified version - in production use a proper expression parser
   */
  private evaluateSimpleExpression(expression: string): boolean {
    // Remove whitespace
    const cleanExpr = expression.trim();

    // Handle boolean literals
    if (cleanExpr === 'true') return true;
    if (cleanExpr === 'false') return false;

    // Handle simple comparisons
    const comparisonOps = ['===', '!==', '==', '!=', '<=', '>=', '<', '>'];
    for (const op of comparisonOps) {
      if (cleanExpr.includes(op)) {
        const parts = cleanExpr.split(op).map(s => s.trim());
        const left = parts[0];
        const right = parts[1];
        if (left && right) {
          return this.compareValues(left, right, op);
        }
      }
    }

    // Handle logical operators
    if (cleanExpr.includes('&&')) {
      const parts = cleanExpr.split('&&').map(s => s.trim());
      return parts.every(part => this.evaluateSimpleExpression(part));
    }

    if (cleanExpr.includes('||')) {
      const parts = cleanExpr.split('||').map(s => s.trim());
      return parts.some(part => this.evaluateSimpleExpression(part));
    }

    // Default to false for unrecognized expressions
    return false;
  }

  private compareValues(left: string, right: string, operator: string): boolean {
    const leftVal = this.parseValue(left);
    const rightVal = this.parseValue(right);

    switch (operator) {
      case '===':
      case '==':
        return leftVal === rightVal;
      case '!==':
      case '!=':
        return leftVal !== rightVal;
      case '<':
        return leftVal < rightVal;
      case '<=':
        return leftVal <= rightVal;
      case '>':
        return leftVal > rightVal;
      case '>=':
        return leftVal >= rightVal;
      default:
        return false;
    }
  }

  private parseValue(value: string): any {
    const trimmed = value.trim();
    
    // Remove quotes for strings
    if ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
        (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
      return trimmed.slice(1, -1);
    }

    // Parse numbers
    const num = Number(trimmed);
    if (!isNaN(num)) {
      return num;
    }

    // Parse booleans
    if (trimmed === 'true') return true;
    if (trimmed === 'false') return false;

    // Return as string
    return trimmed;
  }
}