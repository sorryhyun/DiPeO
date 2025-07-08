import {  DomainApiKey, DomainArrow, DomainHandle, DomainNode, DomainPerson,  apiKeyId } from '@/core/types';
import { type ApiKeyID, type NodeID, type ArrowID, type PersonID, type HandleID, NodeType, Vec2, LLMService } from '@dipeo/domain-models';
import { generateNodeId, generateArrowId, generatePersonId, entityIdGenerators } from '@/core/types/utilities';
import { NODE_CONFIGS_MAP, generateNodeLabel } from '@/features/diagram-editor/config/nodes';

// Helper to create a node
export function createNode(type: NodeType, position: Vec2, initialData?: Record<string, unknown>): DomainNode {
  const id = generateNodeId();
  const nodeConfig = NODE_CONFIGS_MAP[type];
  const configDefaults = nodeConfig ? { ...nodeConfig.defaults } : {};
  
  const label = String(initialData?.label || configDefaults.label || generateNodeLabel(type, id));
  
  return {
    id,
    type,
    position: {
      x: position?.x ?? 0,
      y: position?.y ?? 0
    },
    data: {
      ...configDefaults,
      ...initialData,
      label,
    }
  };
}

// Simplified import state factory
export function createImportState() {
  const nodes = new Map<NodeID, DomainNode>();
  const arrows = new Map<ArrowID, DomainArrow>();
  const persons = new Map<PersonID, DomainPerson>();
  const handles = new Map<string, DomainHandle>();
  const apiKeys = new Map<ApiKeyID, DomainApiKey>();
  
  return {
    nodes,
    arrows,
    persons,
    handles,
    apiKeys,
    
    // Minimal set of methods needed for import
    addNode: (
      type: NodeType, 
      position: Vec2, 
      initialData?: Record<string, unknown>
    ) => {
      const node = createNode(type, position, initialData);
      nodes.set(node.id as NodeID, node);
      
      return node.id;
    },
    
    addArrow: (source: string, target: string, data?: Record<string, unknown>) => {
      const arrowId = generateArrowId();
      arrows.set(arrowId, {
        id: arrowId,
        source: source as HandleID,
        target: target as HandleID,
        data: data || {},
      });
      return arrowId;
    },
    
    addPerson: (label: string, service: string, model: string, apiKeyIdValue?: string) => {
      const personId = generatePersonId();
      persons.set(personId, {
        id: personId,
        label,
        llm_config: {
          api_key_id: apiKeyId(apiKeyIdValue || ''),
          service: service as LLMService,
          model,
          system_prompt: ''
        },
        type: 'person'
      });
      return personId;
    },
    
    addApiKey: (label: string, service: string) => {
      const id = apiKeyId(entityIdGenerators.apiKey());
      apiKeys.set(id, {
        id,
        label,
        service: service as any,
        masked_key: '••••••••'
      });
      return id;
    },
    
    updateNode: (id: NodeID, updates: Partial<DomainNode>) => {
      const node = nodes.get(id);
      if (node && updates.data) {
        node.data = { ...node.data, ...updates.data };
      }
    },
    
    updatePerson: (id: PersonID, updates: Partial<DomainPerson>) => {
      const person = persons.get(id);
      if (person) {
        Object.assign(person, updates);
      }
    },
    
    transaction: (fn: () => void) => fn(),
    clearAll: () => {
      nodes.clear();
      arrows.clear();
      persons.clear();
      handles.clear();
      apiKeys.clear();
    }
  };
}

