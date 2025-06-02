import { useState, useCallback, useRef, useEffect } from 'react';
import { useConsolidatedDiagramStore, useExecutionStore } from '@/core/stores';
import { toast } from 'sonner';
import { createErrorHandlerFactory, PersonDefinition } from '@/shared/types';
import { API_ENDPOINTS, getApiUrl } from '@/shared/utils/apiConfig';
import { isApiKey, parseApiArrayResponse } from '@/shared/utils/typeGuards';
import { useHybridExecution } from './useHybridExecution';
import { createBrowserExecutionOrchestrator } from '@/engine/browser-execution-orchestrator';

const createErrorHandler = createErrorHandlerFactory(toast);

type RunStatus = 'idle' | 'running' | 'success' | 'fail';



export const useDiagramRunner = () => {
  const { exportDiagram } = useConsolidatedDiagramStore();
  const {
    setRunContext,
    clearRunContext,
    clearRunningNodes,
    setCurrentRunningNode
  } = useExecutionStore();
  const [runStatus, setRunStatus] = useState<RunStatus>('idle');
  const [runError, setRunError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  
  // Hybrid execution hook
  const { executeHybrid } = useHybridExecution();
  
  const isComponentMountedRef = useRef(true);
  
  // Manual stop function
  const stopExecution = useCallback(() => {
    console.log('[useDiagramRunner] Manual stop requested');
    clearRunningNodes();
    setCurrentRunningNode(null);
    setRunStatus('idle');
    setRunError(null);
  }, [clearRunningNodes, setCurrentRunningNode]);
  
  useEffect(() => {
    isComponentMountedRef.current = true;
    return () => {
      isComponentMountedRef.current = false;
    };
  }, []);


  const onRunDiagram = useCallback(async () => {
    // Clear any previous execution state
    clearRunContext();
    clearRunningNodes();
    setCurrentRunningNode(null);
    setRunStatus('running');
    setRunError(null);
    setRetryCount(0);

    try {
      const diagramData = exportDiagram();
      
      // Validate API keys first
      try {
        const keysRes = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS));
        if (keysRes.ok) {
          const response = await keysRes.json();
          const apiKeysData = response.apiKeys || response; // Handle both formats
          const apiKeys = parseApiArrayResponse(apiKeysData, isApiKey);
          const validIds = new Set(apiKeys.map(k => k.id));

          // Validate person API keys
          if (apiKeys.length > 0) {
            (diagramData.persons || []).forEach((person: PersonDefinition) => {
              if (person.apiKeyId && !validIds.has(person.apiKeyId)) {
                const fallback = apiKeys.find(k => k.service === person.service);
                if (fallback) {
                  console.warn(
                    `Replaced invalid apiKeyId ${person.apiKeyId} → ${fallback.id}`
                  );
                  person.apiKeyId = fallback.id;
                }
              }
            });
          }
        } else {
          console.warn('Failed to fetch API keys', keysRes.status);
        }
      } catch (keyError) {
        console.warn('API key validation failed:', keyError);
      }

      // Use browser-safe execution orchestrator with automatic server fallback
      const orchestrator = createBrowserExecutionOrchestrator();
      const result = await orchestrator.execute(diagramData as any, {});
      
      if (result.context) {
        setRunContext(result.context);
      }
      setRunStatus('success');
      
      // Show cost if available
      if (result.metadata?.totalCost && result.metadata.totalCost > 0) {
        toast.success(`Execution completed. Total cost: $${result.metadata.totalCost.toFixed(4)}`);
      } else {
        toast.success('Execution completed successfully');
      }
      
      return result;
    } catch (error) {
      // Only update state if component is still mounted
      if (isComponentMountedRef.current) {
        clearRunningNodes();
        setCurrentRunningNode(null);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setRunError(errorMessage);
        console.error('Run Diagram Error:', errorMessage);
        
        // Show error toast using error handler factory
        const errorHandler = createErrorHandler('Diagram Execution');
        errorHandler(new Error(errorMessage));
        
        setRunStatus('fail');
      }
    }
  }, [exportDiagram, clearRunningNodes, clearRunContext, setCurrentRunningNode]);

  const onRunDiagramSync = useCallback(async () => {
    // Fallback to synchronous execution (for debugging or compatibility)
    clearRunContext();
    clearRunningNodes();
    setRunStatus('running');
    setRunError(null);

    try {
        const diagramData = exportDiagram();
        const res = await fetch(getApiUrl(API_ENDPOINTS.RUN_DIAGRAM_SYNC), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(diagramData),
        });

        if (!res.ok) {
          const errText = await res.text();
          throw new Error(`Run Diagram failed: ${errText}`);
        }

        const result = await res.json();
        
        if (result.context) {
          setRunContext(result.context);
        }
        setRunStatus('success');
        return result;
      } catch (error) {
        clearRunningNodes();
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setRunError(errorMessage);
        console.error('[Run Diagram Sync] Error:', errorMessage);
        setRunStatus('fail');
      }
  }, [exportDiagram, clearRunningNodes, clearRunContext]);

  // Hybrid execution mode
  const onRunDiagramHybrid = useCallback(async () => {
    clearRunContext();
    clearRunningNodes();
    setCurrentRunningNode(null);
    setRunStatus('running');
    setRunError(null);
    setRetryCount(0);

    try {
      const diagramData = exportDiagram();
      
      // Execute with hybrid approach
      const result = await executeHybrid(diagramData as any);
      
      if (result.context) {
        setRunContext(result.context);
      }
      
      setRunStatus('success');
      
      // Show cost if available
      if (result.total_cost) {
        toast.success(`Execution completed. Total cost: $${result.total_cost.toFixed(4)}`);
      }
      
      return result;
    } catch (error) {
      clearRunningNodes();
      setCurrentRunningNode(null);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setRunError(errorMessage);
      console.error('[Hybrid Execution] Error:', errorMessage);
      
      // Show error toast
      const errorHandler = createErrorHandler('Hybrid Execution');
      errorHandler(new Error(errorMessage));
      
      setRunStatus('fail');
    }
  }, [exportDiagram, executeHybrid, clearRunningNodes, clearRunContext, setCurrentRunningNode]);

  return {
    runStatus,
    runError,
    retryCount,
    onRunDiagram,
    onRunDiagramSync, // For fallback/debugging
    onRunDiagramHybrid, // Hybrid execution mode
    stopExecution, // Manual stop function
  };
};