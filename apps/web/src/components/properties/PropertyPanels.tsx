import React, { useState, useEffect } from 'react';
import { useConsolidatedDiagramStore } from '@/stores';
import { usePropertyForm as usePropertyFormBase } from '@repo/diagram-ui';
import { toast } from 'sonner';
import {
  UserCheckIcon, GitBranchIcon, DatabaseIcon, ArrowRightIcon,
  UserIcon, FlagIcon, Settings
} from 'lucide-react';
import {
  Input, Spinner, Switch
} from '@repo/ui-kit';
import type {
  PersonJobBlockData, ConditionBlockData, DBBlockData,
  ArrowData, PersonDefinition, EndpointBlockData, ApiKey, JobBlockData,
} from '@repo/core-model';
import { UNIFIED_NODE_CONFIGS } from '@repo/core-model';
import { usePersons } from '@/hooks/useStoreSelectors';

// Import reusable components from properties-ui package
import {
  Panel, Form, FormField, FormGrid,
  TextField, SelectField, TextAreaField,
  FormRow, InlineTextField, InlineSelectField
} from '@repo/properties-ui';

// Create a wrapper that connects to the store
function usePropertyForm<T extends Record<string, any>>(
  nodeId: string,
  initialData: T
) {
  const updateNodeData = useConsolidatedDiagramStore(state => state.updateNodeData);
  return usePropertyFormBase(initialData, (updates) => {
    updateNodeData(nodeId, updates);
  });
}

