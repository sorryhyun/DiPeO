import { useState, useCallback, useRef, useEffect } from 'react';
import { useConsolidatedDiagramStore, useExecutionStore } from '@/stores';
import { toast } from 'sonner';

type RunStatus = 'idle' | 'running' | 'success' | 'fail';

interface StreamUpdate {
  type: string;
  nodeId?: string;
  context?: any;
  total_cost?: number;
  memory_stats?: any;
  error?: string;
  output_preview?: string;
  message?: any;
  conversation_log?: string;
}

export const useDiagramRunner = () => {
  const { exportDiagram } = useConsolidatedDiagramStore();
  const {
    setRunContext,
    clearRunContext,
    clearRunningNodes,
    addRunningNode,
    removeRunningNode,
    setCurrentRunningNode
  } = useExecutionStore();
  // Bypass Vite dev server proxy for streaming in development
  const API_BASE = import.meta.env.DEV ? 'http://localhost:8000' : '';
  // Use direct connection for streaming to bypass potential Vite proxy buffering
  const STREAMING_API_BASE = import.meta.env.DEV 
    ? 'http://localhost:8000'  // Direct connection in dev
    : '';
  const [runStatus, setRunStatus] = useState<RunStatus>('idle');
  const [runError, setRunError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  
  const abortControllerRef = useRef<AbortController | null>(null);
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);
  const isComponentMountedRef = useRef(true);
  
  const MAX_RETRIES = 3;
  const RETRY_DELAY = 1000;
  
  // Cleanup function to properly release all resources
  const cleanup = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (readerRef.current) {
      try {
        readerRef.current.releaseLock();
      } catch (error) {
        // Reader might already be released
        console.warn('Reader cleanup warning:', error);
      }
      readerRef.current = null;
    }
  }, []);

  // Manual stop function
  const stopExecution = useCallback(() => {
    console.log('[useDiagramRunner] Manual stop requested');
    cleanup();
    clearRunningNodes();
    setCurrentRunningNode(null);
    setRunStatus('idle');
    setRunError(null);
  }, [cleanup, clearRunningNodes, setCurrentRunningNode]);
  
  useEffect(() => {
    isComponentMountedRef.current = true;
    return () => {
      isComponentMountedRef.current = false;
      cleanup();
    };
  }, [cleanup]);

  const processStreamUpdate = useCallback((update: StreamUpdate) => {
    // Check if component is still mounted before updating state
    if (!isComponentMountedRef.current) {
      console.log('[Stream Update] Component unmounted, skipping update');
      return;
    }

    const timestamp = new Date().toISOString();
    console.log('[Stream Update]', timestamp, update.type, update.nodeId, `(${Date.now()})`);

    switch (update.type) {
      case 'node_start':
        if (update.nodeId) {
          console.log('[Stream] Starting node:', update.nodeId);
          addRunningNode(update.nodeId);
          setCurrentRunningNode(update.nodeId);
        }
        break;

      case 'node_complete':
        if (update.nodeId) {
          console.log('[Stream] Completing node:', update.nodeId);
          removeRunningNode(update.nodeId);
          setCurrentRunningNode(null);
        }
        break;

      case 'node_error':
        if (update.nodeId) {
          console.error(`Node error: ${update.nodeId}`, update.error);
          removeRunningNode(update.nodeId);
          setCurrentRunningNode(null);
        }
        break;

      case 'execution_complete':
        clearRunningNodes();
        setCurrentRunningNode(null);
        setRunStatus('success');
        if (update.context) {
          setRunContext(update.context);
        }
        
        // Show notification if conversation was saved
        if (update.conversation_log) {
          const logFileName = update.conversation_log.split('/').pop();
          toast.success(`Conversation log saved: ${logFileName}`);
        }
        break;

      case 'execution_error':
        clearRunningNodes();
        setCurrentRunningNode(null);
        setRunStatus('fail');
        if (update.error) {
          setRunError(update.error);
          console.error('Execution error:', update.error);
        }
        break;
      case 'message_added':
        if (update.message) {
          // Dispatch custom event for conversation dashboard
          // Use try-catch to prevent errors if window is not available
          try {
            window.dispatchEvent(new CustomEvent('conversation-update', {
              detail: { type: 'message_added', data: update }
            }));
          } catch (error) {
            console.warn('Failed to dispatch conversation update event:', error);
          }
        }
        break;
      default:
        // Unknown update type - silently ignore
    }
  }, [addRunningNode, removeRunningNode, clearRunningNodes, setRunContext, setCurrentRunningNode]);


  const executeWithRetry = async (fn: () => Promise<any>, retries = 0): Promise<any> => {
    try {
      return await fn();
    } catch (error) {
      // Check if it's a network error or timeout
      const isNetworkError = error instanceof TypeError && error.message.includes('fetch');
      const isTimeout = error instanceof Error && error.message.includes('timeout');
      const isAborted = error instanceof Error && error.message.includes('abort');
      
      if (!isAborted && (isNetworkError || isTimeout) && retries < MAX_RETRIES) {
        console.info(`Retrying execution (attempt ${retries + 1}/${MAX_RETRIES})...`);
        setRetryCount(retries + 1);
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * (retries + 1)));
        
        return executeWithRetry(fn, retries + 1);
      }
      
      throw error;
    }
  };

  const handleRunDiagram = useCallback(async () => {
    // Clear any previous execution state and resources
    cleanup();
    clearRunContext();
    clearRunningNodes();
    setCurrentRunningNode(null);
    setRunStatus('running');
    setRunError(null);
    setRetryCount(0);

    // Create new abort controller for this execution
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    try {
        const diagramData = exportDiagram();
        
        // Validate API keys first
        const keysRes = await fetch(`${API_BASE}/api/apikeys`, { signal });
        if (keysRes.ok) {
          const keys = await keysRes.json();
          const validIds = new Set(Array.isArray(keys) ? keys.map((k: any) => k.id) : []);

          // Validate person API keys
          if (Array.isArray(keys)) {
            (diagramData.persons || []).forEach((person: any) => {
              if (!validIds.has(person.apiKeyId)) {
                const fallback = keys.find((k: any) => k.service === person.service);
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
          console.warn('Failed to fetch /api/apikeys', keysRes.status);
        }

        // Start streaming execution with retry
        const res = await executeWithRetry(async () => {
          const response = await fetch(`${STREAMING_API_BASE}/api/run-diagram`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(diagramData),
            signal,
          });
          
          if (!response.ok && response.status >= 500) {
            // Server errors are retryable
            throw new Error(`Server error: ${response.status}`);
          }
          
          return response;
        });

        if (!res.ok) {
          const errText = await res.text();
          throw new Error(`Run Diagram failed: ${errText}`);
        }

        // Handle streaming response
        const reader = res.body?.getReader();
        if (!reader) {
          throw new Error('Failed to get response reader');
        }

        // Store reader reference for cleanup
        readerRef.current = reader;

        const decoder = new TextDecoder();
        let buffer = '';
        let finalResult: any = null;

        try {
          while (true) {
            // Check if component unmounted or aborted
            if (!isComponentMountedRef.current || signal.aborted) {
              throw new Error('Request was aborted or component unmounted');
            }
            
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
              if (line.trim()) {
                try {
                  // Handle SSE format: "data: {json}"
                  let jsonStr = line;
                  if (line.startsWith('data: ')) {
                    jsonStr = line.substring(6); // Remove "data: " prefix
                  }
                  const update: StreamUpdate = JSON.parse(jsonStr);
                  processStreamUpdate(update);

                  // Capture final result
                  if (update.type === 'execution_complete') {
                    finalResult = update;
                  } else if (update.type === 'execution_error') {
                    throw new Error(update.error || 'Execution failed');
                  }
                  
                  // Add small delay for node transitions to be visible
                  if (update.type === 'node_start' || update.type === 'node_complete') {
                    await new Promise(resolve => setTimeout(resolve, 50));
                  }
                } catch (parseError) {
                  // Only warn for actual parse errors, not execution errors
                  if (parseError instanceof SyntaxError) {
                    console.warn('Failed to parse streaming update:', line, parseError);
                    // Try to extract meaningful information from malformed JSON
                    if (line.includes('error') || line.includes('Error')) {
                      console.error('Possible error in malformed update:', line);
                    }
                    // Continue processing other lines
                  } else {
                    // Re-throw execution errors
                    throw parseError;
                  }
                }
              }
            }
          }

          // Handle any remaining buffer content
          if (buffer.trim()) {
            try {
              // Handle SSE format: "data: {json}"
              let jsonStr = buffer;
              if (buffer.startsWith('data: ')) {
                jsonStr = buffer.substring(6); // Remove "data: " prefix
              }
              const update: StreamUpdate = JSON.parse(jsonStr);
              processStreamUpdate(update);
              if (update.type === 'execution_complete') {
                finalResult = update;
              }
            } catch (parseError) {
              console.warn('Failed to parse final buffer content:', buffer, parseError);
            }
          }

          return finalResult || {};

        } finally {
          // Clear reader reference
          if (readerRef.current) {
            try {
              readerRef.current.releaseLock();
            } catch (error) {
              console.warn('Error releasing reader lock:', error);
            }
            readerRef.current = null;
          }
        }
    } catch (error) {
      // Only update state if component is still mounted
      if (isComponentMountedRef.current) {
        clearRunningNodes();
        setCurrentRunningNode(null);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setRunError(errorMessage);
        console.error('Run Diagram Error:', errorMessage);
        
        // Show error toast
        toast.error(`Run Diagram: ${errorMessage}`);
        
        setRunStatus('fail');
      }
    } finally {
      // Clean up resources
      cleanup();
    }
  }, [exportDiagram, processStreamUpdate, clearRunningNodes, clearRunContext, setCurrentRunningNode, cleanup, API_BASE, STREAMING_API_BASE]);

  const handleRunDiagramSync = useCallback(async () => {
    // Fallback to synchronous execution (for debugging or compatibility)
    clearRunContext();
    clearRunningNodes();
    setRunStatus('running');
    setRunError(null);

    try {
        const diagramData = exportDiagram();
        const res = await fetch(`${API_BASE}/api/run-diagram-sync`, {
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

  return {
    runStatus,
    runError,
    retryCount,
    handleRunDiagram,
    handleRunDiagramSync, // For fallback/debugging
    stopExecution, // Manual stop function
  };
};