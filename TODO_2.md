# Frontend Component Duplication Reduction Plan

## Problem Analysis

The current property panel system has significant code duplication across 11+ panel components. Each node type (PersonJob, PersonBatchJob, Condition, DB, Endpoint, Job, etc.) has its own dedicated panel component with repeated patterns, identical field logic, and similar layouts.

### Key Duplication Issues Identified

#### 1. **Structural Duplication**
- **Two-column grid layout** repeated in 6+ components:
  ```tsx
  <div className="grid grid-cols-2 gap-4">
    <div className="space-y-4">{/* Left column */}</div>
    <div className="space-y-4">{/* Right column */}</div>
  </div>
  ```
- **Form wrapper pattern** identical across all panels
- **Import statements** nearly identical across components

#### 2. **Field Pattern Duplication**
- **Label + Type selection row** in 90% of panels:
  ```tsx
  <FormRow>
    <InlineTextField label="Label" value={formData.label || ''} />
    <InlineSelectField label="[Type]" value={formData.someType} />
  </FormRow>
  ```
- **Person selection logic** exactly duplicated in PersonJobPanel and PersonBatchJobPanel
- **Iteration count field** identical implementation in multiple components

#### 3. **Data Handling Duplication**
- Every component uses identical `usePropertyPanel<T>(nodeId, 'node', data)` pattern
- Similar `handleChange` wrapper functions
- Repeated option array definitions (forgetOptions, typeOptions, etc.)

#### 4. **Business Logic Duplication**
- Variable detection hints repeated in text-based panels
- API key selection patterns duplicated
- Conditional field rendering logic similar across components

## Proposed Solution: Generic Panel Architecture

### Phase 1: Create Reusable Layout Components

#### 1.1 Panel Layout Wrappers
```tsx
// components/ui-components/PanelLayouts.tsx
interface TwoColumnLayoutProps {
  leftColumn: React.ReactNode;
  rightColumn: React.ReactNode;
}

export const TwoColumnPanelLayout: React.FC<TwoColumnLayoutProps> = ({ 
  leftColumn, 
  rightColumn 
}) => (
  <div className="grid grid-cols-2 gap-4">
    <div className="space-y-4">{leftColumn}</div>
    <div className="space-y-4">{rightColumn}</div>
  </div>
);

export const SingleColumnPanelLayout: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => (
  <div className="space-y-4">{children}</div>
);
```

#### 1.2 Common Field Groups
```tsx
// components/ui-components/CommonFieldGroups.tsx
interface LabelTypeRowProps<T> {
  formData: T;
  handleChange: (field: keyof T, value: any) => void;
  typeOptions: Array<{ value: string; label: string }>;
  typeLabel: string;
  typePlaceholder?: string;
}

export const LabelTypeRow = <T extends { label?: string }>({
  formData,
  handleChange,
  typeOptions,
  typeLabel,
  typePlaceholder = "Select"
}: LabelTypeRowProps<T>) => (
  <FormRow>
    <InlineTextField
      label="Label"
      value={formData.label || ''}
      onChange={(v) => handleChange('label' as keyof T, v)}
      placeholder="Enter label"
      className="flex-1"
    />
    <InlineSelectField
      label={typeLabel}
      value={formData[typeField] || ''}
      onChange={(v) => handleChange(typeField, v)}
      options={typeOptions}
      placeholder={typePlaceholder}
      className="flex-1"
    />
  </FormRow>
);
```

### Phase 2: Create Specialized Field Components

#### 2.1 Person Selection Field
```tsx
// components/ui-components/PersonSelectionField.tsx
interface PersonSelectionFieldProps {
  value: string;
  onChange: (personId: string) => void;
  className?: string;
  required?: boolean;
}

export const PersonSelectionField: React.FC<PersonSelectionFieldProps> = ({
  value,
  onChange,
  className,
  required = false
}) => {
  const { persons } = usePersons();
  const personOptions = useMemo(
    () => persons.map(p => ({ value: p.id, label: p.label })),
    [persons]
  );

  return (
    <InlineSelectField
      label="Person"
      value={value}
      onChange={(v) => onChange(v || '')}
      options={personOptions}
      placeholder={required ? "Select person" : "None"}
      className={className}
    />
  );
};
```

