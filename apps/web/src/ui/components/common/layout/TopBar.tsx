import React, { useState, useEffect } from 'react';
import { Layers } from 'lucide-react';
import { Button } from '@/ui/components/common/forms/buttons';
import { Select } from '@/ui/components/common/forms/Select';
import { useUIState } from '@/infrastructure/store/hooks/state';
import { useDiagramManager, useFileOperations, useDiagramSave } from '@/domain/diagram/hooks';
import { useUIOperations, useExecutionOperations } from '@/infrastructure/store/hooks';
import { toast } from 'sonner';
import { useUnifiedStore, useDiagramFormat } from '@/infrastructure/store/unifiedStore';
import { useShallow } from 'zustand/react/shallow';
import { DiagramFormat } from '@dipeo/models';
import { useGetDiagramLazyQuery } from '@/__generated__/graphql';
import { useDiagramLoader } from '@/domain/diagram/hooks/useDiagramLoader';


const TopBar = () => {
  const [selectedFormat, setSelectedFormat] = useState<DiagramFormat>(DiagramFormat.NATIVE);
  const [displayName, setDisplayName] = useState<string>('');
  
  // Use UI state for mode control
  const { activeCanvas, isMonitorMode } = useUIState();
  const { setActiveCanvas, setMonitorMode } = useUIOperations();
  const { stopExecution } = useExecutionOperations();
  
  // Get diagram format from store
  const diagramFormatFromStore = useDiagramFormat();
  
  // Get diagram metadata from store
  const { diagramName, diagramDescription, diagramId, setDiagramName, setDiagramDescription } = useUnifiedStore(
    useShallow(state => ({
      diagramName: state.diagramName,
      diagramDescription: state.diagramDescription,
      diagramId: state.diagramId,
      setDiagramName: state.setDiagramName,
      setDiagramDescription: state.setDiagramDescription,
    }))
  );

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
    isDirty
  } = diagramManager;
  
  // File operations
  const { saveDiagram: saveToFileSystem } = useFileOperations();
  
  // Use the new diagram save hook
  const { isSaving, handleSave } = useDiagramSave({ saveToFileSystem });
  
  // Add GraphQL query and diagram loader
  const [getDiagram] = useGetDiagramLazyQuery();
  const { loadDiagramFromData } = useDiagramLoader();
  

  // Handle monitor mode from URL
  useEffect(() => {
    const checkMonitorParam = () => {
      const params = new URLSearchParams(window.location.search);
      const monitorParam = params.get('monitor') === 'true';
      
      if (monitorParam !== isMonitorMode) {
        setMonitorMode(monitorParam);
        if (monitorParam) {
          // When entering monitor mode from URL, automatically switch to execution canvas
          setActiveCanvas('execution');
        }
      }
    };
    
    // Check on mount
    checkMonitorParam();
    
    // Listen for URL changes
    const handleUrlChange = () => checkMonitorParam();
    window.addEventListener('popstate', handleUrlChange);
    
    return () => {
      window.removeEventListener('popstate', handleUrlChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount
  
  // When monitor mode changes, adjust canvas if needed
  useEffect(() => {
    if (isMonitorMode && activeCanvas === 'main') {
      // When monitor mode is turned on, automatically switch to execution canvas
      setActiveCanvas('execution');
    }
  }, [isMonitorMode, activeCanvas, setActiveCanvas]);
  
  // Helper function to extract format from filename
  const extractFormatFromName = (name: string): { cleanName: string, format: DiagramFormat } => {
    if (name.endsWith('.light.yaml') || name.endsWith('.light.yml')) {
      return { 
        cleanName: name.replace(/\.(light\.(yaml|yml))$/, ''), 
        format: DiagramFormat.LIGHT 
      };
    } else if (name.endsWith('.readable.yaml') || name.endsWith('.readable.yml')) {
      return { 
        cleanName: name.replace(/\.(readable\.(yaml|yml))$/, ''), 
        format: DiagramFormat.READABLE 
      };
    } else if (name.endsWith('.native.json')) {
      return { 
        cleanName: name.replace(/\.native\.json$/, ''), 
        format: DiagramFormat.NATIVE 
      };
    }
    // Default case - no format suffix
    return { cleanName: name, format: DiagramFormat.NATIVE };
  };

  // Helper function to add format suffix to name
  const addFormatSuffix = (name: string, format: DiagramFormat): string => {
    if (format === DiagramFormat.LIGHT) {
      return `${name}.light.yaml`;
    } else if (format === DiagramFormat.READABLE) {
      return `${name}.readable.yaml`;
    } else if (format === DiagramFormat.NATIVE) {
      return `${name}.native.json`;
    }
    return name;
  };

  // Sync format from store - including when it's null (no diagram loaded)
  useEffect(() => {
    if (diagramFormatFromStore !== null) {
      setSelectedFormat(diagramFormatFromStore);
    } else {
      // When no diagram is loaded, default to NATIVE
      setSelectedFormat(DiagramFormat.NATIVE);
    }
  }, [diagramFormatFromStore]);

  // Sync display name and format from diagramName
  useEffect(() => {
    const { cleanName, format } = extractFormatFromName(diagramName);
    setDisplayName(cleanName);
    // Only update format if it's different to avoid loops
    if (format !== selectedFormat) {
      setSelectedFormat(format);
    }
  }, [diagramName]); // eslint-disable-line react-hooks/exhaustive-deps

  // Update diagramName when display name or format changes
  const updateDiagramName = (newDisplayName: string, newFormat: DiagramFormat) => {
    const fullName = addFormatSuffix(newDisplayName, newFormat);
    setDiagramName(fullName);
  };

  // Convert and save functionality
  const handleConvertAndSave = async () => {
    await handleSave({
      selectedFormat,
      diagramName,
      diagramId
    });
  };


  return (
    <header className="p-3 border-b bg-gradient-to-r from-gray-50 to-gray-100 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          {/* Title Row with Format Dropdown */}
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={displayName}
              onChange={(e) => {
                setDisplayName(e.target.value);
                updateDiagramName(e.target.value, selectedFormat);
              }}
              className="w-[450px] px-2 py-1 text-lg font-semibold bg-transparent border-b border-gray-300 hover:border-gray-400 focus:border-blue-500 focus:outline-none transition-colors"
              placeholder="Diagram name (e.g., my_diagram)"
            />
            <Select
              value={selectedFormat}
              onChange={(e) => {
                const newFormat = e.target.value as DiagramFormat;
                setSelectedFormat(newFormat);
                updateDiagramName(displayName, newFormat);
              }}
              className="text-sm px-1 py-1 w-[150px] bg-white border border-gray-300 rounded hover:border-gray-400 focus:border-blue-500 focus:outline-none"
            >
              <option value={DiagramFormat.NATIVE}>.native.json</option>
              <option value={DiagramFormat.READABLE}>.readable.yaml</option>
              <option value={DiagramFormat.LIGHT}>.light.yaml</option>
            </Select>
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
          
          {/* Description Row */}
          <input
            type="text"
            value={diagramDescription}
            onChange={(e) => setDiagramDescription(e.target.value)}
            className="w-full px-2 py-0.5 text-sm text-gray-600 bg-transparent border-b border-gray-200 hover:border-gray-300 focus:border-blue-400 focus:outline-none transition-colors"
            placeholder="Description (optional)"
          />
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Action Buttons */}
          <Button 
            variant="outline" 
            className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors"
            onClick={() => {
              if (window.confirm('Create a new diagram? This will clear the current diagram.')) {
                clearDiagram();
                setDisplayName('');
              }
            }}
            title="Create a new diagram"
          >
            📄 New
          </Button>
          
          {/* Load/Save buttons in vertical layout */}
          <div className="flex flex-col space-y-1">
            <Button
              variant="outline"
              className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors text-sm px-3 py-1"
              onClick={async () => {
                // Build full path with format
                const fullPath = addFormatSuffix(displayName.trim() || 'quicksave', selectedFormat);
                
                try {
                  // Fetch diagram content from server
                  const { data, error } = await getDiagram({
                    variables: { id: fullPath }
                  });
                  
                  if (error) {
                    toast.error(`Failed to load diagram: ${error.message}`);
                    return;
                  }
                  
                  if (data?.diagram) {
                    // Load the diagram data directly without URL changes
                    loadDiagramFromData({
                      nodes: data.diagram.nodes || [],
                      arrows: data.diagram.arrows || [],
                      handles: data.diagram.handles || [],
                      persons: data.diagram.persons || [],
                      metadata: {
                        ...data.diagram.metadata,
                        name: data.diagram.metadata?.name || fullPath,
                        id: data.diagram.metadata?.id || fullPath
                      }
                    });
                    
                    toast.success(`Loaded ${fullPath}`);
                  } else {
                    toast.error('Diagram not found');
                  }
                } catch (err) {
                  console.error('Failed to load diagram:', err);
                  toast.error('Failed to load diagram');
                }
              }}
              title="Load diagram using title"
            >
              📂 Load
            </Button>
            <Button 
              variant="outline" 
              className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors text-sm px-3 py-1"
              onClick={handleConvertAndSave}
              disabled={isSaving}
              title={`Save diagram as ${selectedFormat === DiagramFormat.NATIVE ? 'JSON' : 'YAML'}`}
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-600 mr-1" />
                  <span className="text-xs">Saving...</span>
                </>
              ) : (
                <>💾 Save</>
              )}
            </Button>
          </div>
          
          {/* Divider */}
          <div className="h-6 w-px bg-gray-300 mx-2" />
          
          {/* Execution Mode and Monitor Mode in vertical layout */}
          <div className="flex flex-col items-end space-y-2">
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
                  stopExecution();
                  // When leaving execution mode, readOnly remains controlled by monitor mode
                } else {
                  // Simply switch to execution mode
                  // The ExecutionControls component will handle running the diagram from memory
                  setActiveCanvas('execution');
                }
              }}
              title={activeCanvas === 'execution' ? 'Back to Diagram Canvas' : 'Enter Execution Mode'}
            >
              <Layers className={`h-4 w-4 mr-1 transition-transform duration-300 ${
                activeCanvas === 'execution' ? 'rotate-12' : ''
              }`} />
              {activeCanvas === 'execution' ? 'Exit Execution Mode' : 'Execution Mode'}
            </Button>
            
            <button
              onClick={() => {
                const newMonitorMode = !isMonitorMode;
                setMonitorMode(newMonitorMode);
                
                if (newMonitorMode) {
                  // Add monitor param to URL
                  const url = new URL(window.location.href);
                  url.searchParams.set('monitor', 'true');
                  window.history.replaceState({}, '', url.toString());
                  toast.info('Monitor mode enabled - automatically entering execution mode');
                } else {
                  // Remove monitor param from URL
                  const url = new URL(window.location.href);
                  url.searchParams.delete('monitor');
                  window.history.replaceState({}, '', url.toString());
                  toast.success('Monitor mode disabled');
                }
              }}
              className={`flex items-center space-x-2 px-4 py-2 border rounded-md transition-all duration-300 ${
                isMonitorMode 
                  ? 'bg-blue-100 border-blue-400 hover:bg-blue-200' 
                  : 'bg-white border-gray-300 hover:bg-gray-50 hover:border-gray-400'
              }`}
              title={isMonitorMode ? 'Disable Monitor Mode' : 'Enable Monitor Mode'}
            >
              {isMonitorMode && (
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                </span>
              )}
              <span className="text-sm font-medium">Monitor Mode</span>
              <div
                className={`relative inline-flex h-5 w-11 items-center rounded-full transition-colors ${
                  isMonitorMode ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    isMonitorMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </div>
            </button>
          </div>
        </div>
      </div>

    </header>
  );
};

export default TopBar;