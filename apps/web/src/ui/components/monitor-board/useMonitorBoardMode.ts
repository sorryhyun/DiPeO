import { useEffect, useMemo, useState } from 'react';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';

/**
 * Hook to handle monitor mode based on URL parameters
 * 
 * Behavior:
 * - ?monitor=true - Opens simple single execution monitor mode
 * - ?monitor=board - Opens monitor board (with run picker and multi-execution view)
 * - No monitor param - Normal diagram editing mode
 */
export function useMonitorBoardMode() {
  const setActiveCanvas = useUnifiedStore((state) => state.setActiveCanvas);
  const setMonitorMode = useUnifiedStore((state) => state.setMonitorMode);
  const activeCanvas = useUnifiedStore((state) => state.activeCanvas);

  // Track URL changes to trigger re-parsing
  const [urlKey, setUrlKey] = useState(0);

  // Listen for URL changes (back/forward buttons, programmatic changes)
  useEffect(() => {
    const handlePopState = () => {
      setUrlKey(prev => prev + 1);
    };
    
    const handleUrlChange = () => {
      setUrlKey(prev => prev + 1);
    };

    window.addEventListener('popstate', handlePopState);
    
    // Also listen for programmatic URL changes
    const originalPushState = window.history.pushState;
    const originalReplaceState = window.history.replaceState;
    
    window.history.pushState = function(...args) {
      originalPushState.apply(window.history, args);
      handleUrlChange();
    };
    
    window.history.replaceState = function(...args) {
      originalReplaceState.apply(window.history, args);
      handleUrlChange();
    };

    return () => {
      window.removeEventListener('popstate', handlePopState);
      window.history.pushState = originalPushState;
      window.history.replaceState = originalReplaceState;
    };
  }, []);

  // Parse URL to determine mode (re-runs when URL changes)
  const { isMonitorMode, isBoardMode, executionIds } = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    const monitorParam = params.get('monitor');
    const idsParam = params.get('ids');
    
    if (!monitorParam) {
      return { isMonitorMode: false, isBoardMode: false, executionIds: [] };
    }
    
    const ids = idsParam ? idsParam.split(',').filter(Boolean) : [];
    
    if (monitorParam === 'board') {
      return { isMonitorMode: true, isBoardMode: true, executionIds: ids };
    } else if (monitorParam === 'true') {
      return { isMonitorMode: true, isBoardMode: false, executionIds: [] };
    }
    
    return { isMonitorMode: false, isBoardMode: false, executionIds: [] };
  }, [urlKey]);

  // Show board only when explicitly requested with monitor=board
  const shouldShowBoard = isBoardMode;
  const shouldShowSingleExecution = isMonitorMode && !isBoardMode; // Use single execution for monitor=true

  useEffect(() => {
    if (shouldShowBoard) {
      // Monitor board mode
      setActiveCanvas('monitor');
      setMonitorMode(true);
    } else if (shouldShowSingleExecution) {
      // Simple single execution monitor mode
      setActiveCanvas('execution');
      setMonitorMode(true);
    } else {
      // Default mode - diagram editing
      if (activeCanvas === 'monitor' || activeCanvas === 'execution') {
        setActiveCanvas('main');
        setMonitorMode(false);
      }
    }
  }, [shouldShowBoard, shouldShowSingleExecution, setActiveCanvas, setMonitorMode, activeCanvas]);

  return {
    isMonitorBoard: shouldShowBoard,
    isSingleMonitor: shouldShowSingleExecution,
    executionIds,
  };
}