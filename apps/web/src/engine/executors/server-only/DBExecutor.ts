/**
 * DB executor - handles file I/O and database operations
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext
} from '@/shared/types/core';

import { ServerOnlyExecutor } from '../base-executor';
import { getApiUrl } from '@/shared/utils/apiConfig';

export class DBExecutor extends ServerOnlyExecutor {
  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
    const commonValidation = this.validateCommonInputs(node);
    if (!commonValidation.isValid) {
      return commonValidation;
    }

    const errors: string[] = [];

    // Validate sub type
    const subType = this.getNodeProperty(node, 'subType', '') as string;
    if (!subType) {
      errors.push('Database sub type is required');
    }

    const validSubTypes = ['file', 'fixed_prompt', 'api_tool'];
    if (subType && !validSubTypes.includes(subType)) {
      errors.push(`Invalid sub type. Must be one of: ${validSubTypes.join(', ')}`);
    }

    // Validate source details
    const sourceDetails = this.getNodeProperty(node, 'sourceDetails', '');
    if (!sourceDetails) {
      errors.push('Source details are required');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  async execute(node: Node, context: TypedExecutionContext, _options?: any): Promise<ExecutorResult> {
    const subType = this.getNodeProperty(node, 'subType', '') as string;
    const sourceDetails = this.getNodeProperty(node, 'sourceDetails', '');
    const inputs = this.getInputValues(node, context);
    
    try {
      const result = await this.executeDBOperation(subType, sourceDetails, inputs, node);
      
      return this.createSuccessResult(result, 0, {
        subType,
        sourceDetails,
        executedAt: new Date().toISOString()
      });
    } catch (error) {
      throw this.createExecutionError(
        `Failed to execute DB operation: ${error instanceof Error ? error.message : String(error)}`,
        node,
        { subType, sourceDetails, error: error instanceof Error ? error.message : String(error) }
      );
    }
  }

  /**
   * Execute database operation via backend API
   */
  private async executeDBOperation(
    subType: string,
    sourceDetails: string,
    inputs: Record<string, any>,
    node: Node
  ): Promise<any> {
    // Call backend API for DB operation execution
    const payload = {
      nodeId: node.id,
      sub_type: subType,
      source_details: sourceDetails,
      inputs
    };

    const response = await fetch(getApiUrl('/api/nodes/db/execute'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw this.createExecutionError(
        `DB operation API call failed: ${response.status} ${errorText}`,
        node,
        { 
          subType,
          sourceDetails,
          status: response.status,
          error: errorText
        }
      );
    }

    const result = await response.json();
    
    // Return the result from the API
    return result.output || result.data || result;
  }
}