import { useEffect } from 'react';
import { useDiagramManager } from '@/domain/diagram/hooks';
import { useUIState } from '@/infrastructure/store/hooks';
import { toast } from 'sonner';

export function GlobalKeyboardHandler() {
  const { isMonitorMode } = useUIState();
  const { saveDiagram } = useDiagramManager({
    confirmOnNew: true,
    confirmOnLoad: false,
    autoSave: false,
    autoSaveInterval: 15000
  });

  useEffect(() => {
    const handleKeyDown = async (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        // Don't save in monitor mode
        if (isMonitorMode) {
          console.log('[GlobalKeyboardHandler] Skipping save in monitor mode');
          return;
        }
        try {
          await saveDiagram('quicksave.native.json');
        } catch (error) {
          console.error('Failed to upload diagram:', error);
          toast.error('Failed to upload diagram');
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [saveDiagram, isMonitorMode]);

  return null;
}
