import { defineEntity } from '../entity-config';

export default defineEntity({
  name: 'ApiKey',
  plural: 'ApiKeys',
  
  fields: {
    id: { type: 'ApiKeyID', generated: true, required: true },
    label: { type: 'string', required: true },
    service: { type: 'string', required: true }, // APIServiceType enum
    key: { type: 'string', required: true }, // Encrypted/masked in responses
    created: { type: 'Date', generated: true },
    modified: { type: 'Date', generated: true }
  },
  
  operations: {
    create: {
      input: ['label', 'service', 'key'],
      returnEntity: true
    },
    update: {
      input: ['label', 'key'],
      partial: true
    },
    delete: true,
    list: {
      filters: ['service'],
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