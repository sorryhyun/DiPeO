/**
 * usePersonOperations - Person management hook
 * 
 * This hook provides operations for managing persons (LLM instances) in the store.
 * Built using the store operation factory for consistency.
 */

import { createStoreOperationHook } from './factories';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import { personId, type DomainPerson, type LLMService, type NodeID } from '@/types';

// Create the hook using our factory
export const usePersonOperations = createStoreOperationHook<DomainPerson, [string, LLMService, string]>({
  entityName: 'Person',
  entityNamePlural: 'Persons',
  
  // Store selectors
  selectCollection: (state) => state.persons,
  selectAddAction: (state) => state.addPerson,
  selectUpdateAction: (state) => (id: string, updates: Partial<DomainPerson>) => 
    state.updatePerson(personId(id), updates),
  selectDeleteAction: (state) => (id: string) => 
    state.deletePerson(personId(id)),
  
  // Related data selector - we need to check if API keys exist
  selectRelated: (state) => ({
    apiKeys: state.apiKeys,
    nodes: state.nodes
  }),
  
  // Validation
  validateAdd: (label: string, service: LLMService, model: string) => {
    const errors: string[] = [];
    
    if (!label || label.trim().length === 0) {
      errors.push('Person label is required');
    }
    
    if (!service) {
      errors.push('Service type is required');
    }
    
    if (!model || model.trim().length === 0) {
      errors.push('Model is required');
    }
    
    // Validate service is a valid LLM service
    const validServices: LLMService[] = ['openai', 'claude', 'gemini', 'grok'];
    if (!validServices.includes(service)) {
      errors.push(`Invalid service: ${service}`);
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },
  
  validateUpdate: (_id: string, updates: Partial<DomainPerson>) => {
    const errors: string[] = [];
    
    if (updates.label !== undefined && (!updates.label || updates.label.trim().length === 0)) {
      errors.push('Person label cannot be empty');
    }
    
    if (updates.service !== undefined) {
      const validServices: LLMService[] = ['openai', 'claude', 'gemini', 'grok'];
      if (!validServices.includes(updates.service)) {
        errors.push(`Invalid service: ${updates.service}`);
      }
    }
    
    if (updates.model !== undefined && (!updates.model || updates.model.trim().length === 0)) {
      errors.push('Model cannot be empty');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },
  
  // Lifecycle hooks
  beforeAdd: (label: string, service: LLMService, model: string) => {
    // Trim the label and model before adding
    return [label.trim(), service, model.trim()];
  },
  
  afterAdd: async (_id: string, label: string, _service: LLMService, model: string) => {
    console.log(`Added person: ${label} using ${model}`);
  },
  
  beforeDelete: async (id: string) => {
    // Check if person is being used by any nodes
    const state = useUnifiedStore.getState();
    const nodes = Array.from(state.nodes.values());
    
    const isInUse = nodes.some(node => {
      // Check if node data contains this person ID
      return node.data?.person === id;
    });
    
    if (isInUse) {
      // Still allow deletion but warn the user
      console.warn(`Person ${id} is being used by nodes but will be deleted`);
    }
    
    return true;
  },
  
  afterDelete: async (id: string) => {
    // Clean up any nodes that reference this person
    const state = useUnifiedStore.getState();
    const nodes = Array.from(state.nodes.values());
    
    state.transaction(() => {
      nodes.forEach(node => {
        if (node.data?.person === id) {
          // Remove person reference from node
          state.updateNode(node.id, { 
            data: { ...node.data, person: undefined } 
          });
        }
      });
    });
  },
  
  // Custom messages
  messages: {
    addSuccess: (label: string, _service: LLMService, model: string) => 
      `Added person "${label}" using ${model}`,
    updateSuccess: () => `Updated person`,
    deleteSuccess: () => `Removed person`,
    addError: 'Failed to add person',
    updateError: 'Failed to update person',
    deleteError: 'Failed to remove person'
  },
  
  // Options
  options: {
    useTransaction: true,
    showToasts: true,
    trackDirty: true
  }
});

// Additional utilities for persons

// Export additional utilities specific to persons
export const usePersonUtils = () => {
  const { items, getById } = usePersonOperations();
  const store = useUnifiedStore();
  
  // Get persons by service
  const getByService = (service: LLMService): DomainPerson[] => {
    return items.filter(person => person.service === service);
  };
  
  // Get persons by model
  const getByModel = (model: string): DomainPerson[] => {
    return items.filter(person => person.model === model);
  };
  
  // Find person by label
  const getByLabel = (label: string): DomainPerson | undefined => {
    return items.find(person => person.label === label);
  };
  
  // Get nodes using a specific person
  const getNodesUsingPerson = (personId: string): NodeID[] => {
    const nodes = Array.from(store.nodes.values());
    return nodes
      .filter(node => node.data?.person === personId)
      .map(node => node.id);
  };
  
  // Check if person is in use
  const isPersonInUse = (personId: string): boolean => {
    return getNodesUsingPerson(personId).length > 0;
  };
  
  // Get usage count for a person
  const getUsageCount = (personId: string): number => {
    return getNodesUsingPerson(personId).length;
  };
  
  // Get all unique models being used
  const getUniqueModels = (): string[] => {
    const models = new Set(items.map(person => person.model));
    return Array.from(models);
  };
  
  // Get all unique services being used
  const getUniqueServices = (): LLMService[] => {
    const services = new Set(items.map(person => person.service));
    return Array.from(services) as LLMService[];
  };
  
  return {
    getByService,
    getByModel,
    getByLabel,
    getNodesUsingPerson,
    isPersonInUse,
    getUsageCount,
    getUniqueModels,
    getUniqueServices,
    getPersonById: getById
  };
};