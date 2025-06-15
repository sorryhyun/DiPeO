import { Draft } from 'immer';
import { UnifiedStore } from '../unifiedStore.types';
import { logger } from '@/utils/logger';
import {
  NodeID, ArrowID, PersonID, ApiKeyID, HandleID,
  DomainNode, DomainArrow, DomainPerson, DomainHandle, DomainApiKey,
  NodeKind, Vec2, generateNodeId, generateArrowId, generatePersonId,
  entityIdGenerators, apiKeyId
} from '@/types';
import { generateNodeLabel } from '@/config/nodeMeta';
import { getNodeDefaults } from '@/config';
import { generateNodeHandles } from '@/utils/node/handle-builder';
import { getNodeConfig } from '@/config';

// Helper to create a node
export function createNode(type: NodeKind, position: Vec2, initialData?: Record<string, unknown>): DomainNode {
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
    displayName: label
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
    addNode: (type: NodeKind, position: Vec2, initialData?: Record<string, unknown>) => {
      const node = createNode(type, position, initialData);
      nodes.set(node.id as NodeID, node);
      
      // Auto-generate handles
      const nodeConfig = getNodeConfig(type);
      if (nodeConfig) {
        const nodeHandles = generateNodeHandles(node.id as NodeID, nodeConfig, type);
        nodeHandles.forEach((handle: DomainHandle) => handles.set(handle.id as HandleID, handle));
      }
      
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
        forgettingMode: 'no_forget',
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

// DEPRECATED: Import handler - use GraphQL operations instead
export function importDiagram(state: Draft<UnifiedStore>, data: any) {
  logger.warn('importDiagram helper is deprecated. Use GraphQL operations for import/export.');
  // This function is no longer used as import/export is handled by the backend
}