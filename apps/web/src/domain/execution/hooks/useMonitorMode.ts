/**
 * useMonitorMode - Hook to handle monitor mode auto-execution
 *
 * This hook detects when the app is in monitor mode and automatically
 * monitors CLI-launched executions.
 */

import { useEffect, useRef, useContext } from 'react';
import { useQuery, useLazyQuery } from '@apollo/client';
import { toast } from 'sonner';
import { useExecution } from './useExecution';
import { useDiagramLoader } from '@/domain/diagram/hooks/useDiagramLoader';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import { useUIState, useUIOperations } from '@/infrastructure/store/hooks';
import { nodeId } from '@/infrastructure/types';
import { Status } from '@dipeo/models';
import { GETACTIVECLISESSION_QUERY, GETEXECUTION_QUERY } from '@/__generated__/queries/all-queries';

export interface UseMonitorModeOptions {
  pollCliSessions?: boolean;
  execution?: ReturnType<typeof useExecution>;
}

export function useMonitorMode(options: UseMonitorModeOptions = {}) {
  const { pollCliSessions = true, execution: providedExecution } = options;

  // Track if we've already started execution to prevent double-starts
  const hasStartedRef = useRef(false);
  const lastSessionIdRef = useRef<string | null>(null);
  const clearTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Get execution hook - use provided one or create own instance
  const execution = providedExecution || useExecution({ showToasts: true });

  // Get diagram loading function
  const { loadDiagramFromData } = useDiagramLoader();

  // Get UI operations and state
  const { isMonitorMode: isMonitorModeFromStore } = useUIState();
  const { setActiveCanvas } = useUIOperations();

  // Lazy query to fetch execution state on demand
  const [fetchExecutionState] = useLazyQuery(GETEXECUTION_QUERY, {
    fetchPolicy: 'network-only',
  });

  // Check if we're in monitor mode (from store)
  const isMonitorMode = () => {
    return isMonitorModeFromStore;
  };

  // Track if we're in initial connection phase for faster polling
  const initialConnectionRef = useRef(true);

  // Poll for active CLI session when in monitor mode
  const { data: cliSessionData, loading: cliSessionLoading, error: cliSessionError } = useQuery(GETACTIVECLISESSION_QUERY, {
    skip: !isMonitorMode() || !pollCliSessions,
    pollInterval: initialConnectionRef.current ? 100 : 200, // Fast polling initially, then slower
    fetchPolicy: 'network-only',
  });

  const activeSession = cliSessionData?.active_cli_session;

  // CLI session monitoring handles all execution now
  // No need for URL-based execution logic

  // Handle CLI session monitoring
  useEffect(() => {
    if (!isMonitorMode() || !pollCliSessions || cliSessionLoading || cliSessionError) return;

    if (activeSession?.is_active) {
      // New CLI session detected
      if (activeSession.session_id !== lastSessionIdRef.current) {
        lastSessionIdRef.current = activeSession.session_id;

        // Cancel any pending clear operation
        if (clearTimeoutRef.current) {
          clearTimeout(clearTimeoutRef.current);
          clearTimeoutRef.current = null;
        }

        // console.log('[Monitor] CLI execution:', activeSession.execution_id);
        toast.info(`Connected to CLI execution: ${activeSession.diagram_name}`);

        // Parse diagram data once
        let diagramData: any = null;
        let nodeCount = 0;
        if (activeSession.diagram_data) {
          try {
            diagramData = JSON.parse(activeSession.diagram_data);
            nodeCount = diagramData.nodes?.length || 0;
          } catch (e) {
            console.error('[Monitor] Failed to parse diagram data:', e);
          }
        }

        // Apply node states immediately if available in CLI session
        if (activeSession.node_states && typeof activeSession.node_states === 'object') {
          const store = useUnifiedStore.getState();
          Object.entries(activeSession.node_states).forEach(([nodeIdStr, state]: [string, any]) => {
            if (state?.status) {
              // Map status to the appropriate action
              if (state.status === 'RUNNING') {
                store.updateNodeExecution(nodeId(nodeIdStr), {
                  status: Status.RUNNING,
                  timestamp: Date.now()
                });
              } else if (state.status === 'COMPLETED') {
                store.updateNodeExecution(nodeId(nodeIdStr), {
                  status: Status.COMPLETED,
                  timestamp: Date.now()
                });
              } else if (state.status === 'FAILED') {
                store.updateNodeExecution(nodeId(nodeIdStr), {
                  status: Status.FAILED,
                  timestamp: Date.now(),
                  error: state.error
                });
              }
            }
          });
          // console.log('[Monitor] Applied immediate node states from CLI session:', Object.keys(activeSession.node_states).length);
        }

        // Start three operations in parallel:
        // 1. Load diagram
        // 2. Connect to execution
        // 3. Fetch initial execution state (only if not already provided by CLI session)
        const parallelOps = Promise.all([
          // Load diagram if data is provided
          diagramData ? loadDiagramFromData(diagramData) : Promise.resolve(),

          // Connect to execution immediately (no delay)
          (async () => {
            // console.log('[Monitor] Connecting to execution:', activeSession.execution_id, 'nodeCount:', nodeCount);
            // Preserve node states if they were already applied from CLI session
            execution.connectToExecution(activeSession.execution_id, nodeCount, !!activeSession.node_states);
            hasStartedRef.current = true;
          })(),

          // Only fetch execution state if node states weren't provided by CLI session
          !activeSession.node_states ?
            fetchExecutionState({
              variables: { execution_id: activeSession.execution_id }
            }).catch(error => {
              console.error('[Monitor] Failed to fetch initial execution state:', error);
              return null;
            }) : Promise.resolve(null)
        ]);

        // Switch to execution canvas
        setActiveCanvas('execution');

        // Process results when all operations complete
        parallelOps.then(([, , executionStateResult]) => {
          if (executionStateResult?.data?.execution?.node_states) {
            // Pre-populate node states for immediate highlighting
            const nodeStates = executionStateResult.data.execution.node_states;
            if (nodeStates && typeof nodeStates === 'object') {
              // Access the store directly to update node states
              const store = useUnifiedStore.getState();

              // Process each node state and update the store
              Object.entries(nodeStates).forEach(([nodeIdStr, state]: [string, any]) => {
                if (state?.status) {
                  // Map status to the appropriate action
                  if (state.status === 'RUNNING') {
                    store.updateNodeExecution(nodeId(nodeIdStr), {
                      status: Status.RUNNING,
                      timestamp: Date.now()
                    });
                  } else if (state.status === 'COMPLETED') {
                    store.updateNodeExecution(nodeId(nodeIdStr), {
                      status: Status.COMPLETED,
                      timestamp: Date.now()
                    });
                  } else if (state.status === 'FAILED') {
                    store.updateNodeExecution(nodeId(nodeIdStr), {
                      status: Status.FAILED,
                      timestamp: Date.now(),
                      error: state.error
                    });
                  }
                }
              });
              // console.log('[Monitor] Pre-populated node states:', Object.keys(nodeStates).length);
            }
          }

          // Slow down polling after initial connection (extend to 2 seconds for better coverage)
          setTimeout(() => {
            initialConnectionRef.current = false;
          }, 2000); // Keep fast polling for 2 seconds instead of 1
        });
      }
    } else if (lastSessionIdRef.current) {
      // CLI session ended
      // console.log('[Monitor] CLI session ended');
      lastSessionIdRef.current = null;
      hasStartedRef.current = false;
      initialConnectionRef.current = true; // Reset for next connection

      // Clear diagram after a delay, but only if no new session starts
      clearTimeoutRef.current = setTimeout(() => {
        const store = useUnifiedStore.getState();
        // Double-check: only clear if still in monitor mode and no active session
        // Also check that we don't have a new session ID set
        if (store.isMonitorMode && !lastSessionIdRef.current) {
          store.clearDiagram();
          setActiveCanvas('main');
          toast.info('Ready for next CLI execution');
        }
        clearTimeoutRef.current = null;
      }, 3000); // 3 seconds delay to avoid race conditions
    }
  }, [cliSessionData, cliSessionLoading, cliSessionError, isMonitorMode, pollCliSessions, setActiveCanvas, loadDiagramFromData, execution, fetchExecutionState]);

  // Monitor execution completion to properly clear status
  useEffect(() => {
    if (!isMonitorMode() || !execution) return;

    // When execution completes but we're still in monitor mode
    if (!execution.isRunning && hasStartedRef.current) {
      // console.log('[Monitor] Execution completed, clearing status');
      // Mark that we're no longer tracking an execution
      hasStartedRef.current = false;

      // If there's no active session, clear the session ref
      if (!activeSession?.is_active) {
        lastSessionIdRef.current = null;
      }
    }
  }, [execution?.isRunning, isMonitorMode, activeSession]);

  // Cleanup timeout on unmount or when monitor mode changes
  useEffect(() => {
    return () => {
      if (clearTimeoutRef.current) {
        clearTimeout(clearTimeoutRef.current);
        clearTimeoutRef.current = null;
      }
    };
  }, []);

  return {
    isMonitorMode: isMonitorMode(),
    diagramName: activeSession?.diagram_name || null,
    isExecuting: execution.isRunning,
    hasStarted: hasStartedRef.current,
    execution,
    activeCliSession: activeSession,
    isLoadingCliSession: cliSessionLoading,
    cliSessionError
  };
}
