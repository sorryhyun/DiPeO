import { QuerySpecification } from './query-specifications';
import { QueryOperationType } from './query-enums';

export const createSubscriptionSpec = (
  entity: string, 
  event: string,
  fields: string[]
): QuerySpecification => ({
  name: `on${entity}${event}`,
  operation: QueryOperationType.SUBSCRIPTION,
  entityType: entity,
  description: `Subscribe to ${entity} ${event} events`,
  variables: [
    {
      name: 'filter',
      type: `${entity}SubscriptionFilter`,
      required: false
    }
  ],
  returnType: `${entity}${event}Payload`,
  fields: fields.map(f => ({ name: f, required: true }))
});

export const createExecutionSubscriptionSpec = (): QuerySpecification => ({
  name: 'onExecutionUpdate',
  operation: QueryOperationType.SUBSCRIPTION,
  entityType: 'Execution',
  description: 'Subscribe to execution status updates',
  variables: [
    {
      name: 'executionId',
      type: 'ID!',
      required: true
    }
  ],
  returnType: 'ExecutionUpdate',
  fields: [
    { name: 'id', required: true },
    { name: 'status', required: true },
    { name: 'progress', required: false },
    { 
      name: 'results',
      required: false,
      fields: [
        { name: 'nodeId', required: true },
        { name: 'output', required: true },
        { name: 'error', required: false }
      ]
    },
    {
      name: 'logs',
      required: false,
      fields: [
        { name: 'timestamp', required: true },
        { name: 'level', required: true },
        { name: 'message', required: true }
      ]
    }
  ]
});