/**
 * Execution Converter Module
 *
 * Handles conversions for execution states and updates.
 * Manages transformations between GraphQL, Domain, and Store representations.
 */

import {
  type ExecutionID,
  type DiagramID,
  type NodeID,
  type ExecutionState,
  type NodeState,
  type ExecutionUpdate,
  type LLMUsage,
  type SerializedNodeOutput,
  Status,
  EventType
} from '@dipeo/models';
import type {
  ExecutionStateType,
  ExecutionUpdate as GraphQLExecutionUpdate
} from '@/__generated__/graphql';
import { executionId, diagramId, nodeId } from '@/infrastructure/types/branded';

// Store-specific execution state (optimized for Zustand)
export interface StoreExecutionState {
  id: string | null;
  isRunning: boolean;
  isPaused: boolean;
  runningNodes: Set<NodeID>;
  nodeStates: Map<NodeID, StoreNodeState>;
  context: Record<string, unknown>;
}

// Store-specific node state
export interface StoreNodeState {
  status: Status;
  error?: string;
  timestamp: number;
  skipReason?: string;
}

export class ExecutionConverter {
  /**
   * Convert GraphQL execution state to domain
   */
  static toDomain(graphqlExecution: ExecutionStateType): ExecutionState {
    const nodeStates: Record<string, NodeState> = {};

    if (graphqlExecution.node_states) {
      Object.entries(graphqlExecution.node_states).forEach(([nodeId, state]) => {
        if (state) {
          const nodeState = state as any;
          nodeStates[nodeId] = {
            status: nodeState.status as Status,
            started_at: nodeState.started_at,
            ended_at: nodeState.ended_at,
            error: nodeState.error,
            llm_usage: nodeState.llm_usage as LLMUsage | null
          };
        }
      });
    }

    return {
      id: executionId(graphqlExecution.id),
      status: graphqlExecution.status as Status,
      diagram_id: graphqlExecution.diagram_id ? diagramId(graphqlExecution.diagram_id) : null,
      started_at: graphqlExecution.started_at,
      ended_at: graphqlExecution.ended_at,
      node_states: nodeStates,
      node_outputs: graphqlExecution.node_outputs || {},
      variables: graphqlExecution.variables || {},
      llm_usage: graphqlExecution.llm_usage as LLMUsage,
      error: graphqlExecution.error,
      exec_counts: {},
      executed_nodes: []
    };
  }

  /**
   * Convert GraphQL execution update to domain
   */
  static updateToDomain(update: GraphQLExecutionUpdate): ExecutionUpdate {
    return {
      type: (update as any).event_type as EventType || EventType.EXECUTION_UPDATE,
      execution_id: executionId(update.execution_id),
      data: update.data,
      timestamp: update.timestamp
    };
  }

  /**
   * Convert domain execution state to store format
   */
  static toStore(domainExecution: ExecutionState): StoreExecutionState {
    const nodeStates = new Map<NodeID, StoreNodeState>();
    const runningNodes = new Set<NodeID>();

    Object.entries(domainExecution.node_states).forEach(([nodeId, state]) => {
      const id = nodeId as NodeID;
      nodeStates.set(id, {
        status: state.status,
        error: state.error || undefined,
        timestamp: state.started_at ? new Date(state.started_at).getTime() : Date.now(),
        skipReason: undefined
      });

      if (state.status === Status.RUNNING) {
        runningNodes.add(id);
      }
    });

    return {
      id: domainExecution.id,
      isRunning: domainExecution.status === Status.RUNNING,
      isPaused: domainExecution.status === Status.PAUSED,
      runningNodes,
      nodeStates,
      context: domainExecution.node_outputs
    };
  }

  /**
   * Convert store execution state to domain
   */
  static fromStore(
    storeExecution: StoreExecutionState,
    diagramId?: DiagramID
  ): ExecutionState {
    const nodeStates: Record<string, NodeState> = {};
    let hasFailed = false;

    storeExecution.nodeStates.forEach((state, nodeId) => {
      const timestamp = new Date(state.timestamp);
      nodeStates[nodeId] = {
        status: state.status,
        started_at: timestamp.toISOString(),
        ended_at: state.status !== Status.RUNNING
          ? timestamp.toISOString()
          : null,
        error: state.error || null,
        llm_usage: null
      };

      if (state.status === Status.FAILED) {
        hasFailed = true;
      }
    });

    let status: Status;
    if (storeExecution.isPaused) {
      status = Status.PAUSED;
    } else if (storeExecution.isRunning) {
      status = Status.RUNNING;
    } else {
      status = hasFailed ? Status.FAILED : Status.COMPLETED;
    }

    return {
      id: executionId(storeExecution.id || ''),
      status,
      diagram_id: diagramId || null,
      started_at: new Date().toISOString(),
      ended_at: status === Status.COMPLETED || status === Status.FAILED
        ? new Date().toISOString()
        : null,
      node_states: nodeStates,
      node_outputs: {} as Record<string, SerializedNodeOutput>,
      variables: {},
      llm_usage: { input: 0, output: 0, cached: null, total: 0 },
      error: null,
      exec_counts: {},
      executed_nodes: Array.from(storeExecution.nodeStates.keys())
    };
  }

  /**
   * Process execution update and update store state
   */
  static processUpdate(
    currentState: StoreExecutionState,
    update: ExecutionUpdate
  ): StoreExecutionState {
    const newState = { ...currentState };

    // Handle different update types
    if (update.type === EventType.NODE_STATUS_CHANGED && update.data?.node_id) {
      const id = nodeId(update.data.node_id);
      const status = update.data.status as Status;

      if (status === Status.RUNNING) {
        newState.runningNodes.add(id);
        newState.nodeStates.set(id, {
          status: Status.RUNNING,
          timestamp: Date.now()
        });
      } else if (status === Status.COMPLETED) {
        newState.runningNodes.delete(id);
        const nodeState = newState.nodeStates.get(id);
        if (nodeState) {
          nodeState.status = Status.COMPLETED;
          nodeState.timestamp = Date.now();
        }
        if (update.data.output) {
          newState.context[id] = update.data.output;
        }
      } else if (status === Status.FAILED) {
        newState.runningNodes.delete(id);
        newState.nodeStates.set(id, {
          status: Status.FAILED,
          error: update.data.error || 'Unknown error',
          timestamp: Date.now()
        });
      }
    } else if (update.type === EventType.EXECUTION_STATUS_CHANGED) {
      const status = update.data?.status as Status;
      if (status === Status.COMPLETED || status === Status.FAILED) {
        newState.isRunning = false;
        newState.runningNodes.clear();
      }
    }

    return newState;
  }

  /**
   * Create initial execution state
   */
  static createInitialState(executionId?: string): StoreExecutionState {
    return {
      id: executionId || null,
      isRunning: false,
      isPaused: false,
      runningNodes: new Set(),
      nodeStates: new Map(),
      context: {}
    };
  }
}
