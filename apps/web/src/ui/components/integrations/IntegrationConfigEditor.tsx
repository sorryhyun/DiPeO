/**
 * Dynamic configuration editor for API integrations
 */

import React, { useCallback, useMemo } from 'react';
import { OperationSchema } from '@/domain/integrations/hooks';

export interface IntegrationConfigEditorProps {
  schema: OperationSchema;
  value: any;
  onChange: (value: any) => void;
  readOnly?: boolean;
}

/**
 * Renders a dynamic form based on operation schema
 */
export const IntegrationConfigEditor: React.FC<IntegrationConfigEditorProps> = ({
  schema,
  value,
  onChange,
  readOnly = false,
}) => {
  // Parse schema to extract fields
  const fields = useMemo(() => {
    const extractedFields: Array<{
      name: string;
      type: string;
      required: boolean;
      description?: string;
      default?: any;
      enum?: string[];
    }> = [];

    // Parse request body schema if available
    if (schema.request_body) {
      try {
        const bodySchema = typeof schema.request_body === 'string' 
          ? JSON.parse(schema.request_body) 
          : schema.request_body;
        
        if (bodySchema.properties) {
          Object.entries(bodySchema.properties).forEach(([key, prop]: [string, any]) => {
            extractedFields.push({
              name: key,
              type: prop.type || 'string',
              required: bodySchema.required?.includes(key) || false,
              description: prop.description,
              default: prop.default,
              enum: prop.enum,
            });
          });
        }
      } catch (e) {
        console.error('Failed to parse request body schema:', e);
      }
    }

    // Parse query params schema if available
    if (schema.query_params) {
      try {
        const querySchema = typeof schema.query_params === 'string'
          ? JSON.parse(schema.query_params)
          : schema.query_params;
        
        if (querySchema.properties) {
          Object.entries(querySchema.properties).forEach(([key, prop]: [string, any]) => {
            // Avoid duplicates
            if (!extractedFields.find(f => f.name === key)) {
              extractedFields.push({
                name: key,
                type: prop.type || 'string',
                required: querySchema.required?.includes(key) || false,
                description: prop.description,
                default: prop.default,
                enum: prop.enum,
              });
            }
          });
        }
      } catch (e) {
        console.error('Failed to parse query params schema:', e);
      }
    }

    // If no schema is available, provide a generic JSON editor
    if (extractedFields.length === 0) {
      extractedFields.push({
        name: '_raw',
        type: 'object',
        required: false,
        description: 'Raw configuration (JSON format)',
      });
    }

    return extractedFields;
  }, [schema]);

  // Handle field value change
  const handleFieldChange = useCallback((fieldName: string, fieldValue: any) => {
    if (fieldName === '_raw') {
      onChange(fieldValue);
    } else {
      onChange({
        ...value,
        [fieldName]: fieldValue,
      });
    }
  }, [value, onChange]);

  // Render field based on type
  const renderField = (field: typeof fields[0]) => {
    const fieldValue = field.name === '_raw' ? value : value[field.name] ?? field.default ?? '';

    // Enum field (dropdown)
    if (field.enum && field.enum.length > 0) {
      return (
        <select
          value={fieldValue}
          onChange={(e) => handleFieldChange(field.name, e.target.value)}
          disabled={readOnly}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select...</option>
          {field.enum.map(option => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      );
    }

    // Boolean field (checkbox)
    if (field.type === 'boolean') {
      return (
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={fieldValue === true}
            onChange={(e) => handleFieldChange(field.name, e.target.checked)}
            disabled={readOnly}
            className="mr-2"
          />
          <span className="text-sm">{field.description || 'Enabled'}</span>
        </label>
      );
    }

    // Number field
    if (field.type === 'number' || field.type === 'integer') {
      return (
        <input
          type="number"
          value={fieldValue}
          onChange={(e) => handleFieldChange(field.name, e.target.valueAsNumber)}
          disabled={readOnly}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder={field.description}
        />
      );
    }

    // Array or object field (JSON editor)
    if (field.type === 'array' || field.type === 'object' || field.name === '_raw') {
      return (
        <textarea
          value={typeof fieldValue === 'string' ? fieldValue : JSON.stringify(fieldValue, null, 2)}
          onChange={(e) => {
            try {
              const parsed = JSON.parse(e.target.value);
              handleFieldChange(field.name, parsed);
            } catch {
              // Keep as string if not valid JSON
              handleFieldChange(field.name, e.target.value);
            }
          }}
          disabled={readOnly}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
          rows={6}
          placeholder={field.description || 'Enter JSON...'}
        />
      );
    }

    // Default: text field
    return (
      <input
        type="text"
        value={fieldValue}
        onChange={(e) => handleFieldChange(field.name, e.target.value)}
        disabled={readOnly}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        placeholder={field.description}
      />
    );
  };

  return (
    <div className="space-y-3">
      {fields.map((field) => (
        <div key={field.name}>
          {field.name !== '_raw' && (
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {field.name}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          {renderField(field)}
          {field.description && field.name !== '_raw' && (
            <p className="mt-1 text-xs text-gray-500">{field.description}</p>
          )}
        </div>
      ))}

      {/* Show raw JSON preview */}
      {fields.length > 1 && fields[0].name !== '_raw' && (
        <details className="border-t pt-3">
          <summary className="cursor-pointer text-sm font-medium text-gray-600">
            View Raw JSON
          </summary>
          <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-auto">
            {JSON.stringify(value, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
};