// Hook for importing diagrams from various file formats
import { useCallback, ChangeEvent } from 'react';
import { loadDiagram } from '@/common/utils/diagramOperations';
import { createErrorHandlerFactory } from '@/common/types';
import { toast } from 'sonner';
import { getApiUrl, API_ENDPOINTS } from '@/common/utils/apiConfig';
import { YamlExporter } from '../converters/yamlExporter';
import { LLMYamlImporter } from '../converters/llmYamlImporter';
import { useDownload } from './useDownload';
import {
  readFileAsText,
  detectFileFormat,
  withFileErrorHandling,
  selectFile,
  FileFormat
} from '../utils/fileUtils';

const createErrorHandler = createErrorHandlerFactory(toast);

export const useFileImport = () => {
  const { downloadYaml } = useDownload();

  // Unified import handler for all file types
  const handleFileImport = useCallback(async (file: File) => {
    const errorHandler = createErrorHandler('Import file');
    
    try {
      // Read file content
      const content = await readFileAsText(file);
      
      // Detect format
      const formatInfo = detectFileFormat(content, file.name);
      
      // Process based on format
      switch (formatInfo.format) {
        case 'json': {
          const diagram = JSON.parse(content);
          loadDiagram(diagram);
          toast.success('JSON file imported successfully');
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
          
          const diagram = await res.json();
          loadDiagram(diagram);
          toast.success('YAML file imported successfully');
          break;
        }
        
        case 'llm-yaml': {
          // Use LLM YAML importer
          const diagram = LLMYamlImporter.fromLLMYAML(content);
          loadDiagram(diagram);
          toast.success('LLM-YAML file imported successfully');
          break;
        }
      }
    } catch (error) {
      errorHandler(error as Error);
    }
  }, []);

  // File input change handler
  const onImportFile = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileImport(file);
      // Reset input value to allow re-importing the same file
      event.target.value = '';
    }
  }, [handleFileImport]);

  // Import via file selection dialog
  const importFileWithDialog = useCallback(async () => {
    try {
      const file = await selectFile({
        acceptedTypes: '.json,.yaml,.yml,.llm-yaml'
      });
      await handleFileImport(file);
    } catch (error) {
      // User cancelled or error occurred
      if (error instanceof Error && error.message !== 'No file selected') {
        toast.error(error.message);
      }
    }
  }, [handleFileImport]);

  // Convert JSON to YAML
  const convertJSONtoYAML = useCallback(async (file: File) => {
    const errorHandler = createErrorHandler('Convert JSON to YAML');
    
    try {
      const content = await readFileAsText(file);
      const diagram = JSON.parse(content);
      
      const yamlContent = YamlExporter.toYAML(diagram);
      
      // Download the converted file
      const filename = file.name.replace('.json', '.yaml');
      downloadYaml(yamlContent, filename);
      
      toast.success('JSON converted to YAML successfully');
    } catch (error) {
      errorHandler(error as Error);
    }
  }, [downloadYaml]);

  // Convert JSON to YAML from file input
  const onConvertJSONtoYAML = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      convertJSONtoYAML(file);
      event.target.value = '';
    }
  }, [convertJSONtoYAML]);

  // Import from URL
  const importFromURL = useCallback(async (url: string, _format?: FileFormat) => {
    const errorHandler = createErrorHandler('Import from URL');
    
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
      
      await handleFileImport(virtualFile);
    } catch (error) {
      errorHandler(error as Error);
    }
  }, [handleFileImport]);

  const onImportJSON = withFileErrorHandling(
    async (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file && file.name.endsWith('.json')) {
        await handleFileImport(file);
        event.target.value = '';
      } else {
        throw new Error('Please select a JSON file');
      }
    },
    'Import JSON'
  );

  return {
    onImportFile,
    importFileWithDialog,
    onConvertJSONtoYAML,
    importFromURL,
    onImportJSON,
    // Wrapped versions with error handling
    handleImportYAML: withFileErrorHandling(
      async (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
          await handleFileImport(file);
          event.target.value = '';
        }
      },
      'Import YAML'
    ),
    handleImportJSON: onImportJSON
  };
};