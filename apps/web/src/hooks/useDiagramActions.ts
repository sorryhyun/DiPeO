// apps/web/src/hooks/useDiagramActions.ts
import { useCallback, ChangeEvent } from 'react';
import { useConsolidatedDiagramStore } from '@/stores';
import { YamlExporter } from '@/utils/yamlExporter';
import { downloadFile, downloadJson } from '@/utils/downloadUtils';
import { createAsyncErrorHandler, createErrorHandlerFactory } from '@repo/core-model';
import { toast } from 'sonner';
import { getApiUrl } from '@/utils/apiConfig';

const handleAsyncError = createAsyncErrorHandler(toast);
const createErrorHandler = createErrorHandlerFactory(toast);


export const useDiagramActions = () => {
  const { exportDiagram, loadDiagram } = useConsolidatedDiagramStore();

  // Save as traditional JSON (for backwards compatibility)
  const handleSave = useCallback(() => {
    const diagramData = exportDiagram();
    downloadJson(diagramData, 'agent-diagram.json');
    toast.success('Saved diagram as JSON');
  }, [exportDiagram]);

  // Export as clean YAML
  const handleExportYAML = useCallback(() => {
    try {
      const diagramData = exportDiagram();
      const yamlContent = YamlExporter.toYAML(diagramData);
      downloadFile(yamlContent, 'agent-diagram.yaml', 'text/yaml');
      toast.success('Exported to YAML format');
    } catch (error) {
      console.error('Export YAML error:', error);
      toast.error('Failed to export to YAML format');
    }
  }, [exportDiagram]);

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

          const diagramData = YamlExporter.fromYAML(result);
          loadDiagram(diagramData);
          toast.success('Imported from YAML format');
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

  // Load traditional JSON (for backwards compatibility)
  const handleLoad = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const errorHandler = createErrorHandler('Load Diagram');
    const reader = new FileReader();

    reader.onload = async (e) => {
      await handleAsyncError(
        async () => {
          const result = e.target?.result as string;
          if (!result) {
            throw new Error('Failed to read file content');
          }

          const json = JSON.parse(result);
          loadDiagram(json);
          toast.success('Loaded diagram from JSON');
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
        const yamlContent = YamlExporter.toYAML(diagramData);

        const res = await fetch(getApiUrl('/api/save'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            content: yamlContent,
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
            content: diagramData,
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

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const jsonContent = e.target?.result as string;
        const diagram = JSON.parse(jsonContent);
        const yamlContent = YamlExporter.toYAML(diagram);

        const yamlFilename = file.name.replace('.json', '.yaml');
        downloadFile(yamlContent, yamlFilename, 'text/yaml');
        toast.success('Converted JSON to YAML');
      } catch (error) {
        toast.error('Failed to convert JSON to YAML');
        console.error(error);
      }
    };

    reader.readAsText(file);
  }, []);

  return {
    handleSave,
    handleLoad,
    handleExportYAML,
    handleImportYAML,
    handleSaveToDirectory,
    handleSaveYAMLToDirectory,
    handleConvertJSONtoYAML,
    // Aliases for backwards compatibility with UI
    handleExportMinimal: handleExportYAML,
    handleImportCanonical: handleImportYAML,
    handleExportMinimalToDirectory: handleSaveYAMLToDirectory,
    handleExportCanonical: handleExportYAML, // Add this for TopBar compatibility
  };
};