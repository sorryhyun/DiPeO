import React, { useState, useEffect } from 'react';
import { Layers } from 'lucide-react';
import { Button, FileUploadButton } from '@/components/ui/buttons';
import { useUIState } from '@/hooks/useStoreSelectors';
import { useDiagramManager } from '@/hooks/useDiagramManager';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import { API_ENDPOINTS, getApiUrl } from '@/utils/api';
import { toast } from 'sonner';
import { isApiKey, parseApiArrayResponse, apiKeyId } from '@/types';


const TopBar = () => {
  const [hasCheckedBackend, setHasCheckedBackend] = useState(false);
  const [isMonitorMode, setIsMonitorMode] = useState(false);
  const [isExitingMonitor, setIsExitingMonitor] = useState(false);
  
  // Use unified store with specific selectors to avoid unnecessary re-renders
  const setReadOnly = useUnifiedStore(state => state.setReadOnly);
  const { activeCanvas, setActiveCanvas } = useUIState();
  
  // Use only the diagram manager for file operations - much lighter weight
  const diagramManager = useDiagramManager({
    confirmOnNew: true,
    confirmOnLoad: false
  });
  
  // Extract what we need
  const {
    newDiagram: clearDiagram,
    saveDiagram: onSaveToDirectory,
    loadDiagramFromFile: importFile
  } = diagramManager;
  
  // Create onChange handler for FileUploadButton
  const onImportJSON = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && importFile) {
      void importFile(file);
    }
  };
  
  // Load API keys on mount - backend is the single source of truth
  useEffect(() => {
    const loadApiKeys = async () => {
      try {
        const response = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS));
        if (response.ok) {
          const data = await response.json();
          console.log('[TopBar] Raw API keys data:', data);
          
          // The backend returns an array directly, not wrapped in an object
          const rawKeys = Array.isArray(data) ? data : (data.apiKeys || []);
          console.log('[TopBar] Raw keys array:', rawKeys);
          
          const backendKeys = parseApiArrayResponse(rawKeys, isApiKey);
          console.log('[TopBar] Parsed API keys:', backendKeys);
          
          // Clear existing keys and load fresh from backend
          // This ensures backend file is the single source of truth
          const newApiKeys = new Map();
          
          backendKeys.forEach(key => {
            // Brand the ID properly
            const brandedId = apiKeyId(key.id);
            const brandedKey = { ...key, id: brandedId };
            newApiKeys.set(brandedId, brandedKey);
          });
          
          // Replace entire apiKeys state with backend data
          useUnifiedStore.setState({ apiKeys: newApiKeys });
          
          console.log(`[TopBar] Loaded ${backendKeys.length} API keys from backend`);
          if (backendKeys.length > 0) {
            toast.success(`Loaded ${backendKeys.length} API keys`);
          }
        }
      } catch (error) {
        console.error('[TopBar] Load API Keys error:', error);
        toast.error(`Failed to load API keys: ${(error as Error).message}`);
      }
    };

    loadApiKeys().catch(console.error);
  }, []);
  
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

  // Check backend API keys after initial render to avoid blocking
  useEffect(() => {
    if (hasCheckedBackend) return;

    let cancelled = false;
    
    // Defer the API check to avoid blocking the initial render
    const timeoutId = setTimeout(() => {
      const checkBackendApiKeys = async () => {
        try {
          const res = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS));
          if (!cancelled && res.ok) {
            const data = await res.json();
            const backendKeys = parseApiArrayResponse(data.apiKeys || data, isApiKey);
            
            // Get current apiKeys length from store
            const currentApiKeysLength = useUnifiedStore.getState().apiKeys.size;
            
            if (backendKeys.length > 0 && currentApiKeysLength === 0) {
              // API keys are already loaded in the mount effect above
              // This check is kept for compatibility but keys are not re-added
            }
          }
        } catch (error) {
          if (!cancelled) {
            console.error('[Check Backend API Keys]', error);
            toast.error(`Check Backend API Keys: ${(error as Error).message}`);
          }
        } finally {
          if (!cancelled) {
            setHasCheckedBackend(true);
          }
        }
      };

      checkBackendApiKeys().catch(error => {
        if (!cancelled) {
          console.error('[Check Backend API Keys - Unhandled]', error);
        }
      });
    }, 100); // Small delay to let the UI render first

    // Cleanup function
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [hasCheckedBackend]); // Add hasCheckedBackend to dependencies

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
                setActiveCanvas('main');
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