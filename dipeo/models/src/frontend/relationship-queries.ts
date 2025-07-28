import { QueryField, QuerySpecification } from './query-specifications';

export interface RelationshipConfig {
  field: string;
  type: 'one-to-one' | 'one-to-many' | 'many-to-many';
  targetEntity: string;
  includeByDefault?: boolean;
  defaultFields?: string[];
}

export const createRelationshipField = (
  config: RelationshipConfig
): QueryField => {
  const baseFields = config.defaultFields || ['id', 'name'];
  
  return {
    name: config.field,
    required: false,
    fields: baseFields.map(f => ({ name: f, required: true }))
  };
};

export const createNestedQueryField = (
  parentEntity: string,
  relationship: string,
  fields: QueryField[]
): QueryField => ({
  name: relationship,
  required: false,
  fields: fields
});

export const createConnectionField = (
  fieldName: string,
  nodeFields: QueryField[]
): QueryField => ({
  name: fieldName,
  required: false,
  fields: [
    {
      name: 'edges',
      required: true,
      fields: [
        {
          name: 'node',
          required: true,
          fields: nodeFields
        },
        { name: 'cursor', required: false }
      ]
    },
    {
      name: 'pageInfo',
      required: false,
      fields: [
        { name: 'hasNextPage', required: true },
        { name: 'hasPreviousPage', required: true },
        { name: 'startCursor', required: false },
        { name: 'endCursor', required: false }
      ]
    },
    { name: 'totalCount', required: false }
  ]
});

export const diagramRelationships: RelationshipConfig[] = [
  {
    field: 'nodes',
    type: 'one-to-many',
    targetEntity: 'Node',
    includeByDefault: true,
    defaultFields: ['id', 'type', 'position', 'data']
  },
  {
    field: 'arrows',
    type: 'one-to-many',
    targetEntity: 'Arrow',
    includeByDefault: true,
    defaultFields: ['id', 'source', 'target', 'sourceHandle', 'targetHandle']
  },
  {
    field: 'handles',
    type: 'one-to-many',
    targetEntity: 'Handle',
    includeByDefault: true,
    defaultFields: ['id', 'nodeId', 'type', 'position']
  },
  {
    field: 'persons',
    type: 'many-to-many',
    targetEntity: 'Person',
    includeByDefault: true,
    defaultFields: ['id', 'name', 'llmConfig']
  }
];

export const nodeRelationships: RelationshipConfig[] = [
  {
    field: 'diagram',
    type: 'one-to-one',
    targetEntity: 'Diagram',
    includeByDefault: false,
    defaultFields: ['id', 'name']
  },
  {
    field: 'incomingArrows',
    type: 'one-to-many',
    targetEntity: 'Arrow',
    includeByDefault: false,
    defaultFields: ['id', 'source', 'sourceHandle']
  },
  {
    field: 'outgoingArrows',
    type: 'one-to-many',
    targetEntity: 'Arrow',
    includeByDefault: false,
    defaultFields: ['id', 'target', 'targetHandle']
  }
];