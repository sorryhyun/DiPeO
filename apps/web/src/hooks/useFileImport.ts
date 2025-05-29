// Hook for importing diagrams from UML or YAML
import React, { useCallback } from 'react';
import { useConsolidatedDiagramStore } from '@/stores';
import { createAsyncErrorHandler, createErrorHandlerFactory } from '@repo/core-model';
import { toast } from 'sonner';

const handleAsyncError = createAsyncErrorHandler(toast);
const createErrorHandler = createErrorHandlerFactory(toast);


export const useFileImport = () => {
  const { loadDiagram } = useConsolidatedDiagramStore();

  const handleImportUML = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const errorHandler = createErrorHandler('Import UML');
    
    await handleAsyncError(
      async () => {
        const text = await file.text();
        const res = await fetch('/api/import-uml', {
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
        const res = await fetch('/api/import-yaml', {
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

  return {
    handleImportUML,
    handleImportYAML,
  };
};