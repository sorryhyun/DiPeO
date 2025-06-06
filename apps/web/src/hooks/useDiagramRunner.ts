import { useState, useCallback, useRef, useEffect } from 'react';
import { 
  useSetRunContext,
  useClearRunContext,
  useClearRunningNodes,
  useSetCurrentRunningNode,
  useAddRunningNode,
  useRemoveRunningNode,
  useSkippedNodes,
  exportDiagramState
} from '@/hooks/useStoreSelectors';
import { toast } from 'sonner';
import { PersonDefinition, InteractivePromptData } from '@/types';
import { DiagramData, ExecutionUpdate } from '@/types/api';
import { API_ENDPOINTS, getApiUrl } from '@/utils/api';
import { isApiKey, parseApiArrayResponse } from '@/utils/types';
import { 
  createWebSocketExecutionClient
} from '@/utils/websocket/execution-client';
import { getWebSocketClient } from '@/utils/websocket/client';

// Removed unused createErrorHandler

type RunStatus = 'idle' | 'running' | 'success' | 'fail';



export const useDiagramRunner = () => {
  const setRunContext = useSetRunContext();
  const clearRunContext = useClearRunContext();
  const clearRunningNodes = useClearRunningNodes();
  const setCurrentRunningNode = useSetCurrentRunningNode();
  const addRunningNode = useAddRunningNode();
  const removeRunningNode = useRemoveRunningNode();
  const skippedNodes = useSkippedNodes();
  const [runStatus, setRunStatus] = useState<RunStatus>('idle');
  const [runError, setRunError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [interactivePrompt, setInteractivePrompt] = useState<InteractivePromptData | null>(null);
  
  // WebSocket execution client
  
  // Create WebSocket execution client
  const executionClientRef = useRef(
    createWebSocketExecutionClient(getWebSocketClient({ debug: true }))
  );
  const isComponentMountedRef = useRef(true);
  
  useEffect(() => {
    // Set up interactive prompt handler for WebSocket
    const wsClient = executionClientRef.current;
    if ('setInteractivePromptHandler' in wsClient) {
      wsClient.setInteractivePromptHandler((prompt: InteractivePromptData) => {
        setInteractivePrompt(prompt);
      });
    }
  }, []);
  
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
      const diagramData = exportDiagramState();
      
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

      // Execute diagram using WebSocket client
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
          
          // Handle WebSocket update formats
          const nodeId = 'node_id' in update ? (update as any).node_id : 
                        'nodeId' in update ? (update as any).nodeId : undefined;
          
          switch (update.type) {
            case 'node_start':
              if (nodeId && typeof nodeId === 'string') {
                setCurrentRunningNode(nodeId);
                addRunningNode(nodeId);
              }
              break;
              
            case 'node_complete':
              if (nodeId && typeof nodeId === 'string') {
                removeRunningNode(nodeId);
              }
              break;
              
            case 'conversation_update':
              // Handle conversation streaming updates
              console.log('Conversation update:', update);
              break;
              
            case 'execution_started':
              console.log('Execution started:', update.executionId);
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
      
      if (result.metadata?.totalTokens && result.metadata.totalTokens > 0) {
        summaryMessage = `Execution completed. Total tokens: ${result.metadata.totalTokens.toFixed(2)}`;
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
        
        // Show error toast directly
        toast.error(`Diagram Execution: ${errorMessage}`);
        
        setRunStatus('fail');
      }
    }
  }, [clearRunningNodes, clearRunContext, setCurrentRunningNode, addRunningNode, removeRunningNode]);

  // Execution control functions
  const pauseNode = useCallback((nodeId: string) => {
    if (executionClientRef.current && 'pauseNode' in executionClientRef.current) {
      executionClientRef.current.pauseNode(nodeId);
    }
  }, []);
  
  const resumeNode = useCallback((nodeId: string) => {
    if (executionClientRef.current && 'resumeNode' in executionClientRef.current) {
      executionClientRef.current.resumeNode(nodeId);
    }
  }, []);
  
  const skipNode = useCallback((nodeId: string) => {
    if (executionClientRef.current && 'skipNode' in executionClientRef.current) {
      executionClientRef.current.skipNode(nodeId);
    }
  }, []);
  
  // Interactive prompt response handler
  const sendInteractiveResponse = useCallback((nodeId: string, response: string) => {
    if (executionClientRef.current && 'sendInteractiveResponse' in executionClientRef.current) {
      executionClientRef.current.sendInteractiveResponse(nodeId, response);
      // Clear the prompt after sending response
      setInteractivePrompt(null);
    }
  }, []);
  
  // Cancel interactive prompt
  const cancelInteractivePrompt = useCallback(() => {
    setInteractivePrompt(null);
    // Optionally send empty response to unblock execution
    if (interactivePrompt && executionClientRef.current && 'sendInteractiveResponse' in executionClientRef.current) {
      executionClientRef.current.sendInteractiveResponse(interactivePrompt.nodeId, '');
    }
  }, [interactivePrompt]);

  return {
    runStatus,
    runError,
    retryCount,
    onRunDiagram, // Primary unified execution
    stopExecution, // Manual stop function
    // Control functions
    pauseNode,
    resumeNode,
    skipNode,
    // Interactive prompt handling
    interactivePrompt,
    sendInteractiveResponse,
    cancelInteractivePrompt,
  };
};