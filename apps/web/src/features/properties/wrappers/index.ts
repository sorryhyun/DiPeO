// Direct exports from local ui-components (no store integration needed)
export { Panel } from '../components/ui-components/Panel';
// Re-export generic form components from shared
export { 
  Form, FormField, FormGrid, FormRow, TextAreaField, TextField, SelectField, 
  InlineTextField, InlineSelectField, CheckboxField,
  TwoColumnPanelLayout, SingleColumnPanelLayout
} from '@/shared/components/forms';

// Export specialized property components
export { 
  PersonSelectionField, LabelPersonRow, IterationCountField, 
  VariableDetectionTextArea
} from '../components/ui-components/FormComponents';

// Hooks
export { usePropertyForm } from '../hooks/usePropertyForm';
export { usePropertyPanel } from '../hooks/usePropertyPanel';

// Re-export types
export type {
  PanelProps,
  FormFieldProps
} from '../../../shared/types';