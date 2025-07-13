import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import {
  selectFile,
  saveDiagram as saveDiagramFile,
  downloadFile
} from '@/lib/utils/file';
import { DiagramFormat } from '@dipeo/domain-models';
import { serializeDiagram } from '@/features/diagram-editor/utils/diagramSerializer';
import { createEntityMutation } from '@/lib/graphql/hooks';
import { 
  ConvertDiagramDocument,
  type ConvertDiagramMutation,
  type ConvertDiagramMutationVariables
} from '@/__generated__/graphql';

// Create the mutation hook using factory pattern
const useConvertDiagramMutation = createEntityMutation<ConvertDiagramMutation, ConvertDiagramMutationVariables>({
  entityName: 'Diagram',
  document: ConvertDiagramDocument,
  silent: true, // We handle our own toast messages
});

export const useFileOperations = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [convertDiagram] = useConvertDiagramMutation();

  // LOAD OPERATIONS (from file to browser via server upload)

  const loadFile = useCallback(async (file: File) => {
    setIsProcessing(true);
    try {
      // Save the file to server first
      const result = await saveDiagramFile(file);
      
      if (!result.success) {
        throw new Error(result.message || 'Failed to upload diagram to server');
      }

      // Then load it in the browser by navigating to it
      if (result.diagramId) {
        window.location.href = `/?diagram=${result.diagramId}`;
      }

      toast.success(
        `Saved and loaded ${result.diagramName || 'diagram'} (${result.nodeCount} nodes)`
      );
    } catch (error) {
      console.error('[Load file]', error);
      toast.error(`Load failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, []);

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

  /**
   * Load from URL
   */
  const loadFromURL = useCallback(async (url: string) => {
    setIsProcessing(true);
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch from URL: ${response.statusText}`);
      }
      
      const content = await response.text();
      
      // Create a virtual file object for unified processing
      const virtualFile = new File([content], url.split('/').pop() || 'loaded-file', {
        type: 'text/plain'
      });
      
      await loadFile(virtualFile);
    } catch (error) {
      console.error('[Load from URL]', error);
      toast.error(`Load from URL: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
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
      const diagramContent = serializeDiagram();
      
      // Export via GraphQL - convert format to uppercase for GraphQL enum
      const { data } = await convertDiagram({
        variables: {
          content: diagramContent,
          targetFormat: format,
          includeMetadata
        }
      });
      
      if (!data?.convert_diagram.success) {
        throw new Error(data?.convert_diagram.error || 'Failed to convert diagram');
      }
      
      const exportResult = data.convert_diagram;
      
      // Determine filename
      const actualFilename = filename || exportResult.filename || `diagram.${format === DiagramFormat.NATIVE ? 'json' : 'yaml'}`;
      
      // Download the file
      if (exportResult.content) {
        downloadFile(exportResult.content, actualFilename);
        toast.success(`Exported as ${actualFilename}`);
      }
      
      return {
        success: true,
        filename: actualFilename,
        format: exportResult.format
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
      const diagramContent = serializeDiagram();
      
      const { data } = await convertDiagram({
        variables: {
          content: diagramContent,
          targetFormat: format,
          includeMetadata
        }
      });
      
      if (!data?.convert_diagram.success) {
        throw new Error(data?.convert_diagram.error || 'Failed to convert diagram');
      }
      
      const result = data.convert_diagram;
      
      return {
        content: result.content || '',
        format: result.format || format,
        filename: result.filename || `diagram.${format === DiagramFormat.NATIVE ? 'json' : 'yaml'}`
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
    loadFromURL,
    
    // Save operations
    saveDiagram,
    
    // Export operations
    downloadAs,
    convertFormat,
    
    // Format information
    getAvailableFormats
  };
};