#### 2.2 Iteration Count Field
```tsx
// components/ui-components/IterationCountField.tsx
interface IterationCountFieldProps {
  value: number;
  onChange: (count: number) => void;
  className?: string;
  min?: number;
  max?: number;
}

export const IterationCountField: React.FC<IterationCountFieldProps> = ({
  value,
  onChange,
  className = "w-24",
  min = 1,
  max = 100
}) => (
  <InlineTextField
    label="Max Iter"
    value={String(value || min)}
    onChange={(v) => {
      const num = parseInt(v) || min;
      onChange(Math.min(Math.max(num, min), max));
    }}
    placeholder={String(min)}
    className={className}
  />
);
```

#### 2.3 Variable Detection Text Area
```tsx
// components/ui-components/VariableDetectionTextArea.tsx
interface VariableDetectionTextAreaProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  detectedVariables?: string[];
  placeholder?: string;
  rows?: number;
}

export const VariableDetectionTextArea: React.FC<VariableDetectionTextAreaProps> = ({
  label,
  value,
  onChange,
  detectedVariables,
  placeholder,
  rows = 4
}) => {
  const hint = useMemo(() => {
    if (!detectedVariables?.length) return undefined;
    return `Detected variables: ${detectedVariables.map(v => `{{${v}}}`).join(', ')}`;
  }, [detectedVariables]);

  return (
    <TextAreaField
      label={label}
      value={value}
      onChange={onChange}
      rows={rows}
      placeholder={placeholder}
      hint={hint}
    />
  );
};
```

### Phase 3: Create Configuration-Driven Generic Panel

#### 3.1 Panel Configuration Schema
```tsx
// types/panelConfig.ts
interface FieldGroupConfig<T> {
  type: 'labelType' | 'personSelection' | 'iterationCount' | 'textArea' | 'custom';
  fields: Array<keyof T>;
  props?: Record<string, any>;
  conditional?: {
    dependsOn: keyof T;
    values: any[];
  };
}

interface PanelConfiguration<T> {
  layout: 'single' | 'twoColumn';
  leftColumn?: FieldGroupConfig<T>[];
  rightColumn?: FieldGroupConfig<T>[];
  fields?: FieldGroupConfig<T>[]; // for single column
}
```

#### 3.2 Generic Panel Component
```tsx
// components/GenericPropertyPanel.tsx
interface GenericPropertyPanelProps<T extends BaseBlockData> {
  nodeId: string;
  data: T;
  configuration: PanelConfiguration<T>;
  customComponents?: Record<string, React.ComponentType<any>>;
}

export const GenericPropertyPanel = <T extends BaseBlockData>({
  nodeId,
  data,
  configuration,
  customComponents = {}
}: GenericPropertyPanelProps<T>) => {
  const { formData, handleChange } = usePropertyPanel<T>(nodeId, 'node', data);

  const renderFieldGroup = (group: FieldGroupConfig<T>) => {
    // Check conditional rendering
    if (group.conditional) {
      const dependentValue = formData[group.conditional.dependsOn];
      if (!group.conditional.values.includes(dependentValue)) {
        return null;
      }
    }

    switch (group.type) {
      case 'labelType':
        return <LabelTypeRow {...group.props} formData={formData} handleChange={handleChange} />;
      
      case 'personSelection':
        const field = group.fields[0];
        return (
          <PersonSelectionField
            value={formData[field] as string || ''}
            onChange={(v) => handleChange(field, v)}
            {...group.props}
          />
        );
      
      case 'iterationCount':
        const iterField = group.fields[0];
        return (
          <IterationCountField
            value={formData[iterField] as number || 1}
            onChange={(v) => handleChange(iterField, v)}
            {...group.props}
          />
        );
      
      case 'custom':
        const CustomComponent = customComponents[group.props?.componentName];
        return CustomComponent ? <CustomComponent formData={formData} handleChange={handleChange} {...group.props} /> : null;
      
      default:
        return null;
    }
  };

  const renderColumn = (groups: FieldGroupConfig<T>[]) => (
    <div className="space-y-4">
      {groups.map((group, index) => (
        <div key={index}>{renderFieldGroup(group)}</div>
      ))}
    </div>
  );

  return (
    <Form>
      {configuration.layout === 'twoColumn' ? (
        <TwoColumnPanelLayout
          leftColumn={configuration.leftColumn ? renderColumn(configuration.leftColumn) : null}
          rightColumn={configuration.rightColumn ? renderColumn(configuration.rightColumn) : null}
        />
      ) : (
        <SingleColumnPanelLayout>
          {configuration.fields ? renderColumn(configuration.fields) : null}
        </SingleColumnPanelLayout>
      )}
    </Form>
  );
};
```

