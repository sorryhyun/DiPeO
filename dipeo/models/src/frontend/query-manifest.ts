import { EntityQueryConfig, QueryManifest } from './query-specifications';
import { CrudOperation } from './query-enums';
import { diagramRelationships, nodeRelationships } from './relationship-queries';

export const defaultDiagramFields = [
  { name: 'nodes', required: true, fields: [
    { name: 'id', required: true },
    { name: 'type', required: true },
    { name: 'position', required: true, fields: [
      { name: 'x', required: true },
      { name: 'y', required: true }
    ]},
    { name: 'data', required: true }
  ]},
  { name: 'handles', required: true, fields: [
    { name: 'id', required: true },
    { name: 'node_id', required: true },
    { name: 'label', required: true },
    { name: 'direction', required: true },
    { name: 'data_type', required: true },
    { name: 'position', required: true }
  ]},
  { name: 'arrows', required: true, fields: [
    { name: 'id', required: true },
    { name: 'source', required: true },
    { name: 'target', required: true },
    { name: 'content_type', required: true },
    { name: 'label', required: false },
    { name: 'data', required: false }
  ]},
  { name: 'persons', required: true, fields: [
    { name: 'id', required: true },
    { name: 'label', required: true },
    { name: 'llm_config', required: true, fields: [
      { name: 'service', required: true },
      { name: 'model', required: true },
      { name: 'api_key_id', required: false },
      { name: 'system_prompt', required: false }
    ]},
    { name: 'type', required: true }
  ]},
  { name: 'metadata', required: true, fields: [
    { name: 'id', required: true },
    { name: 'name', required: true },
    { name: 'description', required: false },
    { name: 'version', required: true },
    { name: 'created', required: true },
    { name: 'modified', required: true },
    { name: 'author', required: false },
    { name: 'tags', required: false }
  ]}
];

export const defaultPersonFields = [
  { name: 'id', required: true },
  { name: 'label', required: true },
  { name: 'llm_config', required: true, fields: [
    { name: 'service', required: true },
    { name: 'model', required: true },
    { name: 'api_key_id', required: false },
    { name: 'system_prompt', required: false }
  ]},
  { name: 'type', required: true }
];

export const defaultExecutionFields = [
  { name: 'id', required: true },
  { name: 'status', required: true },
  { name: 'diagram_id', required: true },
  { name: 'started_at', required: true },
  { name: 'ended_at', required: false },
  { name: 'node_states', required: false },
  { name: 'node_outputs', required: false },
  { name: 'variables', required: false },
  { name: 'token_usage', required: false, fields: [
    { name: 'input', required: true },
    { name: 'output', required: true },
    { name: 'cached', required: true }
  ]},
  { name: 'error', required: false },
  { name: 'duration_seconds', required: false },
  { name: 'is_active', required: true }
];

export const defaultNodeFields = [
  { name: 'id', required: true },
  { name: 'type', required: true },
  { name: 'position', required: true, fields: [
    { name: 'x', required: true },
    { name: 'y', required: true }
  ]},
  { name: 'data', required: true }
];

export const queryManifest: QueryManifest = {
  version: '1.0.0',
  entities: [
    {
      entity: 'Diagram',
      operations: [CrudOperation.GET, CrudOperation.LIST, CrudOperation.CREATE, CrudOperation.UPDATE, CrudOperation.DELETE],
      defaultFields: defaultDiagramFields,
      relationships: diagramRelationships.map(rel => ({
        name: rel.field,
        type: rel.targetEntity,
        fields: rel.defaultFields?.map(f => ({ name: f, required: true })) || []
      }))
    },
    {
      entity: 'Person',
      operations: [CrudOperation.GET, CrudOperation.LIST, CrudOperation.CREATE, CrudOperation.UPDATE, CrudOperation.DELETE],
      defaultFields: defaultPersonFields
    },
    {
      entity: 'Execution',
      operations: [CrudOperation.GET, CrudOperation.LIST, CrudOperation.SUBSCRIBE],
      defaultFields: defaultExecutionFields,
      relationships: [
        {
          name: 'results',
          type: 'ExecutionResult',
          fields: [
            { name: 'nodeId', required: true },
            { name: 'output', required: true },
            { name: 'error', required: false }
          ]
        },
        {
          name: 'logs',
          type: 'ExecutionLog',
          fields: [
            { name: 'timestamp', required: true },
            { name: 'level', required: true },
            { name: 'message', required: true }
          ]
        }
      ]
    },
    {
      entity: 'Node',
      operations: [CrudOperation.GET, CrudOperation.LIST, CrudOperation.UPDATE],
      defaultFields: defaultNodeFields,
      relationships: nodeRelationships.map(rel => ({
        name: rel.field,
        type: rel.targetEntity,
        fields: rel.defaultFields?.map(f => ({ name: f, required: true })) || []
      }))
    },
    {
      entity: 'APIKey',
      operations: [CrudOperation.LIST, CrudOperation.CREATE, CrudOperation.DELETE],
      defaultFields: [
        { name: 'id', required: true },
        { name: 'name', required: true },
        { name: 'prefix', required: true },
        { name: 'createdAt', required: true },
        { name: 'lastUsedAt', required: false }
      ]
    }
  ]
};
