import { useState, useCallback, type ChangeEvent } from 'react';
import { useExport } from './useExport';
import { toast } from 'sonner';
import { getApiUrl, API_ENDPOINTS } from '@/utils/api/config';
import { fromNativeYAML, toNativeYAML, LlmYaml } from '@/utils/converters';
import type { 
  DomainDiagram, 
  DomainNode, 
  DomainArrow, 
  DomainPerson, 
  DomainApiKey, 
  DomainHandle,
  NodeID,
  ArrowID,
  PersonID,
  ApiKeyID,
  HandleID
} from '@/types';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import {
  readFileAsText,
  detectFileFormat,
  withFileErrorHandling,
  selectFile,
  downloadFile,
  getFileExtension,
  getMimeType,
  saveDiagramToBackend,
  FileFormat
} from '@/utils/file';

export type SupportedFormat = 'light' | 'native' | 'readable' | 'llm-readable';

// Helper function to convert legacy YAML format to new format
function convertLegacyYamlToExportFormat(data: any): any {
  // If it already has a version field, it's not legacy
  if (data.version) {
    return data;
  }
  
  // Convert legacy format
  const converted = {
    version: '4.0.0', // Add version field
    nodes: (data.nodes || []).map((node: any) => ({
      ...node,
      // Move label from data.label to node.label if needed
      label: node.label || node.data?.label || 'Untitled Node'
    })),
    arrows: (data.arrows || []).map((arrow: any) => {
      // Legacy format has source/target as "nodeId:handleName"
      // Keep the same format for the store format
      return {
        sourceHandle: arrow.source,
        targetHandle: arrow.target,
        data: arrow.data || {}
      };
    }),
    persons: data.persons || [],
    apiKeys: (data.apiKeys || []).map((key: any) => ({
      // New format expects 'name' instead of 'label'
      name: key.label || key.name,
      service: key.service
    })),
    handles: (data.handles || []).map((handle: any) => {
      // Find the node to get its label
      const node = (data.nodes || []).find((n: any) => n.id === handle.nodeId);
      const nodeLabel = node?.data?.label || handle.nodeId;
      
      return {
        nodeLabel,
        label: handle.label,
        direction: handle.direction,
        dataType: handle.dataType,
        position: handle.position,
        maxConnections: handle.maxConnections,
        required: handle.required,
        defaultValue: handle.defaultValue,
        dynamic: handle.dynamic
      };
    }),
    metadata: {
      exported: new Date().toISOString(),
      description: data.description || 'Imported from legacy YAML'
    }
  };
  
  return converted;
}

