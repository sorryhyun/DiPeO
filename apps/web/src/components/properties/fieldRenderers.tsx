import React from 'react';
import { Switch } from '@repo/ui-kit';
import {
  FormField, TextField, SelectField, TextAreaField
} from '@repo/properties-ui';

type FieldConfig = {
  name: string;
  label: string;
  type: string;
  placeholder?: string;
  options?: Array<{ value: string; label: string }>;
  rows?: number;
  hint?: string;
};

type RenderContext = {
  persons: Array<{ id: string; label: string }>;
  data: any;
};

export const renderField = (
  field: FieldConfig,
  formData: Record<string, any>,
  handleChange: (name: string, value: any) => void,
  context: RenderContext
): React.ReactNode => {
  const { name, label, type, placeholder, options, rows, hint } = field;
  const value = formData[name];

  // Special handling for person selection - populate dynamic options
  if (name === 'personId') {
    const personOptions = context.persons.map(p => ({ value: p.id, label: p.label }));
    return (
      <SelectField
        key={name}
        label={label}
        value={value || ''}
        onChange={(v) => handleChange(name, v || undefined)}
        options={personOptions}
        placeholder={placeholder || "Select person"}
      />
    );
  }

  switch (type) {
    case 'text':
      return (
        <TextField
          key={name}
          label={label}
          value={value || ''}
          onChange={(v) => handleChange(name, v)}
          placeholder={placeholder}
        />
      );
      
    case 'number':
      return (
        <TextField
          key={name}
          label={label}
          value={String(value || '')}
          onChange={(v) => handleChange(name, parseInt(v) || undefined)}
          placeholder={placeholder}
        />
      );
      
    case 'textarea':
      return (
        <TextAreaField
          key={name}
          label={label}
          value={value || ''}
          onChange={(v) => handleChange(name, v)}
          rows={rows || 3}
          placeholder={placeholder}
          hint={hint}
        />
      );
      
    case 'select':
      return (
        <SelectField
          key={name}
          label={label}
          value={value || ''}
          onChange={(v) => handleChange(name, v)}
          options={options || []}
          placeholder={placeholder}
        />
      );
      
    case 'checkbox':
      return (
        <FormField key={name} label={label}>
          <Switch
            checked={!!value}
            onChange={(checked: boolean) => handleChange(name, checked)}
          />
        </FormField>
      );
      
    default:
      return null;
  }
};