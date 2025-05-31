import React from 'react';
import { type EndpointBlockData } from '@/shared/types';
import { usePropertyPanel } from '@/features/properties';
import {
  Form,
  SingleColumnPanelLayout,
  TextField,
  SelectField,
  CheckboxField
} from './ui-components/FormComponents';

export const EndpointPanelContent: React.FC<{ nodeId: string; data: EndpointBlockData }> = ({ nodeId, data }) => {
  const { formData, handleChange } = usePropertyPanel<EndpointBlockData>(nodeId, 'node', data);

  const fileFormatOptions = [
    { value: 'text', label: 'Plain Text' },
    { value: 'json', label: 'JSON' },
    { value: 'csv', label: 'CSV' }
  ];

  return (
    <Form>
      <SingleColumnPanelLayout>
        <TextField
          label="Block Label"
          value={formData.label || ''}
          onChange={(v) => handleChange('label', v)}
          placeholder="End"
        />

        <div className="border-t pt-4 space-y-4">
          <CheckboxField
            label="Save output to file"
            checked={formData.saveToFile || false}
            onChange={(checked: boolean) => handleChange('saveToFile', checked)}
            id="saveToFile"
          />

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
                onChange={(v) => handleChange('fileFormat', v as 'text' | 'json' | 'csv')}
                options={fileFormatOptions}
              />
            </>
          )}
        </div>
      </SingleColumnPanelLayout>
    </Form>
  );
};