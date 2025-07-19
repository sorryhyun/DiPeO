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
    create: false,  // Handles are created/updated through diagram mutations
    update: false,
    delete: false,
    list: false,
    get: false
  },
  
  features: {
    timestamps: true,
    softDelete: false
  },
  
  // Handles are part of diagrams and edited through diagram mutations
  service: {
    name: 'diagram_service',
    useCrudAdapter: false
  }
});