import { useCallback } from 'react';
import { useUnifiedStore } from '@/stores/useUnifiedStore';
import type { ExportFormat } from '@/stores/unifiedStore';

export interface UseExportReturn {
  // Export operations
  exportDiagram: () => ExportFormat;
  exportAsJSON: () => string;
  downloadAsJSON: (filename?: string) => void;
  
  // Import operations
  importDiagram: (data: ExportFormat | string) => void;
  importFromFile: (file: File) => Promise<void>;
  
  // Validation
  validateExportData: (data: unknown) => { valid: boolean; errors: string[] };
}

/**
 * Hook for diagram export/import functionality
 * Provides a clean API for exporting and importing diagrams
 */
export function useExport(): UseExportReturn {
  const store = useUnifiedStore();

  // Download diagram as JSON file
  const downloadAsJSON = useCallback((filename?: string) => {
    const json = store.exportAsJSON();
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `diagram-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [store]);

  // Import diagram from file
  const importFromFile = useCallback(async (file: File): Promise<void> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const content = e.target?.result as string;
          store.importDiagram(content);
          resolve();
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };
      
      reader.readAsText(file);
    });
  }, [store]);

  return {
    exportDiagram: store.exportDiagram,
    exportAsJSON: store.exportAsJSON,
    downloadAsJSON,
    importDiagram: store.importDiagram,
    importFromFile,
    validateExportData: store.validateExportData,
  };
}