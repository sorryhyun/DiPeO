import React from 'react';
import { Switch, Input, Select } from '@/components';

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
      <div key={name} className="flex items-center gap-2">
        <label className="text-xs font-medium whitespace-nowrap">{label}</label>
        <Select
          value={String(value || '')}
          onValueChange={(v) => handleChange(name, v || undefined)}
        >
          <Select.Trigger>
            <Select.Value placeholder={placeholder || "Select person"} />
          </Select.Trigger>
          <Select.Content>
            {personOptions.map(opt => (
              <Select.Item key={opt.value} value={opt.value}>
                {opt.label}
              </Select.Item>
            ))}
          </Select.Content>
        </Select>
      </div>
    );
  }

  switch (type) {
    case 'text':
      return (
        <div key={name} className="flex items-center gap-2">
          <label className="text-xs font-medium whitespace-nowrap">{label}</label>
          <Input
            value={String(value || '')}
            onChange={(e) => handleChange(name, e.target.value)}
            placeholder={placeholder}
          />
        </div>
      );
      
    case 'number':
      return (
        <div key={name} className="flex items-center gap-2">
          <label className="text-xs font-medium whitespace-nowrap">{label}</label>
          <Input
            type="number"
            value={String(value || '')}
            onChange={(e) => handleChange(name, parseInt(e.target.value) || undefined)}
            placeholder={placeholder}
          />
        </div>
      );
      
    case 'select':
      return (
        <div key={name} className="flex items-center gap-2">
          <label className="text-xs font-medium whitespace-nowrap">{label}</label>
          <Select
            value={String(value || '')}
            onValueChange={(v) => handleChange(name, v)}
          >
            <Select.Trigger>
              <Select.Value placeholder={placeholder} />
            </Select.Trigger>
            <Select.Content>
              {(options || []).map(opt => (
                <Select.Item key={opt.value} value={opt.value}>
                  {opt.label}
                </Select.Item>
              ))}
            </Select.Content>
          </Select>
        </div>
      );
      
    case 'checkbox':
      return (
        <div key={name} className="space-y-1">
          <label htmlFor={name} className="text-xs font-medium">{label}</label>
          <Switch
            id={name}
            checked={!!value}
            onChange={(checked: boolean) => handleChange(name, checked)}
          />
        </div>
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
    <div key={name} className="space-y-1">
      <label htmlFor={name} className="text-xs font-medium">{label}</label>
      <textarea
        id={name}
        value={String(value || '')}
        onChange={(e) => handleChange(name, e.target.value)}
        rows={rows || 3}
        placeholder={placeholder}
        className="flex w-full rounded-md border border-slate-300 bg-transparent py-1.5 px-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
      />
      {hint && <p className="text-xs text-gray-600">{hint}</p>}
    </div>
  );
};

// Helper function to determine if field should be in right column
export const isTextAreaField = (field: FieldConfig): boolean => {
  return field.type === 'textarea';
};

