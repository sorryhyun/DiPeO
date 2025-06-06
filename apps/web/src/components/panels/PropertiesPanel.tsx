import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Settings } from 'lucide-react';
import { DiagramNode, Arrow, PersonDefinition, ArrowData, PanelConfig, FieldConfig, PropertyFieldConfig } from '../../types';
import { NODE_CONFIGS } from '../../config/nodes';
import { useNodes, useArrows, usePersons, useSelectedElement } from '../../common/utils/storeSelectors';
import { usePropertyPanel } from '../../features/properties';
import { preInitializeModel } from '../../features/properties/utils/propertyHelpers';
import { UnifiedFieldRenderer } from '../../common/components/forms/UnifiedFieldRenderer';
import { Form, FormRow, SingleColumnPanelLayout, TwoColumnPanelLayout } from '../../common/components/forms/FormComponents';
import {
  endpointConfig,
  personJobConfig,
  conditionConfig,
  dbConfig,
  jobConfig,
  personBatchJobConfig,
  arrowConfig,
  personConfig,
  startConfig,
  userResponseConfig,
  notionConfig
} from '../../features/properties/configs';

type UniversalData = DiagramNode['data'] | (ArrowData & { type: 'arrow' }) | (PersonDefinition & { type: 'person' });

interface PropertiesPanelProps {
  className?: string;
}

const PropertiesPanel: React.FC<PropertiesPanelProps> = ({ className }) => {
  const { nodes } = useNodes();
  const { arrows } = useArrows();
  const { persons } = usePersons();
  const { selectedPersonId, selectedNodeId, selectedArrowId } = useSelectedElement();
  const isMonitorMode = useIsReadOnly();

  // Memoize person data
  const personData = useMemo(() => {
    if (!selectedPersonId) return null;
    const person = persons.find(p => p.id === selectedPersonId);
    if (!person) return null;
    return { ...person, type: 'person' as const };
  }, [selectedPersonId, persons]);

  // Memoize arrow data
  const arrowData = useMemo(() => {
    if (!selectedArrowId) return null;
    const arrow = arrows.find(a => a.id === selectedArrowId);
    if (!arrow || !arrow.data) return null;
    
    const sourceNode = nodes.find(n => n.id === arrow.source);
    const isFromConditionBranch = arrow.sourceHandle === 'true' || arrow.sourceHandle === 'false';
    
    return { 
      ...arrow.data,
      id: arrow.data.id || arrow.id,
      type: 'arrow' as const,
      _sourceNodeType: sourceNode?.data.type,
      _isFromConditionBranch: isFromConditionBranch
    };
  }, [selectedArrowId, arrows, nodes]);

  // Get selected data and metadata
  const { selectedData, selectedType, title } = useMemo(() => {
    if (selectedPersonId && personData) {
      return {
        selectedData: personData,
        selectedType: 'person' as const,
        title: `${personData.label || 'Person'} Properties`
      };
    } else if (selectedNodeId) {
      const node = nodes.find(n => n.id === selectedNodeId);
      if (node) {
        return {
          selectedData: node.data,
          selectedType: 'node' as const,
          title: `${node.data.label || 'Block'} Properties`
        };
      }
    } else if (selectedArrowId && arrowData) {
      return {
        selectedData: arrowData,
        selectedType: 'arrow' as const,
        title: 'Arrow Properties'
      };
    }
    
    return {
      selectedData: null,
      selectedType: null,
      title: 'Properties'
    };
  }, [selectedPersonId, selectedNodeId, selectedArrowId, personData, arrowData, nodes]);

  if (!selectedData) {
    return (
      <div className={`h-full bg-white flex flex-col ${className || ''}`}>
        <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b">
          <span className="text-sm font-medium text-gray-700">Properties</span>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <p className="text-sm text-gray-500">Select a block, arrow, or person to see its properties.</p>
        </div>
      </div>
    );
  }

  const selectedId = selectedPersonId || selectedNodeId || selectedArrowId!;

  return (
    <div className={`h-full bg-white flex flex-col ${className || ''}`}>
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b">
        <span className="text-sm font-medium text-gray-700">Properties</span>
      </div>
      <div className="flex-1 overflow-y-auto">
        <PropertiesContent
          nodeId={selectedId}
          data={selectedData}
          entityType={selectedType!}
          title={title}
        />
      </div>
    </div>
  );
};

interface PropertiesContentProps {
  nodeId: string;
  data: UniversalData;
  entityType: 'node' | 'arrow' | 'person';
  title: string;
}

