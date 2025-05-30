import React from 'react';
import { type ConditionBlockData } from '../../../shared/types';
import { usePropertyPanel } from '../hooks/usePropertyPanel';
import {
  Form, FormField,
  TextField, TextAreaField
} from '../wrappers';

export const ConditionPanelContent: React.FC<{ nodeId: string; data: ConditionBlockData }> = ({ nodeId, data }) => {
  const { formData, handleChange } = usePropertyPanel<ConditionBlockData>(nodeId, 'node', data);
  const isMaxIterationMode = formData.conditionType === 'max_iterations';

  return (
    <Form>
      <TextField
        label="Block Label"
        value={formData.label || ''}
        onChange={(v) => handleChange('label', v)}
        placeholder="Condition"
      />

      <FormField label="Condition Type">
        <div className="space-y-2">
          {[
            { value: 'expression', label: 'Python Expression' },
            { value: 'max_iterations', label: 'Detect Max Iterations' }
          ].map(opt => (
            <label key={opt.value} className="flex items-center space-x-2">
              <input
                type="radio"
                checked={opt.value === 'expression' ? !isMaxIterationMode : isMaxIterationMode}
                onChange={() => handleChange('conditionType', opt.value as any)}
                className="text-blue-600"
              />
              <span>{opt.label}</span>
            </label>
          ))}
        </div>
      </FormField>

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
    </Form>
  );
};