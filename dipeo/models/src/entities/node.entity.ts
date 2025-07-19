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
    create: false,  // Nodes are created/updated through diagram mutations
    update: false,
    delete: false,
    list: false,
    get: false
  },
  
  features: {
    timestamps: true,
    softDelete: false
  },
  
  // Nodes are part of diagrams and edited through diagram mutations
  service: {
    name: 'diagram_service',
    useCrudAdapter: false
  }
});