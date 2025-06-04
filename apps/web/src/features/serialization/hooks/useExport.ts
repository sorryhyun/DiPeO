import { useCallback } from 'react';
import { exportDiagram } from '@/common/utils/diagramOperations';
import { YamlExporter } from '../converters/yamlExporter';
import { LLMYamlImporter } from '../converters/llmYamlImporter';
import { useDownload } from './useDownload';
import { createAsyncErrorHandler, createErrorHandlerFactory } from '@/common/types';
import { toast } from 'sonner';
import { getApiUrl, API_ENDPOINTS } from '@/common/utils/apiConfig';

const handleAsyncError = createAsyncErrorHandler(toast);
const createErrorHandler = createErrorHandlerFactory(toast);

export const useExport = () => {
  const { downloadYaml, downloadJson } = useDownload();

  // Export as clean YAML
  const onExportYAML = useCallback(() => {
    const errorHandler = createErrorHandler('Export YAML');
    try {
      const diagramData = exportDiagram();
      const yamlContent = YamlExporter.toYAML(diagramData);
      downloadYaml(yamlContent, 'agent-diagram.yaml');
      toast.success('Exported to YAML format');
    } catch (error) {
      console.error('Export YAML error:', error);
      errorHandler(error instanceof Error ? error : new Error('Failed to export to YAML format'));
    }
  }, [exportDiagram, downloadYaml]);

  // Export as LLM-friendly YAML
  const onExportLLMYAML = useCallback(() => {
    const errorHandler = createErrorHandler('Export LLM YAML');
    try {
      const diagramData = exportDiagram();
      const yamlContent = LLMYamlImporter.toLLMYAML(diagramData);
      downloadYaml(yamlContent, 'agent-diagram-llm.yaml');
      toast.success('Exported to LLM-friendly YAML format');
    } catch (error) {
      console.error('Export LLM YAML error:', error);
      errorHandler(error instanceof Error ? error : new Error('Failed to export to LLM YAML format'));
    }
  }, [exportDiagram, downloadYaml]);

  // Save YAML to backend directory
  const onSaveYAMLToDirectory = useCallback(async (filename?: string) => {
    const errorHandler = createErrorHandler('Save YAML to Directory');

    await handleAsyncError(
      async () => {
        const diagramData = exportDiagram();
        
        // Generate timestamp-based filename if not provided
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        const defaultFilename = `diagram-${timestamp}.yaml`;

        const res = await fetch(getApiUrl(API_ENDPOINTS.SAVE_DIAGRAM), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            diagram: diagramData,
            filename: filename || defaultFilename,
            format: 'yaml'
          }),
        });

        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Save YAML to directory failed: ${errorText}`);
        }

        const result = await res.json();
        if (result.success) {
          toast.success(result.message || 'Saved YAML to yaml_diagrams directory');
        }
      },
      undefined,
      errorHandler
    );
  }, [exportDiagram]);

  // Save LLM-YAML to backend directory
  const onSaveLLMYAMLToDirectory = useCallback(async (filename?: string) => {
    const errorHandler = createErrorHandler('Save LLM-YAML to Directory');

    await handleAsyncError(
      async () => {
        const diagramData = exportDiagram();
        
        // Generate timestamp-based filename with llm-yaml pattern
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        const defaultFilename = `diagram-llm-yaml-${timestamp}.yaml`;

        const res = await fetch(getApiUrl(API_ENDPOINTS.SAVE_DIAGRAM), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            diagram: diagramData,
            filename: filename || defaultFilename,
            format: 'yaml'
          }),
        });

        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Save LLM-YAML to directory failed: ${errorText}`);
        }

        const result = await res.json();
        if (result.success) {
          toast.success(result.message || 'Saved LLM-YAML to llm-yaml_diagrams directory');
        }
      },
      undefined,
      errorHandler
    );
  }, [exportDiagram]);

  // Save JSON to backend directory (for compatibility)
  const onSaveToDirectory = useCallback(async (filename?: string) => {
    const errorHandler = createErrorHandler('Save to Directory');

    await handleAsyncError(
      async () => {
        const diagramData = exportDiagram();

        const res = await fetch(getApiUrl(API_ENDPOINTS.SAVE_DIAGRAM), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            diagram: diagramData,
            filename: filename || 'agent-diagram.json',
            format: 'json'
          }),
        });

        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Save to directory failed: ${errorText}`);
        }

        const result = await res.json();
        if (result.success) {
          toast.success(result.message);
        }
      },
      undefined,
      errorHandler
    );
  }, [exportDiagram]);

  // Export as JSON
  const onExportJSON = useCallback(() => {
    const errorHandler = createErrorHandler('Export JSON');
    try {
      const diagramData = exportDiagram();
      downloadJson(diagramData, 'agent-diagram.json');
      toast.success('Exported to JSON format');
    } catch (error) {
      console.error('Export JSON error:', error);
      errorHandler(error instanceof Error ? error : new Error('Failed to export to JSON format'));
    }
  }, [exportDiagram, downloadJson]);

  return {
    onExportYAML,
    onExportLLMYAML,
    onExportJSON,
    onSaveToDirectory,
    onSaveYAMLToDirectory,
    onSaveLLMYAMLToDirectory,
    onExportCanonical: onExportYAML, // For TopBar compatibility
  };
};