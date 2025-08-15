import { useEffect, useMemo } from 'react';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';

/**
 * Hook to handle monitor mode based on URL parameters
 * 
 * Behavior:
 * - ?monitor=true&ids=exec1,exec2 - Opens multi-run board with specified executions
 * - ?monitor=true&ids=exec1 - Opens single execution monitor
 * - ?monitor=true - Opens single execution monitor (backward compatibility)
 * - No monitor param - Normal diagram editing mode
 */
export function useMonitorBoardMode() {
  const setActiveCanvas = useUnifiedStore((state) => state.setActiveCanvas);
  const setMonitorMode = useUnifiedStore((state) => state.setMonitorMode);
  const activeCanvas = useUnifiedStore((state) => state.activeCanvas);

  // Parse URL to determine mode
  const { isMonitorMode, executionIds } = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    const monitorParam = params.get('monitor');
    const idsParam = params.get('ids');
    
    if (monitorParam !== 'true') {
      return { isMonitorMode: false, executionIds: [] };
    }
    
    const ids = idsParam ? idsParam.split(',').filter(Boolean) : [];
    return { isMonitorMode: true, executionIds: ids };
  }, []);

  // Determine whether to show board or single execution view
  const shouldShowBoard = isMonitorMode && executionIds.length > 1;
  const shouldShowSingleExecution = isMonitorMode && executionIds.length <= 1;

  useEffect(() => {
    if (shouldShowBoard) {
      // Multi-run monitor board mode
      setActiveCanvas('monitor');
      setMonitorMode(true);
    } else if (shouldShowSingleExecution) {
      // Single execution monitor mode
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