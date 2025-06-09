import { createWithEqualityFn } from 'zustand/traditional';
import { devtools, persist } from 'zustand/middleware';
import { shallow } from 'zustand/shallow';
import type { 
  Node, 
  Edge, 
  Connection, 
  NodeChange, 
  EdgeChange,
  OnNodesChange,
  OnEdgesChange,
  OnConnect
} from '@xyflow/react';
import { applyNodeChanges, applyEdgeChanges, addEdge } from '@xyflow/react';
import {
  DomainNode,
  DomainArrow,
  DomainPerson,
  DomainHandle,
  NodeID,
  ArrowID,
  PersonID,
  HandleID,
  ApiKeyID,
  DomainDiagram,
  DomainApiKey,
  NodeKind,
  generateId,
  generateNodeId,
  generateArrowId,
  generatePersonId,
  generateApiKeyId,
  Dict
} from '@/types';
import { DiagramCanvasStore } from './diagramCanvasStore';
import { 
  nodeToReact,
  arrowToReact,
  reactToNode,
  reactToArrow,
  connectionToArrow
} from '@/types/framework/adapters';
import { getNodeConfig } from '@/config';
import { capitalize } from '@/utils/converters/nodeBuilders';
import { generateNodeHandlesFromRegistry } from '@/utils/node/handle-builder';

interface DiagramStore {
  // Internal store instance
  _store: DiagramCanvasStore;
  
  // State
  isReadOnly: boolean;
  
  // Node methods (mapping to DiagramCanvasStore)
  getAllNodes: () => DomainNode[];
  nodeList: () => DomainNode[];
  getNodeById: (id: NodeID) => DomainNode | undefined;
  addNode: (node: DomainNode) => void;
  addNodeByType: (type: NodeKind, position: { x: number; y: number }) => NodeID;
  updateNode: (id: NodeID, updates: Partial<DomainNode>) => void;
  deleteNode: (id: NodeID) => void;
  removeNode: (id: NodeID) => void;
  
  // Arrow methods
  getAllArrows: () => DomainArrow[];
  arrowList: () => DomainArrow[];
  getArrowById: (id: ArrowID) => DomainArrow | undefined;
  addArrow: (arrow: DomainArrow) => void;
  updateArrow: (id: ArrowID, updates: Partial<DomainArrow>) => void;
  deleteArrow: (id: ArrowID) => void;
  removeArrow: (id: ArrowID) => void;
  
  // Person methods
  getAllPersons: () => DomainPerson[];
  personList: () => DomainPerson[];
  getPersonById: (id: PersonID) => DomainPerson | undefined;
  addPerson: (person: DomainPerson) => void;
  createPerson: (data: Omit<DomainPerson, 'id'>) => DomainPerson;
  updatePerson: (id: PersonID, updates: Partial<DomainPerson>) => void;
  deletePerson: (id: PersonID) => void;
  
  // Handle methods
  getNodeHandles: (nodeId: NodeID) => DomainHandle[];
  
  // API Key methods
  getApiKeys: () => DomainApiKey[];
  getAllApiKeys: () => DomainApiKey[];
  getApiKeyById: (id: ApiKeyID) => DomainApiKey | undefined;
  addApiKey: (apiKey: DomainApiKey) => void;
  updateApiKey: (id: ApiKeyID, updates: Partial<DomainApiKey>) => void;
  deleteApiKey: (id: ApiKeyID) => void;
  
  // React Flow handlers
  onNodesChange: OnNodesChange;
  onArrowsChange: OnEdgesChange;
  onConnect: OnConnect;
  
  // Diagram operations
  exportDiagram: () => DomainDiagram;
  loadDiagram: (diagram: DomainDiagram) => void;
  clear: () => void;
  
  // Mode control
  setReadOnly: (readOnly: boolean) => void;
}

