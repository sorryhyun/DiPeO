import { useState, useCallback, useRef, useEffect } from 'react';
import { useDiagramOperationsStore, useExecutionStore } from '@/core/stores';
import { toast } from 'sonner';
import { createErrorHandlerFactory, PersonDefinition } from '@/shared/types';
import { API_ENDPOINTS, getApiUrl } from '@/shared/utils/apiConfig';
import { isApiKey, parseApiArrayResponse } from '@/shared/utils/typeGuards';
import { 
  createUnifiedExecutionClient, 
  type DiagramData, 
  type ExecutionUpdate 
} from '@/engine/unified-execution-client';

const createErrorHandler = createErrorHandlerFactory(toast);

type RunStatus = 'idle' | 'running' | 'success' | 'fail';



export const useDiagramRunner = () => {
  const { exportDiagram } = useDiagramOperationsStore();
  const {
    setRunContext,
    clearRunContext,
    clearRunningNodes,
    setCurrentRunningNode,
    addRunningNode,
    removeRunningNode
  } = useExecutionStore();
  const [runStatus, setRunStatus] = useState<RunStatus>('idle');
  const [runError, setRunError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  
  // Unified execution client
  const executionClientRef = useRef(createUnifiedExecutionClient());
  const isComponentMountedRef = useRef(true);
  
  // Manual stop function
  const stopExecution = useCallback(() => {
    console.log('[useDiagramRunner] Manual stop requested');
    executionClientRef.current.abort();
    clearRunningNodes();
    setCurrentRunningNode(null);
    setRunStatus('idle');
    setRunError(null);
  }, [clearRunningNodes, setCurrentRunningNode]);
  
  useEffect(() => {
    isComponentMountedRef.current = true;
    return () => {
      isComponentMountedRef.current = false;
      executionClientRef.current.abort(); // Cleanup on unmount
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

      // Use unified execution client with SSE streaming
      const result = await executionClientRef.current.execute(
        diagramData as DiagramData, 
        {
          continueOnError: false,
          allowPartial: false,
          debugMode: false
        },
        (update: ExecutionUpdate) => {
          // Handle real-time execution updates
          if (!isComponentMountedRef.current) return;
          
          switch (update.type) {
            case 'node_start':
              if (update.nodeId) {
                setCurrentRunningNode(update.nodeId);
                addRunningNode(update.nodeId);
              }
              break;
              
            case 'node_complete':
              if (update.nodeId) {
                removeRunningNode(update.nodeId);
              }
              break;
              
            case 'conversation_update':
              // Handle conversation streaming updates
              console.log('Conversation update:', update);
              break;
              
            case 'execution_started':
              console.log('Execution started:', update.execution_id);
              break;
              
            case 'execution_complete':
              setCurrentRunningNode(null);
              clearRunningNodes();
              break;
              
            case 'execution_error':
              setCurrentRunningNode(null);
              clearRunningNodes();
              break;
          }
        }
      );
      
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
  }, [exportDiagram, clearRunningNodes, clearRunContext, setCurrentRunningNode, addRunningNode, removeRunningNode]);

  return {
    runStatus,
    runError,
    retryCount,
    onRunDiagram, // Primary unified execution
    stopExecution, // Manual stop function
  };
};