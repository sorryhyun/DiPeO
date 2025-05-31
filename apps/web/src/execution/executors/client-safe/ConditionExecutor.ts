/**
 * Condition node executor - handles boolean logic and branching
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext
} from '@/shared/types/execution';

import { ClientSafeExecutor } from '../base-executor';

export class ConditionExecutor extends ClientSafeExecutor {
  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
    const commonValidation = this.validateCommonInputs(node);
    if (!commonValidation.isValid) {
      return commonValidation;
    }

    const errors: string[] = [];

    // Validate condition expression
    const condition = this.getNodeProperty(node, 'condition', '');
    if (!condition) {
      errors.push('Condition expression is required');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  async execute(node: Node, context: TypedExecutionContext, options?: any): Promise<ExecutorResult> {
    const condition = this.getNodeProperty(node, 'condition', '');
    const inputs = this.getInputValues(node, context);
    
    try {
      // Evaluate the condition using available inputs and context
      const result = this.evaluateCondition(condition, inputs, context);
      
      return this.createSuccessResult(result, 0, {
        condition,
        inputs,
        evaluatedAt: new Date().toISOString()
      });
    } catch (error) {
      throw this.createExecutionError(
        `Failed to evaluate condition: ${error instanceof Error ? error.message : String(error)}`,
        node,
        { condition, inputs, error: error instanceof Error ? error.message : String(error) }
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
    // Create evaluation context with inputs and node outputs
    const evaluationContext = {
      ...inputs,
      ...context.nodeOutputs,
      executionCount: context.nodeExecutionCounts
    };

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
}