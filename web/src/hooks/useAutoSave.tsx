/**
 * React hook for auto-save functionality
 * Integrates AutoSaveManager with React components
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useUnifiedStore } from '@/stores/unifiedStore';
import { AutoSaveManager, type AutoSaveOptions } from '@/stores/managers';
import { toast } from 'sonner';

interface UseAutoSaveOptions extends Omit<AutoSaveOptions, 'onSave' | 'onError'> {
  diagramId: string | null;
  showNotifications?: boolean;
}

interface AutoSaveState {
  enabled: boolean;
  lastSaveTime: number;
  hasUnsavedChanges: boolean;
  saveInProgress: boolean;
}

export function useAutoSave(options: UseAutoSaveOptions) {
  const store = useUnifiedStore();
  const managerRef = useRef<AutoSaveManager | null>(null);
  const [state, setState] = useState<AutoSaveState>({
    enabled: options.enabled ?? true,
    lastSaveTime: 0,
    hasUnsavedChanges: false,
    saveInProgress: false
  });

  // Initialize manager
  useEffect(() => {
    const manager = new AutoSaveManager(store, {
      ...options,
      onSave: (success) => {
        setState(prev => ({
          ...prev,
          lastSaveTime: Date.now(),
          hasUnsavedChanges: false,
          saveInProgress: false
        }));

        if (options.showNotifications && success) {
          toast.success('Auto-saved', {
            duration: 1000,
            position: 'bottom-right'
          });
        }
      },
      onError: (error) => {
        setState(prev => ({
          ...prev,
          saveInProgress: false
        }));

        if (options.showNotifications) {
          toast.error('Auto-save failed');
        }
      }
    });

    managerRef.current = manager;

    // Start monitoring if diagram ID is provided
    if (options.diagramId) {
      manager.start(options.diagramId);
    }

    // Update state periodically
    const interval = setInterval(() => {
      const status = manager.getStatus();
      setState(status);
    }, 1000);

    return () => {
      clearInterval(interval);
      manager.stop();
    };
  }, [options.diagramId]); // Re-create manager if diagram changes

  // Update enabled state
  useEffect(() => {
    if (managerRef.current) {
      managerRef.current.setEnabled(options.enabled ?? true);
    }
  }, [options.enabled]);

  // Manual save function
  const saveNow = useCallback(async () => {
    if (!managerRef.current) return false;

    setState(prev => ({ ...prev, saveInProgress: true }));
    const success = await managerRef.current.saveNow();
    
    if (success && options.showNotifications) {
      toast.success('Saved successfully');
    }
    
    return success;
  }, [options.showNotifications]);

  // Toggle auto-save
  const toggleAutoSave = useCallback(() => {
    const newEnabled = !state.enabled;
    setState(prev => ({ ...prev, enabled: newEnabled }));
    
    if (managerRef.current) {
      managerRef.current.setEnabled(newEnabled);
    }

    if (options.showNotifications) {
      toast.success(newEnabled ? 'Auto-save enabled' : 'Auto-save disabled');
    }
  }, [state.enabled, options.showNotifications]);

  return {
    ...state,
    saveNow,
    toggleAutoSave,
    timeSinceLastSave: state.lastSaveTime ? Date.now() - state.lastSaveTime : null
  };
}

/**
 * Auto-save status indicator component
 */
export function AutoSaveIndicator({ className = '' }: { className?: string }) {
  const { hasUnsavedChanges, saveInProgress, enabled, timeSinceLastSave } = useAutoSave({
    diagramId: useUnifiedStore(state => state.currentDiagramId),
    showNotifications: false
  });

  if (!enabled) {
    return <span className={`text-gray-500 ${className}`}>Auto-save disabled</span>;
  }

  if (saveInProgress) {
    return <span className={`text-blue-500 ${className}`}>Saving...</span>;
  }

  if (hasUnsavedChanges) {
    return <span className={`text-yellow-500 ${className}`}>Unsaved changes</span>;
  }

  if (timeSinceLastSave && timeSinceLastSave < 5000) {
    return <span className={`text-green-500 ${className}`}>Saved</span>;
  }

  return null;
}