import { useState, useCallback, type ChangeEvent } from 'react';
import { useExport } from './useExport';
import { toast } from 'sonner';
import { getApiUrl, API_ENDPOINTS } from '@/utils/api/config';
import { Yaml, LlmYaml } from '@/utils/converters';
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

export type SupportedFormat = 'json' | 'yaml' | 'llm-yaml';


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
        case 'json': {
          const data = JSON.parse(content);
          
          // Check if it's the new export format (has version field)
          if (data.version && Array.isArray(data.nodes)) {
            // New format - use new import system
            importDiagram(data);
            toast.success('JSON file imported successfully');
          } else {
            // Legacy format - import as JSON string for backward compatibility
            // The importDiagram function handles legacy format conversion
            importDiagram(JSON.stringify(data));
            toast.success('JSON file imported successfully (legacy format)');
          }
          break;
        }
        
        case 'yaml': {
          // Use server-side YAML import
          const res = await fetch(getApiUrl(API_ENDPOINTS.IMPORT_YAML), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ yaml: content }),
          });
          
          if (!res.ok) {
            throw new Error('Failed to import YAML file');
          }
          
          const data = await res.json();
          
          // Check format and import appropriately
          if (data.version && Array.isArray(data.nodes)) {
            importDiagram(data);
            toast.success('YAML file imported successfully');
          } else {
            // Legacy YAML format - import as is
            // The importDiagram function handles legacy format conversion
            importDiagram(JSON.stringify(data));
            toast.success('YAML file imported successfully (legacy format)');
          }
          break;
        }
        
        case 'llm-yaml': {
          // Use LLM YAML importer
          const converterDiagram = LlmYaml.fromLLMYAML(content);
          // Import converter diagram - importDiagram handles conversion
          importDiagram(JSON.stringify(converterDiagram));
          toast.success('LLM-YAML file imported successfully');
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
        acceptedTypes: '.json,.yaml,.yml,.llm-yaml'
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

  // Unified export function
  const exportDiagramAs = useCallback(async (format: SupportedFormat, filename?: string) => {
    setIsProcessing(true);
    try {
      let content: string;
      let defaultFilename: string;
      
      switch (format) {
        case 'json': {
          // Use new export format for JSON
          const exportData = exportDiagram();
          content = JSON.stringify(exportData, null, 2);
          defaultFilename = 'example.json';
          break;
        }
          
        case 'yaml': {
          // For YAML, we need to use the actual domain objects from the store
          // since the converter expects DomainNode format, not ExportedNode
          const store = useUnifiedStore.getState();
          const converterDiagram = {
            id: `diagram-${Date.now()}`,
            name: 'Untitled Diagram',
            nodes: Array.from(store.nodes.values()),
            arrows: Array.from(store.arrows.values()),
            persons: Array.from(store.persons.values()),
            apiKeys: Array.from(store.apiKeys.values()),
            handles: Array.from(store.handles.values())
          };
          content = Yaml.toYAML(converterDiagram);
          defaultFilename = 'diagram.yaml';
          break;
        }
          
        case 'llm-yaml': {
          // For LLM-YAML, we need to use the actual domain objects from the store
          // since the converter expects DomainNode format, not ExportedNode
          const store = useUnifiedStore.getState();
          const converterDiagram = {
            id: `diagram-${Date.now()}`,
            name: 'Untitled Diagram',
            nodes: Array.from(store.nodes.values()),
            arrows: Array.from(store.arrows.values()),
            persons: Array.from(store.persons.values()),
            apiKeys: Array.from(store.apiKeys.values()),
            handles: Array.from(store.handles.values())
          };
          content = LlmYaml.toLLMYAML(converterDiagram);
          defaultFilename = 'diagram.llm-yaml';
          break;
        }
          
        default:
          throw new Error(`Unsupported format: ${format}`);
      }
      
      const finalFilename = filename || defaultFilename;
      const mimeType = getMimeType(format);
      
      await downloadEnhanced(content, finalFilename, mimeType);
      toast.success(`Exported as ${format.toUpperCase()}`);
      
      return { content, filename: finalFilename };
    } catch (error) {
      console.error('[Export diagram]', error);
      toast.error(`Export failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [downloadEnhanced]);

  // Save to backend directory using the export functionality
  const saveDiagramToServer = useCallback(async (format: SupportedFormat, filename?: string) => {
    setIsProcessing(true);
    try {
      let diagramData: any;
      
      if (format === 'json') {
        // Use new export format for JSON saves
        const exportData = exportDiagram();
        diagramData = {
          ...exportData,
          id: `diagram-${Date.now()}`,
          name: filename?.replace(/\.[^/.]+$/, '') || 'Untitled Diagram'
        };
      } else {
        // Use actual domain objects for YAML formats
        const store = useUnifiedStore.getState();
        diagramData = {
          id: `diagram-${Date.now()}`,
          name: filename?.replace(/\.[^/.]+$/, '') || 'Untitled Diagram',
          nodes: Array.from(store.nodes.values()),
          arrows: Array.from(store.arrows.values()),
          persons: Array.from(store.persons.values()),
          apiKeys: Array.from(store.apiKeys.values()),
          handles: Array.from(store.handles.values())
        };
      }
      
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

  // Specific download functions
  const downloadJSON = useCallback((data: object, filename: string) => {
    const content = JSON.stringify(data, null, 2);
    return download(content, filename, 'json');
  }, [download]);

  const downloadYAML = useCallback((data: string, filename: string) => {
    return download(data, filename, 'yaml');
  }, [download]);

  const downloadLLMYAML = useCallback((data: string, filename: string) => {
    return download(data, filename, 'llm-yaml');
  }, [download]);

  // ===================
  // CONVERSION OPERATIONS
  // ===================

  // Convert JSON to YAML
  const convertJSONtoYAML = useCallback(async (file: File) => {
    setIsProcessing(true);
    try {
      const content = await readFileAsText(file);
      const diagram = JSON.parse(content);
      
      const yamlContent = Yaml.toYAML(diagram);
      
      // Download the converted file
      const filename = file.name.replace('.json', '.yaml');
      await downloadYAML(yamlContent, filename);
      
      toast.success('JSON converted to YAML successfully');
    } catch (error) {
      console.error('[Convert JSON to YAML]', error);
      toast.error(`Convert JSON to YAML: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [downloadYAML]);

  // ===================
  // ADVANCED OPERATIONS
  // ===================

  // Export all formats
  const exportAllFormats = useCallback(async (baseFilename: string = 'diagram') => {
    setIsProcessing(true);
    try {
      const results = await Promise.allSettled([
        exportDiagramAs('json', `${baseFilename}.json`),
        exportDiagramAs('yaml', `${baseFilename}.yaml`),
        exportDiagramAs('llm-yaml', `${baseFilename}.llm-yaml`)
      ]);
      
      const successful = results.filter(r => r.status === 'fulfilled').length;
      const failed = results.filter(r => r.status === 'rejected').length;
      
      if (successful > 0) {
        toast.success(`Exported ${successful} format(s) successfully${failed > 0 ? `, ${failed} failed` : ''}`);
      } else {
        throw new Error('All exports failed');
      }
    } catch (error) {
      console.error('[Export all formats]', error);
      toast.error(`Export all formats: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [exportDiagramAs]);

  // Clone diagram with new name
  const cloneDiagram = useCallback(async (newName: string, format: SupportedFormat = 'json') => {
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
      
      // Convert to appropriate format based on file type
      const diagramToSave = format === 'json' 
        ? clonedDiagram 
        : { 
            id: clonedDiagram.id, 
            name: newName,
            nodes: exportedData.nodes,
            arrows: exportedData.arrows,
            persons: exportedData.persons,
            apiKeys: exportedData.apiKeys,
            handles: [] // Converter format expects handles
          };
      
      // Save based on format
      let result;
      if (format === 'json') {
        // For JSON, save the export format directly via API
        const response = await fetch(getApiUrl(API_ENDPOINTS.SAVE_DIAGRAM), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            diagram: diagramToSave,
            filename: `${newName}${getFileExtension(format)}`,
            format: format as FileFormat
          })
        });
        result = await response.json();
      } else {
        // For YAML formats, we already have the converter format
        const response = await fetch(getApiUrl(API_ENDPOINTS.SAVE_DIAGRAM), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            diagram: diagramToSave,
            filename: `${newName}${getFileExtension(format)}`,
            format: format as FileFormat
          })
        });
        result = await response.json();
      }
      
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
    
    // Export operations  
    exportJSON: () => exportDiagramAs('json'),
    exportYAML: () => exportDiagramAs('yaml'),
    exportLLMYAML: () => exportDiagramAs('llm-yaml'),
    exportDiagramAs,
    
    // Save operations (save to server)
    saveJSON: (filename?: string) => saveDiagramToServer('json', filename),
    saveYAML: (filename?: string) => saveDiagramToServer('yaml', filename),
    saveLLMYAML: (filename?: string) => saveDiagramToServer('llm-yaml', filename),
    saveDiagramAs: saveDiagramToServer, // Deprecated - use exportDiagramAs for downloads
    
    // Download operations
    download,
    downloadJSON,
    downloadYAML,
    downloadLLMYAML,
    
    // Conversion operations
    convertJSONtoYAML,
    
    // Advanced operations
    exportAllFormats,
    cloneDiagram,
    
    // Utilities
    detectFormat,
    selectFile: selectFileDialog,
    
    // Wrapped versions with error handling
    safeImport: withFileErrorHandling(importFile, 'Import file'),
    safeExport: withFileErrorHandling((format: SupportedFormat) => exportDiagramAs(format), 'Export file'),
    safeDownload: withFileErrorHandling(download, 'Download file'),
    
    // Save to server
    saveDiagramToServer,
  };
};