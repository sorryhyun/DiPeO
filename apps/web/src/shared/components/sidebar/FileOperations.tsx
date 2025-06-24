import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Upload, Download } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/shared/components/ui/buttons/Button';
import { Select } from '@/shared/components/ui/inputs/Select';
import { 
  useSaveDiagramMutation,
  useConvertDiagramMutation,
  useUploadFileMutation
} from '@/__generated__/graphql';
import { DiagramFormat } from '@dipeo/domain-models';
import { useFileOperations } from '@/shared/hooks/useFileOperations';
import { serializeDiagram } from '@/shared/utils/diagramSerializer';

export const FileOperations: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<DiagramFormat>(DiagramFormat.NATIVE);
  const [diagramName, setDiagramName] = useState<string>('diagram');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [saveDiagramMutation] = useSaveDiagramMutation();
  const [convertDiagramMutation] = useConvertDiagramMutation();
  const [uploadFileMutation] = useUploadFileMutation();
  const { saveDiagram } = useFileOperations();

  // Initialize diagram name from URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const currentDiagramId = urlParams.get('diagram');
    if (currentDiagramId) {
      setDiagramName(currentDiagramId);
    }
  }, []);

  const handleFileSelect = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    
    try {
      // First validate the file
      const validateResult = await saveDiagramMutation({
        variables: {
          file,
          validateOnly: true
        }
      });

      if (!validateResult.data?.saveDiagram?.success) {
        throw new Error(validateResult.data?.saveDiagram?.message || 'Validation failed');
      }

      // Validation successful, now save for real
      const saveResult = await saveDiagramMutation({
        variables: {
          file,
          validateOnly: false
        }
      });

      if (!saveResult.data?.saveDiagram?.success) {
        throw new Error(saveResult.data?.saveDiagram?.message || 'Save failed');
      }

      const { diagramId: newDiagramId, diagramName } = saveResult.data.saveDiagram;
      
      toast.success(`Loaded ${diagramName}`);

      // Reload the page to load the new diagram
      if (newDiagramId) {
        window.location.href = `/?diagram=${newDiagramId}`;
      }

    } catch (error) {
      console.error('Save error:', error);
      toast.error(error instanceof Error ? error.message : 'Save failed');
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [saveDiagramMutation]);

  const handleExport = useCallback(async () => {
    try {
      // Use the user-provided name or default
      const finalName = diagramName.trim() || 'diagram';
      
      // Generate filename based on format
      const extension = selectedFormat === DiagramFormat.NATIVE ? 'json' : 'yaml';
      const filename = `${finalName}.${extension}`;
      
      // For native format, use the existing saveDiagram function
      if (selectedFormat === DiagramFormat.NATIVE) {
        await saveDiagram(filename, selectedFormat);
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
      
      if (!convertResult.data?.convertDiagram?.success) {
        throw new Error(convertResult.data?.convertDiagram?.error || 'Conversion failed');
      }
      
      // Get the converted content
      const convertedContent = convertResult.data.convertDiagram.content;
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
      
      if (!uploadResult.data?.uploadFile?.success) {
        throw new Error(uploadResult.data?.uploadFile?.error || 'Upload failed');
      }
      
      // Show success message
      toast.success(`Saved to ${category}/${filename}`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error(error instanceof Error ? error.message : 'Export failed');
    }
  }, [selectedFormat, diagramName, saveDiagram, convertDiagramMutation, uploadFileMutation]);

  const exportFormats = [
    { value: DiagramFormat.NATIVE, label: 'Native JSON' },
    { value: DiagramFormat.READABLE, label: 'Readable YAML' },
    { value: DiagramFormat.LIGHT, label: 'Light YAML' }
  ];

  return (
    <div className="space-y-3">
      {/* Upload file */}
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
              <span>Loading...</span>
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              <span>Convert and Load</span>
            </>
          )}
        </label>
      </div>

      {/* Export */}
      <div className="space-y-2">
        <input
          type="text"
          value={diagramName}
          onChange={(e) => setDiagramName(e.target.value)}
          placeholder="Diagram name"
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        
        <Select
          value={selectedFormat}
          onChange={(e) => setSelectedFormat(e.target.value as DiagramFormat)}
          className="w-full text-sm"
        >
          {exportFormats.map(format => (
            <option key={format.value} value={format.value}>
              {format.label}
            </option>
          ))}
        </Select>
        
        <Button
          onClick={handleExport}
          variant="outline"
          className="w-full text-sm"
          size="sm"
        >
          <Download className="w-4 h-4 mr-2" />
          Convert and Save
        </Button>
      </div>
    </div>
  );
};