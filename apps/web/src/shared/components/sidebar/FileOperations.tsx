import React, { useState, useRef, useCallback } from 'react';
import { Upload, Download } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/shared/components/ui/buttons/Button';
import { Select } from '@/shared/components/ui/inputs/Select';
import { 
  useSaveDiagramMutation
} from '@/__generated__/graphql';
import { DiagramFormat } from '@dipeo/domain-models';
import { useFileOperations } from '@/shared/hooks/useFileOperations';

export const FileOperations: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<DiagramFormat>(DiagramFormat.NATIVE);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [saveDiagramMutation] = useSaveDiagramMutation();
  const { downloadAs } = useFileOperations();

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

      const { diagramId: newDiagramId, diagramName, nodeCount } = saveResult.data.saveDiagram;
      
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
      await downloadAs(selectedFormat, undefined, true);
    } catch (error) {
      console.error('Export error:', error);
      toast.error(error instanceof Error ? error.message : 'Export failed');
    }
  }, [selectedFormat, downloadAs]);

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