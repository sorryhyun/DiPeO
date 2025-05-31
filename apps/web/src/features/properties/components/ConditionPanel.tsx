import React from 'react';
import { type ConditionBlockData } from '@/shared/types';
import { usePropertyPanel } from '@/features/properties';
import {
  Form,
  SingleColumnPanelLayout,
  TextField,
  TextAreaField,
  RadioGroupField
} from './ui-components/FormComponents';

export const ConditionPanelContent: React.FC<{ nodeId: string; data: ConditionBlockData }> = ({ nodeId, data }) => {
  const { formData, handleChange } = usePropertyPanel<ConditionBlockData>(nodeId, 'node', data);
  const isMaxIterationMode = formData.conditionType === 'max_iterations';

  const conditionTypeOptions = [
    { value: 'expression', label: 'Python Expression' },
    { value: 'max_iterations', label: 'Detect Max Iterations' }
  ];

  return (
    <Form>
      <SingleColumnPanelLayout>
        <TextField
          label="Block Label"
          value={formData.label || ''}
          onChange={(v) => handleChange('label', v)}
          placeholder="Condition"
        />

        <RadioGroupField
          label="Condition Type"
          value={formData.conditionType || 'expression'}
          onChange={(v) => handleChange('conditionType', v as 'expression' | 'max_iterations')}
          options={conditionTypeOptions}
        />

        {!isMaxIterationMode ? (
          <TextAreaField
            label="Python Expression"
            value={formData.expression || ''}
            onChange={(v) => handleChange('expression', v)}
            placeholder="e.g., x > 10 and y == 'yes'"
            hint="Use Python boolean expressions with variables from incoming edges."
          />
        ) : (
          <div className="text-sm text-gray-600 p-3 bg-gray-50 rounded">
            This condition will return False when a max iteration limit is detected.
          </div>
        )}
      </SingleColumnPanelLayout>
    </Form>
  );
};