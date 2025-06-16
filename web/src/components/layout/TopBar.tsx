import React, { useState, useEffect } from 'react';
import { Layers, TestTube } from 'lucide-react';
import { Button, FileUploadButton } from '@/components/ui/buttons';
import { useUIState } from '@/hooks/useStoreSelectors';
import { useDiagramManager } from '@/hooks/useDiagramManager';
import { useCanvasOperations } from '@/hooks/useCanvasOperations';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import { useGetApiKeysQuery, useListDiagramsQuery } from '@/__generated__/graphql';
import { toast } from 'sonner';
import { apiKeyId, type DomainDiagram, type DomainNode, type DomainArrow, type DomainPerson, type DomainApiKey, type DomainHandle, type NodeID, type ArrowID, type PersonID, type ApiKeyID, type HandleID } from '@/types';
import { downloadFile } from '@/utils/file';


const TopBar = () => {
  const [isMonitorMode, setIsMonitorMode] = useState(false);
  const [isExitingMonitor, setIsExitingMonitor] = useState(false);
  const [hasLoadedDiagram, setHasLoadedDiagram] = useState(false);
  
  // Use UI state for mode control
  const { activeCanvas, setActiveCanvas } = useUIState();
  const { setReadOnly } = useUnifiedStore();
  
  // Use only the diagram manager for file operations - much lighter weight
  const diagramManager = useDiagramManager({
    confirmOnNew: true,
    confirmOnLoad: false,
    autoSave: true,
    autoSaveInterval: 15000 // Auto-save every 15 seconds
  });
  
  // Extract what we need
  const {
    newDiagram: clearDiagram,
    saveDiagram: onSaveToDirectory,
    loadDiagramFromFile: importFile,
    isDirty
  } = diagramManager;
  
  // Create onChange handler for FileUploadButton
  const onImportYAML = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && importFile) {
      void importFile(file);
    }
  };
  
  // Load API keys on mount - backend is the single source of truth
  const { data: apiKeysData, error: apiKeysError } = useGetApiKeysQuery({
    fetchPolicy: 'cache-first'
  });
  
  // Temporarily commented out to debug infinite loop
  // useEffect(() => {
  //   if (apiKeysData?.apiKeys) {
  //     const backendKeys = apiKeysData.apiKeys;
  //     console.log('[TopBar] Loaded API keys from GraphQL:', backendKeys);
      
  //     // Clear existing keys and load fresh from backend
  //     // This ensures backend file is the single source of truth
  //     const newApiKeys = new Map();
      
  //     backendKeys.forEach(key => {
  //       // Brand the ID properly
  //       const brandedId = apiKeyId(key.id);
  //       const brandedKey = { ...key, id: brandedId };
  //       newApiKeys.set(brandedId, brandedKey);
  //     });
      
  //     // Replace entire apiKeys state with backend data
  //     useUnifiedStore.setState({ apiKeys: newApiKeys });
      
  //     console.log(`[TopBar] Loaded ${backendKeys.length} API keys from backend`);
  //     if (backendKeys.length > 0) {
  //       toast.success(`Loaded ${backendKeys.length} API keys`);
  //     }
  //   }
  // }, []); // Only run once on mount
  
  useEffect(() => {
    if (apiKeysError) {
      console.error('[TopBar] Load API Keys error:', apiKeysError);
      toast.error(`Failed to load API keys: ${apiKeysError.message}`);
    }
  }, [apiKeysError]);
  
  // Load the most recent diagram on startup
  const { data: diagramsData } = useListDiagramsQuery({
    variables: {
      limit: 1, // Get only the most recent
      offset: 0
    },
    skip: hasLoadedDiagram, // Only run once
    fetchPolicy: 'cache-first'
  });
  
  // Load the most recent diagram when we get the list
  useEffect(() => {
    if (!hasLoadedDiagram && diagramsData?.diagrams && diagramsData.diagrams.length > 0) {
      const mostRecentDiagram = diagramsData.diagrams[0];
      if (mostRecentDiagram?.metadata?.id) {
        // Mark as loaded before attempting to load
        setHasLoadedDiagram(true);
        
        // Check if we're not already loading a diagram via URL parameter
        const params = new URLSearchParams(window.location.search);
        if (!params.get('diagram')) {
          // Redirect to load the most recent diagram
          window.location.href = `/?diagram=${mostRecentDiagram.metadata.id}`;
          toast.info(`Loading most recent diagram: ${mostRecentDiagram.metadata?.name || 'Untitled'}`);
        }
      }
    }
  }, [diagramsData, hasLoadedDiagram]);
  
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
            accept=".yaml,.yml,.native.yaml,.readable.yaml,.llm-readable.yaml"
            onChange={onImportYAML}
            variant="outline"
            className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors"
            title="Open diagram from YAML file"
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