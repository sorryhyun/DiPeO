import { defineEntity } from '../entity-config';

export default defineEntity({
  name: 'Arrow',
  plural: 'Arrows',
  
  fields: {
    id: { type: 'ArrowID', generated: true, required: true },
    source: { type: 'HandleID', required: true },
    target: { type: 'HandleID', required: true },
    content_type: { type: 'string', nullable: true }, // ContentType enum
    label: { type: 'string', nullable: true },
    data: { type: 'JSON', nullable: true },
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
    create: false,  // Arrows are created/updated through diagram mutations
    update: false,
    delete: false,
    list: false,
    get: false
  },
  
  features: {
    timestamps: true,
    softDelete: false
  },
  
  // Arrows are part of diagrams and edited through diagram mutations
  service: {
    name: 'diagram_service',
    useCrudAdapter: false
  }
});