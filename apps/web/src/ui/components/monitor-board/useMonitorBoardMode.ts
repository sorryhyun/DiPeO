import { useEffect, useMemo } from 'react';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';

/**
 * Hook to handle monitor mode based on URL parameters
 * 
 * Behavior:
 * - ?monitor=true - Opens monitor board (with run picker and multi-execution view)
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

  // Always show board when monitor=true
  const shouldShowBoard = isMonitorMode;
  const shouldShowSingleExecution = false; // Never use single execution mode

  useEffect(() => {
    if (shouldShowBoard) {
      // Monitor board mode
      setActiveCanvas('monitor');
      setMonitorMode(true);
    } else {
      // Default mode - diagram editing
      if (activeCanvas === 'monitor' || activeCanvas === 'execution') {
        setActiveCanvas('main');
        setMonitorMode(false);
      }
    }
  }, [shouldShowBoard, setActiveCanvas, setMonitorMode, activeCanvas]);

  return {
    isMonitorBoard: shouldShowBoard,
    isSingleMonitor: shouldShowSingleExecution,
    executionIds,
  };
}