// Universal Properties Panel - replaces all individual panels
export const UniversalPropertiesPanel: React.FC<{ nodeId: string; data: any }> = ({ nodeId, data }) => {
  const nodeType = data.type;
  const config = UNIFIED_NODE_CONFIGS[nodeType];
  const { persons } = usePersons();
  const { formData, handleChange } = usePropertyForm(nodeId, data);
  
  if (!config) {
    return (
      <Panel icon={<Settings className="w-5 h-5" />} title="Unknown Node Type">
        <div className="text-red-500">No configuration found for node type: {nodeType}</div>
      </Panel>
    );
  }

  const renderField = (field: any) => {
    const { name, label, type, placeholder, options, rows, hint } = field;
    const value = formData[name];

    // Special handling for person selection - populate dynamic options
    if (name === 'personId') {
      const personOptions = persons.map(p => ({ value: p.id, label: p.label }));
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

  return (
    <Panel icon={<span>{config.emoji}</span>} title={config.propertyTitle}>
      <Form>
        <div className="space-y-4">
          {config.propertyFields.map(renderField)}
        </div>
      </Form>
    </Panel>
  );
};

// ===== Panel Configurations =====
type PanelConfig = {
  [key: string]: {
    icon: React.ReactNode;
    title: string;
    render: (props: any) => React.ReactNode;
  };
};

const PANEL_CONFIGS: PanelConfig = {
  personJob: {
    icon: <UserCheckIcon className="w-5 h-5" />,
    title: "Person Job Properties",
    render: ({ nodeId, data }: { nodeId: string; data: PersonJobBlockData }) => {
      const { persons } = usePersons();
      const { formData, handleChange } = usePropertyForm<PersonJobBlockData>(nodeId, data);

      const modeOptions = [
        { value: 'sync', label: 'Sync' },
        { value: 'batch', label: 'Batch' }
      ];

      const forgetOptions = [
        { value: 'upon_request', label: 'Upon This Request' },
        { value: 'no_forget', label: 'Do Not Forget' },
        { value: 'on_every_turn', label: 'On Every Turn' }
      ];

      const personOptions = persons.map(p => ({ value: p.id, label: p.label }));

      return (
        <Form>
          <div className="grid grid-cols-2 gap-4">
            {/* Left column - Option properties */}
            <div className="space-y-4">
              <FormRow>
                <InlineTextField
                  label="Label"
                  value={formData.label || ''}
                  onChange={(v) => handleChange('label', v)}
                  placeholder="Person Job"
                  className="flex-1"
                />
                <InlineSelectField
                  label="Person"
                  value={formData.personId || ''}
                  onChange={(v) => handleChange('personId', v || undefined)}
                  options={personOptions}
                  placeholder="None"
                  className="flex-1"
                />
              </FormRow>

              <FormRow>
                <InlineSelectField
                  label="Mode"
                  value={formData.mode || 'sync'}
                  onChange={(v) => handleChange('mode', v as any)}
                  options={modeOptions}
                  className="flex-1"
                />
                <InlineSelectField
                  label="Forget"
                  value={formData.contextCleaningRule || 'upon_request'}
                  onChange={(v) => handleChange('contextCleaningRule', v as any)}
                  options={forgetOptions}
                  className="flex-1"
                />
                <InlineTextField
                  label="Max Iter"
                  value={String(formData.iterationCount || 1)}
                  onChange={(v) => handleChange('iterationCount', parseInt(v) || 1)}
                  placeholder="1"
                  className="w-24"
                />
              </FormRow>
            </div>

            {/* Right column - Text properties */}
            <div className="space-y-4">
              <TextAreaField
                label="Default Prompt"
                value={formData.defaultPrompt || ''}
                onChange={(v) => handleChange('defaultPrompt', v)}
                rows={6}
                placeholder="Enter default prompt. Use {{variable_name}} for variables."
                hint={data.detectedVariables?.length ?
                  `Detected variables: ${data.detectedVariables.map(v => `{{${v}}}`).join(', ')}` :
                  undefined}
              />

              <TextAreaField
                label="First-Only Prompt"
                value={formData.firstOnlyPrompt || ''}
                onChange={(v) => handleChange('firstOnlyPrompt', v)}
                rows={4}
                placeholder="Prompt to use only on first execution."
              />
            </div>
          </div>
        </Form>
      );
    }
  },

  condition: {
    icon: <GitBranchIcon className="w-5 h-5" />,
    title: "Condition Properties",
    render: ({ nodeId, data }: { nodeId: string; data: ConditionBlockData }) => {
      const { formData, handleChange } = usePropertyForm<ConditionBlockData>(nodeId, data);
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
    }
  },

  db: {
    icon: <DatabaseIcon className="w-5 h-5" />,
    title: "Database Properties",
    render: ({ nodeId, data }: { nodeId: string; data: DBBlockData }) => {
      const { formData, handleChange } = usePropertyForm<DBBlockData>(nodeId, data);
      const [uploading, setUploading] = useState(false);

      const dbTypeOptions = [
        { value: 'fixed_prompt', label: 'Fixed Prompt' },
        { value: 'file', label: 'File' }
      ];

      const handleFileUpload = async (file: File) => {
        // File upload logic (extracted for brevity)
        setUploading(true);
        try {
          const form = new FormData();
          form.append('file', file);
          const res = await fetch('/api/upload-file', { method: 'POST', body: form });
          if (!res.ok) throw new Error('Upload failed');
          const { path } = await res.json();
          handleChange('sourceDetails', path);
          toast.success(`File uploaded: ${file.name}`);
        } catch (error) {
          toast.error('Upload failed');
        } finally {
          setUploading(false);
        }
      };

      return (
        <Form>
          <div className="grid grid-cols-2 gap-4">
            {/* Left column - Option properties */}
            <div className="space-y-4">
              <FormRow>
                <InlineTextField
                  label="Label"
                  value={formData.label || ''}
                  onChange={(v) => handleChange('label', v)}
                  placeholder="Database"
                  className="flex-1"
                />
                <InlineSelectField
                  label="Source Type"
                  value={formData.subType || 'fixed_prompt'}
                  onChange={(v) => handleChange('subType', v as any)}
                  options={dbTypeOptions}
                  className="flex-1"
                />
              </FormRow>
            </div>

            {/* Right column - Text properties */}
            <div className="space-y-4">
              {formData.subType === 'file' ? (
                <FormField label="File Path">
                  <Input
                    type="text"
                    value={formData.sourceDetails || ''}
                    placeholder="Or upload a file below"
                    onChange={(e) => handleChange('sourceDetails', e.target.value)}
                  />
                  <Input
                    type="file"
                    accept=".txt,.docx,.doc,.pdf,.csv,.json"
                    className="mt-2"
                    disabled={uploading}
                    onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                  />
                  {uploading && (
                    <div className="flex items-center mt-2 text-sm text-gray-600">
                      <Spinner size="sm" className="mr-2" />
                      <span>Uploading...</span>
                    </div>
                  )}
                </FormField>
              ) : (
                <TextAreaField
                  label="Prompt Content"
                  value={formData.sourceDetails || ''}
                  onChange={(v) => handleChange('sourceDetails', v)}
                  placeholder="Enter your prompt content"
                  rows={5}
                  hint="Enter the fixed prompt text that will be used by this database block"
                />
              )}
            </div>
          </div>
        </Form>
      );
    }
  },

  arrow: {
    icon: <ArrowRightIcon className="w-5 h-5" />,
    title: "Arrow Properties",
    render: ({ arrowId, data }: { arrowId: string; data: ArrowData }) => {
      const { updateArrowData, arrows, nodes } = useConsolidatedDiagramStore();
      const { formData, handleChange: updateForm } = usePropertyForm<ArrowData>(arrowId, data);

      const arrow = arrows.find(e => e.id === arrowId);
      const sourceNode = arrow ? nodes.find(n => n.id === arrow.source) : null;
      const isFromConditionNode = sourceNode?.type === 'conditionNode';
      const fixed = data.edgeKind === 'fixed';

      const handleChange = (field: keyof ArrowData, value: any) => {
        if (field === 'label' && formData.contentType === 'raw_text') {
          updateForm('label', value);
          updateForm('variableName', value);
          updateArrowData(arrowId, { label: value, variableName: value });
        } else {
          updateForm(field, value);
          updateArrowData(arrowId, { [field]: value });
        }
      };

      const contentTypeOptions = [
        ...(!fixed ? [
          { value: 'raw_text', label: 'Raw Text' },
          { value: 'variable_in_object', label: 'Variable in Object' }
        ] : []),
        { value: 'conversation_state', label: 'Conversation State' }
      ];

      return (
        <Form>
          <FormGrid columns={2}>
            <TextField
              label="Arrow Label"
              value={formData.label || ''}
              onChange={(v) => handleChange('label', v)}
              placeholder="e.g., user_query"
            />
            {!isFromConditionNode && (
              <SelectField
                label="Content Type"
                value={formData.contentType || (fixed ? 'whole' : 'raw_text')}
                onChange={(v) => handleChange('contentType', v as any)}
                options={contentTypeOptions}
                disabled={fixed}
              />
            )}
          </FormGrid>

          {formData.contentType === 'variable_in_object' && !isFromConditionNode && (
            <TextField
              label="Object Key Path"
              value={formData.objectKeyPath || ''}
              onChange={(v) => handleChange('objectKeyPath', v)}
              placeholder="e.g., user.name or data.items[0].value"
            />
          )}

          {data.sourceBlockId === data.targetBlockId && (
            <FormField label="Loop Radius">
              <Input
                type="number"
                min={10}
                value={formData.loopRadius ?? 30}
                onChange={(e) => handleChange('loopRadius', e.target.valueAsNumber)}
              />
            </FormField>
          )}
        </Form>
      );
    }
  },

  person: {
    icon: <UserIcon className="w-5 h-5" />,
    title: "Person Properties",
    render: ({ personId, data }: { personId: string; data: PersonDefinition }) => {
      const { updatePerson } = useConsolidatedDiagramStore();
      const { formData, handleChange: updateData } = usePropertyForm<PersonDefinition>(personId, data);

      // API Keys state
      const [apiKeysList, setApiKeysList] = useState<ApiKey[]>([]);
      const [loadingApiKeys, setLoadingApiKeys] = useState(false);
      const [apiKeysError, setApiKeysError] = useState<string | null>(null);

      // Models state
      const [modelOptions, setModelOptions] = useState<{ value: string; label: string }[]>([]);
      const [loadingModels, setLoadingModels] = useState(false);
      const [modelError, setModelError] = useState<string | null>(null);

      // Effects for loading data
      useEffect(() => {
        const fetchApiKeys = async () => {
          setLoadingApiKeys(true);
          try {
            const res = await fetch('/api/apikeys');
            if (!res.ok) throw new Error('Failed to load API keys');
            const body = await res.json();
            setApiKeysList(body.apiKeys);
          } catch (err) {
            setApiKeysError(err instanceof Error ? err.message : 'Failed to load API keys');
          } finally {
            setLoadingApiKeys(false);
          }
        };
        fetchApiKeys();
      }, []);

      useEffect(() => {
        if (!formData.service || !formData.apiKeyId) {
          setModelOptions([]);
          return;
        }
        setLoadingModels(true);
        fetch(`/api/models?service=${formData.service}&apiKeyId=${formData.apiKeyId}`)
          .then(res => res.json())
          .then(body => setModelOptions(body.models.map((m: string) => ({ value: m, label: m }))))
          .catch(err => setModelError(err.message))
          .finally(() => setLoadingModels(false));
      }, [formData.service, formData.apiKeyId]);

      const handleChange = (field: keyof PersonDefinition, value: any) => {
        updateData(field, value);
        updatePerson(personId, { [field]: value });
      };

      const serviceOptions = [
        { value: 'chatgpt', label: 'ChatGPT' },
        { value: 'claude', label: 'Claude' },
        { value: 'gemini', label: 'Gemini' },
        { value: 'grok', label: 'Grok' },
        { value: 'custom', label: 'Custom' }
      ];

      const apiKeyOptions = apiKeysList
        .filter(k => k.service === formData.service)
        .map(key => ({ value: key.id, label: key.name }));

      return (
        <Form>
          <FormGrid columns={2}>
            <TextField
              label="Person Name"
              value={formData.label || ''}
              onChange={(v) => handleChange('label', v)}
              placeholder="Person Name"
            />
            <SelectField
              label="Service"
              value={formData.service || ''}
              onChange={(v) => handleChange('service', v)}
              options={serviceOptions}
            />
            <SelectField
              label="API Key"
              value={formData.apiKeyId || ''}
              onChange={(v) => handleChange('apiKeyId', v)}
              options={apiKeyOptions}
              placeholder="Select API Key"
              loading={loadingApiKeys}
              error={apiKeysError}
            />
            <SelectField
              label="Model"
              value={formData.modelName || ''}
              onChange={(v) => handleChange('modelName', v)}
              options={modelOptions}
              placeholder="Select Model"
              loading={loadingModels}
              error={modelError}
              disabled={modelOptions.length === 0}
            />
          </FormGrid>

          <TextAreaField
            label="System Prompt"
            value={formData.systemPrompt || ''}
            onChange={(v) => handleChange('systemPrompt', v)}
            placeholder="Enter system prompt"
          />
        </Form>
      );
    }
  },

  endpoint: {
    icon: <FlagIcon className="w-5 h-5" />,
    title: "Endpoint Properties",
    render: ({ nodeId, data }: { nodeId: string; data: EndpointBlockData }) => {
      const { formData, handleChange } = usePropertyForm<EndpointBlockData>(nodeId, data);

      const fileFormatOptions = [
        { value: 'text', label: 'Plain Text' },
        { value: 'json', label: 'JSON' },
        { value: 'csv', label: 'CSV' }
      ];

      return (
        <Form>
          <TextField
            label="Block Label"
            value={formData.label || ''}
            onChange={(v) => handleChange('label', v)}
            placeholder="End"
          />

          <div className="border-t pt-4">
            <FormField label="Save output to file" className="flex items-center space-x-2">
              <Switch
                id="saveToFile"
                checked={formData.saveToFile || false}
                onChange={(checked: boolean) => handleChange('saveToFile', checked)}
              />
            </FormField>

            {formData.saveToFile && (
              <>
                <TextField
                  label="File Path"
                  value={formData.filePath || ''}
                  onChange={(v) => handleChange('filePath', v)}
                  placeholder="results/output.txt"
                />
                <SelectField
                  label="File Format"
                  value={formData.fileFormat || 'text'}
                  onChange={(v) => handleChange('fileFormat', v as any)}
                  options={fileFormatOptions}
                />
              </>
            )}
          </div>
        </Form>
      );
    }
  },

  job: {
    icon: <Settings className="w-5 h-5" />,
    title: "Job Properties",
    render: (props: { nodeId: string; data: JobBlockData }) => <JobPanelContent {...props} />
  }
};

// Job Panel Content Component
const JobPanelContent: React.FC<{ nodeId: string; data: JobBlockData }> = ({ nodeId, data }) => {
      const { formData, handleChange } = usePropertyForm<JobBlockData>(nodeId, data);
      
      // API Keys state for web search
      const [apiKeysList, setApiKeysList] = useState<ApiKey[]>([]);
      const [loadingApiKeys, setLoadingApiKeys] = useState(false);
      
      // Load API keys on mount
      useEffect(() => {
        const fetchApiKeys = async () => {
          setLoadingApiKeys(true);
          try {
            const res = await fetch('/api/apikeys');
            if (!res.ok) throw new Error('Failed to load API keys');
            const body = await res.json();
            setApiKeysList(body.apiKeys);
          } catch (err) {
            console.error('Failed to load API keys:', err);
          } finally {
            setLoadingApiKeys(false);
          }
        };
        fetchApiKeys();
      }, []);

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
              {apiConfig.apiType !== 'notion' && (
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

// Keep only the panels that are still in use
export const ArrowPropertiesPanel: React.FC<{ arrowId: string; data: ArrowData }> = (props) => (
  <Panel {...PANEL_CONFIGS.arrow}>{PANEL_CONFIGS.arrow.render(props)}</Panel>
);

export const PersonPropertiesPanel: React.FC<{ personId: string; data: PersonDefinition }> = (props) => (
  <Panel {...PANEL_CONFIGS.person}>{PANEL_CONFIGS.person.render(props)}</Panel>
);