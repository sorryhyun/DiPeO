/**
 * Job node executor - handles stateless operations like filtering and transformation
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext
} from '@/shared/types/execution';

import { ClientSafeExecutor } from '../base-executor';

export class JobExecutor extends ClientSafeExecutor {
  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
    const commonValidation = this.validateCommonInputs(node);
    if (!commonValidation.isValid) {
      return commonValidation;
    }

    const errors: string[] = [];

    // Validate job type
    const jobType = this.getNodeProperty(node, 'jobType', '');
    if (!jobType) {
      errors.push('Job type is required');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  async execute(node: Node, context: TypedExecutionContext, options?: any): Promise<ExecutorResult> {
    const jobType = this.getNodeProperty(node, 'jobType', '');
    const inputs = this.getInputValues(node, context);
    
    try {
      const result = await this.executeJob(jobType, inputs, node);
      
      return this.createSuccessResult(result, 0, {
        jobType,
        inputKeys: Object.keys(inputs),
        executedAt: new Date().toISOString()
      });
    } catch (error) {
      throw this.createExecutionError(
        `Failed to execute job: ${error instanceof Error ? error.message : String(error)}`,
        node,
        { jobType, inputs, error: error instanceof Error ? error.message : String(error) }
      );
    }
  }

  /**
   * Execute a specific job type
   */
  private async executeJob(jobType: string, inputs: Record<string, any>, node: Node): Promise<any> {
    switch (jobType.toLowerCase()) {
      case 'filter':
        return this.executeFilter(inputs, node);
      case 'transform':
        return this.executeTransform(inputs, node);
      case 'aggregate':
        return this.executeAggregate(inputs, node);
      case 'sort':
        return this.executeSort(inputs, node);
      default:
        throw new Error(`Unsupported job type: ${jobType}`);
    }
  }

  private executeFilter(inputs: Record<string, any>, node: Node): any {
    const data = this.getFirstInputValue(inputs);
    const filterExpression = this.getNodeProperty(node, 'filterExpression', '');
    
    if (!Array.isArray(data)) {
      throw new Error('Filter job requires array input');
    }

    if (!filterExpression) {
      return data; // No filter, return all
    }

    // Simple filtering - in production use a proper expression evaluator
    return data.filter(item => {
      try {
        return this.evaluateFilterExpression(filterExpression, item);
      } catch {
        return false;
      }
    });
  }

  private executeTransform(inputs: Record<string, any>, node: Node): any {
    const data = this.getFirstInputValue(inputs);
    const transformExpression = this.getNodeProperty(node, 'transformExpression', '');
    
    if (!transformExpression) {
      return data; // No transform, return as-is
    }

    if (Array.isArray(data)) {
      return data.map(item => this.applyTransform(transformExpression, item));
    } else {
      return this.applyTransform(transformExpression, data);
    }
  }

  private executeAggregate(inputs: Record<string, any>, node: Node): any {
    const data = this.getFirstInputValue(inputs);
    const aggregateType = this.getNodeProperty(node, 'aggregateType', 'count');
    const field = this.getNodeProperty(node, 'field', '');
    
    if (!Array.isArray(data)) {
      throw new Error('Aggregate job requires array input');
    }

    switch (aggregateType.toLowerCase()) {
      case 'count':
        return data.length;
      case 'sum':
        return data.reduce((sum, item) => sum + (field ? item[field] : item), 0);
      case 'avg':
        const total = data.reduce((sum, item) => sum + (field ? item[field] : item), 0);
        return total / data.length;
      case 'min':
        return Math.min(...data.map(item => field ? item[field] : item));
      case 'max':
        return Math.max(...data.map(item => field ? item[field] : item));
      default:
        throw new Error(`Unsupported aggregate type: ${aggregateType}`);
    }
  }

  private executeSort(inputs: Record<string, any>, node: Node): any {
    const data = this.getFirstInputValue(inputs);
    const sortField = this.getNodeProperty(node, 'sortField', '');
    const sortOrder = this.getNodeProperty(node, 'sortOrder', 'asc');
    
    if (!Array.isArray(data)) {
      throw new Error('Sort job requires array input');
    }

    const sortedData = [...data].sort((a, b) => {
      const aVal = sortField ? a[sortField] : a;
      const bVal = sortField ? b[sortField] : b;
      
      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return sortedData;
  }

  private getFirstInputValue(inputs: Record<string, any>): any {
    const values = Object.values(inputs);
    return values.length > 0 ? values[0] : null;
  }

  private evaluateFilterExpression(expression: string, item: any): boolean {
    // Simple filter evaluation - replace item properties in expression
    let evaluatedExpression = expression;
    
    if (typeof item === 'object' && item !== null) {
      for (const [key, value] of Object.entries(item)) {
        const regex = new RegExp(`\\b${key}\\b`, 'g');
        const stringValue = typeof value === 'string' ? `"${value}"` : String(value);
        evaluatedExpression = evaluatedExpression.replace(regex, stringValue);
      }
    }

    // Use simple boolean evaluation
    return this.evaluateSimpleBoolean(evaluatedExpression);
  }

  private applyTransform(expression: string, item: any): any {
    // Simple transform - in production use a proper template engine
    if (typeof item === 'object' && item !== null) {
      let result = expression;
      for (const [key, value] of Object.entries(item)) {
        const regex = new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g');
        result = result.replace(regex, String(value));
      }
      return result;
    }
    return item;
  }

  // Reuse the evaluateSimpleBoolean from ConditionExecutor
  private evaluateSimpleBoolean(expression: string): boolean {
    const cleaned = expression.trim();
    
    if (cleaned === 'true') return true;
    if (cleaned === 'false') return false;
    
    const comparisonOps = ['===', '!==', '==', '!=', '<=', '>=', '<', '>'];
    for (const op of comparisonOps) {
      if (cleaned.includes(op)) {
        const parts = cleaned.split(op).map(s => s.trim());
        if (parts.length === 2) {
          return this.compareValues(parts[0]!, parts[1]!, op);
        }
      }
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
    
    if ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
        (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
      return trimmed.slice(1, -1);
    }

    const num = Number(trimmed);
    if (!isNaN(num)) {
      return num;
    }

    if (trimmed === 'true') return true;
    if (trimmed === 'false') return false;

    return trimmed;
  }
}