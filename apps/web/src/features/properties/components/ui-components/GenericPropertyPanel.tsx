import React from 'react';
import { PanelConfig, FieldConfig } from '@/shared/types/panelConfig';
import { usePropertyPanel } from '../../hooks/usePropertyPanel';
import {
  Form,
  TwoColumnPanelLayout,
  SingleColumnPanelLayout,
  FormRow,
  InlineTextField,
  InlineSelectField,
  TextAreaField,
  CheckboxField,
  IterationCountField,
  PersonSelectionField,
  LabelPersonRow,
  VariableDetectionTextArea
} from './FormComponents';

interface GenericPropertyPanelProps<T extends Record<string, any>> {
  nodeId: string;
  data: T;
  config: PanelConfig<T>;
}

export const GenericPropertyPanel = <T extends Record<string, any>>({
  nodeId,
  data,
  config
}: GenericPropertyPanelProps<T>) => {
  const { formData, handleChange } = usePropertyPanel<T>(nodeId, 'node', data);
  
  // Type-safe update function
  const updateField = (name: string, value: any) => {
    handleChange(name as keyof T, value);
  };
  
  // Field renderer function
  const renderField = (fieldConfig: FieldConfig, index: number): React.ReactNode => {
    // Check conditional rendering
    if (fieldConfig.conditional) {
      const fieldValue = formData[fieldConfig.conditional.field];
      const { values, operator = 'includes' } = fieldConfig.conditional;
      
      let shouldRender = false;
      switch (operator) {
        case 'equals':
          shouldRender = values.includes(fieldValue);
          break;
        case 'notEquals':
          shouldRender = !values.includes(fieldValue);
          break;
        case 'includes':
        default:
          shouldRender = values.includes(fieldValue);
          break;
      }
      
      if (!shouldRender) return null;
    }

    const key = fieldConfig.name ? `${fieldConfig.name}-${index}` : `field-${index}`;

    switch (fieldConfig.type) {
      case 'text': {
        return (
          <InlineTextField
            key={key}
            label={fieldConfig.label || ''}
            value={formData[fieldConfig.name] || ''}
            onChange={(v) => updateField(fieldConfig.name, v)}
            placeholder={fieldConfig.placeholder}
            className={fieldConfig.className}
          />
        );
      }

      case 'select': {
        const options = typeof fieldConfig.options === 'function' 
          ? fieldConfig.options() 
          : fieldConfig.options;
        
        return (
          <InlineSelectField
            key={key}
            label={fieldConfig.label || ''}
            value={formData[fieldConfig.name] || ''}
            onChange={(v) => updateField(fieldConfig.name, v)}
            options={options}
            placeholder={fieldConfig.placeholder}
            className={fieldConfig.className}
          />
        );
      }

      case 'textarea': {
        return (
          <TextAreaField
            key={key}
            label={fieldConfig.label || ''}
            value={formData[fieldConfig.name] || ''}
            onChange={(v) => updateField(fieldConfig.name, v)}
            rows={fieldConfig.rows}
            placeholder={fieldConfig.placeholder}
          />
        );
      }

      case 'checkbox': {
        return (
          <CheckboxField
            key={key}
            label={fieldConfig.label || ''}
            checked={!!formData[fieldConfig.name]}
            onChange={(checked) => updateField(fieldConfig.name, checked)}
          />
        );
      }

      case 'variableTextArea': {
        return (
          <VariableDetectionTextArea
            key={key}
            label={fieldConfig.label || ''}
            value={formData[fieldConfig.name] || ''}
            onChange={(v) => updateField(fieldConfig.name, v)}
            rows={fieldConfig.rows}
            placeholder={fieldConfig.placeholder}
            detectedVariables={data.detectedVariables}
          />
        );
      }

      case 'labelPersonRow': {
        return (
          <LabelPersonRow
            key={key}
            labelValue={formData.label || ''}
            onLabelChange={(v) => updateField('label', v)}
            personValue={formData.personId || ''}
            onPersonChange={(v) => updateField('personId', v)}
            labelPlaceholder={fieldConfig.labelPlaceholder}
            personPlaceholder={fieldConfig.personPlaceholder}
          />
        );
      }

      case 'iterationCount': {
        return (
          <IterationCountField
            key={key}
            value={formData[fieldConfig.name] || 1}
            onChange={(v) => updateField(fieldConfig.name, v)}
            min={fieldConfig.min}
            max={fieldConfig.max}
            label={fieldConfig.label}
            className={fieldConfig.className}
          />
        );
      }

      case 'personSelect': {
        return (
          <PersonSelectionField
            key={key}
            value={formData[fieldConfig.name] || ''}
            onChange={(v) => updateField(fieldConfig.name, v)}
            placeholder={fieldConfig.placeholder}
            className={fieldConfig.className}
          />
        );
      }

      case 'row': {
        return (
          <FormRow key={key} className={fieldConfig.className}>
            {fieldConfig.fields.map((field, fieldIndex) => renderField(field, fieldIndex))}
          </FormRow>
        );
      }

      case 'custom': {
        // For complex custom components
        const CustomComponent = fieldConfig.component;
        return (
          <CustomComponent
            key={key}
            formData={formData}
            handleChange={updateField}
            {...fieldConfig.props}
          />
        );
      }

      default:
        console.warn(`Unknown field type: ${(fieldConfig as any).type}`);
        return null;
    }
  };

  // Render based on layout
  if (config.layout === 'single') {
    return (
      <Form>
        <SingleColumnPanelLayout>
          {config.fields?.map((field, index) => renderField(field, index))}
        </SingleColumnPanelLayout>
      </Form>
    );
  }

  return (
    <Form>
      <TwoColumnPanelLayout
        leftColumn={
          <>{config.leftColumn?.map((field, index) => renderField(field, index))}</>
        }
        rightColumn={
          <>{config.rightColumn?.map((field, index) => renderField(field, index))}</>
        }
      />
    </Form>
  );
};