import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { nanoid } from 'nanoid';

// Simplified types - no more over-engineering
export interface Node {
  id: string;
  type: 'start' | 'job' | 'person_job' | 'condition' | 'db' | 'endpoint' | 'user_response' | 'notion' | 'person_batch_job';
  position: { x: number; y: number };
  data: Record<string, any>;
}

export interface Arrow {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  data?: Record<string, any>;
}

export interface Person {
  id: string;
  label: string;
  service?: string;
  apiKeyId?: string;
  modelName?: string;
  options?: Record<string, any>;
}

interface DiagramStore {
  // Data
  nodes: Node[];
  arrows: Arrow[];
  persons: Person[];
  
  // Actions (direct, no CRUD utils)
  addNode: (type: Node['type'], position: { x: number; y: number }) => void;
  updateNode: (id: string, data: any) => void;
  deleteNode: (id: string) => void;
  
  addArrow: (source: string, target: string, sourceHandle?: string, targetHandle?: string) => void;
  updateArrow: (id: string, data: any) => void;
  deleteArrow: (id: string) => void;
  
  addPerson: (person: Omit<Person, 'id'>) => void;
  updatePerson: (id: string, data: Partial<Person>) => void;
  deletePerson: (id: string) => void;
  
  // Batch operations
  setNodes: (nodes: Node[]) => void;
  setArrows: (arrows: Arrow[]) => void;
  setPersons: (persons: Person[]) => void;
  
  // Utility
  clear: () => void;
  loadDiagram: (data: { nodes: Node[]; arrows: Arrow[]; persons: Person[] }) => void;
  exportDiagram: () => { nodes: Node[]; arrows: Arrow[]; persons: Person[] };
}

export const useDiagramStore = create<DiagramStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        nodes: [],
        arrows: [],
        persons: [],
        
        // Node actions
        addNode: (type, position) => {
          const id = `${type}-${nanoid(6)}`;
          const newNode: Node = {
            id,
            type,
            position,
            data: { type, id } // Minimal default data
          };
          set({ nodes: [...get().nodes, newNode] });
        },
        
        updateNode: (id, data) => {
          set({
            nodes: get().nodes.map(node =>
              node.id === id ? { ...node, data: { ...node.data, ...data } } : node
            )
          });
        },
        
        deleteNode: (id) => {
          set({
            nodes: get().nodes.filter(node => node.id !== id),
            arrows: get().arrows.filter(arrow => arrow.source !== id && arrow.target !== id)
          });
        },
        
        // Arrow actions
        addArrow: (source, target, sourceHandle, targetHandle) => {
          const id = `arrow-${nanoid(6)}`;
          const newArrow: Arrow = {
            id,
            source,
            target,
            sourceHandle,
            targetHandle,
            data: {}
          };
          set({ arrows: [...get().arrows, newArrow] });
        },
        
        updateArrow: (id, data) => {
          set({
            arrows: get().arrows.map(arrow =>
              arrow.id === id ? { ...arrow, data: { ...arrow.data, ...data } } : arrow
            )
          });
        },
        
        deleteArrow: (id) => {
          set({ arrows: get().arrows.filter(arrow => arrow.id !== id) });
        },
        
        // Person actions
        addPerson: (person) => {
          const id = `person-${nanoid(6)}`;
          set({ persons: [...get().persons, { ...person, id }] });
        },
        
        updatePerson: (id, data) => {
          set({
            persons: get().persons.map(person =>
              person.id === id ? { ...person, ...data } : person
            )
          });
        },
        
        deletePerson: (id) => {
          set({ persons: get().persons.filter(person => person.id !== id) });
        },
        
        // Batch operations
        setNodes: (nodes) => set({ nodes }),
        setArrows: (arrows) => set({ arrows }),
        setPersons: (persons) => set({ persons }),
        
        // Utility
        clear: () => set({ nodes: [], arrows: [], persons: [] }),
        
        loadDiagram: (data) => {
          set({
            nodes: data.nodes || [],
            arrows: data.arrows || [],
            persons: data.persons || []
          });
        },
        
        exportDiagram: () => ({
          nodes: get().nodes,
          arrows: get().arrows,
          persons: get().persons
        })
      }),
      {
        name: 'dipeo-diagram',
        partialize: (state) => ({
          nodes: state.nodes,
          arrows: state.arrows,
          persons: state.persons
        })
      }
    )
  )
);