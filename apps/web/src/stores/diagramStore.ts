import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { nanoid } from 'nanoid';
import { produce, enableMapSet } from 'immer';
import { applyNodeChanges, applyEdgeChanges, Connection, NodeChange, EdgeChange } from '@xyflow/react';
import { Node, Arrow, Person, ApiKey } from '@/types';

// Enable Immer MapSet plugin for Map and Set support
enableMapSet();

// Type definitions for Maps
type NodeMap = Map<string, Node>;
type ArrowMap = Map<string, Arrow>;
type PersonMap = Map<string, Person>;
type ApiKeyMap = Map<string, ApiKey>;

export interface DiagramStore {
  // Maps for O(1) access
  nodes: NodeMap;
  arrows: ArrowMap;
  persons: PersonMap;
  apiKeys: ApiKeyMap;

  // Selectors (memoized) - only recompute if underlying Map mutated
  nodeList: () => Node[];
  arrowList: () => Arrow[];
  personList: () => Person[];
  apiKeyList: () => ApiKey[];

  // Node mutators
  addNode: (type: Node['type'], position: { x: number; y: number }) => void;
  updateNode: (id: string, data: Record<string, unknown>) => void;
  deleteNode: (id: string) => void;
  upsertNode: (partial: Partial<Node> & Pick<Node, 'id'>) => void;

  // Arrow mutators
  addArrow: (source: string, target: string, sourceHandle?: string, targetHandle?: string) => void;
  updateArrow: (id: string, data: Record<string, unknown>) => void;
  deleteArrow: (id: string) => void;
  upsertArrow: (partial: Partial<Arrow> & Pick<Arrow, 'id'>) => void;

  // Person mutators
  addPerson: (person: Omit<Person, 'id'>) => void;
  updatePerson: (id: string, data: Partial<Person>) => void;
  deletePerson: (id: string) => void;
  getPersonById: (id: string) => Person | undefined;

  // API Key mutators
  addApiKey: (apiKey: Omit<ApiKey, 'id'>) => void;
  updateApiKey: (id: string, data: Partial<ApiKey>) => void;
  deleteApiKey: (id: string) => void;
  getApiKeyById: (id: string) => ApiKey | undefined;
  setApiKeys: (apiKeys: ApiKey[]) => void;

  // Batch operations
  setNodes: (nodes: Node[]) => void;
  setArrows: (arrows: Arrow[]) => void;
  setPersons: (persons: Person[]) => void;

  // Flow compatibility
  onNodesChange: (changes: NodeChange[]) => void;
  onArrowsChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;

  // Utility
  clear: () => void;
  loadDiagram: (data: { nodes: Node[]; arrows: Arrow[]; persons: Person[]; apiKeys?: ApiKey[] }) => void;
  exportDiagram: () => { nodes: Node[]; arrows: Arrow[]; persons: Person[]; apiKeys: ApiKey[] };

  // Compatibility properties
  isReadOnly?: boolean;
  setReadOnly?: (readOnly: boolean) => void;
}

// Helpers
const throttle = <Args extends unknown[], Return>(
  fn: (...args: Args) => Return, 
  ms: number
): (...args: Args) => void => {
  let last = 0;
  let tid: ReturnType<typeof setTimeout> | null = null;
  return (...args: Args) => {
    const now = performance.now();
    if (now - last > ms) {
      last = now;
      fn(...args);
    } else {
      if (tid) clearTimeout(tid);
      tid = setTimeout(() => {
        last = performance.now();
        fn(...args);
      }, ms);
    }
  };
};

const toMap = <T extends { id: string }>(arr: T[]): Map<string, T> =>
  new Map(arr.map(obj => [obj.id, obj]));

