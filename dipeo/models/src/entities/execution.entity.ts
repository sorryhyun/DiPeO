import { defineEntity } from '../entity-config';

export default defineEntity({
  name: 'Execution',
  plural: 'Executions',
  
  fields: {
    id: { type: 'ExecutionID', generated: true, required: true },
    status: { type: 'string', required: true }, // ExecutionStatus enum
    diagram_id: { type: 'DiagramID', nullable: true },
    started_at: { type: 'Date', required: true },
    ended_at: { type: 'Date', nullable: true },
    node_states: { type: 'JSON', required: true }, // Record<string, NodeState>
    node_outputs: { type: 'JSON', required: true }, // Record<string, Record<string, any>>
    token_usage: { type: 'JSON', required: true }, // TokenUsage
    error: { type: 'string', nullable: true },
    variables: { type: 'JSON', required: true },
    exec_counts: { type: 'JSON', required: true }, // Record<string, number>
    executed_nodes: { type: 'string[]', required: true }
  },
  
  relations: {
    diagram: {
      type: 'Diagram',
      relation: 'one-to-many',
      required: false
    }
  },
  
  operations: {
    create: {
      input: ['diagram_id', 'variables'],
      returnEntity: true
    },
    update: {
      input: ['status', 'node_states', 'node_outputs', 'token_usage', 'error', 'variables', 'exec_counts', 'executed_nodes', 'ended_at'],
      partial: true
    },
    delete: false,
    list: {
      filters: ['diagram_id', 'status'],
      sortable: ['started_at', 'ended_at'],
      pagination: true
    },
    get: true,
    custom: {
      updateNodeState: {
        name: 'updateNodeState',
        type: 'mutation',
        input: ['execution_id', 'node_id', 'state'],
        returns: 'ExecutionType',
        implementation: 'result = await execution_service.update_node_state(execution_id, node_id, state)\nreturn ExecutionType.from_pydantic(result)'
      },
      addNodeOutput: {
        name: 'addNodeOutput',
        type: 'mutation',
        input: ['execution_id', 'node_id', 'output'],
        returns: 'ExecutionType',
        implementation: 'result = await execution_service.add_node_output(execution_id, node_id, output)\nreturn ExecutionType.from_pydantic(result)'
      }
    }
  },
  
  features: {
    timestamps: false, // We have custom started_at/ended_at
    softDelete: false
  },
  
  // Map to the existing execution_service
  service: {
    name: 'execution_service',
    useCrudAdapter: true
  }
});