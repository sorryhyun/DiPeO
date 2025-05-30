import React from 'react';
import { toast } from 'sonner';
import { Input } from '@repo/ui-kit';
import { createErrorHandlerFactory, type JobBlockData } from '@repo/core-model';
import { usePropertyPanel } from '../hooks/usePropertyPanel';
import { useApiKeys } from '../hooks/useApiKeys';
import {
  Form, FormField, FormRow,
  InlineTextField, InlineSelectField, TextAreaField, SelectField
} from '@repo/properties-ui';

export const JobPanelContent: React.FC<{ nodeId: string; data: JobBlockData }> = ({ nodeId, data }) => {
  const { formData, handleChange } = usePropertyPanel<JobBlockData>(nodeId, 'node', data);
  
  // Use shared API keys hook
  const { apiKeysList, loading: loadingApiKeys } = useApiKeys();

  const jobTypeOptions = [
    { value: 'code', label: 'Code Execution' },
    { value: 'api_tool', label: 'API Tool' },
    { value: 'diagram_link', label: 'Diagram Link' }
  ];

  // Parse API config if subType is api_tool
  const apiConfig = formData.subType === 'api_tool' && formData.sourceDetails
    ? (() => {
        try {
          return JSON.parse(formData.sourceDetails);
        } catch {
          return {};
        }
      })()
    : {};

  const handleApiConfigChange = (field: string, value: any) => {
    const newConfig = { ...apiConfig, [field]: value };
    handleChange('sourceDetails', JSON.stringify(newConfig, null, 2));
  };

  const apiTypeOptions = [
    { value: 'notion', label: 'Notion' },
    { value: 'slack', label: 'Slack (Coming Soon)' },
    { value: 'web_search', label: 'Web Search' },
    { value: 'github', label: 'GitHub (Coming Soon)' }
  ];

  const notionActionOptions = [
    { value: 'query_database', label: 'Query Database' },
    { value: 'create_page', label: 'Create Page' },
    { value: 'update_page', label: 'Update Page' },
    { value: 'search', label: 'Search' }
  ];

  return (
    <Form>
      <FormRow>
        <InlineTextField
          label="Label"
          value={formData.label || ''}
          onChange={(v) => handleChange('label', v)}
          placeholder="Job"
          className="flex-1"
        />
        <InlineSelectField
          label="Type"
          value={formData.subType || 'code'}
          onChange={(v) => handleChange('subType', v as any)}
          options={jobTypeOptions}
          className="flex-1"
        />
      </FormRow>

      {formData.subType === 'api_tool' ? (
        <>
          <FormRow>
            <InlineSelectField
              label="API Type"
              value={apiConfig.apiType || 'notion'}
              onChange={(v) => handleApiConfigChange('apiType', v)}
              options={apiTypeOptions}
              className="flex-1"
            />
            {apiConfig.apiType === 'notion' && (
              <InlineSelectField
                label="Action"
                value={apiConfig.action || 'query_database'}
                onChange={(v) => handleApiConfigChange('action', v)}
                options={notionActionOptions}
                className="flex-1"
              />
            )}
          </FormRow>

          {apiConfig.apiType === 'notion' && (
            <>
              {(apiConfig.action === 'query_database' || apiConfig.action === 'create_page') && (
                <FormField label="Database ID">
                  <Input
                    type="text"
                    value={apiConfig.databaseId || ''}
                    onChange={(e) => handleApiConfigChange('databaseId', e.target.value)}
                    placeholder="Enter Notion database ID"
                  />
                  <p className="text-xs text-gray-500 mt-1">The ID of the Notion database to query or add pages to</p>
                </FormField>
              )}

              {apiConfig.action === 'update_page' && (
                <FormField label="Page ID">
                  <Input
                    type="text"
                    value={apiConfig.pageId || ''}
                    onChange={(e) => handleApiConfigChange('pageId', e.target.value)}
                    placeholder="Enter Notion page ID"
                  />
                  <p className="text-xs text-gray-500 mt-1">The ID of the Notion page to update</p>
                </FormField>
              )}

              {apiConfig.action === 'search' && (
                <FormField label="Search Query">
                  <Input
                    type="text"
                    value={apiConfig.query || ''}
                    onChange={(e) => handleApiConfigChange('query', e.target.value)}
                    placeholder="Enter search query"
                  />
                  <p className="text-xs text-gray-500 mt-1">Query to search in Notion</p>
                </FormField>
              )}

              {(apiConfig.action === 'create_page' || apiConfig.action === 'update_page') && (
                <TextAreaField
                  label="Properties (JSON)"
                  value={apiConfig.properties ? JSON.stringify(apiConfig.properties, null, 2) : ''}
                  onChange={(v) => {
                    try {
                      const parsed = JSON.parse(v);
                      handleApiConfigChange('properties', parsed);
                    } catch {
                      // Invalid JSON, store as-is for now
                      handleApiConfigChange('properties', v);
                    }
                  }}
                  placeholder={'{\n  "Name": {\n    "title": [{"text": {"content": "Page Title"}}]\n  }\n}'}
                  rows={6}
                  hint="Notion page properties in JSON format"
                />
              )}

              {apiConfig.action === 'query_database' && (
                <>
                  <TextAreaField
                    label="Filter (JSON)"
                    value={apiConfig.filter ? JSON.stringify(apiConfig.filter, null, 2) : ''}
                    onChange={(v) => {
                      try {
                        const parsed = v ? JSON.parse(v) : null;
                        handleApiConfigChange('filter', parsed);
                      } catch {
                        // Invalid JSON, store as-is for now
                        handleApiConfigChange('filter', v);
                      }
                    }}
                    placeholder={'{\n  "property": "Status",\n  "select": {\n    "equals": "Done"\n  }\n}'}
                    rows={4}
                    hint="Optional Notion filter object"
                  />
                  <TextAreaField
                    label="Sorts (JSON)"
                    value={apiConfig.sorts ? JSON.stringify(apiConfig.sorts, null, 2) : ''}
                    onChange={(v) => {
                      try {
                        const parsed = v ? JSON.parse(v) : null;
                        handleApiConfigChange('sorts', parsed);
                      } catch {
                        // Invalid JSON, store as-is for now
                        handleApiConfigChange('sorts', v);
                      }
                    }}
                    placeholder={'[\n  {\n    "property": "Created",\n    "direction": "descending"\n  }\n]'}
                    rows={3}
                    hint="Optional array of sort objects"
                  />
                </>
              )}
            </>
          )}

          {apiConfig.apiType === 'web_search' && (
            <>
              <FormRow>
                <InlineSelectField
                  label="Search Provider"
                  value={apiConfig.provider || 'serper'}
                  onChange={(v) => handleApiConfigChange('provider', v)}
                  options={[
                    { value: 'serper', label: 'Serper (Google)' },
                    { value: 'bing', label: 'Bing Search' },
                  ]}
                  className="flex-1"
                />
                <InlineTextField
                  label="Results"
                  value={String(apiConfig.numResults || 10)}
                  onChange={(v) => handleApiConfigChange('numResults', parseInt(v) || 10)}
                  placeholder="10"
                  className="w-24"
                />
              </FormRow>

              <FormField label="Search Query">
                <Input
                  type="text"
                  value={apiConfig.query || ''}
                  onChange={(e) => handleApiConfigChange('query', e.target.value)}
                  placeholder="Enter search query or use input from previous node"
                />
              </FormField>

              <SelectField
                label="Output Format"
                value={apiConfig.outputFormat || 'full'}
                onChange={(v) => handleApiConfigChange('outputFormat', v)}
                options={[
                  { value: 'full', label: 'Full Results (JSON)' },
                  { value: 'urls_only', label: 'URLs Only (Array)' },
                  { value: 'snippets', label: 'Title + Snippets' },
                ]}
              />

              <SelectField
                label="API Key"
                value={apiConfig.apiKeyId || ''}
                onChange={(v) => handleApiConfigChange('apiKeyId', v)}
                options={apiKeysList
                  .filter(k => k.service === 'custom')
                  .map(k => ({ value: k.id, label: k.name }))}
                placeholder="Select API Key for Web Search"
                loading={loadingApiKeys}
              />
            </>
          )}
          {apiConfig.apiType !== 'notion' && apiConfig.apiType !== 'web_search' && (
            <div className="text-sm text-gray-500 p-4 bg-gray-50 rounded">
              {apiConfig.apiType} integration coming soon...
            </div>
          )}
        </>
      ) : (
        <TextAreaField
          label="Details"
          value={formData.sourceDetails || ''}
          onChange={(v) => handleChange('sourceDetails', v)}
          placeholder={
            formData.subType === 'code' ? 'Enter Python code...' :
            formData.subType === 'diagram_link' ? 'Enter diagram path...' :
            'Enter details...'
          }
          rows={8}
          hint={
            formData.subType === 'code' ? 'Python code to execute. Available variables from incoming edges.' :
            formData.subType === 'diagram_link' ? 'Path to linked diagram file.' :
            undefined
          }
        />
      )}
    </Form>
  );
};