// Store implementation
export const useDiagramStore = create<DiagramStore>()(
  devtools(
    subscribeWithSelector(
      persist(
        (set, get) => {
          // Throttled commit for drag-move
          const commitDrag = throttle((changes: NodeChange[]) => {
            // Filter out dimension changes here as well
            const filteredChanges = changes.filter(change => change.type !== 'dimensions');
            const currentNodes = get().nodeList();
            const updatedNodes = applyNodeChanges(filteredChanges, currentNodes) as Node[];
            set(
              produce<DiagramStore>(draft => {
                updatedNodes.forEach(n => {
                  draft.nodes.set(n.id, n);
                });
              })
            );
          }, 50);

          return {
            // State - using Maps for O(1) operations
            nodes: new Map(),
            arrows: new Map(),
            persons: new Map(),
            apiKeys: new Map(),

            // Selectors - convert Maps to arrays only when needed
            nodeList: () => Array.from(get().nodes.values()),
            arrowList: () => Array.from(get().arrows.values()),
            personList: () => Array.from(get().persons.values()),
            apiKeyList: () => Array.from(get().apiKeys.values()),

            // Node mutators
            addNode: (type, position) => {
              const id = `${type}-${nanoid(4)}`;
              const newNode: Node = {
                id,
                type,
                position,
                data: { type, id }
              };
              set(
                produce(draft => {
                  draft.nodes.set(id, newNode);
                })
              );
            },

            updateNode: (id, data) =>
              set(
                produce(draft => {
                  const node = draft.nodes.get(id);
                  if (node) {
                    node.data = { ...node.data, ...data };
                  }
                })
              ),

            deleteNode: (id) =>
              set(
                produce(draft => {
                  draft.nodes.delete(id);
                  // Remove connected arrows
                  const arrowsToDelete: string[] = [];
                  draft.arrows.forEach((arrow: Arrow, arrowId: string) => {
                    if (arrow.source === id || arrow.target === id) {
                      arrowsToDelete.push(arrowId);
                    }
                  });
                  arrowsToDelete.forEach(arrowId => draft.arrows.delete(arrowId));
                })
              ),

            upsertNode: (node) =>
              set(
                produce(draft => {
                  const existing = draft.nodes.get(node.id);
                  draft.nodes.set(node.id, { ...existing, ...node } as Node);
                })
              ),

            // Arrow mutators
            addArrow: (source, target, sourceHandle, targetHandle) => {
              const id = `arrow-${nanoid(4)}`;
              const newArrow: Arrow = {
                id,
                source,
                target,
                sourceHandle,
                targetHandle,
                data: {}
              };
              set(
                produce(draft => {
                  draft.arrows.set(id, newArrow);
                })
              );
            },

            updateArrow: (id, data) =>
              set(
                produce(draft => {
                  const arrow = draft.arrows.get(id);
                  if (arrow) {
                    arrow.data = { ...arrow.data, ...data };
                  }
                })
              ),

            deleteArrow: (id) =>
              set(
                produce(draft => {
                  draft.arrows.delete(id);
                })
              ),

            upsertArrow: (arrow) =>
              set(
                produce(draft => {
                  const existing = draft.arrows.get(arrow.id);
                  draft.arrows.set(arrow.id, { ...existing, ...arrow } as Arrow);
                })
              ),

            // Person mutators
            addPerson: (person) => {
              const id = `person-${nanoid(4)}`;
              set(
                produce(draft => {
                  draft.persons.set(id, { ...person, id });
                })
              );
            },

            updatePerson: (id, data) =>
              set(
                produce(draft => {
                  const person = draft.persons.get(id);
                  if (person) {
                    Object.assign(person, data);
                  }
                })
              ),

            deletePerson: (id) =>
              set(
                produce(draft => {
                  draft.persons.delete(id);
                })
              ),

            getPersonById: (id) => get().persons.get(id),

            // API Key mutators
            addApiKey: (apiKeyData) => {
              const newApiKey = {
                ...apiKeyData,
                id: `APIKEY_${nanoid().slice(0, 6).replace(/-/g, '_').toUpperCase()}`
              } as ApiKey;
              set(
                produce(draft => {
                  draft.apiKeys.set(newApiKey.id, newApiKey);
                })
              );
            },

            updateApiKey: (id, data) =>
              set(
                produce(draft => {
                  const apiKey = draft.apiKeys.get(id);
                  if (apiKey) {
                    Object.assign(apiKey, data);
                  }
                })
              ),

            deleteApiKey: (id) =>
              set(
                produce(draft => {
                  draft.apiKeys.delete(id);
                })
              ),

            getApiKeyById: (id) => get().apiKeys.get(id),

            setApiKeys: (apiKeys) =>
              set({
                apiKeys: toMap(apiKeys)
              }),

            // Batch operations
            setNodes: (nodes) => set({ nodes: toMap(nodes) }),
            setArrows: (arrows) => set({ arrows: toMap(arrows) }),
            setPersons: (persons) => set({ persons: toMap(persons) }),

            // Flow compatibility
            onNodesChange: (changes) => {
              // Filter out dimension changes to prevent width modification
              const filteredChanges = changes.filter(change => change.type !== 'dimensions');
              
              // Separate position changes during drag from other changes
              const isDragging = filteredChanges.some(
                change => change.type === 'position' && 'dragging' in change && change.dragging
              );

              if (isDragging) {
                commitDrag(filteredChanges);
              } else {
                const currentNodes = get().nodeList();
                const updatedNodes = applyNodeChanges(filteredChanges, currentNodes) as Node[];
                set(
                  produce(draft => {
                    updatedNodes.forEach(n => {
                      draft.nodes.set(n.id, n);
                    });
                  })
                );
              }
            },

            onArrowsChange: (changes) => {
              const currentArrows = get().arrowList();
              const updatedArrows = applyEdgeChanges(changes, currentArrows) as Arrow[];
              set(
                produce(draft => {
                  updatedArrows.forEach(a => {
                    draft.arrows.set(a.id, a);
                  });
                })
              );
            },

            onConnect: ({ source, target, sourceHandle, targetHandle }) => {
              if (!source || !target) return;
              const id = `arrow-${nanoid(4)}`;
              get().upsertArrow({ id, source, target, sourceHandle, targetHandle, data: {} } as Arrow);
            },

            // Utility
            clear: () =>
              set({
                nodes: new Map(),
                arrows: new Map(),
                persons: new Map(),
                apiKeys: new Map()
              }),

            loadDiagram: (data) =>
              set({
                nodes: toMap(data.nodes || []),
                arrows: toMap(data.arrows || []),
                persons: toMap(data.persons || []),
                apiKeys: toMap(data.apiKeys || [])
              }),

            exportDiagram: () => ({
              nodes: get().nodeList().map(node => {
                // Filter out UI state properties that React Flow adds
                const nodeData = { ...node } as Record<string, any>;
                delete nodeData.selected;
                delete nodeData.dragging;
                
                // Round position values
                if (nodeData.position) {
                  nodeData.position = {
                    x: Math.round(nodeData.position.x * 10) / 10,
                    y: Math.round(nodeData.position.y * 10) / 10
                  };
                }
                
                return nodeData as Node;
              }),
              arrows: get().arrowList().map(arrow => {
                // Filter out UI state properties from arrows
                const arrowData = { ...arrow } as Record<string, any>;
                delete arrowData.selected;
                delete arrowData.dragging;
                
                return arrowData as Arrow;
              }),
              persons: get().personList(),
              apiKeys: get().apiKeyList()
            }),

            // Compatibility
            isReadOnly: false,
            setReadOnly: (readOnly: boolean) => set({ isReadOnly: readOnly })
          };
        },
        {
          name: 'dipeo-diagram-v2',
          // Serialize Maps to arrays for localStorage
          partialize: (state) => ({
            nodes: state.nodeList(),
            arrows: state.arrowList(),
            persons: state.personList(),
            apiKeys: state.apiKeyList()
          }),
          // Restore arrays back to Maps on load
          merge: (persistedState: unknown, currentState: DiagramStore) => {
            if (!persistedState) return currentState;
            const persisted = persistedState as {
              nodes?: Node[];
              arrows?: Arrow[];
              persons?: Person[];
              apiKeys?: ApiKey[];
            };
            return {
              ...currentState,
              nodes: toMap(persisted.nodes || []),
              arrows: toMap(persisted.arrows || []),
              persons: toMap(persisted.persons || []),
              apiKeys: toMap(persisted.apiKeys || [])
            };
          }
        }
      )
    )
  )
);