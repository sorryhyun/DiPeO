import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { PersonDefinition } from '@/shared/types';
import { createPersonCrudActions } from "@/shared/utils/storeCrudUtils";

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
    )
  )
);