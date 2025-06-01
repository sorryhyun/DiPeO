// Hook for importing diagrams from UML or YAML
import React, { useCallback, ChangeEvent } from 'react';
import { useConsolidatedDiagramStore } from '@/shared/stores';
import { createAsyncErrorHandler, createErrorHandlerFactory } from '@/shared/types';
import { toast } from 'sonner';
import { getApiUrl, API_ENDPOINTS } from '@/shared/utils/apiConfig';
import { YamlExporter } from '../converters/yamlExporter';
import { LLMYamlImporter } from '../converters/llmYamlImporter';
import { useDownload } from '@/shared/hooks/useDownload';

const handleAsyncError = createAsyncErrorHandler(toast);
const createErrorHandler = createErrorHandlerFactory(toast);


export const useFileImport = () => {
  const { loadDiagram } = useConsolidatedDiagramStore();
  const { downloadYaml } = useDownload();

  const handleImportUML = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const errorHandler = createErrorHandler('Import UML');
    
    await handleAsyncError(
      async () => {
        const text = await file.text();
        const res = await fetch(getApiUrl(API_ENDPOINTS.IMPORT_UML), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ uml: text }),
        });
        
        if (!res.ok) {
          throw new Error('Import UML failed');
        }
        
        const diagram = await res.json();
        loadDiagram(diagram);
      },
      undefined,
      errorHandler
    );
  }, [loadDiagram]);

  const handleImportYAML = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const errorHandler = createErrorHandler('Import YAML');
    
    await handleAsyncError(
      async () => {
        const text = await file.text();
        const res = await fetch(getApiUrl(API_ENDPOINTS.IMPORT_YAML), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ yaml: text }),
        });
        
        if (!res.ok) {
          throw new Error('Import YAML failed');
        }
        
        const diagram = await res.json();
        loadDiagram(diagram);
      },
      undefined,
      errorHandler
    );
  }, [loadDiagram]);

  // Import from YAML (client-side parsing)
  const onImportYAML = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const errorHandler = createErrorHandler('Import YAML');
    const reader = new FileReader();

    reader.onload = async (e) => {
      await handleAsyncError(
        async () => {
          const result = e.target?.result as string;
          if (!result) {
            throw new Error('Failed to read file content');
          }

          // Try to detect YAML format
          let diagramData;
          if (result.includes('flow:') && (result.includes('prompts:') || result.includes('agents:'))) {
            // LLM-friendly format
            diagramData = LLMYamlImporter.fromLLMYAML(result);
            toast.success('Imported from LLM-friendly YAML format');
          } else {
            // Standard format
            diagramData = YamlExporter.fromYAML(result);
            toast.success('Imported from YAML format');
          }
          loadDiagram(diagramData);
        },
        undefined,
        errorHandler
      );
    };

    reader.onerror = () => {
      errorHandler(new Error('Failed to read file'));
    };

    reader.readAsText(file);
  }, [loadDiagram]);

  // Convert between formats
  const onConvertJSONtoYAML = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const errorHandler = createErrorHandler('Convert JSON to YAML');
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const jsonContent = e.target?.result as string;
        const diagram = JSON.parse(jsonContent);
        const yamlContent = YamlExporter.toYAML(diagram);

        const yamlFilename = file.name.replace('.json', '.yaml');
        downloadYaml(yamlContent, yamlFilename);
        toast.success('Converted JSON to YAML');
      } catch (error) {
        console.error(error);
        errorHandler(error instanceof Error ? error : new Error('Failed to convert JSON to YAML'));
      }
    };

    reader.readAsText(file);
  }, [downloadYaml]);

  return {
    handleImportUML,
    handleImportYAML,
    onImportYAML,
    onConvertJSONtoYAML,
  };
};