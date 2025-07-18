import { defineEntity } from '../entity-config';

export default defineEntity({
  name: 'Handle',
  plural: 'Handles',
  
  fields: {
    id: { type: 'HandleID', generated: true, required: true },
    node_id: { type: 'NodeID', required: true },
    label: { type: 'string', required: true }, // HandleLabel enum
    direction: { type: 'string', required: true }, // HandleDirection enum
    data_type: { type: 'string', required: true }, // DataType enum
    position: { type: 'string', nullable: true }, // 'left' | 'right' | 'top' | 'bottom'
    diagram_id: { type: 'DiagramID', required: true },
    created: { type: 'Date', generated: true },
    modified: { type: 'Date', generated: true }
  },
  
  relations: {
    node: {
      type: 'Node',
      relation: 'one-to-many',
      required: true
    },
    diagram: {
      type: 'Diagram',
      relation: 'one-to-many',
      required: true
    }
  },
  
  operations: {
    create: {
      input: ['node_id', 'label', 'direction', 'data_type', 'position', 'diagram_id'],
      returnEntity: true
    },
    update: {
      input: ['label', 'direction', 'data_type', 'position'],
      partial: true
    },
    delete: true,
    list: {
      filters: ['diagram_id', 'node_id'],
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