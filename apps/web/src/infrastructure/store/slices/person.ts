import { DomainPerson, PersonID, apiKeyId } from '@/infrastructure/types';
import { generatePersonId } from '@/infrastructure/types/utilities';
import { LLMService } from '@dipeo/models';
import { Converters } from '@/infrastructure/services';
import type { UnifiedStore, SetState, GetState, StoreApiType } from '../types';

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
  importPersonsFromGraphQL: (graphqlPersons: unknown[]) => void;

  // Clear and restore operations
  clearPersons: () => void;
  restorePersons: (persons: Map<PersonID, DomainPerson>) => void;
  restorePersonsSilently: (persons: Map<PersonID, DomainPerson>) => void;
}



export const createPersonSlice = (
  set: SetState,
  _get: GetState,
  _api: StoreApiType
): PersonSlice => ({
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

      set((state: UnifiedStore) => {
        state.persons.set(person.id as PersonID, person);
        // Update personsArray directly in the same transaction
        state.personsArray = Array.from(state.persons.values());
        state.dataVersion += 1;
      });

      return person.id as PersonID;
    },

    updatePerson: (id, updates) => set((state: UnifiedStore) => {
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
        // Update personsArray directly in the same transaction
        state.personsArray = Array.from(state.persons.values());
        state.dataVersion += 1;
      }
    }),

    deletePerson: (id) => set((state: UnifiedStore) => {
      state.persons.delete(id);
      // Update personsArray directly in the same transaction
      state.personsArray = Array.from(state.persons.values());
      state.dataVersion += 1;
    }),

    // Batch operations
    batchUpdatePersons: (updates) => set((state: UnifiedStore) => {
      updates.forEach(({ id, updates: personUpdates }) => {
        const person = state.persons.get(id);
        if (person) {
          state.persons.set(id, { ...person, ...personUpdates });
        }
      });
      // Update personsArray directly in the same transaction
      state.personsArray = Array.from(state.persons.values());
      state.dataVersion += 1;
    }),

    importPersons: (persons) => set((state: UnifiedStore) => {
      persons.forEach(person => {
        state.persons.set(person.id as PersonID, person);
      });
      // Update personsArray directly in the same transaction
      state.personsArray = Array.from(state.persons.values());
      state.dataVersion += 1;
    }),

    importPersonsFromGraphQL: (graphqlPersons) => set((state: UnifiedStore) => {
      // Use Converters to convert GraphQL persons to domain format
      graphqlPersons.forEach(graphqlPerson => {
        try {
          const domainPerson = Converters.convertGraphQLPerson(graphqlPerson);
          state.persons.set(domainPerson.id as PersonID, domainPerson);
        } catch (error) {
          console.error('Failed to convert GraphQL person:', error, graphqlPerson);
        }
      });
      // Update personsArray directly in the same transaction
      state.personsArray = Array.from(state.persons.values());
      state.dataVersion += 1;
    }),

    // Clear and restore operations
    clearPersons: () => set((state: UnifiedStore) => {
      state.persons.clear();
      // Update personsArray directly in the same transaction
      state.personsArray = [];
      state.dataVersion += 1;
    }),

    restorePersons: (persons) => set((state: UnifiedStore) => {
      state.persons = new Map(persons);
      // Update personsArray directly in the same transaction
      state.personsArray = Array.from(state.persons.values());
      state.dataVersion += 1;
    }),

    restorePersonsSilently: (persons) => set((state: UnifiedStore) => {
      state.persons = new Map(persons);
      // Update personsArray but don't increment dataVersion
      state.personsArray = Array.from(state.persons.values());
    })
});
