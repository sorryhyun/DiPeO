import { defineEntity } from '../entity-config';

export default defineEntity({
  name: 'Diagram',
  plural: 'Diagrams',
  
  fields: {
    id: { type: 'DiagramID', generated: true, required: true },
    name: { type: 'string', required: true },
    description: { type: 'string', nullable: true },
    version: { type: 'string', required: true, default: '2.0.0' },
    author: { type: 'string', nullable: true },
    tags: { type: 'string[]', nullable: true },
    created: { type: 'Date', generated: true },
    modified: { type: 'Date', generated: true }
  },
  
  operations: {
    create: {
      input: ['name', 'description', 'author', 'tags'],
      returnEntity: true
    },
    update: {
      input: ['name', 'description', 'author', 'tags'],
      partial: true
    },
    delete: true,
    list: {
      filters: ['name', 'author'],
      sortable: ['name', 'created', 'modified'],
      pagination: true
    },
    get: true
  },
  
  features: {
    timestamps: true,
    softDelete: false
  }
});