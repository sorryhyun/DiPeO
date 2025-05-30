import React from 'react';
import { Switch } from '@repo/ui-kit';
import { type EndpointBlockData } from '@repo/core-model';
import { usePropertyPanel } from '../hooks/usePropertyPanel';
import {
  Form, FormField,
  TextField, SelectField
} from '../wrappers';

export const EndpointPanelContent: React.FC<{ nodeId: string; data: EndpointBlockData }> = ({ nodeId, data }) => {
  const { formData, handleChange } = usePropertyPanel<EndpointBlockData>(nodeId, 'node', data);

  const fileFormatOptions = [
    { value: 'text', label: 'Plain Text' },
    { value: 'json', label: 'JSON' },
    { value: 'csv', label: 'CSV' }
  ];

  return (
    <Form>
      <TextField
        label="Block Label"
        value={formData.label || ''}
        onChange={(v) => handleChange('label', v)}
        placeholder="End"
      />

      <div className="border-t pt-4">
        <FormField label="Save output to file" className="flex items-center space-x-2">
          <Switch
            id="saveToFile"
            checked={formData.saveToFile || false}
            onChange={(checked: boolean) => handleChange('saveToFile', checked)}
          />
        </FormField>

        {formData.saveToFile && (
          <>
            <TextField
              label="File Path"
              value={formData.filePath || ''}
              onChange={(v) => handleChange('filePath', v)}
              placeholder="results/output.txt"
            />
            <SelectField
              label="File Format"
              value={formData.fileFormat || 'text'}
              onChange={(v) => handleChange('fileFormat', v as any)}
              options={fileFormatOptions}
            />
          </>
        )}
      </div>
    </Form>
  );
};