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
    create: {
      input: ['label', 'llm_config', 'diagram_id'],
      returnEntity: true
    },
    update: {
      input: ['label', 'llm_config'],
      partial: true
    },
    delete: true,
    list: {
      filters: ['diagram_id', 'label'],
      sortable: ['label', 'created'],
      pagination: true
    },
    get: true
  },
  
  features: {
    timestamps: true,
    softDelete: false
  }
});