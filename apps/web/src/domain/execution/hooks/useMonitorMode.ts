/**
 * useMonitorMode - Hook to handle monitor mode auto-execution
 * 
 * This hook detects when the app is in monitor mode and automatically
 * monitors CLI-launched executions.
 */

import { useEffect, useRef, useContext } from 'react';
import { useQuery, gql } from '@apollo/client';
import { toast } from 'sonner';
import { useExecution } from './useExecution';
import { useDiagramLoader } from '@/domain/diagram/hooks/useDiagramLoader';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import { useUIState, useUIOperations } from '@/infrastructure/store/hooks';

const ACTIVE_CLI_SESSION_QUERY = gql`
  query ActiveCliSession {
    active_cli_session {
      session_id
      execution_id
      diagram_name
      diagram_format
      started_at
      is_active
      diagram_data
    }
  }
`;

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
  
  // Check if we're in monitor mode (from store)
  const isMonitorMode = () => {
    return isMonitorModeFromStore;
  };
  
  // Poll for active CLI session when in monitor mode
  const { data: cliSessionData, loading: cliSessionLoading, error: cliSessionError } = useQuery(ACTIVE_CLI_SESSION_QUERY, {
    skip: !isMonitorMode() || !pollCliSessions,
    pollInterval: 500, // Poll every 500ms for faster response
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
        
        // Load diagram if data is provided
        if (activeSession.diagram_data) {
          try {
            const diagramData = JSON.parse(activeSession.diagram_data);
            loadDiagramFromData(diagramData);
          } catch (e) {
            console.error('[Monitor] Failed to parse diagram data:', e);
          }
        }
        
        // Switch to execution canvas
        setActiveCanvas('execution');
        
        // Add a small delay to ensure React Flow has time to initialize nodes/handles
        // This prevents the "Couldn't create edge" error
        setTimeout(() => {
          // Connect to the CLI execution directly (no URL params needed)
          const nodeCount = activeSession.diagram_data ? 
            JSON.parse(activeSession.diagram_data).nodes?.length || 0 : 
            0;
          
          // console.log('[Monitor] Connecting to execution:', activeSession.execution_id, 'nodeCount:', nodeCount);
          execution.connectToExecution(activeSession.execution_id, nodeCount);
          hasStartedRef.current = true;
        }, 100); // 100ms delay for React Flow to initialize
      }
    } else if (lastSessionIdRef.current) {
      // CLI session ended
      // console.log('[Monitor] CLI session ended');
      lastSessionIdRef.current = null;
      hasStartedRef.current = false;
      
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
  }, [cliSessionData, cliSessionLoading, cliSessionError, isMonitorMode, pollCliSessions, setActiveCanvas, loadDiagramFromData, execution]);
  
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