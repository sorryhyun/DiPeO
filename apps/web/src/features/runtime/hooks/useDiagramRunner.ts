import { useState, useCallback, useRef, useEffect } from 'react';
import { useExecutionStore } from '@/state/stores';
import { exportDiagram } from '@/common/utils/diagramOperations';
import { toast } from 'sonner';
import { createErrorHandlerFactory, PersonDefinition } from '@/common/types';
import { API_ENDPOINTS, getApiUrl } from '@/common/utils/apiConfig';
import { isApiKey, parseApiArrayResponse } from '@/common/utils/typeGuards';
import { 
  createWebSocketExecutionClient,
  type DiagramData,
  type ExecutionUpdate
} from '@/features/runtime/websocket-execution-client';
import { getWebSocketClient } from '@/features/runtime/websocket-client';
import type { InteractivePromptData } from '@/features/runtime/components/InteractivePromptModal';

const createErrorHandler = createErrorHandlerFactory(toast);

type RunStatus = 'idle' | 'running' | 'success' | 'fail';



export const useDiagramRunner = () => {
  const {
    setRunContext,
    clearRunContext,
    clearRunningNodes,
    setCurrentRunningNode,
    addRunningNode,
    removeRunningNode,
    skippedNodes
  } = useExecutionStore();
  const [runStatus, setRunStatus] = useState<RunStatus>('idle');
  const [runError, setRunError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [interactivePrompt, setInteractivePrompt] = useState<InteractivePromptData | null>(null);
  
  // Always use WebSocket execution (SSE has been deprecated)
  const useWebSocket = true;
  
  // Create WebSocket execution client
  const executionClientRef = useRef(
    createWebSocketExecutionClient(getWebSocketClient({ debug: true }))
  );
  const isComponentMountedRef = useRef(true);
  
  useEffect(() => {
    if (useWebSocket) {
      console.log('[useDiagramRunner] Using WebSocket execution client');
      // Set up interactive prompt handler for WebSocket
      const wsClient = executionClientRef.current;
      if ('setInteractivePromptHandler' in wsClient) {
        wsClient.setInteractivePromptHandler((prompt: InteractivePromptData) => {
          setInteractivePrompt(prompt);
        });
      }
    } else {
      console.log('[useDiagramRunner] Using SSE execution client');
    }
  }, [useWebSocket]);
  
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
          
          // Handle both SSE and WebSocket update formats
          const nodeId = 'node_id' in update ? update.node_id : 
                        'nodeId' in update ? update.nodeId : undefined;
          
          switch (update.type) {
            case 'node_start':
              if (nodeId) {
                setCurrentRunningNode(nodeId);
                addRunningNode(nodeId);
              }
              break;
              
            case 'node_complete':
              if (nodeId) {
                removeRunningNode(nodeId);
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
      
      // Show execution summary
      const skipCount = Object.keys(skippedNodes).length;
      let summaryMessage = 'Execution completed successfully';
      
      if (result.metadata?.totalCost && result.metadata.totalCost > 0) {
        summaryMessage = `Execution completed. Total cost: $${result.metadata.totalCost.toFixed(4)}`;
      }
      
      if (skipCount > 0) {
        summaryMessage += ` • ${skipCount} node${skipCount > 1 ? 's' : ''} skipped`;
      }
      
      toast.success(summaryMessage);
      
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
  }, [clearRunningNodes, clearRunContext, setCurrentRunningNode, addRunningNode, removeRunningNode]);

  // Execution control functions (only available with WebSocket)
  const pauseNode = useCallback((nodeId: string) => {
    if (useWebSocket && executionClientRef.current && 'pauseNode' in executionClientRef.current) {
      executionClientRef.current.pauseNode(nodeId);
    }
  }, [useWebSocket]);
  
  const resumeNode = useCallback((nodeId: string) => {
    if (useWebSocket && executionClientRef.current && 'resumeNode' in executionClientRef.current) {
      executionClientRef.current.resumeNode(nodeId);
    }
  }, [useWebSocket]);
  
  const skipNode = useCallback((nodeId: string) => {
    if (useWebSocket && executionClientRef.current && 'skipNode' in executionClientRef.current) {
      executionClientRef.current.skipNode(nodeId);
    }
  }, [useWebSocket]);
  
  // Interactive prompt response handler
  const sendInteractiveResponse = useCallback((nodeId: string, response: string) => {
    if (useWebSocket && executionClientRef.current && 'sendInteractiveResponse' in executionClientRef.current) {
      executionClientRef.current.sendInteractiveResponse(nodeId, response);
      // Clear the prompt after sending response
      setInteractivePrompt(null);
    }
  }, [useWebSocket]);
  
  // Cancel interactive prompt
  const cancelInteractivePrompt = useCallback(() => {
    setInteractivePrompt(null);
    // Optionally send empty response to unblock execution
    if (interactivePrompt && useWebSocket && executionClientRef.current && 'sendInteractiveResponse' in executionClientRef.current) {
      executionClientRef.current.sendInteractiveResponse(interactivePrompt.nodeId, '');
    }
  }, [interactivePrompt, useWebSocket]);

  return {
    runStatus,
    runError,
    retryCount,
    onRunDiagram, // Primary unified execution
    stopExecution, // Manual stop function
    // Control functions (WebSocket only)
    pauseNode,
    resumeNode,
    skipNode,
    isWebSocketEnabled: useWebSocket,
    // Interactive prompt handling
    interactivePrompt,
    sendInteractiveResponse,
    cancelInteractivePrompt,
  };
};