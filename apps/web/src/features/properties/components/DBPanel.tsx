import React, { useState } from 'react';
import { toast } from 'sonner';
import { Input, Spinner } from '@repo/ui-kit';
import { getApiUrl, API_ENDPOINTS } from '@/utils/apiConfig';
import { createErrorHandlerFactory, type DBBlockData } from '@repo/core-model';
import { usePropertyPanel } from '../hooks/usePropertyPanel';
import {
  Form, FormField, FormRow,
  InlineTextField, InlineSelectField, TextAreaField
} from '../wrappers';

export const DBPanelContent: React.FC<{ nodeId: string; data: DBBlockData }> = ({ nodeId, data }) => {
  const { formData, handleChange } = usePropertyPanel<DBBlockData>(nodeId, 'node', data);
  const [uploading, setUploading] = useState(false);

  const dbTypeOptions = [
    { value: 'fixed_prompt', label: 'Fixed Prompt' },
    { value: 'file', label: 'File' }
  ];

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(getApiUrl(API_ENDPOINTS.UPLOAD_FILE), { method: 'POST', body: form });
      if (!res.ok) throw new Error('Upload failed');
      const { path } = await res.json();
      handleChange('sourceDetails', path);
      toast.success(`File uploaded: ${file.name}`);
    } catch (error) {
      const createErrorHandler = createErrorHandlerFactory(toast);
      createErrorHandler('File upload failed')(error as Error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Form>
      <div className="grid grid-cols-2 gap-4">
        {/* Left column - Option properties */}
        <div className="space-y-4">
          <FormRow>
            <InlineTextField
              label="Label"
              value={formData.label || ''}
              onChange={(v) => handleChange('label', v)}
              placeholder="Database"
              className="flex-1"
            />
            <InlineSelectField
              label="Source Type"
              value={formData.subType || 'fixed_prompt'}
              onChange={(v) => handleChange('subType', v as any)}
              options={dbTypeOptions}
              className="flex-1"
            />
          </FormRow>
        </div>

        {/* Right column - Text properties */}
        <div className="space-y-4">
          {formData.subType === 'file' ? (
            <FormField label="File Path">
              <Input
                type="text"
                value={formData.sourceDetails || ''}
                placeholder="Or upload a file below"
                onChange={(e) => handleChange('sourceDetails', e.target.value)}
              />
              <Input
                type="file"
                accept=".txt,.docx,.doc,.pdf,.csv,.json"
                className="mt-2"
                disabled={uploading}
                onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
              />
              {uploading && (
                <div className="flex items-center mt-2 text-sm text-gray-600">
                  <Spinner size="sm" className="mr-2" />
                  <span>Uploading...</span>
                </div>
              )}
            </FormField>
          ) : (
            <TextAreaField
              label="Prompt Content"
              value={formData.sourceDetails || ''}
              onChange={(v) => handleChange('sourceDetails', v)}
              placeholder="Enter your prompt content"
              rows={5}
              hint="Enter the fixed prompt text that will be used by this database block"
            />
          )}
        </div>
      </div>
    </Form>
  );
};