export const useFileOperations = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const { exportDiagram, importDiagram } = useExport();

  // Enhanced download with File System Access API support
  const downloadEnhanced = useCallback(async (
    data: string | Blob,
    filename: string,
    mimeType?: string
  ) => {
    setIsDownloading(true);
    
    try {
      const blob = data instanceof Blob 
        ? data 
        : new Blob([data], { type: mimeType || 'text/plain' });
      
      // Try modern File System Access API first if available
      if ('showSaveFilePicker' in window && typeof window.showSaveFilePicker === 'function') {
        try {
          const handle = await window.showSaveFilePicker({
            suggestedName: filename,
            types: [{
              description: 'Files',
              accept: {
                'text/plain': ['.txt'],
                'application/json': ['.json'],
                'text/yaml': ['.yaml', '.yml', '.llm-yaml'],
                'text/csv': ['.csv'],
                'text/markdown': ['.md'],
              },
            }],
          });
          
          const writable = await handle.createWritable();
          await writable.write(blob);
          await writable.close();
          return;
        } catch (err) {
          // User cancelled or API not supported, fall back to traditional method
          if (err instanceof Error && err.name !== 'AbortError') {
            console.warn('File System Access API failed, falling back to traditional download:', err);
          }
        }
      }
      
      // Fall back to unified download utilities
      if (data instanceof Blob) {
        // Convert Blob to URL and download
        const url = URL.createObjectURL(data);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        downloadFile(data, filename);
      }
      
    } catch (error) {
      console.error('Download failed:', error);
      throw error;
    } finally {
      setIsDownloading(false);
    }
  }, []);

  // ===================
  // IMPORT OPERATIONS
  // ===================

  // Unified import handler for all file types
  const importFile = useCallback(async (file: File) => {
    setIsProcessing(true);
    try {
      // Read file content
      const content = await readFileAsText(file);
      
      // Detect format
      const formatInfo = detectFileFormat(content, file.name);
      
      // Process based on format
      switch (formatInfo.format) {
        case 'light': {
          // Use YAML converter for light format
          const YamlConverter = (await import('@/utils/converters/formats/yaml')).YamlConverter;
          const converter = new YamlConverter();
          const converterDiagram = converter.deserialize(content);
          importDiagram(JSON.stringify(converterDiagram));
          toast.success('Light YAML file imported successfully');
          break;
        }
        
        case 'native': {
          // Use native YAML converter for DomainDiagram format
          const domainDiagram = fromNativeYAML(content);
          // Import domain diagram directly - no conversion needed
          importDiagram(JSON.stringify(domainDiagram));
          toast.success('Native YAML file imported successfully');
          break;
        }
        
        case 'readable': {
          // Use Readable YAML importer
          const ReadableConverter = (await import('@/utils/converters/formats/readable')).ReadableConverter;
          const converter = new ReadableConverter();
          const converterDiagram = converter.deserialize(content);
          // Import converter diagram - importDiagram handles conversion
          importDiagram(JSON.stringify(converterDiagram));
          toast.success('Readable YAML file imported successfully');
          break;
        }
        
        case 'llm-readable': {
          // Use LLM YAML importer
          const converterDiagram = LlmYaml.fromLLMYAML(content);
          // Import converter diagram - importDiagram handles conversion
          importDiagram(JSON.stringify(converterDiagram));
          toast.success('LLM-readable YAML file imported successfully');
          break;
        }
        
        default:
          throw new Error(`Unsupported file format: ${formatInfo.format}`);
      }
    } catch (error) {
      console.error('[Import file]', error);
      toast.error(`Import file: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [importDiagram]);

  // Import via file selection dialog
  const importWithDialog = useCallback(async () => {
    try {
      const file = await selectFile({
        acceptedTypes: '.yaml,.yml,.native.yaml,.readable.yaml,.llm-readable.yaml'
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

  // Import from URL
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
  // EXPORT OPERATIONS
  // ===================



  // Save to backend directory using the export functionality
  const saveDiagramToServer = useCallback(async (format: SupportedFormat, filename?: string) => {
    setIsProcessing(true);
    try {
      // Use actual domain objects for all YAML formats
      const store = useUnifiedStore.getState();
      const diagramData = {
        version: '1.0',  // Add version field for YAML compatibility
        id: `diagram-${Date.now()}`,
        name: filename?.replace(/\.[^/.]+$/, '') || 'Untitled Diagram',
        nodes: Array.from(store.nodes.values()),
        arrows: Array.from(store.arrows.values()),
        persons: Array.from(store.persons.values()),
        apiKeys: Array.from(store.apiKeys.values()),
        handles: Array.from(store.handles.values())
      };
      
      const finalFilename = filename || `diagram${getFileExtension(format)}`;
      const result = await saveDiagramToBackend(diagramData, {
        filename: finalFilename,
        format: format as FileFormat
      });
      
      if (result.success) {
        toast.success(`Saved ${format.toUpperCase()} to: ${result.filename}`);
      } else {
        throw new Error('Failed to save diagram');
      }
      
      return result;
    } catch (error) {
      console.error('[Save diagram]', error);
      toast.error(`Save failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, []);

  // ===================
  // DOWNLOAD OPERATIONS  
  // ===================

  // Type-safe download function
  const download = useCallback(async (
    data: string | Blob,
    filename: string,
    format?: SupportedFormat
  ) => {
    const mimeType = format ? getMimeType(format) : undefined;
    return downloadEnhanced(data, filename, mimeType);
  }, [downloadEnhanced]);



  // Clone diagram with new name
  const cloneDiagram = useCallback(async (newName: string, format: SupportedFormat = 'light') => {
    setIsProcessing(true);
    try {
      // Use new export format for cloning
      const exportedData = exportDiagram();
      
      // Create a cloned diagram with metadata
      const clonedDiagram = {
        ...exportedData,
        id: `diagram-${  Date.now()}`,
        name: newName,
        metadata: {
          name: newName,
          clonedAt: new Date().toISOString()
        }
      };
      
      // Use actual domain objects for YAML formats
      const store = useUnifiedStore.getState();
      const diagramToSave = {
        version: '1.0',  // Add version field for YAML compatibility
        id: clonedDiagram.id,
        name: newName,
        nodes: Array.from(store.nodes.values()),
        arrows: Array.from(store.arrows.values()),
        persons: Array.from(store.persons.values()),
        apiKeys: Array.from(store.apiKeys.values()),
        handles: Array.from(store.handles.values())
      };
      
      // Save the cloned diagram
      const response = await fetch(getApiUrl(API_ENDPOINTS.SAVE_DIAGRAM), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          diagram: diagramToSave,
          filename: `${newName}${getFileExtension(format)}`,
          format: format as FileFormat
        })
      });
      const result = await response.json();
      
      if (result.success) {
        toast.success(`Cloned diagram as: ${result.filename}`);
      }
      
      return result;
    } catch (error) {
      console.error('[Clone diagram]', error);
      toast.error(`Clone failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [exportDiagram]);

  // ===================
  // UTILITY FUNCTIONS
  // ===================

  // File input change handler
  const handleFileInput = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      importFile(file);
      // Reset input value to allow re-importing the same file
      event.target.value = '';
    }
  }, [importFile]);

  // Detect file format utility
  const detectFormat = useCallback((content: string, filename: string) => {
    return detectFileFormat(content, filename);
  }, []);

  // Select file utility
  const selectFileDialog = useCallback((options?: { acceptedTypes?: string }) => {
    return selectFile(options);
  }, []);

  return {
    // State
    isProcessing,
    isDownloading,
    
    // Import operations
    importFile,
    importWithDialog,
    importFromURL,
    handleFileInput,
    
    // Save operations (save to server)
    saveLight: (filename?: string) => saveDiagramToServer('light', filename),
    saveNative: (filename?: string) => saveDiagramToServer('native', filename),
    saveReadable: (filename?: string) => saveDiagramToServer('readable', filename),
    saveLLMReadable: (filename?: string) => saveDiagramToServer('llm-readable', filename),
    saveDiagramAs: saveDiagramToServer, // Deprecated - use exportDiagramAs for downloads

    // Download operations
    download,
    cloneDiagram,
    
    // Utilities
    detectFormat,
    selectFile: selectFileDialog,
    
    // Wrapped versions with error handling
    safeImport: withFileErrorHandling(importFile, 'Import file'),
    safeExport: withFileErrorHandling((format: SupportedFormat) => saveDiagramToServer(format), 'Export file'),
    safeDownload: withFileErrorHandling(download, 'Download file'),
    
    // Save to server
    saveDiagramToServer,
  };
};