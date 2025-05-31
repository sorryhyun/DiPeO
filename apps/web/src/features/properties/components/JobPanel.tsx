import React from 'react';
import { type JobBlockData } from '@/shared/types';
import { usePropertyPanel } from '@/features/properties';
import { useApiKeys } from '../hooks/useApiKeys';
import {
  Form,
  TwoColumnPanelLayout,
  FormRow,
  InlineTextField,
  InlineSelectField,
  TextAreaField,
  SelectField,
  TextField
} from './ui-components/FormComponents';

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

  const handleApiConfigChange = (field: string, value: string | number | object | null) => {
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

  const renderBasicFields = () => (
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
        onChange={(v) => handleChange('subType', v as 'code' | 'api_tool' | 'diagram_link')}
        options={jobTypeOptions}
        className="flex-1"
      />
    </FormRow>
  );

  const renderApiTypeFields = () => (
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
  );

  const renderNotionFields = () => {
    if (apiConfig.apiType !== 'notion') return null;

    return (
      <>
        {(apiConfig.action === 'query_database' || apiConfig.action === 'create_page') && (
          <TextField
            label="Database ID"
            value={apiConfig.databaseId || ''}
            onChange={(v) => handleApiConfigChange('databaseId', v)}
            placeholder="Enter Notion database ID"
          />
        )}

        {apiConfig.action === 'update_page' && (
          <TextField
            label="Page ID"
            value={apiConfig.pageId || ''}
            onChange={(v) => handleApiConfigChange('pageId', v)}
            placeholder="Enter Notion page ID"
          />
        )}

        {apiConfig.action === 'search' && (
          <TextField
            label="Search Query"
            value={apiConfig.query || ''}
            onChange={(v) => handleApiConfigChange('query', v)}
            placeholder="Enter search query"
          />
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
    );
  };

  const renderWebSearchFields = () => {
    if (apiConfig.apiType !== 'web_search') return null;

    return (
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

        <TextField
          label="Search Query"
          value={apiConfig.query || ''}
          onChange={(v) => handleApiConfigChange('query', v)}
          placeholder="Enter search query or use input from previous node"
        />

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
    );
  };

  return (
    <Form>
      {renderBasicFields()}

      <TwoColumnPanelLayout
        leftColumn={
          formData.subType === 'api_tool' ? (
            <>
              {renderApiTypeFields()}
              {renderNotionFields()}
              {renderWebSearchFields()}
              {apiConfig.apiType !== 'notion' && apiConfig.apiType !== 'web_search' && (
                <div className="text-sm text-gray-500 p-4 bg-gray-50 rounded">
                  {apiConfig.apiType} integration coming soon...
                </div>
              )}
            </>
          ) : null
        }
        rightColumn={
          formData.subType !== 'api_tool' ? (
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
          ) : null
        }
      />
    </Form>
  );
};