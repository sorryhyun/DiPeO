import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import type { PersonID, DomainPerson } from '@/types';

interface PersonsData {
  // Maps and arrays
  persons: Map<PersonID, DomainPerson>;
  personsArray: DomainPerson[];
  
  // Statistics
  personCount: number;
  personsByService: Record<string, number>;
  
  // Usage info
  usedPersonIds: Set<PersonID>;
  unusedPersons: DomainPerson[];
}

/**
 * Focused selector hook for persons data
 * Provides all person-related state with computed values
 * 
 * @example
 * ```typescript
 * const { persons, unusedPersons, personsByService } = usePersonsData();
 * ```
 */
export const usePersonsData = (): PersonsData => {
  return useUnifiedStore(
    useShallow(state => {
      // Calculate used persons
      const usedPersonIds = new Set<PersonID>();
      state.nodes.forEach(node => {
        if (node.type === 'person_job' && node.data.personId) {
          usedPersonIds.add(node.data.personId);
        }
      });
      
      // Calculate persons by service
      const personsByService: Record<string, number> = {};
      const personsArray = state.personsArray || Array.from(state.persons.values());
      
      personsArray.forEach(person => {
        personsByService[person.service] = (personsByService[person.service] || 0) + 1;
      });
      
      // Get unused persons
      const unusedPersons = personsArray.filter(
        person => !usedPersonIds.has(person.id)
      );
      
      return {
        persons: state.persons,
        personsArray,
        personCount: state.persons.size,
        personsByService,
        usedPersonIds,
        unusedPersons
      };
    })
  );
};

/**
 * Hook to get a single person by ID
 */
export const usePersonData = (personId: PersonID | null): DomainPerson | null => {
  return useUnifiedStore(state => personId ? state.persons.get(personId) ?? null : null);
};

/**
 * Hook to check if a person is in use
 */
export const useIsPersonInUse = (personId: PersonID): boolean => {
  return useUnifiedStore(state => 
    state.isPersonInUse?.(personId) ||
    Array.from(state.nodes.values()).some(
      node => node.type === 'person_job' && node.data.personId === personId
    )
  );
};

/**
 * Hook to get persons by service
 */
export const usePersonsByService = (service: string): DomainPerson[] => {
  return useUnifiedStore(
    useShallow(state => 
      state.getPersonsByService?.(service) ||
      (state.personsArray || Array.from(state.persons.values()))
        .filter(person => person.service === service)
    )
  );
};

/**
 * Hook to get person usage statistics
 */
export const usePersonUsageStats = () => {
  return useUnifiedStore(
    useShallow(state => {
      const usageCount: Record<PersonID, number> = {};
      
      state.nodes.forEach(node => {
        if (node.type === 'person_job' && node.data.personId) {
          usageCount[node.data.personId] = (usageCount[node.data.personId] || 0) + 1;
        }
      });
      
      return {
        usageCount,
        totalPersons: state.persons.size,
        usedPersons: Object.keys(usageCount).length,
        unusedPersons: state.persons.size - Object.keys(usageCount).length
      };
    })
  );
};