const PropertiesContent: React.FC<PropertiesContentProps> = ({ nodeId, data, entityType, title }) => {
  const [asyncOptions, setAsyncOptions] = useState<Record<string, Array<{ value: string; label: string }>>>({});
  const prevDepsRef = useRef<{ service?: string; apiKeyId?: string }>({});
  const reloadInProgressRef = useRef(false);
  const isMonitorMode = false; // TODO: Add monitor mode check
  
  const { formData, handleChange } = usePropertyPanel(nodeId, entityType, data as any);
  
  const nodeType = data.type;
  const nodeConfig = nodeType in NODE_CONFIGS ? NODE_CONFIGS[nodeType as keyof typeof NODE_CONFIGS] : undefined;
  
  // Get panel configuration
  const panelConfig = useMemo((): PanelConfig<Record<string, unknown>> | null => {
    switch (nodeType) {
      case 'endpoint':
        return endpointConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'person_job':
        return personJobConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'condition':
        return conditionConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'db':
        return dbConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'job':
        return jobConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'person_batch_job':
        return personBatchJobConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'arrow':
        return arrowConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'person':
        return personConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'start':
        return startConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'user_response':
        return userResponseConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'notion':
        return notionConfig as unknown as PanelConfig<Record<string, unknown>>;
      default:
        return null;
    }
  }, [nodeType]);

  // Load async options for non-dependent fields
  useEffect(() => {
    const loadAsyncOptions = async () => {
      if (!panelConfig) return;
      
      const fieldsToProcess: FieldConfig[] = [];
      
      const collectFields = (fields: any[]) => {
        fields.forEach((field: any) => {
          if (field.type === 'select' && typeof field.options === 'function' && !field.dependsOn) {
            fieldsToProcess.push(field);
          } else if (field.type === 'row' && field.fields) {
            collectFields(field.fields);
          }
        });
      };
      
      if (panelConfig.fields) collectFields(panelConfig.fields);
      if (panelConfig.leftColumn) collectFields(panelConfig.leftColumn);
      if (panelConfig.rightColumn) collectFields(panelConfig.rightColumn);
      
      const optionsMap: Record<string, Array<{ value: string; label: string }>> = {};
      
      for (const field of fieldsToProcess) {
        try {
          if (field.type === 'select' && typeof field.options === 'function' && field.name) {
            const result = (field.options as () => Promise<Array<{ value: string; label: string }>> | Array<{ value: string; label: string }>)();
            const options = result instanceof Promise ? await result : result;
            optionsMap[field.name] = options;
          }
        } catch (error) {
          console.error(`Failed to load options for field ${field.name}:`, error);
          if (field.name) {
            optionsMap[field.name] = [];
          }
        }
      }
      
      setAsyncOptions(optionsMap);
    };
    
    loadAsyncOptions();
  }, [panelConfig]);

  // Reload dependent options when dependencies change
  useEffect(() => {
    const reloadDependentOptions = async () => {
      if (!panelConfig) return;
      
      const currentService = formData.service as string;
      const currentApiKeyId = formData.apiKeyId as string;
      
      if (prevDepsRef.current.service === currentService && 
          prevDepsRef.current.apiKeyId === currentApiKeyId) {
        return;
      }
      
      if (reloadInProgressRef.current) return;
      
      reloadInProgressRef.current = true;
      prevDepsRef.current = { service: currentService, apiKeyId: currentApiKeyId };
      
      try {
        const fieldsToUpdate: FieldConfig[] = [];
        
        const collectDependentFields = (fields: any[]) => {
          fields.forEach((field: any) => {
            if (field.type === 'select' && field.dependsOn && typeof field.options === 'function') {
              fieldsToUpdate.push(field);
            } else if (field.type === 'row' && field.fields) {
              collectDependentFields(field.fields);
            }
          });
        };
        
        collectDependentFields(panelConfig.fields || []);
        collectDependentFields(panelConfig.leftColumn || []);
        collectDependentFields(panelConfig.rightColumn || []);
        
        if (fieldsToUpdate.length === 0) return;
        
        const updatedOptions: Record<string, Array<{ value: string; label: string }>> = {};
        let hasUpdates = false;
        
        for (const field of fieldsToUpdate) {
          if (field.type === 'select' && field.dependsOn && field.name && typeof field.options === 'function') {
            try {
              const result = (field.options as (formData: any) => Promise<Array<{ value: string; label: string }>>)(formData);
              const options = result instanceof Promise ? await result : result;
              updatedOptions[field.name] = options;
              hasUpdates = true;
            } catch (error) {
              console.error(`Failed to reload options for dependent field ${field.name}:`, error);
              updatedOptions[field.name] = [];
              hasUpdates = true;
            }
          }
        }
        
        if (hasUpdates) {
          setAsyncOptions(prev => ({ ...prev, ...updatedOptions }));
        }
      } finally {
        reloadInProgressRef.current = false;
      }
    };
    
    reloadDependentOptions();
  }, [formData.service, formData.apiKeyId, panelConfig]);

  const updateField = async (name: string, value: unknown) => {
    if (isMonitorMode) return;

    handleChange(name as keyof typeof formData, value as any);
    
    if (data.type === 'person' && name === 'modelName') {
      const service = formData.service || data.service;
      const apiKeyId = formData.apiKeyId || data.apiKeyId;
      
      if (service && value && apiKeyId) {
        try {
          await preInitializeModel(
            service as string,
            value as string,
            apiKeyId as string
          );
        } catch (error) {
          console.warn('Failed to pre-initialize model:', error);
        }
      }
    }
  };

  const convertFieldConfig = (fieldConfig: any): PropertyFieldConfig | null => {
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
    
    let type: PropertyFieldConfig['type'] = 'string';
    let multiline = false;
    let min: number | undefined;
    let max: number | undefined;
    
    switch (fieldConfig.type) {
      case 'text':
        type = 'string';
        break;
      case 'select':
        type = 'select';
        break;
      case 'textarea':
      case 'variableTextArea':
        type = 'string';
        multiline = true;
        break;
      case 'checkbox':
        type = 'boolean';
        break;
      case 'iterationCount':
        type = 'number';
        min = fieldConfig.min;
        max = fieldConfig.max;
        break;
      case 'labelPersonRow':
      case 'personSelect':
        type = 'person';
        break;
      default:
        return null;
    }
    
    let options: PropertyFieldConfig['options'];
    if (fieldConfig.type === 'select') {
      if (Array.isArray(fieldConfig.options)) {
        options = fieldConfig.options;
      } else if (fieldConfig.name && asyncOptions[fieldConfig.name]) {
        options = asyncOptions[fieldConfig.name];
      }
    }
    
    const baseField: PropertyFieldConfig = {
      name: fieldConfig.name || '',
      label: fieldConfig.label || '',
      type,
      options,
      multiline,
      min,
      max
    };
    
    if ('placeholder' in fieldConfig) {
      baseField.placeholder = fieldConfig.placeholder;
    }
    if ('required' in fieldConfig) {
      baseField.isRequired = (fieldConfig as any).required;
    }
    if ('helperText' in fieldConfig) {
      baseField.helperText = (fieldConfig as any).helperText;
    }
    if ('acceptedFileTypes' in fieldConfig) {
      baseField.acceptedFileTypes = (fieldConfig as any).acceptedFileTypes;
    }
    
    baseField.customProps = {
      disabled: isMonitorMode || ('disabled' in fieldConfig ? fieldConfig.disabled : false),
      detectedVariables: (data as any).detectedVariables as string[] | undefined
    };
    
    return baseField;
  };

  const renderField = (fieldConfig: any, index: number): React.ReactNode => {
    const convertedConfig = convertFieldConfig(fieldConfig);
    if (!convertedConfig) return null;
    
    const key = fieldConfig.name ? `${fieldConfig.name}-${index}` : `field-${index}`;
    
    if (fieldConfig.type === 'row' && fieldConfig.fields) {
      return (
        <FormRow key={key} className={fieldConfig.className}>
          {fieldConfig.fields.map((field, idx) => renderField(field, idx))}
        </FormRow>
      );
    }
    
    if (fieldConfig.type === 'labelPersonRow') {
      return (
        <FormRow key={key}>
          <UnifiedFieldRenderer
            field={{
              name: 'label',
              label: 'Label',
              type: 'string',
              placeholder: fieldConfig.labelPlaceholder
            }}
            value={formData.label}
            onChange={(v) => updateField('label', v)}
          />
          <UnifiedFieldRenderer
            field={{
              name: 'personId',
              label: 'Person',
              type: 'person',
              placeholder: fieldConfig.personPlaceholder
            }}
            value={formData.personId}
            onChange={(v) => updateField('personId', v)}
          />
        </FormRow>
      );
    }
    
    return (
      <UnifiedFieldRenderer
        key={key}
        field={convertedConfig}
        value={formData[convertedConfig.name]}
        onChange={(v) => updateField(convertedConfig.name, v)}
        nodeData={data}
        className={fieldConfig.className}
      />
    );
  };

  const renderSection = (fields: any[] | undefined) => {
    if (!fields) return null;
    return fields.map((field, index) => renderField(field, index));
  };

  if (!panelConfig) {
    return (
      <div className="p-4 space-y-4">
        <div className="flex items-center space-x-2 border-b pb-2">
          <Settings className="w-5 h-5" />
          <h3 className="text-lg font-semibold">Unknown Node Type</h3>
        </div>
        <div className="space-y-4">
          <div className="text-red-500">No configuration found for node type: {nodeType}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center space-x-2 border-b pb-2">
        <span>{(nodeConfig as any)?.icon || '⚙️'}</span>
        <h3 className="text-lg font-semibold">
          {nodeConfig?.label ? `${nodeConfig.label} Properties` : `${nodeType} Properties`}
        </h3>
      </div>
      <div className="space-y-4">
        <Form>
          {panelConfig.layout === 'twoColumn' ? (
            <TwoColumnPanelLayout
              leftColumn={renderSection(panelConfig.leftColumn)}
              rightColumn={renderSection(panelConfig.rightColumn)}
            />
          ) : panelConfig.layout === 'single' ? (
            <SingleColumnPanelLayout>
              {renderSection(panelConfig.fields)}
            </SingleColumnPanelLayout>
          ) : (
            renderSection(panelConfig.fields)
          )}
        </Form>
      </div>
    </div>
  );
};

export default PropertiesPanel;