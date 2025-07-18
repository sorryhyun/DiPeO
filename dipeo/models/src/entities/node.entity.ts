import { defineEntity } from '../entity-config';

export default defineEntity({
  name: 'Node',
  plural: 'Nodes',
  
  fields: {
    id: { type: 'NodeID', generated: true, required: true },
    type: { type: 'string', required: true }, // NodeType enum
    position: { type: 'JSON', required: true }, // Vec2
    data: { type: 'JSON', required: true }, // Record<string, any>
    diagram_id: { type: 'DiagramID', required: true },
    created: { type: 'Date', generated: true },
    modified: { type: 'Date', generated: true }
  },
  
  relations: {
    diagram: {
      type: 'Diagram',
      relation: 'one-to-many',
      required: true
    }
  },
  
  operations: {
    create: {
      input: ['type', 'position', 'data', 'diagram_id'],
      returnEntity: true
    },
    update: {
      input: ['type', 'position', 'data'],
      partial: true
    },
    delete: true,
    list: {
      filters: ['diagram_id', 'type'],
      sortable: ['created'],
      pagination: true
    },
    get: true
  },
  
  features: {
    timestamps: true,
    softDelete: false
  }
});