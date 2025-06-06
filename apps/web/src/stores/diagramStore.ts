import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { nanoid } from 'nanoid';
import { Node, Arrow, Person, ApiKey } from '@/types';
import { applyNodeChanges, applyEdgeChanges, Connection, NodeChange, EdgeChange } from '@xyflow/react';

export interface DiagramStore {
  // Data
  nodes: Node[];
  arrows: Arrow[];
  persons: Person[];
  apiKeys: ApiKey[];
  
  // Node actions
  addNode: (type: Node['type'], position: { x: number; y: number }) => void;
  updateNode: (id: string, data: Record<string, unknown>) => void;
  deleteNode: (id: string) => void;
  
  // Arrow actions
  addArrow: (source: string, target: string, sourceHandle?: string, targetHandle?: string) => void;
  updateArrow: (id: string, data: Record<string, unknown>) => void;
  deleteArrow: (id: string) => void;
  
  // Person actions
  addPerson: (person: Omit<Person, 'id'>) => void;
  updatePerson: (id: string, data: Partial<Person>) => void;
  deletePerson: (id: string) => void;
  getPersonById: (id: string) => Person | undefined;
  
  // API Key actions
  addApiKey: (apiKey: Omit<ApiKey, 'id'>) => void;
  updateApiKey: (id: string, data: Partial<ApiKey>) => void;
  deleteApiKey: (id: string) => void;
  getApiKeyById: (id: string) => ApiKey | undefined;
  setApiKeys: (apiKeys: ApiKey[]) => void;
  
  // Batch operations
  setNodes: (nodes: Node[]) => void;
  setArrows: (arrows: Arrow[]) => void;
  setPersons: (persons: Person[]) => void;
  
  // Utility
  clear: () => void;
  loadDiagram: (data: { nodes: Node[]; arrows: Arrow[]; persons: Person[]; apiKeys?: ApiKey[] }) => void;
  exportDiagram: () => { nodes: Node[]; arrows: Arrow[]; persons: Person[]; apiKeys: ApiKey[] };
  
  // Compatibility properties
  isReadOnly?: boolean;
  setReadOnly?: (readOnly: boolean) => void;
  
  // Flow compatibility
  onNodesChange: (changes: NodeChange[]) => void;
  onArrowsChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
}

export const useDiagramStore = create<DiagramStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        nodes: [],
        arrows: [],
        persons: [],
        apiKeys: [],
        
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
        
        getPersonById: (id: string) => get().persons.find(p => p.id === id),
        
        // API Key actions
        addApiKey: (apiKeyData) => {
          const newApiKey = {
            ...apiKeyData,
            id: `APIKEY_${nanoid().slice(0, 6).replace(/-/g, '_').toUpperCase()}`
          } as ApiKey;
          set({ apiKeys: [...get().apiKeys, newApiKey] });
        },
        
        updateApiKey: (id, data) => {
          set({
            apiKeys: get().apiKeys.map(key =>
              key.id === id ? { ...key, ...data } : key
            )
          });
        },
        
        deleteApiKey: (id) => {
          set({ apiKeys: get().apiKeys.filter(key => key.id !== id) });
        },
        
        getApiKeyById: (id: string) => get().apiKeys.find(key => key.id === id),
        
        setApiKeys: (apiKeys) => set({ apiKeys }),
        
        // Batch operations
        setNodes: (nodes) => set({ nodes }),
        setArrows: (arrows) => set({ arrows }),
        setPersons: (persons) => set({ persons }),
        
        // Utility
        clear: () => set({ nodes: [], arrows: [], persons: [], apiKeys: [] }),
        
        loadDiagram: (data) => {
          set({
            nodes: data.nodes || [],
            arrows: data.arrows || [],
            persons: data.persons || [],
            apiKeys: data.apiKeys || []
          });
        },
        
        exportDiagram: () => ({
          nodes: get().nodes,
          arrows: get().arrows,
          persons: get().persons,
          apiKeys: get().apiKeys
        }),
        
        // Compatibility
        isReadOnly: false,
        setReadOnly: (readOnly: boolean) => set({ isReadOnly: readOnly }),
        
        // Flow compatibility
        onNodesChange: (changes) => {
          set({
            nodes: applyNodeChanges(changes, get().nodes) as Node[]
          });
        },
        
        onArrowsChange: (changes) => {
          set({
            arrows: applyEdgeChanges(changes, get().arrows).map(edge => ({
              ...edge,
              sourceHandle: edge.sourceHandle || undefined,
              targetHandle: edge.targetHandle || undefined
            })) as Arrow[]
          });
        },
        
        onConnect: (connection) => {
          if (connection.source && connection.target) {
            get().addArrow(
              connection.source,
              connection.target,
              connection.sourceHandle || undefined,
              connection.targetHandle || undefined
            );
          }
        }
      }),
      {
        name: 'dipeo-diagram',
        partialize: (state) => ({
          nodes: state.nodes,
          arrows: state.arrows,
          persons: state.persons,
          apiKeys: state.apiKeys
        })
      }
    )
  )
);