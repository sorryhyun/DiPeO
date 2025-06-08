import { createWithEqualityFn } from 'zustand/traditional';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { generateShortId, generateArrowId } from '@/utils/id';
import { produce, enableMapSet } from 'immer';
import { applyNodeChanges, applyEdgeChanges, Connection, NodeChange, EdgeChange } from '@xyflow/react';
import { Node, Arrow, Person, ApiKey, Handle, NodeKind } from '@/types';
import { NodeID, ArrowID, PersonID, HandleID } from '@/types/branded';
import { createHandleId, parseHandleId } from '@/utils/canvas/handle-adapter';
import { generateNodeHandles, getDefaultHandles } from '@/utils/node';
import { getNodeConfig } from '@/config/helpers';
import { canConnect } from '@/utils/connection-validator';
import { validateConnection } from '@/utils/connections/typed-connection';
import { convertNodeMap } from '@/utils/connections/diagram-bridge';

// Enable Immer MapSet plugin for Map and Set support
enableMapSet();

// Type definitions for Maps
type NodeMap = Map<string, Node>;
type ArrowMap = Map<string, Arrow>;
type PersonMap = Map<string, Person>;
type ApiKeyMap = Map<string, ApiKey>;

export interface DiagramCanvasStore {
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

  // Node mutators (support both string and branded types)
  addNode: (type: Node['type'], position: { x: number; y: number }) => void;
  updateNode: {
    (id: NodeID, data: Record<string, unknown>): void;
    (id: string, data: Record<string, unknown>): void;
  };
  deleteNode: {
    (id: NodeID): void;
    (id: string): void;
  };
  upsertNode: (partial: Partial<Node> & Pick<Node, 'id'>) => void;

  // Arrow mutators (support both string and branded types)
  addArrow: (source: string, target: string, sourceHandle?: string, targetHandle?: string) => void;
  updateArrow: {
    (id: ArrowID, data: Record<string, unknown>): void;
    (id: string, data: Record<string, unknown>): void;
  };
  deleteArrow: {
    (id: ArrowID): void;
    (id: string): void;
  };
  upsertArrow: (partial: Partial<Arrow> & Pick<Arrow, 'id'>) => void;

  // Person mutators (support both string and branded types)
  addPerson: (person: Omit<Person, 'id'>) => void;
  updatePerson: {
    (id: PersonID, data: Partial<Person>): void;
    (id: string, data: Partial<Person>): void;
  };
  deletePerson: {
    (id: PersonID): void;
    (id: string): void;
  };
  getPersonById: {
    (id: PersonID): Person | undefined;
    (id: string): Person | undefined;
  };

  // API Key mutators
  addApiKey: (apiKey: Omit<ApiKey, 'id'>) => void;
  updateApiKey: (id: string, data: Partial<ApiKey>) => void;
  deleteApiKey: (id: string) => void;
  getApiKeyById: (id: string) => ApiKey | undefined;

  // Flow compatibility
  onNodesChange: (changes: NodeChange[]) => void;
  onArrowsChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;

  // Handle registry
  getHandleById: (handleId: string) => { node: Node; handle: Handle } | undefined;
  getHandlesForNode: (nodeId: string) => Handle[];
  
  // Utility
  clear: () => void;
  
  // Compatibility properties
  isReadOnly?: boolean;
  setReadOnly?: (readOnly: boolean) => void;
  
  // Validation methods
  validateAllConnections: () => { valid: Arrow[]; invalid: Array<{ arrow: Arrow; error: string }> };
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

// Store implementation
export const useDiagramCanvasStore = createWithEqualityFn<DiagramCanvasStore>()(
  devtools(
    subscribeWithSelector(
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
            produce<DiagramCanvasStore>(draft => {
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
              ? generateNodeHandles(id, nodeConfig, type) 
              : getDefaultHandles(id, type);
            
            const newNode: Node = {
              id,
              type,
              position,
              data: { type, id },
              handles,
              // Add ReactFlow required properties
              draggable: true,
              selectable: true,
              connectable: true
            } as Node;
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
                
                // Generate handles if not present
                const nodeId = node.id || existing?.id;
                if (!nodeId) {
                  console.error('Cannot upsert node without id');
                  return;
                }
                
                const nodeType = node.type || existing?.type;
                if (!nodeType) {
                  console.error('Cannot upsert node without type');
                  return;
                }
                
                const handles = node.handles || existing?.handles || (() => {
                  const nodeConfig = getNodeConfig(nodeType as NodeKind);
                  return nodeConfig 
                    ? generateNodeHandles(nodeId, nodeConfig, nodeType) 
                    : getDefaultHandles(nodeId, nodeType);
                })();
                
                const updatedNode = { 
                  ...existing, 
                  ...node,
                  handles,
                  // Ensure ReactFlow properties are preserved
                  draggable: node.draggable ?? existing?.draggable ?? true,
                  selectable: node.selectable ?? existing?.selectable ?? true,
                  connectable: node.connectable ?? existing?.connectable ?? true
                } as Node;
                draft.nodes.set(node.id, updatedNode);
              })
            ),

          // Arrow mutators
          addArrow: (sourceNodeId, targetNodeId, sourceHandleName = 'output', targetHandleName = 'input') => {
            const id = generateArrowId();
            // Create handle IDs from node IDs and handle names
            const sourceHandleId = createHandleId(sourceNodeId, sourceHandleName);
            const targetHandleId = createHandleId(targetNodeId, targetHandleName);
            
            // Validate connection using legacy system first
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
            
            // Enhanced type-safe validation using the typed connection system
            try {
              const diagramNodes = convertNodeMap(get().nodes);
              
              // Create a temporary arrow object for validation
              // The validateConnection function expects the new Arrow type from @/types/arrow
              const tempArrow = {
                id: id as ArrowID,
                source: sourceHandleId as HandleID,
                target: targetHandleId as HandleID
              };
              
              const typedValidation = validateConnection(tempArrow, diagramNodes);
              if (!typedValidation.valid) {
                console.error(`Type-safe validation failed: ${typedValidation.error}`);
                // Log detailed information for debugging
                console.error('Connection details:', {
                  source: sourceHandleId,
                  target: targetHandleId,
                  error: typedValidation.error,
                  sourceNode: parseHandleId(sourceHandleId),
                  targetNode: parseHandleId(targetHandleId)
                });
                
                // Fall back to legacy validation for now
                console.warn('Falling back to legacy validation due to type-safe validation failure');
              }
            } catch (error) {
              // If typed validation fails, log the error but don't block the connection
              console.error('Error during typed validation:', error);
              console.warn('Continuing with legacy validation only');
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
              id: `APIKEY_${generateShortId().slice(0, 6).toUpperCase()}`
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
            const { nodeId } = parseHandleId(handleId);
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

          // Compatibility
          isReadOnly: false,
          setReadOnly: (readOnly: boolean) => set({ isReadOnly: readOnly }),
          
          // Validation methods
          validateAllConnections: () => {
            const state = get();
            const diagramNodes = convertNodeMap(state.nodes);
            const arrows = state.arrowList();
            
            const valid: Arrow[] = [];
            const invalid: Array<{ arrow: Arrow; error: string }> = [];
            
            for (const arrow of arrows) {
              const typedArrow = {
                id: arrow.id as ArrowID,
                source: arrow.source as HandleID,
                target: arrow.target as HandleID
              };
              
              const result = validateConnection(typedArrow, diagramNodes);
              if (result.valid) {
                valid.push(arrow);
              } else {
                invalid.push({ arrow, error: result.error || 'Unknown error' });
              }
            }
            
            return { valid, invalid };
          }
        };
      }
    )
  )
);