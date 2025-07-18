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
    create: {
      input: ['source', 'target', 'content_type', 'label', 'data', 'diagram_id'],
      returnEntity: true
    },
    update: {
      input: ['source', 'target', 'content_type', 'label', 'data'],
      partial: true
    },
    delete: true,
    list: {
      filters: ['diagram_id'],
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