import React, { useState, useEffect, useCallback } from 'react';
import { Layers } from 'lucide-react';
import { Button } from '@/shared/components/forms/buttons';
import { Select } from '@/shared/components/forms/Select';
import { useUIState } from '@/core/store/hooks/state';
import { useDiagramManager, useFileOperations } from '@/features/diagram-editor/hooks';
import { useUIOperations, useExecutionOperations } from '@/core/store/hooks';
import { toast } from 'sonner';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { useShallow } from 'zustand/react/shallow';
import { DiagramFormat } from '@dipeo/domain-models';
import { useConvertDiagramMutation, useUploadFileMutation } from '@/__generated__/graphql';
import { serializeDiagram } from '@/features/diagram-editor/utils/diagramSerializer';


const TopBar = () => {
  const [isMonitorMode, setIsMonitorMode] = useState(false);
  const [isExitingMonitor, setIsExitingMonitor] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<DiagramFormat>(DiagramFormat.NATIVE);
  const [isSaving, setIsSaving] = useState(false);
  
  // Use UI state for mode control
  const { activeCanvas } = useUIState();
  const { setReadOnly, setActiveCanvas } = useUIOperations();
  const { stopExecution } = useExecutionOperations();
  
  // Get diagram metadata from store
  const { diagramName, diagramDescription, setDiagramName, setDiagramDescription } = useUnifiedStore(
    useShallow(state => ({
      diagramName: state.diagramName,
      diagramDescription: state.diagramDescription,
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
    saveDiagram: basicSaveDiagram,
    isDirty
  } = diagramManager;
  
  // File operations and GraphQL mutations
  const { saveDiagram: saveToFileSystem } = useFileOperations();
  const [convertDiagramMutation] = useConvertDiagramMutation();
  const [uploadFileMutation] = useUploadFileMutation();
  

  // Handle monitor mode and format detection
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const isMonitor = params.get('monitor') === 'true';
    setIsMonitorMode(isMonitor);
    
    // Only set read-only mode for monitor mode, don't auto-switch to execution
    if (isMonitor) {
      setReadOnly?.(true);
    }
    
    // Detect format from current diagram URL
    const currentDiagramId = params.get('diagram');
    if (currentDiagramId && currentDiagramId.includes('/')) {
      const format = currentDiagramId.split('/')[0];
      if (format === 'native') {
        setSelectedFormat(DiagramFormat.NATIVE);
      } else if (format === 'readable') {
        setSelectedFormat(DiagramFormat.READABLE);
      } else if (format === 'light') {
        setSelectedFormat(DiagramFormat.LIGHT);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount

  // Convert and save functionality
  const handleConvertAndSave = useCallback(async () => {
    try {
      setIsSaving(true);
      // Use the user-provided name or default
      const finalName = diagramName.trim() || 'diagram';
      
      // Generate filename based on format
      const extension = selectedFormat === DiagramFormat.NATIVE ? 'json' : 'yaml';
      const filename = `${finalName}.${extension}`;
      
      // For native format, use the existing saveDiagram function
      if (selectedFormat === DiagramFormat.NATIVE) {
        await saveToFileSystem(filename, selectedFormat);
        const formatDir = selectedFormat.toLowerCase();
        toast.success(`Saved to ${formatDir}/${filename}`);
        return;
      }
      
      // For light and readable formats, use convert + upload approach
      // First, serialize the current diagram state
      const diagramContent = serializeDiagram();
      
      // Convert diagram to the desired format
      const convertResult = await convertDiagramMutation({
        variables: {
          content: diagramContent,
          targetFormat: selectedFormat,
          includeMetadata: true
        }
      });
      
      if (!convertResult.data?.convert_diagram?.success) {
        throw new Error(convertResult.data?.convert_diagram?.error || 'Conversion failed');
      }
      
      // Get the converted content
      const convertedContent = convertResult.data.convert_diagram.content;
      if (!convertedContent) {
        throw new Error('No content returned from conversion');
      }
      
      // Determine the category based on format
      const category = `diagrams/${selectedFormat}`;
      
      // Create a File object from the converted content
      const file = new File([convertedContent], filename, { 
        type: 'text/yaml' 
      });
      
      // Upload the file directly to diagrams/{format}/ directory
      const uploadResult = await uploadFileMutation({
        variables: {
          file,
          category
        }
      });
      
      if (!uploadResult.data?.upload_file?.success) {
        throw new Error(uploadResult.data?.upload_file?.error || 'Upload failed');
      }
      
      // Show success message
      toast.success(`Saved to ${category}/${filename}`);
    } catch (error) {
      console.error('Save error:', error);
      toast.error(error instanceof Error ? error.message : 'Save failed');
    } finally {
      setIsSaving(false);
    }
  }, [selectedFormat, diagramName, saveToFileSystem, convertDiagramMutation, uploadFileMutation]);


  return (
    <header className="p-3 border-b bg-gradient-to-r from-gray-50 to-gray-100 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          {/* Title Row with Buttons */}
          <div className="flex items-center gap-1">
            <input
              type="text"
              value={diagramName}
              onChange={(e) => setDiagramName(e.target.value)}
              className="w-48 px-2 py-1 text-lg font-semibold bg-transparent border-b border-gray-300 hover:border-gray-400 focus:border-blue-500 focus:outline-none transition-colors"
              placeholder="Diagram Title"
            />
            {/* Action Buttons */}
            <div className="flex items-center space-x-1">
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
                // Use title from input field
                const name = diagramName.trim() || 'quicksave';
                
                // Map DiagramFormat enum to string format
                let format = 'native';
                if (selectedFormat === DiagramFormat.LIGHT) {
                  format = 'light';
                } else if (selectedFormat === DiagramFormat.READABLE) {
                  format = 'readable';
                } else if (selectedFormat === DiagramFormat.NATIVE) {
                  format = 'native';
                }
                
                // Build the diagram path
                const diagramPath = `${format}/${name}`;
                
                // Update URL and trigger reload
                const newUrl = `/?diagram=${diagramPath}`;
                window.history.pushState({}, '', newUrl);
                
                // Dispatch popstate event to trigger diagram loader
                window.dispatchEvent(new PopStateEvent('popstate'));
                
                toast.info(`Loading ${diagramPath}...`);
              }}
              title="Load diagram using title"
            >
              📂 Load
            </Button>
            <Button 
              variant="outline" 
              className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors"
              onClick={handleConvertAndSave}
              disabled={isSaving}
              title={`Save diagram as ${selectedFormat === DiagramFormat.NATIVE ? 'JSON' : 'YAML'}`}
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-1" />
                  <span>Saving...</span>
                </>
              ) : (
                <>💾 Save</>
              )}
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
          </div>
          
          {/* Description Row */}
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={diagramDescription}
              onChange={(e) => setDiagramDescription(e.target.value)}
              className="flex-1 min-w-[300px] px-2 py-0.5 text-sm text-gray-600 bg-transparent border-b border-gray-200 hover:border-gray-300 focus:border-blue-400 focus:outline-none transition-colors"
              placeholder="Description (optional)"
            />
            <Select
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value as DiagramFormat)}
              className="text-sm px-2 py-0.5 bg-white border border-gray-300 rounded hover:border-gray-400 focus:border-blue-500 focus:outline-none"
            >
              <option value={DiagramFormat.NATIVE}>Native JSON</option>
              <option value={DiagramFormat.READABLE}>Readable YAML</option>
              <option value={DiagramFormat.LIGHT}>Light YAML</option>
            </Select>
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