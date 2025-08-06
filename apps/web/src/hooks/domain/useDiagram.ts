import { useMemo, useCallback } from 'react';
import { useResource, type ResourceOperations } from '../core/useResource';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { DiagramConverter } from '@/core/services/converters';
import { DiagramFormat, type DomainDiagram, type DomainNode } from '@dipeo/models';
import { 
  useGetDiagramQuery,
  useCreateDiagramMutation,
  useDeleteDiagramMutation,
  useListDiagramsQuery
} from '@/__generated__/graphql';

export interface DiagramOperations extends Omit<ResourceOperations<DomainDiagram>, 'validate'> {
  loadFromFile: (file: File) => Promise<void>;
  exportAs: (format: DiagramFormat) => Promise<void>;
  validate: () => Promise<{ isValid: boolean; errors: string[] }>;
  clearAll: () => void;
}

export interface UseDiagramOptions {
  diagramId?: string;
  autoLoad?: boolean;
  syncWithStore?: boolean;
  showToasts?: boolean;
}

export function useDiagram(options: UseDiagramOptions = {}) {
  const {
    diagramId,
    syncWithStore = true,
    showToasts = true
  } = options;
  
  const store = useUnifiedStore();
  const [createDiagram] = useCreateDiagramMutation();
  const [deleteDiagram] = useDeleteDiagramMutation();
  
  const operations: DiagramOperations = useMemo(() => ({
    fetch: async (id?: string) => {
      const targetId = id || diagramId;
      if (!targetId) throw new Error('No diagram ID provided');
      
      const { data } = await useGetDiagramQuery({
        variables: { id: targetId }
      }).refetch();
      
      if (!data?.diagram) {
        throw new Error('Diagram not found');
      }
      
      const domainDiagram = DiagramConverter.toDomain(data.diagram) as DomainDiagram;
      
      if (syncWithStore && domainDiagram) {
        const jsonString = JSON.stringify(domainDiagram);
        await store.importDiagram(jsonString);
      }
      
      return domainDiagram;
    },
    
    list: async (params?: Record<string, any>) => {
      const { data } = await useListDiagramsQuery({
        variables: {
          offset: params?.offset || 0,
          limit: params?.limit || 50,
          filter: params?.filter
        }
      }).refetch();
      
      if (!data?.diagrams) {
        return [];
      }
      
      return data.diagrams.map(d => DiagramConverter.toDomain(d) as DomainDiagram);
    },
    
    create: async (data: Partial<DomainDiagram>) => {
      const { data: result } = await createDiagram({
        variables: {
          input: {
            name: data.metadata?.name || 'Untitled Diagram',
            description: data.metadata?.description
          }
        }
      });
      
      if (!result?.create_diagram) {
        throw new Error('Failed to create diagram');
      }
      
      const domainDiagram = DiagramConverter.toDomain(result.create_diagram?.diagram || {}) as DomainDiagram;
      
      if (syncWithStore && domainDiagram) {
        const jsonString = JSON.stringify(domainDiagram);
        await store.importDiagram(jsonString);
      }
      
      return domainDiagram;
    },
    
    update: async (id: string, data: Partial<DomainDiagram>) => {
      // Since there's no update mutation, use create with existing ID
      // or just update the store directly
      if (syncWithStore) {
        // Update nodes and arrows in store
        if (data.nodes) {
          data.nodes.forEach(node => {
            store.updateNode(node.id, node);
          });
        }
        if (data.arrows) {
          data.arrows.forEach(arrow => {
            store.updateArrow(arrow.id, arrow);
          });
        }
        if (data.metadata?.name) {
          store.setDiagramName(data.metadata.name);
        }
        if (data.metadata?.description) {
          store.setDiagramDescription(data.metadata.description);
        }
      }
      return { ...data } as DomainDiagram;
    },
    
    delete: async (id: string) => {
      const { data } = await deleteDiagram({
        variables: { id }
      });
      
      if (data?.delete_diagram && syncWithStore) {
        store.clearDiagram();
      }
      
      return data?.delete_diagram?.success || false;
    },
    
    
    loadFromFile: async (file: File) => {
      const content = await file.text();
      let diagram: DomainDiagram;
      
      try {
        if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
          const yaml = await import('js-yaml');
          diagram = yaml.load(content) as DomainDiagram;
        } else {
          diagram = JSON.parse(content) as DomainDiagram;
        }
      } catch (error) {
        throw new Error(`Failed to parse file: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
      
      if (syncWithStore && diagram) {
        const jsonString = JSON.stringify(diagram);
        await store.importDiagram(jsonString);
      }
    },
    
    exportAs: async (format: DiagramFormat) => {
      const diagram = store.exportDiagram();
      let content: string;
      let filename: string;
      let mimeType: string;
      
      switch (format) {
        case DiagramFormat.NATIVE:
          content = JSON.stringify(diagram, null, 2);
          filename = 'diagram.json';
          mimeType = 'application/json';
          break;
        case DiagramFormat.READABLE: {
          content = JSON.stringify(diagram, null, 2);
          filename = 'diagram.readable.json';
          mimeType = 'application/json';
          break;
        }
        case DiagramFormat.LIGHT:
          content = JSON.stringify(diagram, null, 2);
          filename = 'diagram.light.json';
          mimeType = 'application/json';
          break;
        default:
          throw new Error(`Unsupported format: ${format}`);
      }
      
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
    
    validate: async () => {
      return store.validateDiagram();
    },
    
    clearAll: () => {
      store.clearAll();
    }
  }), [diagramId, syncWithStore, store, createDiagram, deleteDiagram]);
  
  const resource = useResource<DomainDiagram>('Diagram', operations, {
    showToasts,
    optimisticUpdates: true,
    onSuccess: (operation, data) => {
      console.log(`[Diagram] ${operation} successful`, data);
    },
    onError: (operation, error) => {
      console.error(`[Diagram] ${operation} failed:`, error);
    }
  });
  
  const currentDiagram = useMemo(() => {
    if (syncWithStore) {
      const nodes = Array.from(store.nodes.values());
      const arrows = Array.from(store.arrows.values());
      const persons = Array.from(store.persons.values());
      const handles = Array.from(store.handles.values());
      
      return {
        nodes,
        arrows,
        persons,
        handles,
        metadata: {
          id: store.diagramId,
          name: store.diagramName,
          description: store.diagramDescription,
          createdAt: new Date(),
          modifiedAt: new Date()
        }
      } as DomainDiagram;
    }
    return resource.data;
  }, [syncWithStore, store, resource.data]);
  
  return {
    ...resource,
    diagram: currentDiagram,
    operations,
    
    addNode: useCallback((node: DomainNode) => {
      if (syncWithStore) {
        store.addNode(node);
      }
    }, [syncWithStore, store]),
    
    updateNode: useCallback((nodeId: string, data: Partial<DomainNode>) => {
      if (syncWithStore) {
        store.updateNode(nodeId, data);
      }
    }, [syncWithStore, store]),
    
    removeNode: useCallback((nodeId: string) => {
      if (syncWithStore) {
        store.removeNode(nodeId);
      }
    }, [syncWithStore, store]),
    
    clearDiagram: useCallback(() => {
      operations.clearAll();
    }, [operations])
  };
}