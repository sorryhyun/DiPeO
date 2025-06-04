import { useEffect } from 'react';

interface KeyboardShortcutsConfig {
  onDelete?: () => void;
  onEscape?: () => void;
  onSave?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
}

export const useKeyboardShortcuts = (config: KeyboardShortcutsConfig) => {
  const { onDelete, onEscape, onSave, onUndo, onRedo } = config;
  
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Delete key
      if (e.key === 'Delete' && onDelete) {
        e.preventDefault();
        onDelete();
      }
      
      // Escape key
      if (e.key === 'Escape' && onEscape) {
        e.preventDefault();
        onEscape();
      }
      
      // Ctrl+S or Cmd+S for save
      if ((e.ctrlKey || e.metaKey) && e.key === 's' && onSave) {
        e.preventDefault();
        onSave();
      }
      
      // Ctrl+Z or Cmd+Z for undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey && onUndo) {
        e.preventDefault();
        onUndo();
      }
      
      // Ctrl+Shift+Z or Cmd+Shift+Z for redo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey && onRedo) {
        e.preventDefault();
        onRedo();
      }
      
      // Ctrl+Y or Cmd+Y for redo (alternative)
      if ((e.ctrlKey || e.metaKey) && e.key === 'y' && onRedo) {
        e.preventDefault();
        onRedo();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onDelete, onEscape, onSave, onUndo, onRedo]);
};