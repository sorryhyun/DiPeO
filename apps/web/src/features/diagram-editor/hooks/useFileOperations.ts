import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import {
  selectFile,
  saveDiagram as saveDiagramFile,
  downloadFile
} from '@/lib/utils/file';
import { DiagramFormat } from '@dipeo/models';
import { serializeDiagram } from '@/features/diagram-editor/utils/diagramSerializer';
import { createEntityMutation } from '@/lib/graphql/hooks';
import { 
  ConvertDiagramFormatDocument,
  type ConvertDiagramFormatMutation,
  type ConvertDiagramFormatMutationVariables,
  useGetDiagramLazyQuery
} from '@/__generated__/graphql';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import { useDiagramLoader } from '@/features/diagram-editor/hooks/useDiagramLoader';

// Create the mutation hook using factory pattern
const useConvertDiagramMutation = createEntityMutation<ConvertDiagramFormatMutation, ConvertDiagramFormatMutationVariables>({
  entityName: 'Diagram',
  document: ConvertDiagramFormatDocument,
  silent: true, // We handle our own toast messages
});

export const useFileOperations = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [convertDiagram] = useConvertDiagramMutation();
  const [getDiagram] = useGetDiagramLazyQuery();
  const { loadDiagramFromData } = useDiagramLoader();

  // LOAD OPERATIONS (from file to browser via server upload)

  const loadFile = useCallback(async (file: File) => {
    setIsProcessing(true);
    try {
      // Save the file to server first
      const result = await saveDiagramFile(file);
      
      if (!result.success) {
        throw new Error(result.message || 'Failed to upload diagram to server');
      }

      // Load the diagram content directly without URL changes
      if (result.diagramId) {
        const { data, error } = await getDiagram({
          variables: { id: result.diagramId }
        });
        
        if (error) {
          throw new Error(`Failed to load diagram: ${error.message}`);
        }
        
        if (data?.diagram) {
          // Load the diagram data directly
          loadDiagramFromData({
            nodes: data.diagram.nodes || [],
            arrows: data.diagram.arrows || [],
            handles: data.diagram.handles || [],
            persons: data.diagram.persons || [],
            metadata: {
              ...data.diagram.metadata,
              name: data.diagram.metadata?.name || result.diagramId, // Use diagramId as fallback
              id: data.diagram.metadata?.id || result.diagramId
            }
          });
          
          toast.success(
            `Loaded ${result.diagramName || 'diagram'} (${result.nodeCount} nodes)`
          );
        } else {
          throw new Error('Diagram not found');
        }
      }
    } catch (error) {
      console.error('[Load file]', error);
      toast.error(`Load failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [getDiagram, loadDiagramFromData]);

  /**
   * Load via file selection dialog
   */
  const loadWithDialog = useCallback(async () => {
    try {
      const file = await selectFile({
        acceptedTypes: '.yaml,.yml,.json'
      });
      await loadFile(file);
    } catch (error) {
      // User cancelled or error occurred
      if (error instanceof Error && error.message !== 'No file selected') {
        toast.error(error.message);
        throw error;
      }
    }
  }, [loadFile]);


  
  // UPLOAD OPERATIONS
  

  const saveDiagram = useCallback(async (
    filename?: string,
    format?: DiagramFormat
  ) => {
    setIsProcessing(true);
    try {
      // Serialize the current diagram state
      const diagramContent = serializeDiagram();
      
      // Use the regular upload for all saves
      const actualFilename = filename || 'diagram.json';
      const actualFormat = format || DiagramFormat.NATIVE;
      
      const content = JSON.stringify(diagramContent, null, 2);
      
      const file = new File([content], actualFilename, { 
        type: actualFilename.endsWith('.json') ? 'application/json' : 'text/yaml' 
      });
      
      // Save the diagram
      const saveResult = await saveDiagramFile(file, actualFormat);
      
      if (!saveResult.success) {
        throw new Error(saveResult.message || 'Failed to save diagram');
      }
      
      // Update the format in the store
      const store = useUnifiedStore.getState();
      store.setDiagramFormat(actualFormat);
      
      // Silent save - no toast notification
      return saveResult;
    } catch (error) {
      console.error('[Upload diagram]', error);
      toast.error(`Upload failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, []);

  
  // EXPORT OPERATIONS
  

  const downloadAs = useCallback(async (
    format: DiagramFormat = DiagramFormat.NATIVE,
    filename?: string,
    includeMetadata: boolean = true
  ) => {
    setIsProcessing(true);
    try {
      // Serialize the current diagram state
      const diagramContent = JSON.stringify(serializeDiagram());
      
      // Export via GraphQL - convert format to uppercase for GraphQL enum
      const { data } = await convertDiagram({
        variables: {
          content: diagramContent,
          fromFormat: DiagramFormat.NATIVE,
          toFormat: format
        }
      });
      
      if (!data?.convert_diagram_format.success) {
        throw new Error(data?.convert_diagram_format.error || 'Failed to convert diagram');
      }
      
      const exportResult = data.convert_diagram_format;
      
      // Determine filename
      const actualFilename = filename || `diagram.${format === DiagramFormat.NATIVE ? 'json' : 'yaml'}`;
      
      // Download the file
      if (exportResult.content) {
        downloadFile(exportResult.content, actualFilename);
        toast.success(`Exported as ${actualFilename}`);
      }
      
      return {
        success: true,
        filename: actualFilename,
        format: exportResult.format || format
      };
    } catch (error) {
      console.error('[Export diagram]', error);
      toast.error(`Export failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [convertDiagram]);

  /**
   * Convert diagram to specified format (without downloading)
   */
  const convertFormat = useCallback(async (
    format: DiagramFormat = DiagramFormat.NATIVE,
    includeMetadata: boolean = true
  ): Promise<{ content: string; format: string; filename: string }> => {
    try {
      const diagramContent = JSON.stringify(serializeDiagram());
      
      const { data } = await convertDiagram({
        variables: {
          content: diagramContent,
          fromFormat: DiagramFormat.NATIVE,
          toFormat: format
        }
      });
      
      if (!data?.convert_diagram_format.success) {
        throw new Error(data?.convert_diagram_format.error || 'Failed to convert diagram');
      }
      
      const result = data.convert_diagram_format;
      
      return {
        content: result.content || '',
        format: result.format || format,
        filename: `diagram.${format === DiagramFormat.NATIVE ? 'json' : 'yaml'}`
      };
    } catch (error) {
      console.error('[Convert format]', error);
      toast.error(`Conversion failed: ${(error as Error).message}`);
      throw error;
    }
  }, [convertDiagram]);

  
  // FORMAT INFORMATION
  

  /**
   * Get available formats
   */
  const getAvailableFormats = useCallback(() => {
    // Hardcode the formats that the backend supports
    return [
      {
        format: DiagramFormat.NATIVE,
        metadata: {
          id: DiagramFormat.NATIVE,
          displayName: 'Native JSON',
          description: 'Full-fidelity format with GraphQL schema compatibility',
          fileExtension: '.json',
          supportsImport: true,
          supportsExport: true
        }
      },
      {
        format: DiagramFormat.LIGHT,
        metadata: {
          id: DiagramFormat.LIGHT,
          displayName: 'Light YAML',
          description: 'Simplified format using labels',
          fileExtension: '.yaml',
          supportsImport: true,
          supportsExport: true
        }
      },
      {
        format: DiagramFormat.READABLE,
        metadata: {
          id: DiagramFormat.READABLE,
          displayName: 'Readable Workflow',
          description: 'Human-friendly format',
          fileExtension: '.yaml',
          supportsImport: true,
          supportsExport: true
        }
      }
    ];
  }, []);

  return {
    // State
    isProcessing,
    
    // Load operations
    loadDiagram: loadFile,
    loadWithDialog,
    
    // Save operations
    saveDiagram,
    
    // Export operations
    downloadAs,
    convertFormat,
    
    // Format information
    getAvailableFormats
  };
};