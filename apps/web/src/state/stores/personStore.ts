import { create } from 'zustand';
import { devtools, subscribeWithSelector, persist } from 'zustand/middleware';
import { PersonDefinition } from '@/common/types';
import { createPersonCrudActions } from "@/common/utils/storeCrudUtils";

export interface PersonState {
  persons: PersonDefinition[];
  
  addPerson: (person: Omit<PersonDefinition, 'id'>) => void;
  updatePerson: (personId: string, data: Partial<PersonDefinition>) => void;
  deletePerson: (personId: string) => void;
  getPersonById: (personId: string) => PersonDefinition | undefined;
  clearPersons: () => void;
  setPersons: (persons: PersonDefinition[]) => void;
}

export const usePersonStore = create<PersonState>()(
  devtools(
    persist(
      subscribeWithSelector(
        (set, get) => ({
          persons: [],
          
          // Person operations using generic CRUD
          ...createPersonCrudActions<PersonDefinition>(
            () => get().persons,
            (persons) => set({ persons }),
            'PERSON'
          ),
          
          setPersons: (persons: PersonDefinition[]) => {
            set({ persons });
          },
        })
      ),
      {
        name: 'dipeo-person-store',
        // Only persist persons data, not functions
        partialize: (state) => ({ 
          persons: state.persons 
        }),
      }
    )
  )
);