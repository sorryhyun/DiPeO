import React, { useState, useRef, useCallback } from 'react';
import { Upload, Download } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/shared/components/ui/buttons/Button';
import { Select } from '@/shared/components/ui/inputs/Select';
import { 
  useUploadDiagramMutation,
  useExportDiagramMutation 
} from '@/__generated__/graphql';
import { DiagramFormat } from '@dipeo/domain-models';
import { downloadFile } from '@/shared/utils/file';
import { useFileOperations } from '@/shared/hooks/useFileOperations';
import { exportDiagramAsGraphQLSchema } from '@/utils/graphqlSchemaExporter';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';

export const FileOperations: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<DiagramFormat | 'GRAPHQL'>(DiagramFormat.NATIVE);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Get current diagram ID from URL
  const searchParams = new URLSearchParams(window.location.search);
  const diagramId = searchParams.get('diagram');

  const [uploadDiagram] = useUploadDiagramMutation();
  const { exportAndDownload } = useFileOperations();

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
    try {
      // Handle GraphQL schema export specially (client-side)
      if (selectedFormat === 'GRAPHQL') {
        // Get current diagram state
        const store = useUnifiedStore.getState();
        const diagramState = {
          nodes: Array.from(store.nodes.values()),
          arrows: Array.from(store.arrows.values()),
          handles: Array.from(store.handles.values())
        };
        
        // Generate GraphQL schema
        const schema = exportDiagramAsGraphQLSchema(diagramState);
        
        // Download the schema file
        downloadFile(schema, 'schema.graphql', 'text/plain');
        toast.success('GraphQL schema exported successfully');
        return;
      }

      // For other formats, use the stateful export
      await exportAndDownload(selectedFormat as DiagramFormat, undefined, true);

    } catch (error) {
      console.error('Save error:', error);
      toast.error(error instanceof Error ? error.message : 'Save failed');
    }
  }, [selectedFormat, exportAndDownload]);

  // Define export formats for sidebar display
  const exportFormats = [
    { value: DiagramFormat.NATIVE, label: 'Native JSON' },
    { value: DiagramFormat.READABLE, label: 'Readable YAML' },
    { value: DiagramFormat.LIGHT, label: 'Light YAML' },
    { value: 'GRAPHQL', label: 'GraphQL Schema' }
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
          onChange={(e) => setSelectedFormat(e.target.value as DiagramFormat | 'GRAPHQL')}
          className="w-full text-sm"
        >
          {exportFormats.map(format => (
            <option key={format.value} value={format.value}>
              {format.label}
            </option>
          ))}
        </Select>
        
        <Button
          onClick={handleSave}
          variant="outline"
          className="w-full text-sm"
          size="sm"
        >
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>
    </div>
  );
};