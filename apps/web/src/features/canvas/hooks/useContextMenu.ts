import { useState, useCallback } from 'react';

export interface ContextMenuState {
  position: { x: number; y: number } | null;
  target: 'pane' | 'node' | 'edge';
}

export const useContextMenu = () => {
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    position: null,
    target: 'pane',
  });

  const openContextMenu = useCallback((x: number, y: number, target: 'pane' | 'node' | 'edge') => {
    setContextMenu({ position: { x, y }, target });
  }, []);

  const closeContextMenu = useCallback(() => {
    setContextMenu({ position: null, target: 'pane' });
  }, []);

  return {
    contextMenu,
    openContextMenu,
    closeContextMenu,
    isOpen: contextMenu.position !== null,
  };
};