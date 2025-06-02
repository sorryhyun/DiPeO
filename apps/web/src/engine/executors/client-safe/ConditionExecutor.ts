/**
 * Condition node executor - handles boolean logic and branching
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext
} from '@/shared/types/core';

import { ClientSafeExecutor } from '../base-executor';

export class ConditionExecutor extends ClientSafeExecutor {
  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
    const commonValidation = this.validateCommonInputs(node);
    if (!commonValidation.isValid) {
      return commonValidation;
    }

    const errors: string[] = [];

    // Check condition type
    const conditionType = this.getNodeProperty(node, 'conditionType', 'expression');
    
    if (conditionType === 'expression') {
      // Validate condition expression
      const condition = this.getNodeProperty(node, 'expression', '');
      if (!condition) {
        errors.push('Condition expression is required');
      }
    } else if (conditionType === 'max_iterations') {
      // No specific validation needed for max_iterations type
    } else {
      errors.push(`Invalid condition type: ${conditionType}`);
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  async execute(node: Node, context: TypedExecutionContext, options?: any): Promise<ExecutorResult> {
    const conditionType = this.getNodeProperty(node, 'conditionType', 'expression') as string;
    const inputs = this.getInputValues(node, context);
    
    try {
      let result: boolean;
      
      if (conditionType === 'max_iterations') {
        // Check if any preceding nodes have reached max iterations
        result = this.checkPrecedingNodesMaxIterations(node, context);
      } else {
        // Default to expression evaluation
        const expression = this.getNodeProperty(node, 'expression', '');
        result = this.evaluateCondition(expression, inputs, context);
      }
      
      return this.createSuccessResult(result, 0, {
        conditionType,
        inputs,
        evaluatedAt: new Date().toISOString()
      });
    } catch (error) {
      throw this.createExecutionError(
        `Failed to evaluate condition: ${error instanceof Error ? error.message : String(error)}`,
        node,
        { conditionType, inputs, error: error instanceof Error ? error.message : String(error) }
      );
    }
  }

  /**
   * Evaluate a condition expression
   */
  private evaluateCondition(
    condition: string, 
    inputs: Record<string, any>, 
    context: TypedExecutionContext
  ): boolean {
    // Create evaluation context with inputs and flattened node outputs
    const evaluationContext: Record<string, any> = {
      ...inputs,
      executionCount: context.nodeExecutionCounts
    };

    // Flatten node outputs to make their properties directly accessible
    for (const [nodeId, nodeOutput] of Object.entries(context.nodeOutputs)) {
      if (typeof nodeOutput === 'object' && nodeOutput !== null) {
        // Spread object properties to make them accessible (e.g., {counter: 1} -> counter: 1)
        Object.assign(evaluationContext, nodeOutput);
      } else {
        // For primitive values, use the node ID as key
        evaluationContext[nodeId] = nodeOutput;
      }
    }

    console.log(`[ConditionExecutor] Evaluating "${condition}" with context:`, evaluationContext);

    // Simple expression evaluation
    // In production, you'd want to use a more robust expression evaluator
    return this.evaluateExpression(condition, evaluationContext);
  }

  /**
   * Simple expression evaluator for conditions
   */
  private evaluateExpression(expression: string, context: Record<string, any>): boolean {
    // Replace variables in the expression
    let evaluatedExpression = expression;
    
    for (const [key, value] of Object.entries(context)) {
      const regex = new RegExp(`\\b${key}\\b`, 'g');
      const stringValue = typeof value === 'string' ? `"${value}"` : String(value);
      evaluatedExpression = evaluatedExpression.replace(regex, stringValue);
    }

    // Handle basic comparisons and boolean logic
    try {
      // This is a simplified evaluator - in production use a proper expression parser
      return this.evaluateSimpleBoolean(evaluatedExpression);
    } catch (error) {
      console.warn(`Failed to evaluate expression "${expression}":`, error);
      return false;
    }
  }

  private evaluateSimpleBoolean(expression: string): boolean {
    const cleaned = expression.trim();
    
    // Handle boolean literals
    if (cleaned === 'true') return true;
    if (cleaned === 'false') return false;
    
    // Handle simple comparisons
    const comparisonOps = ['===', '!==', '==', '!=', '<=', '>=', '<', '>'];
    for (const op of comparisonOps) {
      if (cleaned.includes(op)) {
        const parts = cleaned.split(op).map(s => s.trim());
        if (parts.length === 2) {
          return this.compareValues(parts[0]!, parts[1]!, op);
        }
      }
    }

    // Handle logical operators
    if (cleaned.includes('&&')) {
      const parts = cleaned.split('&&').map(s => s.trim());
      return parts.every(part => this.evaluateSimpleBoolean(part));
    }

    if (cleaned.includes('||')) {
      const parts = cleaned.split('||').map(s => s.trim());
      return parts.some(part => this.evaluateSimpleBoolean(part));
    }

    return false;
  }

  private compareValues(left: string, right: string, operator: string): boolean {
    const leftVal = this.parseValue(left || '');
    const rightVal = this.parseValue(right || '');

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

    return trimmed;
  }

  /**
   * Check if any preceding nodes have reached their max iterations
   */
  private checkPrecedingNodesMaxIterations(node: Node, context: TypedExecutionContext): boolean {
    // Get all incoming nodes
    const incomingArrows = context.incomingArrows[node.id] || [];
    
    // Check all directly connected source nodes
    for (const arrow of incomingArrows) {
      const sourceNodeId = arrow.source;
      if (!sourceNodeId) continue;
      
      const sourceNode = context.nodesById[sourceNodeId];
      if (!sourceNode) continue;
      
      // Check if this node has max iterations defined and has reached them
      const executionCount = context.nodeExecutionCounts[sourceNodeId] || 0;
      const maxIterations = sourceNode.data?.iterationCount || sourceNode.data?.maxIterations;
      
      if (maxIterations && executionCount >= maxIterations) {
        console.log(`[ConditionExecutor] Node ${sourceNodeId} has reached max iterations (${executionCount}/${maxIterations})`);
        return true;
      }
    }
    
    // Also check for any nodes that might be in a cycle with this condition node
    // Look for nodes that feed back to the same nodes this condition feeds to
    const outgoingArrows = context.outgoingArrows[node.id] || [];
    for (const outArrow of outgoingArrows) {
      const targetNodeId = outArrow.target;
      if (!targetNodeId) continue;
      
      // Find nodes that connect to this same target (potential loop participants)
      for (const [nodeId, nodeArrows] of Object.entries(context.outgoingArrows)) {
        if (nodeId === node.id) continue; // Skip self
        
        const nodeConnectsToSameTarget = nodeArrows.some(arrow => arrow.target === targetNodeId);
        if (nodeConnectsToSameTarget) {
          const loopNode = context.nodesById[nodeId];
          if (!loopNode) continue;
          
          const executionCount = context.nodeExecutionCounts[nodeId] || 0;
          const maxIterations = loopNode.data?.iterationCount || loopNode.data?.maxIterations;
          
          if (maxIterations && executionCount >= maxIterations) {
            console.log(`[ConditionExecutor] Loop participant ${nodeId} has reached max iterations (${executionCount}/${maxIterations})`);
            return true;
          }
        }
      }
    }
    
    // No nodes have reached max iterations
    return false;
  }
}