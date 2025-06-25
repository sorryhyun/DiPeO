import {  DomainApiKey, DomainArrow, DomainHandle, DomainNode, DomainPerson,  apiKeyId } from '@/core/types';
import { type ApiKeyID, type NodeID, type ArrowID, type PersonID, NodeType, Vec2 } from '@dipeo/domain-models';
import { generateNodeId, generateArrowId, generatePersonId, entityIdGenerators } from '@/core/types/utilities';
import { generateNodeLabel } from '@/core/config/nodeMeta';
import { getNodeDefaults } from '@/core/config';

// Helper to create a node
export function createNode(type: NodeType, position: Vec2, initialData?: Record<string, unknown>): DomainNode {
  const id = generateNodeId();
  const configDefaults = getNodeDefaults(type);
  
  const label = initialData?.label || configDefaults.label || generateNodeLabel(type, id);
  
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
    },
    displayName: label,
    handles: [] // Handles will be added separately
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
    addNode: (type: NodeType, position: Vec2, initialData?: Record<string, unknown>) => {
      const node = createNode(type, position, initialData);
      nodes.set(node.id as NodeID, node);
      
      return node.id;
    },
    
    addArrow: (source: string, target: string, data?: Record<string, unknown>) => {
      const arrowId = generateArrowId();
      arrows.set(arrowId, {
        id: arrowId,
        source: source as any,
        target: target as any,
        data: data || {},
      });
      return arrowId;
    },
    
    addPerson: (label: string, service: string, model: string) => {
      const personId = generatePersonId();
      persons.set(personId, {
        id: personId,
        label,
        apiKeyId: '',
        service: service as any,
        model,
        systemPrompt: '',
        type: 'person',
        maskedApiKey: null
      });
      return personId;
    },
    
    addApiKey: (label: string, service: string) => {
      const id = apiKeyId(entityIdGenerators.apiKey());
      apiKeys.set(id, {
        id,
        label,
        service: service as any,
        maskedKey: '••••••••'
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

