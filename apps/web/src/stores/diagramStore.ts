import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { generateShortId, entityIdGenerators } from '@/utils/id';
import { produce, enableMapSet } from 'immer';
import { applyNodeChanges, applyEdgeChanges, Connection, NodeChange, EdgeChange } from '@xyflow/react';
import { Node, Arrow, Person, ApiKey, Handle } from '@/types';
import { createHandleId, parseHandleId } from '@/utils/canvas/handle-adapter';
import { generateNodeHandles, getDefaultHandles } from '@/utils/node';
import { getNodeConfig } from '@/config/helpers';
import { canConnect } from '@/utils/connection-validator';

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

  // Handle registry
  getHandleById: (handleId: string) => { node: Node; handle: Handle } | undefined;
  getHandlesForNode: (nodeId: string) => Handle[];
  
  // Utility
  clear: () => void;
  loadDiagram: (data: { nodes: Node[]; arrows: Arrow[]; persons: Person[]; apiKeys?: ApiKey[] }) => void;
  exportDiagram: () => { nodes: Node[]; arrows: Arrow[]; persons: Person[]; apiKeys: ApiKey[] };
  
  // Label-based persistence
  exportDiagramWithLabels: () => { nodes: any[]; arrows: any[]; persons: any[]; apiKeys: any[] };
  loadDiagramFromLabels: (data: { nodes?: any[]; arrows?: any[]; persons?: any[]; apiKeys?: any[] }) => void;

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
            // Convert our Node[] to NodeBase[] for ReactFlow
            const rfNodes = currentNodes as any[];
            const updatedRfNodes = applyNodeChanges(filteredChanges, rfNodes);
            // Convert back to our Node type
            const updatedNodes = updatedRfNodes as Node[];
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
              const id = `${type}-${generateShortId().slice(0, 4)}`;
              const nodeConfig = getNodeConfig(type);
              const handles = nodeConfig 
                ? generateNodeHandles(id, nodeConfig) 
                : getDefaultHandles(id, type);
              
              const newNode: Node = {
                id,
                type,
                position,
                data: { type, id },
                handles
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
                    // Parse handle IDs to get node IDs
                    const { nodeId: sourceNodeId } = parseHandleId(arrow.source);
                    const { nodeId: targetNodeId } = parseHandleId(arrow.target);
                    // Delete arrow if it connects to/from this node
                    if (sourceNodeId === id || targetNodeId === id) {
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
            addArrow: (sourceNodeId, targetNodeId, sourceHandleName = 'output', targetHandleName = 'input') => {
              const id = `arrow-${generateShortId().slice(0, 4)}`;
              // Create handle IDs from node IDs and handle names
              const sourceHandleId = createHandleId(sourceNodeId, sourceHandleName);
              const targetHandleId = createHandleId(targetNodeId, targetHandleName);
              
              // Validate connection
              const state = get();
              const validation = canConnect(
                sourceHandleId,
                targetHandleId,
                state.nodes,
                state.arrowList()
              );
              
              if (!validation.valid) {
                console.warn(`Connection validation failed: ${validation.reason}`);
                return;
              }
              
              const newArrow: Arrow = {
                id,
                source: sourceHandleId,  // Handle ID
                target: targetHandleId,  // Handle ID
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
              const id = `person-${generateShortId().slice(0, 4)}`;
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
                id: entityIdGenerators.apiKey()
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
                // Convert our Node[] to NodeBase[] for ReactFlow
                const rfNodes = currentNodes as any[];
                const updatedRfNodes = applyNodeChanges(filteredChanges, rfNodes);
                // Convert back to our Node type
                const updatedNodes = updatedRfNodes as Node[];
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
              // Convert our Arrow[] to EdgeBase[] for ReactFlow
              const rfEdges = currentArrows as any[];
              const updatedRfEdges = applyEdgeChanges(changes, rfEdges);
              // Convert back to our Arrow type
              const updatedArrows = updatedRfEdges as Arrow[];
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
              // In ReactFlow, source/target are node IDs, sourceHandle/targetHandle are handle names
              const sourceHandleName = sourceHandle || 'output';
              const targetHandleName = targetHandle || 'input';
              
              // Pre-validate before calling addArrow
              const sourceHandleId = createHandleId(source, sourceHandleName);
              const targetHandleId = createHandleId(target, targetHandleName);
              const state = get();
              const validation = canConnect(
                sourceHandleId,
                targetHandleId,
                state.nodes,
                state.arrowList()
              );
              
              if (!validation.valid) {
                // TODO: Show user-friendly error message
                console.error(`Cannot connect: ${validation.reason}`);
                return;
              }
              
              // Use addArrow which now includes validation
              get().addArrow(source, target, sourceHandleName, targetHandleName);
            },

            // Handle registry
            getHandleById: (handleId) => {
              const { nodeId, handleName } = parseHandleId(handleId);
              const node = get().nodes.get(nodeId);
              if (!node || !node.handles) return undefined;
              
              const handle = node.handles.find(h => h.id === handleId);
              if (!handle) return undefined;
              
              return { node, handle };
            },
            
            getHandlesForNode: (nodeId) => {
              const node = get().nodes.get(nodeId);
              return node?.handles || [];
            },

            // Utility
            clear: () =>
              set({
                nodes: new Map(),
                arrows: new Map(),
                persons: new Map(),
                apiKeys: new Map()
              }),

            loadDiagram: (data) => {
              // Check if this is the new label-based format
              if (data.nodes && data.nodes.length > 0 && data.nodes[0] && !data.nodes[0].id) {
                // New format - use label-based loader
                get().loadDiagramFromLabels(data);
              } else {
                // Old format - direct load
                set({
                  nodes: toMap(data.nodes || []),
                  arrows: toMap(data.arrows || []),
                  persons: toMap(data.persons || []),
                  apiKeys: toMap(data.apiKeys || [])
                });
              }
            },

            exportDiagram: () => {
              // Use label-based export
              return get().exportDiagramWithLabels();
            },
            
            exportDiagramWithLabels: () => {
              const state = get();
              const nodes = state.nodeList();
              const arrows = state.arrowList();
              const persons = state.personList();
              const apiKeys = state.apiKeyList();
              
              // Create ID to label mappings
              const nodeIdToLabel = new Map<string, string>();
              const personIdToLabel = new Map<string, string>();
              const apiKeyIdToLabel = new Map<string, string>();
              
              // Build mappings
              nodes.forEach(node => {
                const label = (node.data as any).label || node.id;
                nodeIdToLabel.set(node.id, label);
              });
              persons.forEach(person => {
                personIdToLabel.set(person.id, person.label || person.id);
              });
              apiKeys.forEach(apiKey => {
                apiKeyIdToLabel.set(apiKey.id, apiKey.name || apiKey.id);
              });
              
              // Export nodes without IDs, using labels for references
              const exportedNodes = nodes.map(node => {
                const nodeData = { ...node } as Record<string, any>;
                delete nodeData.id;
                delete nodeData.selected;
                delete nodeData.dragging;
                
                // Remove id from data property by creating a new object
                if (nodeData.data?.id) {
                  const { id: _, ...dataWithoutId } = nodeData.data;
                  nodeData.data = dataWithoutId;
                }
                
                // Replace ID references with labels
                if (nodeData.data.personId && personIdToLabel.has(nodeData.data.personId)) {
                  nodeData.data.personLabel = personIdToLabel.get(nodeData.data.personId);
                  delete nodeData.data.personId;
                }
                
                // Round position values
                if (nodeData.position) {
                  nodeData.position = {
                    x: Math.round(nodeData.position.x * 10) / 10,
                    y: Math.round(nodeData.position.y * 10) / 10
                  };
                }
                
                // Add label as top-level property
                nodeData.label = (node.data as any).label || node.id;
                
                return nodeData;
              });
              
              // Export arrows without IDs, using labels for source/target
              const exportedArrows = arrows.map(arrow => {
                const arrowData = { ...arrow } as Record<string, any>;
                delete arrowData.id;
                delete arrowData.selected;
                delete arrowData.dragging;
                
                // Clean up data property - remove id
                if (arrowData.data?.id) {
                  const { id: _, ...dataWithoutId } = arrowData.data;
                  arrowData.data = dataWithoutId;
                }
                
                // Parse handle IDs to extract node IDs and handle names
                const { nodeId: sourceNodeId, handleName: sourceHandleName } = parseHandleId(arrow.source);
                const { nodeId: targetNodeId, handleName: targetHandleName } = parseHandleId(arrow.target);
                
                // Replace node IDs with labels
                arrowData.sourceLabel = nodeIdToLabel.get(sourceNodeId) || sourceNodeId;
                arrowData.targetLabel = nodeIdToLabel.get(targetNodeId) || targetNodeId;
                arrowData.sourceHandle = `${arrowData.sourceLabel}-${sourceHandleName}`;
                arrowData.targetHandle = `${arrowData.targetLabel}-${targetHandleName}`;
                
                delete arrowData.source;
                delete arrowData.target;
                
                return arrowData;
              });
              
              // Export persons without IDs, using labels for API key references
              const exportedPersons = persons.map(person => {
                const personData = { ...person } as Record<string, any>;
                delete personData.id;
                
                // Replace API key ID with label
                if (personData.apiKeyId && apiKeyIdToLabel.has(personData.apiKeyId)) {
                  personData.apiKeyLabel = apiKeyIdToLabel.get(personData.apiKeyId);
                  delete personData.apiKeyId;
                }
                
                // Use label as name if not already set
                personData.name = person.label || person.id;
                
                return personData;
              });
              
              // Export API keys without IDs
              const exportedApiKeys = apiKeys.map(apiKey => {
                const apiKeyData = { ...apiKey } as Record<string, any>;
                delete apiKeyData.id;
                return apiKeyData;
              });
              
              return {
                nodes: exportedNodes,
                arrows: exportedArrows,
                persons: exportedPersons,
                apiKeys: exportedApiKeys
              };
            },
            
            loadDiagramFromLabels: (data: { 
              nodes?: Array<Partial<Node> & { label?: string; type: Node['type']; data?: any }>; 
              arrows?: Array<{ sourceLabel?: string; targetLabel?: string; sourceHandle?: string; targetHandle?: string; data?: any }>; 
              persons?: Array<Partial<Person> & { name?: string; apiKeyLabel?: string }>; 
              apiKeys?: Array<Partial<ApiKey> & { name: string }> 
            }) => {
              // Handle duplicate labels by appending suffixes
              const ensureUniqueLabel = (label: string, existingLabels: Set<string>): string => {
                if (!existingLabels.has(label)) {
                  existingLabels.add(label);
                  return label;
                }
                
                // Try appending numbers
                let counter = 2;
                while (existingLabels.has(`${label}_${counter}`)) {
                  counter++;
                }
                const uniqueLabel = `${label}_${counter}`;
                existingLabels.add(uniqueLabel);
                return uniqueLabel;
              };
              
              // Track used labels
              const usedNodeLabels = new Set<string>();
              const usedPersonLabels = new Set<string>();
              const usedApiKeyLabels = new Set<string>();
              
              // Create label to ID mappings
              const nodeLabelToId = new Map<string, string>();
              const personLabelToId = new Map<string, string>();
              const apiKeyLabelToId = new Map<string, string>();
              
              // Process API keys first
              const apiKeys: ApiKey[] = (data.apiKeys || []).map((apiKeyData) => {
                const id = entityIdGenerators.apiKey();
                const label = ensureUniqueLabel(apiKeyData.name || 'API Key', usedApiKeyLabels);
                apiKeyLabelToId.set(label, id);
                
                return {
                  ...apiKeyData,
                  id,
                  name: label,
                  service: apiKeyData.service || 'custom'
                } as ApiKey;
              });
              
              // Process persons
              const persons: Person[] = (data.persons || []).map((personData) => {
                const id = `person-${generateShortId().slice(0, 4)}`;
                const label = ensureUniqueLabel(personData.name || personData.label || 'Person', usedPersonLabels);
                personLabelToId.set(label, id);
                
                // Resolve API key reference
                let apiKeyId = personData.apiKeyId;
                if (personData.apiKeyLabel && apiKeyLabelToId.has(personData.apiKeyLabel)) {
                  apiKeyId = apiKeyLabelToId.get(personData.apiKeyLabel);
                }
                
                return {
                  ...personData,
                  id,
                  label,
                  apiKeyId
                };
              });
              
              // Process nodes
              const nodes: Node[] = (data.nodes || []).map((nodeData) => {
                const id = `${nodeData.type}-${generateShortId().slice(0, 4)}`;
                const label = ensureUniqueLabel(nodeData.label || nodeData.data?.label || nodeData.type, usedNodeLabels);
                nodeLabelToId.set(label, id);
                
                // Resolve person reference
                let personId = nodeData.data?.personId;
                if (nodeData.data?.personLabel && personLabelToId.has(nodeData.data.personLabel)) {
                  personId = personLabelToId.get(nodeData.data.personLabel);
                }
                
                return {
                  ...nodeData,
                  id,
                  type: nodeData.type,
                  position: nodeData.position || { x: 0, y: 0 },
                  data: {
                    ...nodeData.data,
                    id,
                    label,
                    personId
                  }
                } as Node;
              });
              
              // Process arrows
              const arrows: Arrow[] = (data.arrows || [])
                .map((arrowData) => {
                const id = `arrow-${generateShortId().slice(0, 4)}`;
                
                // Resolve source/target node IDs from labels
                let sourceNodeId = arrowData.sourceLabel ? nodeLabelToId.get(arrowData.sourceLabel) : undefined;
                let targetNodeId = arrowData.targetLabel ? nodeLabelToId.get(arrowData.targetLabel) : undefined;
                
                // If no mapping found, try to use the label as is (might be an ID)
                if (!sourceNodeId && arrowData.sourceLabel) {
                  sourceNodeId = arrowData.sourceLabel;
                }
                if (!targetNodeId && arrowData.targetLabel) {
                  targetNodeId = arrowData.targetLabel;
                }
                
                // Construct handle IDs from node IDs and handle names
                let sourceHandleId = '';
                let targetHandleId = '';
                
                if (sourceNodeId && arrowData.sourceHandle) {
                  // Extract handle name from label-based handle
                  // e.g., "aa-output-default" -> "output-default"
                  const handleParts = arrowData.sourceHandle.split('-');
                  const handleName = handleParts.slice(1).join('-');
                  sourceHandleId = createHandleId(sourceNodeId, handleName);
                }
                
                if (targetNodeId && arrowData.targetHandle) {
                  // Extract handle name from label-based handle
                  // e.g., "bb-input-first" -> "input-first"
                  const handleParts = arrowData.targetHandle.split('-');
                  const handleName = handleParts.slice(1).join('-');
                  targetHandleId = createHandleId(targetNodeId, handleName);
                }
                
                // Fallback if no handle information
                if (!sourceHandleId && sourceNodeId) {
                  sourceHandleId = createHandleId(sourceNodeId, 'output');
                }
                if (!targetHandleId && targetNodeId) {
                  targetHandleId = createHandleId(targetNodeId, 'input');
                }
                
                // Skip arrow if we couldn't resolve both handle IDs
                if (!sourceHandleId || !targetHandleId) {
                  console.warn(`Cannot create arrow: missing handle IDs`, arrowData);
                  return null;
                }
                
                return {
                  ...arrowData,
                  id,
                  source: sourceHandleId,
                  target: targetHandleId,
                  data: {
                    ...arrowData.data,
                    id
                  }
                };
              })
              .filter((arrow) => arrow !== null) as Arrow[];
              
              // Set all data
              set({
                nodes: toMap(nodes),
                arrows: toMap(arrows),
                persons: toMap(persons),
                apiKeys: toMap(apiKeys)
              });
            },

            // Compatibility
            isReadOnly: false,
            setReadOnly: (readOnly: boolean) => set({ isReadOnly: readOnly })
          };
        },
        {
          name: 'dipeo-diagram-v2',
          // Serialize Maps to arrays for localStorage using label-based format
          partialize: (state) => state.exportDiagramWithLabels(),
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