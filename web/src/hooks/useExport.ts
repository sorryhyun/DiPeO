import { useCallback } from 'react';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import type { ExportFormat } from '@/stores';

export interface UseExportReturn {
  // Export operations
  exportDiagram: () => ExportFormat;
  
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
    importDiagram: store.importDiagram,
    importFromFile,
    validateExportData: store.validateExportData,
  };
}