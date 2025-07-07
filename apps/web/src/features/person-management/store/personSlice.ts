import { StateCreator } from 'zustand';
import { DomainPerson, PersonID, apiKeyId } from '@/core/types';
import { generatePersonId } from '@/core/types/utilities';
import { LLMService } from '@dipeo/domain-models';
import { UnifiedStore } from '@/core/store/unifiedStore.types';

export interface PersonSlice {
  // Core data
  persons: Map<PersonID, DomainPerson>;
  
  // Person operations
  addPerson: (label: string, service: string, model: string) => PersonID;
  updatePerson: (id: PersonID, updates: Partial<DomainPerson>) => void;
  deletePerson: (id: PersonID) => void;
  
  // Batch operations
  batchUpdatePersons: (updates: Array<{id: PersonID, updates: Partial<DomainPerson>}>) => void;
  importPersons: (persons: DomainPerson[]) => void;
}


// Helper to handle post-change operations
const afterChange = (state: UnifiedStore) => {
  state.dataVersion += 1;
};

export const createPersonSlice: StateCreator<
  UnifiedStore,
  [['zustand/immer', never]],
  [],
  PersonSlice
> = (set, _get) => ({
    // Initialize data
    persons: new Map(),
  
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
        afterChange(state);
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
        afterChange(state);
      }
    }),
    
    deletePerson: (id) => set(state => {
      const deleted = state.persons.delete(id);
      if (deleted) {
        afterChange(state);
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
        afterChange(state);
      }
    }),
    
    importPersons: (persons) => set(state => {
      persons.forEach(person => {
        state.persons.set(person.id as PersonID, person);
      });
      afterChange(state);
    })
});