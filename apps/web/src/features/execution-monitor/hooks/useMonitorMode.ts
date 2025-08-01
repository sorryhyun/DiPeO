/**
 * useMonitorMode - Hook to handle monitor mode auto-execution
 * 
 * This hook detects when the app is in monitor mode and automatically
 * monitors CLI-launched executions.
 */

import { useEffect, useRef } from 'react';
import { useQuery, gql } from '@apollo/client';
import { toast } from 'sonner';
import { useExecution } from './useExecution';
import { useDiagramLoader } from '@/features/diagram-editor/hooks/useDiagramLoader';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { useUIState, useUIOperations } from '@/core/store/hooks';

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
}

export function useMonitorMode(options: UseMonitorModeOptions = {}) {
  const { pollCliSessions = true } = options;
  
  // Track if we've already started execution to prevent double-starts
  const hasStartedRef = useRef(false);
  const lastSessionIdRef = useRef<string | null>(null);
  
  // Get execution hook
  const execution = useExecution({ showToasts: true });
  
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
    pollInterval: 2000, // Poll every 2 seconds
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
        
        console.log('[Monitor] Detected active CLI session:', activeSession.execution_id);
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
        
        // Switch to execution canvas and start monitoring
        setActiveCanvas('execution');
        
        // Connect to the CLI execution directly (no URL params needed)
        const nodeCount = activeSession.diagram_data ? 
          JSON.parse(activeSession.diagram_data).nodes?.length || 0 : 
          0;
        
        execution.connectToExecution(activeSession.execution_id, nodeCount);
        hasStartedRef.current = true;
      }
    } else if (lastSessionIdRef.current) {
      // CLI session ended
      console.log('[Monitor] CLI session ended');
      lastSessionIdRef.current = null;
      
      // Clear diagram after a short delay
      setTimeout(() => {
        const store = useUnifiedStore.getState();
        if (store.isMonitorMode) {
          store.clearDiagram();
          setActiveCanvas('main');
          toast.info('CLI execution completed - diagram cleared');
        }
      }, 1000);
    }
  }, [cliSessionData, cliSessionLoading, cliSessionError, isMonitorMode, pollCliSessions, setActiveCanvas, loadDiagramFromData, execution]);
  
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