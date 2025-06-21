import { useEffect } from 'react';
import { useDiagramManager } from '@/features/diagram-editor/hooks';
import { toast } from 'sonner';

export function GlobalKeyboardHandler() {
  const { saveDiagram } = useDiagramManager({
    confirmOnNew: true,
    confirmOnLoad: false,
    autoSave: false, // Disable auto-save here since TopBar already handles it
    autoSaveInterval: 15000
  });

  useEffect(() => {
    const handleKeyDown = async (e: KeyboardEvent) => {
      // Skip if typing in input fields
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      // Ctrl/Cmd + S for upload
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        try {
          await saveDiagram();
          // Success toast is already shown by saveDiagram
        } catch (error) {
          console.error('Failed to upload diagram:', error);
          toast.error('Failed to upload diagram');
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [saveDiagram]);

  return null; // This component doesn't render anything
}