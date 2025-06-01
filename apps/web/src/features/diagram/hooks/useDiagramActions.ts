// apps/web/src/hooks/useDiagramActions.ts
import { useCallback, ChangeEvent } from 'react';
import { useConsolidatedDiagramStore } from '@/shared/stores';
import { YamlExporter } from '@/features/diagram';
import { LLMYamlImporter } from '@/features/diagram/utils/llmYamlImporter';
import { useDownload } from '@/shared/hooks/useDownload';
import { createAsyncErrorHandler, createErrorHandlerFactory } from '@/shared/types';
import { toast } from 'sonner';
import { getApiUrl } from '@/shared/utils/apiConfig';

const handleAsyncError = createAsyncErrorHandler(toast);
const createErrorHandler = createErrorHandlerFactory(toast);


export const useDiagramActions = () => {
  const { exportDiagram, loadDiagram } = useConsolidatedDiagramStore();
  const { downloadYaml } = useDownload();


  // Export as clean YAML
  const handleExportYAML = useCallback(() => {
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

  // Import from YAML
  const handleImportYAML = useCallback((event: ChangeEvent<HTMLInputElement>) => {
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


  // Save YAML to backend directory
  const handleSaveYAMLToDirectory = useCallback(async (filename?: string) => {
    const errorHandler = createErrorHandler('Save YAML to Directory');

    await handleAsyncError(
      async () => {
        const diagramData = exportDiagram();

        const res = await fetch(getApiUrl('/api/save'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            diagram: diagramData,
            filename: filename || 'agent-diagram.yaml',
            format: 'yaml'
          }),
        });

        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Save YAML to directory failed: ${errorText}`);
        }

        const result = await res.json();
        if (result.success) {
          toast.success('Saved YAML to project root');
        }
      },
      undefined,
      errorHandler
    );
  }, [exportDiagram]);

  // Save JSON to backend directory (for compatibility)
  const handleSaveToDirectory = useCallback(async (filename?: string) => {
    const errorHandler = createErrorHandler('Save to Directory');

    await handleAsyncError(
      async () => {
        const diagramData = exportDiagram();

        const res = await fetch(getApiUrl('/api/save'), {
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

  // Convert between formats
  const handleConvertJSONtoYAML = useCallback((event: ChangeEvent<HTMLInputElement>) => {
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
  }, []);

  // Export as LLM-friendly YAML
  const handleExportLLMYAML = useCallback(() => {
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

  return {
    handleExportYAML,
    handleExportLLMYAML,
    handleImportYAML,
    handleSaveToDirectory,
    handleSaveYAMLToDirectory,
    handleConvertJSONtoYAML,
    handleExportCanonical: handleExportYAML, // Add this for TopBar compatibility
  };
};