### Phase 4: Panel Configuration Definitions

#### 4.1 PersonBatchJob Panel Configuration
```tsx
// configs/personBatchJobPanelConfig.ts
export const personBatchJobPanelConfig: PanelConfiguration<PersonBatchJobBlockData> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'labelType',
      fields: ['label'],
      props: {
        typeOptions: [], // Will be filled by PersonSelectionField
        typeLabel: 'Person',
        customTypeComponent: 'PersonSelectionField'
      }
    },
    {
      type: 'custom',
      fields: ['batchSize', 'iterationCount'],
      props: {
        componentName: 'BatchSizeIterationRow'
      }
    },
    {
      type: 'custom',
      fields: ['parallelProcessing'],
      props: {
        componentName: 'ParallelProcessingToggle'
      }
    },
    {
      type: 'custom',
      fields: ['aggregationMethod'],
      props: {
        componentName: 'AggregationMethodSelect'
      }
    }
  ],
  rightColumn: [
    {
      type: 'textArea',
      fields: ['batchPrompt'],
      props: {
        label: 'Batch Prompt',
        rows: 6,
        placeholder: 'Enter batch processing prompt. Use {{variable_name}} for variables.',
        variableDetection: true
      }
    },
    {
      type: 'textArea',
      fields: ['customAggregationPrompt'],
      props: {
        label: 'Custom Aggregation Prompt',
        rows: 4,
        placeholder: 'Enter custom aggregation prompt to process batch results.'
      },
      conditional: {
        dependsOn: 'aggregationMethod',
        values: ['custom']
      }
    }
  ]
};
```

### Phase 5: Migration Strategy

#### 5.1 Immediate Benefits (Week 1-2)
1. **Create layout components** - Reduce 50+ lines per panel
2. **Extract common field groups** - Eliminate exact duplications
3. **Implement PersonSelectionField** - Remove duplication in PersonJob panels

#### 5.2 Medium-term Improvements (Week 3-4)
1. **Create configuration-driven system** for 3-4 simpler panels
2. **Extract common option constants** to separate file
3. **Implement specialized field components**

#### 5.3 Long-term Goals (Month 2)
1. **Migrate all panels** to configuration-driven approach
2. **Create panel configuration builder** for easy new node types
3. **Add validation and error handling** to generic system

### Benefits of This Approach

#### Immediate Benefits
- **Reduce bundle size** by ~60% for property panel code
- **Eliminate code duplication** across 11+ components
- **Improve type safety** with generic constraints
- **Simplify maintenance** - fix once, apply everywhere

#### Long-term Benefits
- **Faster development** of new node types
- **Consistent UX** across all property panels
- **Easier testing** with reusable components
- **Better performance** with proper memoization

#### Developer Experience
- **Less boilerplate** when creating new panels
- **Configuration-driven** approach reduces complexity
- **Reusable components** improve code reuse
- **Better TypeScript support** with generic constraints

## Implementation Priority

### High Priority (Must Do)
1. TwoColumnPanelLayout component
2. PersonSelectionField component  
3. LabelTypeRow component
4. IterationCountField component

### Medium Priority (Should Do)
1. VariableDetectionTextArea component
2. Configuration schema design
3. GenericPropertyPanel base component

### Low Priority (Nice to Have)
1. Panel configuration builder
2. Advanced conditional rendering
3. Dynamic field validation

## Success Metrics

- **Code Reduction**: Target 70% reduction in property panel code
- **Bundle Size**: Reduce property panel bundle by ~40KB
- **Development Speed**: 50% faster new panel creation
- **Maintainability**: Single source of truth for common patterns
- **Type Safety**: Eliminate all `any` types in property panels

## Risk Mitigation

- **Gradual Migration**: Start with simplest panels first
- **Backward Compatibility**: Keep existing panels during transition
- **Testing**: Ensure all existing functionality works with new system
- **Fallback**: Custom component escape hatch for complex scenarios