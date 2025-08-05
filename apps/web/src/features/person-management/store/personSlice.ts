import { StateCreator } from 'zustand';
import { DomainPerson, PersonID, apiKeyId } from '@/core/types';
import { generatePersonId } from '@/core/types/utilities';
import { LLMService } from '@dipeo/models';
import { UnifiedStore } from '@/core/store/unifiedStore.types';
import { ConversionService } from '@/core/services';

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
  importPersonsFromGraphQL: (graphqlPersons: any[]) => void;
  
  // Clear and restore operations
  clearPersons: () => void;
  restorePersons: (persons: Map<PersonID, DomainPerson>) => void;
  restorePersonsSilently: (persons: Map<PersonID, DomainPerson>) => void;
}



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
        state.triggerArraySync();
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
        state.triggerArraySync();
      }
    }),
    
    deletePerson: (id) => set(state => {
      state.persons.delete(id);
      state.triggerArraySync();
    }),
  
    // Batch operations
    batchUpdatePersons: (updates) => set(state => {
      updates.forEach(({ id, updates: personUpdates }) => {
        const person = state.persons.get(id);
        if (person) {
          state.persons.set(id, { ...person, ...personUpdates });
        }
      });
      state.triggerArraySync();
    }),
    
    importPersons: (persons) => set(state => {
      persons.forEach(person => {
        state.persons.set(person.id as PersonID, person);
      });
      state.triggerArraySync();
    }),
    
    importPersonsFromGraphQL: (graphqlPersons) => set(state => {
      // Use ConversionService to convert GraphQL persons to domain format
      graphqlPersons.forEach(graphqlPerson => {
        try {
          const domainPerson = ConversionService.convertGraphQLPerson(graphqlPerson);
          state.persons.set(domainPerson.id as PersonID, domainPerson);
        } catch (error) {
          console.error('Failed to convert GraphQL person:', error, graphqlPerson);
        }
      });
      state.triggerArraySync();
    }),
    
    // Clear and restore operations
    clearPersons: () => set(state => {
      state.persons.clear();
      state.triggerArraySync();
    }),
    
    restorePersons: (persons) => set(state => {
      state.persons = new Map(persons);
      state.triggerArraySync();
    }),
    
    restorePersonsSilently: (persons) => set(state => {
      state.persons = new Map(persons);
      // No markPersonsChanged call - dataVersion not incremented
    })
});