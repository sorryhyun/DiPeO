import React, { useState, useEffect } from 'react';
import { Layers } from 'lucide-react';
import { Button, FileUploadButton } from '@/components/ui/buttons';
import { useUIState, useDiagram } from '@/hooks';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import { API_ENDPOINTS, getApiUrl } from '@/utils/api';
import { toast } from 'sonner';
import { isApiKey, parseApiArrayResponse } from '@/types';


const TopBar = () => {
  const [hasCheckedBackend, setHasCheckedBackend] = useState(false);
  const [isMonitorMode, setIsMonitorMode] = useState(false);
  const [isExitingMonitor, setIsExitingMonitor] = useState(false);
  
  // Use unified store
  const store = useUnifiedStore();
  const apiKeys = Array.from(store.apiKeys.values());
  const setReadOnly = store.setReadOnly;
  const { activeCanvas, toggleCanvas, setActiveCanvas } = useUIState();
  
  // Use the unified diagram hook
  const diagram = useDiagram({
    enableFileOperations: true,
    enableInteractions: false,
    enableMonitoring: true
  });
  
  // Extract what we need from diagram
  const {
    clear: clearDiagram,
    isMonitorMode: isReadOnly,
    saveJSON: onSaveToDirectory,
  } = diagram;
  
  // Create onChange handler for FileUploadButton
  const onImportJSON = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && diagram.importFile) {
      diagram.importFile(file);
    }
  };
  
  // Load API keys on mount
  useEffect(() => {
    // TODO: Implement API key loading from backend
    // For now, API keys are managed directly through the store
  }, []);
  
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const isMonitor = params.get('monitor') === 'true';
    setIsMonitorMode(isMonitor);
    
    // Only set read-only mode for monitor mode, don't auto-switch to execution
    if (isMonitor) {
      setReadOnly?.(true);
    }
    const checkBackendApiKeys = async () => {
      try {
        const res = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS));
        if (res.ok) {
          const data = await res.json();
          const backendKeys = parseApiArrayResponse(data.apiKeys || data, isApiKey);
          
          if (backendKeys.length > 0 && apiKeys.length === 0) {
            // TODO: Implement adding API keys to unified store
            // For now, API keys need to be added through the API keys modal
            console.log('Found backend API keys:', backendKeys);
          }
          
          // API keys modal is now in the sidebar
        }
      } catch (error) {
        console.error('[Check Backend API Keys]', error);
        toast.error(`Check Backend API Keys: ${(error as Error).message}`);
      } finally {
        setHasCheckedBackend(true);
      }
    };

    if (!hasCheckedBackend) {
      checkBackendApiKeys().catch(console.error);
    }
  }, [hasCheckedBackend, apiKeys.length, setReadOnly, setActiveCanvas]);

  // Keyboard shortcuts could be added here if needed

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
                toast.success('Created new diagram');
              }
            }}
            title="Create a new diagram"
          >
            📄 New
          </Button>
          <FileUploadButton
            accept=".json"
            onChange={onImportJSON}
            variant="outline"
            className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors"
            title="Open diagram from JSON file"
          >
            📂 Open
          </FileUploadButton>
          <Button 
            variant="outline" 
            className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors"
            onClick={() => onSaveToDirectory?.()?.catch(console.error)}
            title="Save diagram to server (diagrams folder)"
          >
            💾 Save
          </Button>
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
                toggleCanvas();
                // Exit read-only mode when leaving execution mode
                setReadOnly?.(false);
                // Also exit monitor mode when leaving execution mode
                setIsMonitorMode(false);
              } else {
                setActiveCanvas('execution');
                // Set the diagram to read-only when entering execution mode
                setReadOnly?.(true);
                // Also activate monitor mode when entering execution mode
                setIsMonitorMode(true);
              }
            }}
            title={activeCanvas === 'execution' ? 'Back to Diagram Canvas' : 'Enter Execution Mode'}
          >
            <Layers className={`h-4 w-4 mr-1 transition-transform duration-300 ${
              activeCanvas === 'execution' ? 'rotate-12' : ''
            }`} />
            {activeCanvas === 'execution' ? 'Exit Execution Mode' : 'Execution Mode'}
          </Button>
          
          {(isMonitorMode || isReadOnly) ? (
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