/**
 * Execution domain service - manages diagram execution logic
 * Handles execution lifecycle, state management, and real-time updates
 */

import {
  Status,
  EventType,
  type ExecutionID,
  type DiagramID,
  type NodeID,
  type NodeState,
} from '@dipeo/models';
import { GraphQLService } from '../api/graphql';
import { Converters } from '../converters';
import { ExecuteDiagramDocument, ControlExecutionDocument, ExecutionUpdatesDocument } from '@/__generated__/graphql';

/**
 * Execution state management
 */
interface ExecutionState {
  id: ExecutionID;
  diagramId: DiagramID;
  status: Status;
  nodeStates: Map<NodeID, NodeState>;
  startedAt?: Date;
  endedAt?: Date;
  error?: string;
  result?: Record<string, any>;
}

/**
 * Execution domain service
 */
export class ExecutionService {
  private static activeExecutions = new Map<ExecutionID, ExecutionState>();
  private static subscriptions = new Map<ExecutionID, any>();

  /**
   * Start a new execution
   */
  static async startExecution(
    diagramId: DiagramID,
    inputData?: Record<string, any>,
  ): Promise<ExecutionID> {
    // Call GraphQL mutation
    const result = await GraphQLService.mutate(
      ExecuteDiagramDocument,
      {
        input: {
          diagram_id: diagramId,
          input_data: inputData,
        },
      },
    );

    const executionId = result.execute_diagram.execution.id as ExecutionID;

    // Initialize local state
    this.activeExecutions.set(executionId, {
      id: executionId,
      diagramId,
      status: Status.PENDING,
      nodeStates: new Map(),
      startedAt: new Date(),
    });

    // Subscribe to updates
    this.subscribeToUpdates(executionId);

    return executionId;
  }

  /**
   * Stop an execution
   */
  static async stopExecution(executionId: ExecutionID): Promise<void> {
    // Call GraphQL mutation
    await GraphQLService.mutate(
      ControlExecutionDocument,
      {
        input: {
          execution_id: executionId,
          action: 'STOP',
        },
      },
    );

    // Clean up local state
    this.cleanupExecution(executionId);
  }

  /**
   * Subscribe to execution updates
   */
  private static subscribeToUpdates(executionId: ExecutionID): void {
    const subscription = GraphQLService.subscribe(
      ExecutionUpdatesDocument,
      { executionId },
    ).subscribe({
      next: (data) => {
        this.handleExecutionUpdate(executionId, data.data.executionStateUpdate);
      },
      error: (error) => {
        console.error('Execution subscription error:', error);
        this.cleanupExecution(executionId);
      },
    });

    this.subscriptions.set(executionId, subscription);
  }

  /**
   * Handle execution state update
   */
  private static handleExecutionUpdate(
    executionId: ExecutionID,
    update: any,
  ): void {
    const execution = this.activeExecutions.get(executionId);
    if (!execution) return;

    // Update node state
    if (update.node_id && update.status) {
      execution.nodeStates.set(update.node_id, {
        status: update.status as Status,
        output: update.result,
        error: update.error,
        started_at: update.timestamp,
        ended_at: update.status === Status.COMPLETED ? update.timestamp : null,
      });
    }

    // Update overall execution state
    if (update.type === EventType.EXECUTION_STATUS_CHANGED && update.data?.status) {
      execution.status = update.data.status as Status;
    }

    // Check if execution completed
    if (execution.status === Status.COMPLETED ||
        execution.status === Status.FAILED) {
      execution.endedAt = new Date();
      this.cleanupExecution(executionId);
    }
  }

  /**
   * Clean up execution resources
   */
  private static cleanupExecution(executionId: ExecutionID): void {
    // Unsubscribe
    const subscription = this.subscriptions.get(executionId);
    if (subscription) {
      subscription.unsubscribe();
      this.subscriptions.delete(executionId);
    }

    // Remove from active executions after a delay
    setTimeout(() => {
      this.activeExecutions.delete(executionId);
    }, 5000);
  }

  /**
   * Get execution state
   */
  static getExecutionState(executionId: ExecutionID): ExecutionState | undefined {
    return this.activeExecutions.get(executionId);
  }

  /**
   * Get all active executions
   */
  static getActiveExecutions(): ExecutionState[] {
    return Array.from(this.activeExecutions.values());
  }

  /**
   * Calculate execution progress
   */
  static calculateProgress(execution: ExecutionState): number {
    if (execution.nodeStates.size === 0) return 0;

    let completed = 0;
    execution.nodeStates.forEach(state => {
      if (state.status === Status.COMPLETED) {
        completed++;
      }
    });

    return (completed / execution.nodeStates.size) * 100;
  }

  /**
   * Get execution duration
   */
  static getExecutionDuration(execution: ExecutionState): number {
    if (!execution.startedAt) return 0;

    const endTime = execution.endedAt || new Date();
    return endTime.getTime() - execution.startedAt.getTime();
  }

  /**
   * Format execution result for display
   */
  static formatExecutionResult(result: Record<string, any>): string {
    if (typeof result === 'string') {
      return result;
    }

    if (typeof result === 'object' && result !== null) {
      return JSON.stringify(result, null, 2);
    }

    return String(result);
  }

  /**
   * Get node execution order
   */
  static getExecutionOrder(execution: ExecutionState): NodeID[] {
    const order: NodeID[] = [];

    // Sort nodes by start time
    const sortedNodes = Array.from(execution.nodeStates.entries())
      .sort((a, b) => {
        const aTime = a[1].started_at ? new Date(a[1].started_at).getTime() : 0;
        const bTime = b[1].started_at ? new Date(b[1].started_at).getTime() : 0;
        return aTime - bTime;
      });

    sortedNodes.forEach(([nodeId]) => {
      order.push(nodeId);
    });

    return order;
  }

  /**
   * Check if execution can be retried
   */
  static canRetry(execution: ExecutionState): boolean {
    return execution.status === Status.FAILED;
  }

  /**
   * Retry a failed execution
   */
  static async retryExecution(executionId: ExecutionID): Promise<ExecutionID> {
    const execution = this.activeExecutions.get(executionId);
    if (!execution || !this.canRetry(execution)) {
      throw new Error('Execution cannot be retried');
    }

    // Start new execution with same parameters
    return this.startExecution(execution.diagramId);
  }
}
