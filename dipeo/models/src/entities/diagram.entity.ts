import { defineEntity } from '../entity-config';

export default defineEntity({
  name: 'Diagram',
  plural: 'Diagrams',
  
  fields: {
    id: { type: 'DiagramID', generated: true, required: true },
    name: { type: 'string', required: true },
    description: { type: 'string', required: false },
    format: { type: 'string', required: true, default: 'native' }, // native, light, readable
    content: { type: 'JSON', required: true }, // DomainDiagram
    created: { type: 'Date', generated: true },
    modified: { type: 'Date', generated: true }
  },
  
  operations: {
    create: false,  // Use custom mutations
    update: false,  // Use custom mutations
    delete: false,  // Use custom mutations
    list: false,    // Use custom queries
    get: false      // Use custom queries
  },
  
  features: {
    timestamps: true,
    softDelete: false
  },
  
  // Diagram operations are complex and implemented manually
  service: {
    name: 'integrated_diagram_service',
    useCrudAdapter: false
  }
});