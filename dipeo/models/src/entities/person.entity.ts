import { defineEntity } from '../entity-config';

export default defineEntity({
  name: 'Person',
  plural: 'Persons',
  
  fields: {
    id: { type: 'PersonID', generated: true, required: true },
    label: { type: 'string', required: true },
    type: { type: 'string', required: true, default: 'person' },
    llm_config: { type: 'JSON', required: true }, // PersonLLMConfig
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
    create: false,
    update: false,
    delete: false,
    list: false,
    get: false
  },
  
  features: {
    timestamps: true,
    softDelete: false
  },
  
  // Map to the existing diagram_service (persons are part of diagrams)
  service: {
    name: 'diagram_service',
    useCrudAdapter: false
  }
});