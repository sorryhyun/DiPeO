import { useCallback } from 'react';
import { exportDiagramState } from '@/common/utils/storeSelectors';
import { YamlExporter } from '../converters/yamlExporter';
import { LLMYamlImporter } from '../converters/llmYamlImporter';
import { useDownload } from './useDownload';
import { toast } from 'sonner';
import {
  downloadFile,
  getFileExtension
} from '@/common/utils/fileOperations';
import { withFileErrorHandling } from '../utils/fileUtils';
import { saveDiagram } from '@/common/utils/apiClient';
import { 
  FileFormat,
  SaveFileOptions
} from '../utils/fileUtils';

export const useExport = () => {
  const { downloadYaml, downloadJson } = useDownload();

  // Unified export function
  const exportDiagramAs = useCallback(async (format: FileFormat, filename?: string) => {
    const diagramData = exportDiagramState();
    let content: string;
    let defaultFilename: string;
    
    switch (format) {
      case 'json':
        content = JSON.stringify(diagramData, null, 2);
        defaultFilename = 'diagram.json';
        break;
        
      case 'yaml':
        content = YamlExporter.toYAML(diagramData);
        defaultFilename = 'diagram.yaml';
        break;
        
      case 'llm-yaml':
        content = LLMYamlImporter.toLLMYAML(diagramData);
        defaultFilename = 'diagram.llm-yaml';
        break;
        
      default:
        throw new Error(`Unsupported format: ${format}`);
    }
    
    const finalFilename = filename || defaultFilename;
    
    downloadFile(content, finalFilename);
    toast.success(`Exported as ${format.toUpperCase()}`);
    
    return { content, filename: finalFilename };
  }, []);

  // Save to backend directory
  const saveDiagramAs = useCallback(async (format: FileFormat, filename?: string) => {
    const diagramData = exportDiagramState();
    
    const options: SaveFileOptions = {
      format,
      filename,
      defaultFilename: `diagram${getFileExtension(format)}`
    };
    
    const result = await saveDiagram(diagramData, `${options.filename}${getFileExtension(options.format)}`);
    
    if (result.success) {
      toast.success(`Saved ${format.toUpperCase()} to: ${result.filename}`);
    }
    
    return result;
  }, []);

  // Export functions with error handling
  const onExportJSON = withFileErrorHandling(
    async () => {
      await exportDiagramAs('json');
    },
    'Export JSON'
  );

  const onExportYAML = withFileErrorHandling(
    async () => {
      await exportDiagramAs('yaml');
    },
    'Export YAML'
  );

  const onExportLLMYAML = withFileErrorHandling(
    async () => {
      await exportDiagramAs('llm-yaml');
    },
    'Export LLM-YAML'
  );

  // Save functions with error handling
  const onSaveToDirectory = withFileErrorHandling(
    async (filename?: string) => {
      await saveDiagramAs('json', filename);
    },
    'Save JSON to directory'
  );

  const onSaveYAMLToDirectory = withFileErrorHandling(
    async (filename?: string) => {
      await saveDiagramAs('yaml', filename);
    },
    'Save YAML to directory'
  );

  const onSaveLLMYAMLToDirectory = withFileErrorHandling(
    async (filename?: string) => {
      await saveDiagramAs('llm-yaml', filename);
    },
    'Save LLM-YAML to directory'
  );

  // Batch export function
  const exportAllFormats = useCallback(async (baseFilename: string = 'diagram') => {
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
    }
  }, [exportDiagramAs]);

  // Clone diagram with new name
  const cloneDiagram = useCallback(async (newName: string, format: FileFormat = 'json') => {
    const diagramData = exportDiagramState();
    
    // Create a cloned diagram with metadata
    const clonedDiagram = {
      ...diagramData,
      metadata: {
        name: newName,
        clonedAt: new Date().toISOString()
      }
    };
    
    return saveDiagram(clonedDiagram, `${newName}${getFileExtension(format)}`);
  }, []);

  return {
    // Basic export functions
    onExportJSON,
    onExportYAML,
    onExportLLMYAML,
    
    // Save to backend functions
    onSaveToDirectory,
    onSaveYAMLToDirectory,
    onSaveLLMYAMLToDirectory,
    
    // Advanced functions
    exportDiagramAs,
    saveDiagramAs,
    exportAllFormats,
    cloneDiagram,
    
    // Legacy compatibility (can be removed later)
    downloadYaml,
    downloadJson
  };
};