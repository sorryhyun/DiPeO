/**
 * Client-safe executors that can run in the browser environment
 * These executors handle pure computation and logic without external API calls
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext
} from '@/shared/types/execution';

import { ClientSafeExecutor } from './base-executor';

/**
 * Start node executor - initializes execution flow
 */
export class StartExecutor extends ClientSafeExecutor {
  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
    const commonValidation = this.validateCommonInputs(node);
    if (!commonValidation.isValid) {
      return commonValidation;
    }

    // Start nodes should not have incoming connections
    const incomingArrows = context.incomingArrows[node.id] || [];
    if (incomingArrows.length > 0) {
      return {
        isValid: false,
        errors: ['Start nodes should not have incoming connections']
      };
    }

    return { isValid: true, errors: [] };
  }

  async execute(node: Node, context: TypedExecutionContext, options?: any): Promise<ExecutorResult> {
    // Start nodes can have initial data
    const initialData = this.getNodeProperty(node, 'initialData', {});
    
    return this.createSuccessResult(initialData, 0, {
      executionTime: Date.now() - context.startTime,
      isStartNode: true
    });
  }
}

/**
 * Condition node executor - handles boolean logic and branching
 */
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
        `Failed to evaluate condition: ${error.message}`,
        node,
        { condition, inputs, error: error.message }
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
        const [left, right] = cleaned.split(op).map(s => s.trim());
        return this.compareValues(left, right, op);
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

    return trimmed;
  }
}

/**
 * Job node executor - handles stateless operations like filtering and transformation
 */
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
        `Failed to execute job: ${error.message}`,
        node,
        { jobType, inputs, error: error.message }
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
        const [left, right] = cleaned.split(op).map(s => s.trim());
        return this.compareValues(left, right, op);
      }
    }

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

/**
 * Endpoint node executor - handles output and finalization
 */
export class EndpointExecutor extends ClientSafeExecutor {
  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
    const commonValidation = this.validateCommonInputs(node);
    if (!commonValidation.isValid) {
      return commonValidation;
    }

    // Endpoint nodes should have incoming connections
    const incomingArrows = context.incomingArrows[node.id] || [];
    if (incomingArrows.length === 0) {
      return {
        isValid: false,
        errors: ['Endpoint nodes should have at least one incoming connection']
      };
    }

    return { isValid: true, errors: [] };
  }

  async execute(node: Node, context: TypedExecutionContext, options?: any): Promise<ExecutorResult> {
    const inputs = this.getInputValues(node, context);
    const outputFormat = this.getNodeProperty(node, 'outputFormat', 'json');
    
    try {
      const output = this.formatOutput(inputs, outputFormat, node);
      
      return this.createSuccessResult(output, 0, {
        outputFormat,
        inputCount: Object.keys(inputs).length,
        finalizedAt: new Date().toISOString(),
        isEndpoint: true
      });
    } catch (error) {
      throw this.createExecutionError(
        `Failed to format endpoint output: ${error.message}`,
        node,
        { outputFormat, inputs, error: error.message }
      );
    }
  }

  /**
   * Format the output according to the specified format
   */
  private formatOutput(inputs: Record<string, any>, format: string, node: Node): any {
    switch (format.toLowerCase()) {
      case 'json':
        return this.formatAsJSON(inputs);
      case 'text':
        return this.formatAsText(inputs, node);
      case 'csv':
        return this.formatAsCSV(inputs);
      case 'raw':
        return this.formatAsRaw(inputs);
      default:
        return inputs; // Default to raw inputs
    }
  }

  private formatAsJSON(inputs: Record<string, any>): string {
    return JSON.stringify(inputs, null, 2);
  }

  private formatAsText(inputs: Record<string, any>, node: Node): string {
    const template = this.getNodeProperty(node, 'textTemplate', '');
    
    if (template) {
      // Apply template with inputs
      let result = template;
      for (const [key, value] of Object.entries(inputs)) {
        const regex = new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g');
        result = result.replace(regex, String(value));
      }
      return result;
    }

    // Default text format
    return Object.entries(inputs)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n');
  }

  private formatAsCSV(inputs: Record<string, any>): string {
    // Simple CSV format - assumes inputs contain arrays or objects
    const firstValue = Object.values(inputs)[0];
    
    if (Array.isArray(firstValue) && firstValue.length > 0 && typeof firstValue[0] === 'object') {
      // Array of objects -> CSV
      const headers = Object.keys(firstValue[0]);
      const csvRows = [
        headers.join(','),
        ...firstValue.map(row => 
          headers.map(header => JSON.stringify(row[header] || '')).join(',')
        )
      ];
      return csvRows.join('\n');
    }

    // Fallback: convert inputs to simple CSV
    const headers = Object.keys(inputs);
    const values = Object.values(inputs);
    return `${headers.join(',')}\n${values.map(v => JSON.stringify(v)).join(',')}`;
  }

  private formatAsRaw(inputs: Record<string, any>): any {
    // Return the first input value if there's only one, otherwise return all inputs
    const values = Object.values(inputs);
    return values.length === 1 ? values[0] : inputs;
  }
}