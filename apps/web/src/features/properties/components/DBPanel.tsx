import React from 'react';
import { toast } from 'sonner';
import { getApiUrl, API_ENDPOINTS } from '@/shared/utils/apiConfig';
import { createErrorHandlerFactory, type DBBlockData } from '@/shared/types';
import { usePropertyPanel } from '@/features/properties';
import {
  Form,
  TwoColumnPanelLayout,
  FormRow,
  InlineTextField,
  InlineSelectField,
  TextAreaField,
  FileUploadField
} from './ui-components/FormComponents';

export const DBPanelContent: React.FC<{ nodeId: string; data: DBBlockData }> = ({ nodeId, data }) => {
  const { formData, handleChange } = usePropertyPanel<DBBlockData>(nodeId, 'node', data);

  const dbTypeOptions = [
    { value: 'fixed_prompt', label: 'Fixed Prompt' },
    { value: 'file', label: 'File' }
  ];

  const handleFileUpload = async (file: File) => {
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
    }
  };

  return (
    <Form>
      <TwoColumnPanelLayout
        leftColumn={
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
              onChange={(v) => handleChange('subType', v as 'fixed_prompt' | 'file')}
              options={dbTypeOptions}
              className="flex-1"
            />
          </FormRow>
        }
        rightColumn={
          formData.subType === 'file' ? (
            <FileUploadField
              label="File Path"
              value={formData.sourceDetails || ''}
              onChange={(v) => handleChange('sourceDetails', v)}
              onFileUpload={handleFileUpload}
              accept=".txt,.docx,.doc,.pdf,.csv,.json"
              placeholder="Enter file path or upload below"
            />
          ) : (
            <TextAreaField
              label="Prompt Content"
              value={formData.sourceDetails || ''}
              onChange={(v) => handleChange('sourceDetails', v)}
              placeholder="Enter your prompt content"
              rows={5}
              hint="Enter the fixed prompt text that will be used by this database block"
            />
          )
        }
      />
    </Form>
  );
};