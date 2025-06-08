import { createWithEqualityFn } from 'zustand/traditional';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { produce } from 'immer';
import { generateShortId, entityIdGenerators } from '@/utils/id';
import { createHandleId, parseHandleId } from '@/utils/canvas/handle-adapter';
import { generateNodeHandles, getDefaultHandles } from '@/utils/node';
import { getNodeConfig } from '@/config/helpers';
import { Node, Arrow, Person, ApiKey } from '@/types';
import { NodeKind } from '@/types';

type NodeMap = Map<string, Node>;
type ArrowMap = Map<string, Arrow>;
type PersonMap = Map<string, Person>;
type ApiKeyMap = Map<string, ApiKey>;

export interface DiagramExportStore {
  // Label-based persistence
  exportDiagramWithLabels: () => { 
    nodes: Record<string, unknown>[]; 
    arrows: Record<string, unknown>[]; 
    persons: Record<string, unknown>[]; 
    apiKeys: Record<string, unknown>[] 
  };
  loadDiagramFromLabels: (data: { 
    nodes?: Record<string, unknown>[]; 
    arrows?: Record<string, unknown>[]; 
    persons?: Record<string, unknown>[]; 
    apiKeys?: Record<string, unknown>[] 
  }) => void;
  
  // Legacy export/import
  exportDiagram: () => { nodes: Node[]; arrows: Arrow[]; persons: Person[]; apiKeys: ApiKey[] };
  loadDiagram: (data: { nodes: Node[]; arrows: Arrow[]; persons: Person[]; apiKeys?: ApiKey[] }) => void;
  
  // Access to underlying data (needed for export functions)
  nodes: NodeMap;
  arrows: ArrowMap;
  persons: PersonMap;
  apiKeys: ApiKeyMap;
  
  // Setters
  setNodes: (nodes: Node[]) => void;
  setArrows: (arrows: Arrow[]) => void;
  setPersons: (persons: Person[]) => void;
  setApiKeys: (apiKeys: ApiKey[]) => void;
}

const toMap = <T extends { id: string }>(arr: T[]): Map<string, T> =>
  new Map(arr.map(obj => [obj.id, obj]));

export const useDiagramExportStore = createWithEqualityFn<DiagramExportStore>()(
  devtools(
    subscribeWithSelector(
      persist(
        (set, get) => ({
          // State - using Maps for O(1) operations
          nodes: new Map(),
          arrows: new Map(),
          persons: new Map(),
          apiKeys: new Map(),

          // Batch operations
          setNodes: (nodes) => set({ nodes: toMap(nodes) }),
          setArrows: (arrows) => set({ arrows: toMap(arrows) }),
          setPersons: (persons) => set({ persons: toMap(persons) }),
          setApiKeys: (apiKeys) => set({ apiKeys: toMap(apiKeys) }),

          loadDiagram: (data) => {
            // Check if this is the new label-based format
            if (data.nodes && data.nodes.length > 0 && data.nodes[0] && !data.nodes[0].id) {
              // New format - use label-based loader
              get().loadDiagramFromLabels(data);
            } else {
              // Old format - ensure nodes have ReactFlow properties and handles
              const nodesWithDefaults = (data.nodes || []).map(node => {
                // Generate handles if not present
                const handles = node.handles || (() => {
                  const nodeConfig = getNodeConfig(node.type as NodeKind);
                  return nodeConfig 
                    ? generateNodeHandles(node.id, nodeConfig, node.type) 
                    : getDefaultHandles(node.id, node.type);
                })();
                
                return {
                  ...node,
                  handles,
                  draggable: node.draggable ?? true,
                  selectable: node.selectable ?? true,
                  connectable: node.connectable ?? true
                };
              });
              
              set({
                nodes: toMap(nodesWithDefaults),
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
            const nodes = Array.from(state.nodes.values());
            const arrows = Array.from(state.arrows.values());
            const persons = Array.from(state.persons.values());
            const apiKeys = Array.from(state.apiKeys.values());
            
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
              
              // Generate handles if not provided
              const nodeConfig = getNodeConfig(nodeData.type);
              const handles = nodeData.handles || (nodeConfig 
                ? generateNodeHandles(id, nodeConfig, nodeData.type) 
                : getDefaultHandles(id, nodeData.type));
              
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
                },
                handles,
                // Add ReactFlow required properties
                draggable: nodeData.draggable ?? true,
                selectable: nodeData.selectable ?? true,
                connectable: nodeData.connectable ?? true
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
          }
        }),
        {
          name: 'dipeo-diagram-export-v2',
          // Serialize Maps to arrays for localStorage using label-based format
          partialize: (state) => state.exportDiagramWithLabels(),
          // Restore arrays back to Maps on load
          merge: (persistedState: unknown, currentState: DiagramExportStore) => {
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