import { useMemo, useCallback } from 'react';
import { useResource, type ResourceOperations } from '../core/useResource';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import { DiagramConverter } from '@/infrastructure/converters';
import { Converters } from '@/infrastructure/services';
import { DiagramFormat, type DomainDiagram, type DomainNode } from '@dipeo/models';
import { 
  useGetDiagramQuery,
  useCreateDiagramMutation,
  useDeleteDiagramMutation,
  useListDiagramsQuery
} from '@/__generated__/graphql';

// Wrapper type to satisfy useResource constraints
interface DiagramResource extends DomainDiagram {
  id?: string;
}

export interface DiagramOperations extends Omit<ResourceOperations<DiagramResource>, 'validate'> {
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
      
      const domainDiagram = DiagramConverter.toDomain(data.diagram) as DiagramResource;
      
      if (syncWithStore && domainDiagram) {
        const jsonString = JSON.stringify(domainDiagram);
        await store.importDiagram(jsonString);
      }
      
      return { ...domainDiagram, id: targetId };
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
      
      return data.diagrams.map(d => ({ ...DiagramConverter.toDomain(d), id: d.metadata?.id || undefined } as DiagramResource));
    },
    
    create: async (data: Partial<DiagramResource>) => {
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
      
      const domainDiagram = DiagramConverter.toDomain(result.create_diagram?.diagram || {}) as DiagramResource;
      
      if (syncWithStore && domainDiagram) {
        const jsonString = JSON.stringify(domainDiagram);
        await store.importDiagram(jsonString);
      }
      
      return { ...domainDiagram, id: result.create_diagram?.diagram?.metadata?.id || undefined };
    },
    
    update: async (id: string, data: Partial<DiagramResource>) => {
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
      return { ...data, id } as DiagramResource;
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
      let diagram: DiagramResource;
      
      try {
        if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
          const yaml = await import('js-yaml');
          diagram = yaml.load(content) as DiagramResource;
        } else {
          diagram = JSON.parse(content) as DiagramResource;
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
      const diagramJson = store.exportDiagram();
      const diagram = JSON.parse(diagramJson);
      let content: string;
      let filename: string;
      let mimeType: string;
      
      switch (format) {
        case DiagramFormat.NATIVE:
          content = JSON.stringify(diagram, null, 2);
          filename = 'diagram.native.json';
          mimeType = 'application/json';
          break;
        case DiagramFormat.READABLE: {
          const yaml = await import('js-yaml');
          content = yaml.dump(diagram);
          filename = 'diagram.readable.yaml';
          mimeType = 'text/yaml';
          break;
        }
        case DiagramFormat.LIGHT: {
          const yaml = await import('js-yaml');
          content = yaml.dump(diagram);
          filename = 'diagram.light.yaml';
          mimeType = 'text/yaml';
          break;
        }
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
  
  const resource = useResource<DiagramResource>('Diagram', operations as unknown as ResourceOperations<DiagramResource>, {
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
          version: '1.0.0',
          created: new Date().toISOString(),
          modified: new Date().toISOString(),
          createdAt: new Date(),
          modifiedAt: new Date()
        }
      } as DiagramResource;
    }
    return resource.data;
  }, [syncWithStore, store, resource.data]);
  
  return {
    ...resource,
    diagram: currentDiagram,
    operations,
    
    addNode: useCallback((node: DomainNode) => {
      if (syncWithStore) {
        store.addNode(node.type, node.position, node.data);
      }
    }, [syncWithStore, store]),
    
    updateNode: useCallback((nodeId: string, data: Partial<DomainNode>) => {
      if (syncWithStore) {
        store.updateNode(Converters.toNodeId(nodeId), data);
      }
    }, [syncWithStore, store]),
    
    removeNode: useCallback((nodeId: string) => {
      if (syncWithStore) {
        store.deleteNode(Converters.toNodeId(nodeId));
      }
    }, [syncWithStore, store]),
    
    clearDiagram: useCallback(() => {
      operations.clearAll();
    }, [operations])
  };
}