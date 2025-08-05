import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import type { DomainPerson } from '@/core/types';
import { NodeType, PersonID } from '@dipeo/models';

interface PersonsData {
  // Maps and arrays
  persons: Map<PersonID, DomainPerson>;
  personsMap: Map<PersonID, DomainPerson>; // Alias for backward compatibility
  personsArray: DomainPerson[];
  personIds: PersonID[];
  
  // Statistics
  personCount: number;
  personsByService: Record<string, number>;
  uniqueServices: string[];
  uniqueModels: string[];
  
  // Usage info
  usedPersonIds: Set<PersonID>;
  unusedPersons: DomainPerson[];
  
  // Query methods
  getPersonById: (id: PersonID) => DomainPerson | null;
  getPersonByLabel: (label: string) => DomainPerson | null;
  getPersonsByService: (service: string) => DomainPerson[];
  getPersonsByModel: (model: string) => DomainPerson[];
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
  const { persons, nodes } = useUnifiedStore(
    useShallow(state => ({
      persons: state.persons,
      nodes: state.nodes
    }))
  );
  
  // Convert to array once
  const personsArray = Array.from(persons.values());
  
  // Calculate used persons
  const usedPersonIds = new Set<PersonID>();
  nodes.forEach(node => {
    if (node.type === NodeType.PERSON_JOB && node.data?.personId) {
      usedPersonIds.add(node.data.personId);
    }
  });
  
  // Calculate persons by service
  const personsByService: Record<string, number> = {};
  personsArray.forEach(person => {
    const service = person.llm_config?.service || 'unknown';
    personsByService[service] = (personsByService[service] || 0) + 1;
  });
  
  // Get unused persons
  const unusedPersons = personsArray.filter(
    person => !usedPersonIds.has(person.id as PersonID)
  );
  
  // Extract person IDs
  const personIds = personsArray.map(p => p.id as PersonID);
  
  // Get unique services and models
  const uniqueServices = Array.from(new Set(personsArray.map(p => p.llm_config?.service).filter(Boolean))).sort();
  const uniqueModels = Array.from(new Set(personsArray.map(p => p.llm_config?.model).filter(Boolean))).sort();
  
  // Query functions
  const getPersonById = (id: PersonID): DomainPerson | null => {
    return persons.get(id) || null;
  };
  
  const getPersonByLabel = (label: string): DomainPerson | null => {
    return personsArray.find(p => p.label === label) || null;
  };
  
  const getPersonsByService = (service: string): DomainPerson[] => {
    return personsArray.filter(p => p.llm_config?.service === service);
  };
  
  const getPersonsByModel = (model: string): DomainPerson[] => {
    return personsArray.filter(p => p.llm_config?.model === model);
  };
  
  return {
    persons,
    personsMap: persons, // Alias for backward compatibility
    personsArray,
    personIds,
    personCount: persons.size,
    personsByService,
    uniqueServices,
    uniqueModels,
    usedPersonIds,
    unusedPersons,
    getPersonById,
    getPersonByLabel,
    getPersonsByService,
    getPersonsByModel
  };
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
      node => node.type === NodeType.PERSON_JOB && node.data?.personId === personId
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
        .filter(person => person.llm_config?.service === service)
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
        if (node.type === NodeType.PERSON_JOB && node.data?.personId) {
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