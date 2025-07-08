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
  
  // Clear and restore operations
  clearPersons: () => void;
  restorePersons: (persons: Map<PersonID, DomainPerson>) => void;
  restorePersonsSilently: (persons: Map<PersonID, DomainPerson>) => void;
}


// Helper to track person changes
const markPersonsChanged = (state: UnifiedStore) => {
  // Increment dataVersion to trigger array sync via middleware
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
        type: 'person'
      };
      
      set(state => {
        state.persons.set(person.id as PersonID, person);
        markPersonsChanged(state);
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
        markPersonsChanged(state);
      }
    }),
    
    deletePerson: (id) => set(state => {
      state.persons.delete(id);
      markPersonsChanged(state);
    }),
  
    // Batch operations
    batchUpdatePersons: (updates) => set(state => {
      updates.forEach(({ id, updates: personUpdates }) => {
        const person = state.persons.get(id);
        if (person) {
          state.persons.set(id, { ...person, ...personUpdates });
        }
      });
      markPersonsChanged(state);
    }),
    
    importPersons: (persons) => set(state => {
      persons.forEach(person => {
        state.persons.set(person.id as PersonID, person);
      });
      markPersonsChanged(state);
    }),
    
    // Clear and restore operations
    clearPersons: () => set(state => {
      state.persons.clear();
      markPersonsChanged(state);
    }),
    
    restorePersons: (persons) => set(state => {
      state.persons = new Map(persons);
      markPersonsChanged(state);
    }),
    
    restorePersonsSilently: (persons) => set(state => {
      state.persons = new Map(persons);
      // No markPersonsChanged call - dataVersion not incremented
    })
});