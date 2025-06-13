import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import {
  readFileAsText,
  detectFileFormat,
  selectFile,
  downloadFile,
  saveDiagramToBackend,
  FileFormat
} from '@/utils/file';
import {
  converterRegistry,
  storeDomainConverter,
  SupportedFormat
} from '@/utils/converters/core';
import type { DomainDiagram } from '@/types';

export const useUnifiedFileOperations = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const store = useUnifiedStore();

  // ===================
  // EXPORT OPERATIONS
  // ===================

  /**
   * Export diagram to specified format
   */
  const exportDiagram = useCallback((format: SupportedFormat): string => {
    // Convert store state to domain model
    const storeState = {
      nodes: store.nodes,
      arrows: store.arrows,
      handles: store.handles,
      persons: store.persons,
      apiKeys: store.apiKeys
    };
    const domainDiagram = storeDomainConverter.storeToDomain(storeState);
    
    // Get converter for format and serialize
    const converter = converterRegistry.get(format);
    return converter.serialize(domainDiagram);
  }, [store]);

  /**
   * Export and download diagram in specified format
   */
  const exportAndDownload = useCallback(async (
    format: SupportedFormat,
    filename?: string
  ) => {
    setIsDownloading(true);
    try {
      const content = exportDiagram(format);
      const converter = converterRegistry.get(format);
      const finalFilename = filename || `diagram${converter.fileExtension}`;
      
      await downloadFile(content, finalFilename, 'text/yaml');
      toast.success(`Exported as ${format} format`);
    } catch (error) {
      console.error('Export failed:', error);
      toast.error(`Export failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsDownloading(false);
    }
  }, [exportDiagram]);

  // ===================
  // IMPORT OPERATIONS
  // ===================

  /**
   * Import diagram from content and format
   */
  const importDiagram = useCallback((
    content: string,
    format: SupportedFormat
  ): void => {
    // Get converter for format and deserialize
    const converter = converterRegistry.get(format);
    const domainDiagram = converter.deserialize(content);
    
    // Convert domain model to store state
    const storeData = storeDomainConverter.domainToStore(domainDiagram);
    
    // Clear existing data and load new diagram
    store.clearAll();
    store.transaction(() => {
      // Add entities using store actions
      if (storeData.apiKeys) {
        storeData.apiKeys.forEach((apiKey, id) => {
          store.addApiKey(apiKey.label, apiKey.service);
        });
      }
      
      if (storeData.persons) {
        storeData.persons.forEach((person, id) => {
          store.addPerson(person.label, person.service, person.model);
        });
      }
      
      if (storeData.nodes) {
        storeData.nodes.forEach((node, id) => {
          store.addNode(node.type, node.position, node.data);
        });
      }
      
      if (storeData.arrows) {
        storeData.arrows.forEach((arrow, id) => {
          store.addArrow(arrow.source, arrow.target, arrow.data);
        });
      }
    });
  }, [store]);

  /**
   * Import diagram from file
   */
  const importFile = useCallback(async (file: File) => {
    setIsProcessing(true);
    try {
      // Read file content
      const content = await readFileAsText(file);
      
      // Detect format
      const formatInfo = detectFileFormat(content, file.name);
      
      // Validate format is supported
      if (!converterRegistry.has(formatInfo.format as SupportedFormat)) {
        throw new Error(`Unsupported file format: ${formatInfo.format}`);
      }
      
      // Import using unified pipeline
      importDiagram(content, formatInfo.format as SupportedFormat);
      
      const metadata = converterRegistry.getMetadata(formatInfo.format as SupportedFormat);
      toast.success(`${metadata?.displayName || formatInfo.format} file imported successfully`);
    } catch (error) {
      console.error('[Import file]', error);
      toast.error(`Import failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [importDiagram]);

  /**
   * Import via file selection dialog
   */
  const importWithDialog = useCallback(async () => {
    try {
      const file = await selectFile({
        acceptedTypes: '.yaml,.yml,.native.yaml,.readable.yaml,.llm-readable.yaml,.llm.yaml'
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
    format: SupportedFormat,
    filename?: string
  ) => {
    setIsProcessing(true);
    try {
      // Export diagram to format
      const content = exportDiagram(format);
      
      // Parse for backend (expects JSON/YAML object)
      const data = format.includes('yaml') || format.includes('readable')
        ? (await import('yaml')).parse(content)
        : JSON.parse(content);
      
      // Save to backend
      const result = await saveDiagramToBackend(data, {
        format: format as FileFormat,
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
  }, [exportDiagram]);

  // ===================
  // FORMAT INFORMATION
  // ===================

  /**
   * Get available formats with metadata
   */
  const getAvailableFormats = useCallback((): Array<{
    format: SupportedFormat;
    metadata: ReturnType<typeof converterRegistry.getMetadata>;
  }> => {
    return converterRegistry.getFormats().map(format => ({
      format,
      metadata: converterRegistry.getMetadata(format)
    }));
  }, []);

  return {
    // State
    isProcessing,
    isDownloading,
    
    // Export operations
    exportDiagram,
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