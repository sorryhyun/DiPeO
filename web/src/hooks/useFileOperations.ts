import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import {
  readFileAsText,
  selectFile,
  downloadFile,
  uploadDiagram,
  saveDiagramToBackend
} from '@/utils/file';
import { 
  useExportDiagramMutation,
  ExportDiagramDocument,
  DiagramFormat
} from '@/__generated__/graphql';
import { apolloClient } from '@/graphql/client';

export const useFileOperations = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const store = useUnifiedStore();
  const [exportDiagramMutation] = useExportDiagramMutation();

  // Get current diagram ID from store or props
  const diagramId = null; // TODO: Pass diagram ID from parent component

  // ===================
  // EXPORT OPERATIONS
  // ===================

  /**
   * Export and download diagram in specified format
   */
  const exportAndDownload = useCallback(async (
    format: DiagramFormat,
    filename?: string,
    includeMetadata: boolean = true
  ) => {
    if (!diagramId) {
      toast.error('No diagram to export');
      return;
    }

    setIsDownloading(true);
    try {
      const { data } = await exportDiagramMutation({
        variables: {
          diagramId,
          format,
          includeMetadata
        }
      });

      if (!data?.exportDiagram.success) {
        throw new Error(data?.exportDiagram.error || 'Export failed');
      }

      const { content, filename: exportFilename } = data.exportDiagram;
      if (!content) {
        throw new Error('No content returned from export');
      }

      // Download the file
      await downloadFile(content, exportFilename || filename || 'diagram.yaml', 'text/yaml');
      toast.success(`Exported as ${format} format`);
    } catch (error) {
      console.error('Export failed:', error);
      toast.error(`Export failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsDownloading(false);
    }
  }, [diagramId, exportDiagramMutation]);

  // ===================
  // IMPORT OPERATIONS
  // ===================

  /**
   * Import diagram from file using GraphQL
   */
  const importFile = useCallback(async (file: File) => {
    setIsProcessing(true);
    try {
      const result = await uploadDiagram(file);
      
      if (!result.success) {
        throw new Error(result.message || 'Import failed');
      }

      // Reload the page to load the new diagram
      if (result.diagramId) {
        window.location.href = `/?diagram=${result.diagramId}`;
      }

      toast.success(
        `Imported ${result.diagramName || 'diagram'} (${result.nodeCount} nodes)`
      );
    } catch (error) {
      console.error('[Import file]', error);
      toast.error(`Import failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, []);

  /**
   * Import via file selection dialog
   */
  const importWithDialog = useCallback(async () => {
    try {
      const file = await selectFile({
        acceptedTypes: '.yaml,.yml,.json'
      });
      await importFile(file);
    } catch (error) {
      // User cancelled or error occurred
      if (error instanceof Error && error.message !== 'No file selected') {
        toast.error(error.message);
        throw error;
      }
    }
  }, [importFile]);

  /**
   * Import from URL
   */
  const importFromURL = useCallback(async (url: string) => {
    setIsProcessing(true);
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch from URL: ${response.statusText}`);
      }
      
      const content = await response.text();
      
      // Create a virtual file object for unified processing
      const virtualFile = new File([content], url.split('/').pop() || 'imported-file', {
        type: 'text/plain'
      });
      
      await importFile(virtualFile);
    } catch (error) {
      console.error('[Import from URL]', error);
      toast.error(`Import from URL: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [importFile]);

  // ===================
  // SAVE TO BACKEND
  // ===================

  /**
   * Save diagram to backend in specified format
   */
  const saveDiagramToServer = useCallback(async (
    format?: DiagramFormat,
    filename?: string
  ) => {
    if (!diagramId) {
      toast.error('No diagram to save');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await saveDiagramToBackend(diagramId, {
        format: format || DiagramFormat.Native,
        filename
      });
      
      toast.success(`Saved to server as ${result.filename}`);
      return result;
    } catch (error) {
      console.error('[Save to server]', error);
      toast.error(`Save failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [diagramId]);

  // ===================
  // FORMAT INFORMATION
  // ===================

  /**
   * Get available formats
   */
  const getAvailableFormats = useCallback(() => {
    // Hardcode the formats that the backend supports
    return [
      {
        format: DiagramFormat.Native,
        metadata: {
          id: DiagramFormat.Native,
          displayName: 'Native YAML',
          description: 'Full-fidelity format with all details',
          fileExtension: '.yaml',
          supportsImport: true,
          supportsExport: true
        }
      },
      {
        format: DiagramFormat.Light,
        metadata: {
          id: DiagramFormat.Light,
          displayName: 'Light YAML',
          description: 'Simplified format using labels',
          fileExtension: '.yaml',
          supportsImport: true,
          supportsExport: true
        }
      },
      {
        format: DiagramFormat.Readable,
        metadata: {
          id: DiagramFormat.Readable,
          displayName: 'Readable Workflow',
          description: 'Human-friendly format',
          fileExtension: '.yaml',
          supportsImport: true,
          supportsExport: true
        }
      },
      {
        format: DiagramFormat.Llm,
        metadata: {
          id: DiagramFormat.Llm,
          displayName: 'LLM-Friendly',
          description: 'Optimized for AI understanding',
          fileExtension: '.yaml',
          supportsImport: false,
          supportsExport: true
        }
      }
    ];
  }, []);

  return {
    // State
    isProcessing,
    isDownloading,
    
    // Export operations
    exportAndDownload,
    
    // Import operations
    importFile,
    importWithDialog,
    importFromURL,
    
    // Backend operations
    saveDiagramToServer,
    
    // Format information
    getAvailableFormats
  };
};