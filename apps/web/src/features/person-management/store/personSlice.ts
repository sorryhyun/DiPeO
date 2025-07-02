import { StateCreator } from 'zustand';
import { DomainPerson, PersonID, apiKeyId } from '@/core/types';
import { generatePersonId } from '@/core/types/utilities';
import { LLMService, NodeType } from '@dipeo/domain-models';
import { UnifiedStore } from '@/core/store/unifiedStore.types';

export interface PersonSlice {
  // Core data
  persons: Map<PersonID, DomainPerson>;
  personsArray: DomainPerson[];
  
  // Person operations
  addPerson: (label: string, service: string, model: string) => PersonID;
  updatePerson: (id: PersonID, updates: Partial<DomainPerson>) => void;
  deletePerson: (id: PersonID) => void;
  
  // Batch operations
  batchUpdatePersons: (updates: Array<{id: PersonID, updates: Partial<DomainPerson>}>) => void;
  importPersons: (persons: DomainPerson[]) => void;
  
  // Person queries
  getPersonByLabel: (label: string) => DomainPerson | undefined;
  getPersonsByService: (service: string) => DomainPerson[];
  getUnusedPersons: () => DomainPerson[];
  
  // Validation
  isPersonInUse: (personId: PersonID) => boolean;
  canDeletePerson: (personId: PersonID) => boolean;
}

export const createPersonSlice: StateCreator<
  UnifiedStore,
  [['zustand/immer', never]],
  [],
  PersonSlice
> = (set, get) => {
  // Helper function to sync array with map
  const syncPersonsArray = (state: any) => {
    state.personsArray = Array.from(state.persons.values());
  };

  return {
    // Initialize data
    persons: new Map(),
    
    // Array property - synced with Map for React components
    personsArray: [],
  
    // Person operations
    addPerson: (label, service, model) => {
      const person: DomainPerson = {
        id: generatePersonId(),
        label,
        llm_config: {
          api_key_id: apiKeyId(''),
          service: service as LLMService,
          model,
          system_prompt: ''
        },
        type: 'person',
        masked_api_key: null
      };
      
      set(state => {
        state.persons.set(person.id as PersonID, person);
        syncPersonsArray(state);
        state.dataVersion += 1;
      });
      
      return person.id as PersonID;
    },
  
    updatePerson: (id, updates) => set(state => {
      const person = state.persons.get(id);
      if (person) {
        // Handle nested llm_config updates
        const updatedPerson = { ...person };
        
        // Check for nested llm_config fields in the updates
        const flatUpdates = { ...updates } as Record<string, unknown>;
        const llmConfigUpdates: Record<string, unknown> = {};
        
        // Extract nested llm_config fields
        Object.keys(flatUpdates).forEach(key => {
          if (key.startsWith('llm_config.')) {
            const field = key.substring('llm_config.'.length);
            llmConfigUpdates[field] = flatUpdates[key];
            delete flatUpdates[key];
          }
        });
        
        // Apply flat updates first
        Object.assign(updatedPerson, flatUpdates);
        
        // Apply llm_config updates if any
        if (Object.keys(llmConfigUpdates).length > 0) {
          updatedPerson.llm_config = {
            ...updatedPerson.llm_config,
            ...llmConfigUpdates
          };
        }
        
        state.persons.set(id, updatedPerson);
        syncPersonsArray(state);
        state.dataVersion += 1;
      }
    }),
    
    deletePerson: (id) => set(state => {
      // Check if person is in use
      const isInUse = Array.from(state.nodes.values()).some(
        node => node.type === NodeType.PERSON_JOB && node.data.person_id === id
      );
      
      if (!isInUse && state.persons.delete(id)) {
        syncPersonsArray(state);
        state.dataVersion += 1;
      }
    }),
  
    // Batch operations
    batchUpdatePersons: (updates) => set(state => {
      let hasChanges = false;
      updates.forEach(({ id, updates: personUpdates }) => {
        const person = state.persons.get(id);
        if (person) {
          state.persons.set(id, { ...person, ...personUpdates });
          hasChanges = true;
        }
      });
      
      if (hasChanges) {
        syncPersonsArray(state);
        state.dataVersion += 1;
      }
    }),
    
    importPersons: (persons) => set(state => {
      persons.forEach(person => {
        state.persons.set(person.id as PersonID, person);
      });
      syncPersonsArray(state);
      state.dataVersion += 1;
    }),
  
    // Person queries
    getPersonByLabel: (label) => {
      const state = get();
      return Array.from(state.persons.values()).find(
        person => person.label === label
      );
    },
    
    getPersonsByService: (service) => {
      const state = get();
      return Array.from(state.persons.values()).filter(
        person => person.llm_config?.service === service
      );
    },
    
    getUnusedPersons: () => {
      const state = get();
      const usedPersonIds = new Set<PersonID>();
    
      state.nodes.forEach(node => {
        if (node.type === NodeType.PERSON_JOB && node.data.person_id) {
          usedPersonIds.add(node.data.person_id);
        }
      });
      
      return Array.from(state.persons.values()).filter(
        person => !usedPersonIds.has(person.id as PersonID)
      );
    },
    
    // Validation
    isPersonInUse: (personId) => {
      const state = get();
      return Array.from(state.nodes.values()).some(
        node => node.type === NodeType.PERSON_JOB && node.data.person_id === personId
      );
    },
  
    canDeletePerson: (personId) => {
      const state = get();
      return !state.isPersonInUse(personId);
    }
  };
};