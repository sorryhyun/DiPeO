import React, { useState, useEffect } from 'react';
import { Layers } from 'lucide-react';
import { Button } from '@/shared/components/ui/buttons';
import { useUIState } from '@/shared/hooks/selectors';
import { useDiagramManager } from '@/features/diagram-editor/hooks';
import { useUnifiedStore } from '@/shared/hooks';
import { toast } from 'sonner';


const TopBar = () => {
  const [isMonitorMode, setIsMonitorMode] = useState(false);
  const [isExitingMonitor, setIsExitingMonitor] = useState(false);
  
  // Use UI state for mode control
  const { activeCanvas } = useUIState();
  const { setReadOnly, setActiveCanvas } = useUnifiedStore();

  // NOTE: This is the ONLY place where auto-save should be enabled to avoid duplicate saves
  const diagramManager = useDiagramManager({
    confirmOnNew: true,
    confirmOnLoad: false,
    autoSave: true,
    autoSaveInterval: 15000 // Auto-save every 15 seconds
  });
  
  // Extract what we need
  const {
    newDiagram: clearDiagram,
    saveDiagram: onUploadToDirectory,
    isDirty
  } = diagramManager;
  

  // Handle monitor mode separately
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const isMonitor = params.get('monitor') === 'true';
    setIsMonitorMode(isMonitor);
    
    // Only set read-only mode for monitor mode, don't auto-switch to execution
    if (isMonitor) {
      setReadOnly?.(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount


  return (
    <header className="p-3 border-b bg-gradient-to-r from-gray-50 to-gray-100 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors"
            onClick={() => {
              if (window.confirm('Create a new diagram? This will clear the current diagram.')) {
                clearDiagram();
                // Status shown in indicator
              }
            }}
            title="Create a new diagram"
          >
            📄 New
          </Button>
          <Button
            variant="outline"
            className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors"
            onClick={() => {
              // Load quicksave.json by updating the URL parameter and refreshing
              const url = new URL(window.location.href);
              url.searchParams.set('diagram', 'native/quicksave');
              
              // Loading quicksave
              
              // Refresh the page with the new URL
              window.location.href = url.toString();
            }}
            title="Get quicksave.json from server"
          >
            📂 Load Quicksave
          </Button>
          <Button 
            variant="outline" 
            className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors"
            onClick={() => onUploadToDirectory?.('quicksave.json')?.catch(console.error)}
            title="Upload diagram as quicksave.json"
          >
            💾 Quicksave
          </Button>
          {/* Auto-save status indicator */}
          <div className="flex items-center space-x-1 px-2 py-1 text-xs text-gray-600">
            {isDirty ? (
              <>
                <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                <span>Unsaved changes</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 bg-green-500 rounded-full" />
                <span>Saved</span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* Execution controls moved to ExecutionControls component */}
        </div>
        
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            className={`bg-white transition-all duration-300 ${
              activeCanvas === 'execution'
                ? 'bg-green-100 border-green-400 hover:bg-green-200' 
                : 'hover:bg-gray-50 hover:border-gray-300'
            }`}
            onClick={() => {
              if (activeCanvas === 'execution') {
                setActiveCanvas('main');
                // Clear execution state when leaving execution mode
                const { stopExecution } = useUnifiedStore.getState();
                stopExecution();
                // When leaving execution mode, readOnly remains controlled by monitor mode
              } else {
                setActiveCanvas('execution');
                // Execution mode has its own read-only state (executionReadOnly)
                // Monitor mode (readOnly) remains independent
              }
            }}
            title={activeCanvas === 'execution' ? 'Back to Diagram Canvas' : 'Enter Execution Mode'}
          >
            <Layers className={`h-4 w-4 mr-1 transition-transform duration-300 ${
              activeCanvas === 'execution' ? 'rotate-12' : ''
            }`} />
            {activeCanvas === 'execution' ? 'Exit Execution Mode' : 'Execution Mode'}
          </Button>
          
          {isMonitorMode ? (
            <div className="flex items-center space-x-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-md">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
              </span>
              <span className="text-sm font-medium">Monitor Mode Active</span>
              <button
                onClick={() => {
                  setIsExitingMonitor(true);
                  // Don't clear diagram when exiting monitor mode
                  setReadOnly?.(false);
                  setIsMonitorMode(false);
                  // Remove monitor param from URL
                  const url = new URL(window.location.href);
                  url.searchParams.delete('monitor');
                  window.history.replaceState({}, '', url.toString());
                  toast.success('Exited monitor mode');
                  setTimeout(() => setIsExitingMonitor(false), 300);
                }}
                disabled={isExitingMonitor}
                className={`ml-2 text-xs px-2 py-1 rounded transition-all ${
                  isExitingMonitor 
                    ? 'bg-red-600 text-white cursor-not-allowed opacity-75' 
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {isExitingMonitor ? 'Exiting...' : 'Exit'}
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2 px-3 py-1 bg-gray-100 text-gray-600 rounded-md">
              <span className="relative flex h-3 w-3">
                <span className="relative inline-flex rounded-full h-3 w-3 bg-gray-400"></span>
              </span>
              <span className="text-sm font-medium">Monitor Mode Off</span>
            </div>
          )}
        </div>
      </div>

    </header>
  );
};

export default TopBar;