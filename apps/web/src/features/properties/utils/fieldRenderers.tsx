import React from 'react';
import { Switch } from '@/shared/components';
import {
  FormField, TextAreaField,
  InlineTextField, InlineSelectField
} from '../wrappers';

type FieldConfig = {
  name: string;
  label: string;
  type: string;
  placeholder?: string;
  options?: Array<{ value: string; label: string }>;
  rows?: number;
  hint?: string;
};

type RenderContext<T = Record<string, unknown>> = {
  persons: Array<{ id: string; label: string }>;
  data: T;
};

// Render inline fields (for horizontal layout)
export const renderInlineField = (
  field: FieldConfig,
  formData: Record<string, unknown>,
  handleChange: (name: string, value: unknown) => void,
  context: RenderContext
): React.ReactNode => {
  const { name, label, type, placeholder, options } = field;
  const value = formData[name];

  // Special handling for person selection - populate dynamic options
  if (name === 'personId') {
    const personOptions = context.persons.map(p => ({ value: p.id, label: p.label }));
    return (
      <InlineSelectField
        key={name}
        label={label}
        value={String(value || '')}
        onChange={(v) => handleChange(name, v || undefined)}
        options={personOptions}
        placeholder={placeholder || "Select person"}
      />
    );
  }

  switch (type) {
    case 'text':
      return (
        <InlineTextField
          key={name}
          label={label}
          value={String(value || '')}
          onChange={(v) => handleChange(name, v)}
          placeholder={placeholder}
        />
      );
      
    case 'number':
      return (
        <InlineTextField
          key={name}
          label={label}
          value={String(value || '')}
          onChange={(v) => handleChange(name, parseInt(v) || undefined)}
          placeholder={placeholder}
        />
      );
      
    case 'select':
      return (
        <InlineSelectField
          key={name}
          label={label}
          value={String(value || '')}
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

// Render textarea fields (for right column)
export const renderTextAreaField = (
  field: FieldConfig,
  formData: Record<string, unknown>,
  handleChange: (name: string, value: unknown) => void,
  _context: RenderContext
): React.ReactNode => {
  const { name, label, placeholder, rows, hint } = field;
  const value = formData[name];

  return (
    <TextAreaField
      key={name}
      label={label}
      value={String(value || '')}
      onChange={(v) => handleChange(name, v)}
      rows={rows || 3}
      placeholder={placeholder}
      hint={hint}
    />
  );
};

// Helper function to determine if field should be in right column
export const isTextAreaField = (field: FieldConfig): boolean => {
  return field.type === 'textarea';
};

