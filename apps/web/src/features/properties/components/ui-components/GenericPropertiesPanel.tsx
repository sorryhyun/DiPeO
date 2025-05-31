import React, { useState, useEffect } from 'react';
import { Select, SelectItem, Label } from '@/shared/components';
import { Panel } from './Panel';
import { Form, FormField, TextField, TextAreaField } from './FormComponents';
import { GenericPropertiesPanelProps, FieldConfig } from '@/shared/types';

export function GenericPropertiesPanel({ 
  nodeId, 
  nodeType, 
  fields, 
  title,
  icon,
  data = {},
  onChange
}: GenericPropertiesPanelProps) {
  const [formData, setFormData] = useState<Record<string, unknown>>(data);

  useEffect(() => {
    setFormData(data);
  }, [data]);

  const handleChange = (fieldName: string, value: unknown) => {
    const newData = { ...formData, [fieldName]: value };
    setFormData(newData);
    if (onChange) {
      onChange(nodeId, newData);
    }
  };

  const renderField = (field: FieldConfig) => {
    const rawValue = formData[field.name];
    const value = rawValue != null ? String(rawValue) : '';

    switch (field.type) {
      case 'text':
        return (
          <TextField
            key={field.name}
            label={field.label}
            value={value}
            onChange={(v) => handleChange(field.name, v)}
            placeholder={field.placeholder}
            id={field.name}
          />
        );

      case 'number':
        return (
          <FormField key={field.name} label={field.label} id={field.name}>
            <input
              id={field.name}
              type="number"
              value={value}
              onChange={(e) => handleChange(field.name, e.target.value)}
              placeholder={field.placeholder}
              required={field.required}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </FormField>
        );

      case 'textarea':
        return (
          <TextAreaField
            key={field.name}
            label={field.label}
            value={value}
            onChange={(v) => handleChange(field.name, v)}
            placeholder={field.placeholder}
            rows={field.rows || 3}
            id={field.name}
            hint={field.hint}
          />
        );

      case 'select':
        return (
          <FormField key={field.name} label={field.label} id={field.name}>
            <Select
              id={field.name}
              value={value}
              onValueChange={(v) => handleChange(field.name, v)}
            >
              <SelectItem value="">{field.placeholder || `Select ${field.label.toLowerCase()}`}</SelectItem>
              {field.options?.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </Select>
          </FormField>
        );

      case 'checkbox': {
        const isChecked = rawValue === true || rawValue === 'true' || rawValue === '1';
        return (
          <FormField key={field.name} label="" className="flex items-center space-x-2">
            <input
              type="checkbox"
              id={field.name}
              checked={isChecked}
              onChange={(e) => handleChange(field.name, e.target.checked)}
              className="w-4 h-4"
            />
            <Label htmlFor={field.name} className="cursor-pointer">
              {field.label}
            </Label>
          </FormField>
        );
      }

      default:
        return null;
    }
  };

  return (
    <Panel icon={icon} title={title}>
      <Form>
        {fields.map(renderField)}
      </Form>
    </Panel>
  );
}