export const useDiagramStore = createWithEqualityFn<DiagramStore>()(
  devtools(
    persist(
      (set, get) => {
        // Create internal store instance
        const store = new DiagramCanvasStore();
        
        // Helper to save to history after modifications
        const saveHistory = (action?: string) => {
          // Use setTimeout to ensure state is updated before saving
          setTimeout(() => {
            const historyStore = (window as unknown as { __historyStore?: { saveToHistory: (action?: string) => void } }).__historyStore;
            if (historyStore) {
              historyStore.saveToHistory(action);
            }
          }, 0);
        };
        
        return {
          _store: store,
          isReadOnly: false,
          
          // Node methods
          getAllNodes: () => store.getAllNodes(),
          nodeList: () => store.getAllNodes(),
          
          getNodeById: (id: NodeID) => store.getNode(id),
          
          addNode: (node: DomainNode) => {
            store.addNode(node);
            
            // Generate and add handles if not already present
            const existingHandles = store.getNodeHandles(node.id);
            if (existingHandles.length === 0) {
              const handles = generateNodeHandlesFromRegistry(node.id, node.type);
              handles.forEach(handle => store.addHandle(handle));
            }
            
            set({});
            saveHistory('addNode');
          },
          
          addNodeByType: (type: NodeKind, position: { x: number; y: number }) => {
            const id = generateNodeId();
            const nodeConfig = getNodeConfig(type);
            const defaults = nodeConfig?.defaults || {};
            
            const node: DomainNode = {
              id,
              type,
              position,
              data: {
                label: nodeConfig?.label || capitalize(type),
                ...defaults
              }
            };
            store.addNode(node);
            
            // Generate and add handles for the node
            const handles = generateNodeHandlesFromRegistry(id, type);
            handles.forEach(handle => store.addHandle(handle));
            
            set({});
            saveHistory('addNodeByType');
            return id;
          },
          
          updateNode: (id: NodeID, updates: Partial<DomainNode>) => {
            const node = store.getNode(id);
            if (node) {
              const updated = { ...node, ...updates };
              store.removeNode(id);
              store.addNode(updated);
              set({});
              saveHistory('updateNode');
            }
          },
          
          deleteNode: (id: NodeID) => {
            store.removeNode(id);
            set({});
            saveHistory('deleteNode');
          },
          
          removeNode: (id: NodeID) => {
            store.removeNode(id);
            set({});
            saveHistory('removeNode');
          },
          
          // Arrow methods
          getAllArrows: () => store.getAllArrows(),
          arrowList: () => store.getAllArrows(),
          
          getArrowById: (id: ArrowID) => store.getArrow(id),
          
          addArrow: (arrow: DomainArrow) => {
            store.addArrow(arrow);
            set({});
            saveHistory('addArrow');
          },
          
          updateArrow: (id: ArrowID, updates: Partial<DomainArrow>) => {
            const arrow = store.getArrow(id);
            if (arrow) {
              const updated = { ...arrow, ...updates };
              store.removeArrow(id);
              store.addArrow(updated);
              set({});
              saveHistory('updateArrow');
            }
          },
          
          deleteArrow: (id: ArrowID) => {
            store.removeArrow(id);
            set({});
            saveHistory('deleteArrow');
          },
          
          removeArrow: (id: ArrowID) => {
            store.removeArrow(id);
            set({});
            saveHistory('removeArrow');
          },
          
          // Person methods
          getAllPersons: () => store.getAllPersons(),
          personList: () => store.getAllPersons(),
          
          getPersonById: (id: PersonID) => store.getPerson(id),
          
          addPerson: (person: DomainPerson) => {
            store.addPerson(person);
            set({});
            saveHistory('addPerson');
          },
          
          createPerson: (data: Omit<DomainPerson, 'id'>) => {
            const person: DomainPerson = {
              ...data,
              id: generatePersonId()
            };
            store.addPerson(person);
            set({});
            saveHistory('createPerson');
            return person;
          },
          
          updatePerson: (id: PersonID, updates: Partial<DomainPerson>) => {
            const person = store.getPerson(id);
            if (person) {
              const updated = { ...person, ...updates };
              store.removePerson(id);
              store.addPerson(updated);
              set({});
              saveHistory('updatePerson');
            }
          },
          
          deletePerson: (id: PersonID) => {
            store.removePerson(id);
            set({});
            saveHistory('deletePerson');
          },
          
          // Handle methods
          getNodeHandles: (nodeId: NodeID) => store.getNodeHandles(nodeId),
          
          // API Key methods
          getApiKeys: () => store.getAllApiKeys(),
          getAllApiKeys: () => store.getAllApiKeys(),
          
          getApiKeyById: (id: ApiKeyID) => store.getApiKey(id),
          
          addApiKey: (apiKey: DomainApiKey) => {
            store.addApiKey(apiKey);
            set({});
            saveHistory('addApiKey');
          },
          
          updateApiKey: (id: ApiKeyID, updates: Partial<DomainApiKey>) => {
            const apiKey = store.getApiKey(id);
            if (apiKey) {
              const updated = { ...apiKey, ...updates };
              store.removeApiKey(id);
              store.addApiKey(updated);
              set({});
              saveHistory('updateApiKey');
            }
          },
          
          deleteApiKey: (id: ApiKeyID) => {
            store.removeApiKey(id);
            set({});
            saveHistory('deleteApiKey');
          },
          
          // React Flow handlers
          onNodesChange: (changes: NodeChange[]) => {
            if (get().isReadOnly) return;
            
            // Convert current nodes to React Flow format
            const currentNodes = get().getAllNodes().map(node => {
              const handles = get().getNodeHandles(node.id);
              return nodeToReact(node, handles);
            });
            
            // Apply changes
            const updatedNodes = applyNodeChanges(changes, currentNodes);
            
            // Convert back to domain nodes and update store
            const { _store } = get();
            // Remove all existing nodes first
            _store.getAllNodes().forEach(node => _store.removeNode(node.id));
            // Add updated nodes
            updatedNodes.forEach(rfNode => {
              const domainNode = reactToNode(rfNode);
              _store.addNode(domainNode);
            });
            
            set({});
            saveHistory('onNodesChange');
          },
          
          onArrowsChange: (changes: EdgeChange[]) => {
            if (get().isReadOnly) return;
            
            // Convert current arrows to React Flow format
            const currentEdges = get().getAllArrows().map(arrowToReact);
            
            // Apply changes
            const updatedEdges = applyEdgeChanges(changes, currentEdges);
            
            // Convert back to domain arrows and update store
            const { _store } = get();
            // Remove all existing arrows first
            _store.getAllArrows().forEach(arrow => _store.removeArrow(arrow.id));
            // Add updated arrows
            updatedEdges.forEach(rfEdge => {
              const domainArrow = reactToArrow(rfEdge);
              _store.addArrow(domainArrow);
            });
            
            set({});
            saveHistory('onArrowsChange');
          },
          
          onConnect: (connection: Connection) => {
            if (get().isReadOnly) return;
            
            const arrow = connectionToArrow(connection);
            if (arrow) {
              get().addArrow(arrow);
            }
          },
          
          // Diagram operations
          exportDiagram: (): DomainDiagram => {
            const { _store } = get();
            
            // Convert arrays to Records
            const nodes: Record<NodeID, DomainNode> = {};
            _store.getAllNodes().forEach(node => {
              nodes[node.id] = node;
            });
            
            const handles: Record<HandleID, DomainHandle> = {};
            _store.getAllHandles().forEach(handle => {
              handles[handle.id] = handle;
            });
            
            const arrows: Record<ArrowID, DomainArrow> = {};
            _store.getAllArrows().forEach(arrow => {
              arrows[arrow.id] = arrow;
            });
            
            const persons: Record<PersonID, DomainPerson> = {};
            _store.getAllPersons().forEach(person => {
              persons[person.id] = person;
            });
            
            const apiKeys: Record<ApiKeyID, DomainApiKey> = {};
            _store.getAllApiKeys().forEach(apiKey => {
              apiKeys[apiKey.id] = apiKey;
            });
            
            return {
              nodes,
              handles,
              arrows,
              persons,
              apiKeys,
              metadata: {
                version: '2.0.0',
                created: new Date().toISOString(),
                modified: new Date().toISOString()
              }
            };
          },
          
          loadDiagram: (diagram: DomainDiagram) => {
            const { _store } = get();
            
            // Clear all existing data
            _store.clear();
            
            // Load nodes first
            Object.values(diagram.nodes).forEach(node => _store.addNode(node));
            
            // Load handles, but generate them if missing
            if (Object.keys(diagram.handles).length === 0 && Object.keys(diagram.nodes).length > 0) {
              // No handles in the diagram, generate them for all nodes
              Object.values(diagram.nodes).forEach(node => {
                const handles = generateNodeHandlesFromRegistry(node.id, node.type);
                handles.forEach(handle => _store.addHandle(handle));
              });
            } else {
              // Load existing handles
              Object.values(diagram.handles).forEach(handle => _store.addHandle(handle));
            }
            
            // Load remaining data
            Object.values(diagram.arrows).forEach(arrow => _store.addArrow(arrow));
            Object.values(diagram.persons).forEach(person => _store.addPerson(person));
            Object.values(diagram.apiKeys).forEach(apiKey => _store.addApiKey(apiKey));
            
            set({});
            saveHistory('loadDiagram');
          },
          
          clear: () => {
            const { _store } = get();
            _store.clear();
            set({});
            saveHistory('clear');
          },
          
          // Mode control
          setReadOnly: (readOnly: boolean) => set({ isReadOnly: readOnly })
        };
      },
      {
        name: 'diagram-store',
        partialize: (state) => ({
          // Don't persist the internal store instance
          isReadOnly: state.isReadOnly
        })
      }
    ),
    {
      name: 'DiagramStore'
    }
  ),
  shallow
);

// Export selector hooks
export const useNodes = () => useDiagramStore((state) => state.getAllNodes());
export const useArrows = () => useDiagramStore((state) => state.getAllArrows());
export const usePersons = () => useDiagramStore((state) => state.getAllPersons());
export const useApiKeys = () => useDiagramStore((state) => state.getApiKeys());
export const useIsReadOnly = () => useDiagramStore((state) => state.isReadOnly);