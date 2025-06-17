import React, { useState, useRef, useCallback } from 'react';
import { Upload, Download, FileUp } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/shared/components/ui/buttons/Button';
import { Select } from '@/shared/components/ui/inputs/Select';
import { 
  DiagramFormat,
  useUploadDiagramMutation,
  useSaveDiagramMutation 
} from '@/__generated__/graphql';

export const FileOperations: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<DiagramFormat>(DiagramFormat.Native);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Get current diagram ID from URL
  const searchParams = new URLSearchParams(window.location.search);
  const diagramId = searchParams.get('diagram');

  const [uploadDiagram] = useUploadDiagramMutation();
  const [saveDiagram] = useSaveDiagramMutation();

  const handleFileSelect = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    
    try {
      // First validate the file
      const validateResult = await uploadDiagram({
        variables: {
          file,
          validateOnly: true
        }
      });

      if (!validateResult.data?.uploadDiagram?.success) {
        throw new Error(validateResult.data?.uploadDiagram?.message || 'Validation failed');
      }

      // Show validation success
      toast.success(`Valid ${validateResult.data.uploadDiagram.formatDetected} format detected`);

      // Now upload for real
      const uploadResult = await uploadDiagram({
        variables: {
          file,
          validateOnly: false
        }
      });

      if (!uploadResult.data?.uploadDiagram?.success) {
        throw new Error(uploadResult.data?.uploadDiagram?.message || 'Upload failed');
      }

      const { diagramId: newDiagramId, diagramName, nodeCount } = uploadResult.data.uploadDiagram;
      
      toast.success(
        <div className="flex flex-col gap-1">
          <span className="font-medium">Upload successful!</span>
          <span className="text-sm opacity-80">
            {diagramName} • {nodeCount} nodes
          </span>
        </div>
      );

      // Reload the page to load the new diagram
      if (newDiagramId) {
        window.location.href = `/?diagram=${newDiagramId}`;
      }

    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [uploadDiagram]);

  const handleSave = useCallback(async () => {
    if (!diagramId) {
      toast.error('No diagram to save');
      return;
    }

    try {
      const result = await saveDiagram({
        variables: {
          diagramId: diagramId as any, // Type assertion needed for DiagramID type
          format: selectedFormat
        }
      });

      if (!result.data?.saveDiagram?.success) {
        throw new Error(result.data?.saveDiagram?.error || 'Save failed');
      }

      toast.success(result.data.saveDiagram.message || `Diagram saved as ${selectedFormat}`);

    } catch (error) {
      console.error('Save error:', error);
      toast.error(error instanceof Error ? error.message : 'Save failed');
    }
  }, [diagramId, selectedFormat, saveDiagram]);

  // Define export formats for sidebar display
  const exportFormats = [
    { value: DiagramFormat.Native, label: 'Native JSON' },
    { value: DiagramFormat.Readable, label: 'Readable YAML' },
    { value: DiagramFormat.Light, label: 'Light YAML' },
    { value: DiagramFormat.Llm, label: 'LLM Domain' }
  ];

  return (
    <div className="space-y-3">
      {/* Import */}
      <div className="relative">
        <input
          ref={fileInputRef}
          type="file"
          accept=".yaml,.yml,.json"
          onChange={handleFileSelect}
          className="hidden"
          id="diagram-upload-sidebar"
        />
        
        <label
          htmlFor="diagram-upload-sidebar"
          className={`
            flex items-center justify-center gap-2 w-full px-3 py-2
            border rounded-lg cursor-pointer text-sm font-medium
            transition-all duration-200
            ${isUploading 
              ? 'border-blue-400 bg-blue-50 text-blue-700' 
              : 'border-gray-300 bg-white hover:bg-gray-50 text-gray-700'
            }
          `}
        >
          {isUploading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
              <span>Importing...</span>
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              <span>Import Diagram</span>
            </>
          )}
        </label>
      </div>

      {/* Export */}
      <div className="space-y-2">
        <Select
          value={selectedFormat}
          onChange={(e) => setSelectedFormat(e.target.value as DiagramFormat)}
          className="w-full text-sm"
          disabled={!diagramId}
        >
          {exportFormats.map(format => (
            <option key={format.value} value={format.value}>
              Save as {format.label}
            </option>
          ))}
        </Select>
        
        <Button
          onClick={handleSave}
          disabled={!diagramId}
          variant={diagramId ? 'outline' : 'secondary'}
          className="w-full text-sm"
          size="sm"
        >
          <Download className="w-4 h-4 mr-2" />
          Save
        </Button>
      </div>
    </div>
  );
};