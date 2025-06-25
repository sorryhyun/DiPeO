import { StateCreator } from 'zustand';
import { DomainPerson } from '@/core/types';
import { generatePersonId } from '@/core/types/utilities';
import { ForgettingMode, LLMService, NodeType, type PersonID } from '@dipeo/domain-models';
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
> = (set, get) => ({
  // Initialize data
  persons: new Map(),
  personsArray: [],
  
  // Person operations
  addPerson: (label, service, model) => {
    const person: DomainPerson = {
      id: generatePersonId(),
      label,
      apiKeyId: '',
      service: service as LLMService,
      model,
      systemPrompt: '',
      type: 'person',
      maskedApiKey: null
    };
    
    set(state => {
      state.persons.set(person.id as PersonID, person);
      state.personsArray = Array.from(state.persons.values());
      state.dataVersion += 1;
    });
    
    return person.id as PersonID;
  },
  
  updatePerson: (id, updates) => set(state => {
    const person = state.persons.get(id);
    if (person) {
      const updatedPerson = { ...person, ...updates };
      state.persons.set(id, updatedPerson);
      state.personsArray = Array.from(state.persons.values());
      state.dataVersion += 1;
    }
  }),
  
  deletePerson: (id) => set(state => {
    // Check if person is in use
    const isInUse = Array.from(state.nodes.values()).some(
      node => node.type === NodeType.PERSON_JOB && node.data.personId === id
    );
    
    if (!isInUse && state.persons.delete(id)) {
      state.personsArray = Array.from(state.persons.values());
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
      state.personsArray = Array.from(state.persons.values());
      state.dataVersion += 1;
    }
  }),
  
  importPersons: (persons) => set(state => {
    persons.forEach(person => {
      state.persons.set(person.id as PersonID, person);
    });
    state.personsArray = Array.from(state.persons.values());
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
      person => person.service === service
    );
  },
  
  getUnusedPersons: () => {
    const state = get();
    const usedPersonIds = new Set<PersonID>();
    
    state.nodes.forEach(node => {
      if (node.type === NodeType.PERSON_JOB && node.data.personId) {
        usedPersonIds.add(node.data.personId);
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
      node => node.type === NodeType.PERSON_JOB && node.data.personId === personId
    );
  },
  
  canDeletePerson: (personId) => {
    const state = get();
    return !state.isPersonInUse(personId);
  }
});