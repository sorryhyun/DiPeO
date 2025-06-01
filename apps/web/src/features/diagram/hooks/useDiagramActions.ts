// apps/web/src/hooks/useDiagramActions.ts
// Minimal orchestration layer for diagram actions
import { useFileImport } from '@/features/serialization/hooks/useFileImport';
import { useExport } from '@/features/serialization/hooks/useExport';

export const useDiagramActions = () => {
  // Import hooks from serialization
  const { onImportYAML, onConvertJSONtoYAML } = useFileImport();
  const { 
    onExportYAML, 
    onExportLLMYAML, 
    onSaveToDirectory, 
    onSaveYAMLToDirectory,
    onExportCanonical 
  } = useExport();

  // Return orchestrated actions
  return {
    onExportYAML,
    onExportLLMYAML,
    onImportYAML,
    onSaveToDirectory,
    onSaveYAMLToDirectory,
    onConvertJSONtoYAML,
    onExportCanonical,
  };
};