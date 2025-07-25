// Auto-generated node configuration for template_job
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { templateJobFields } from '../fields/TemplateJobFields';

export const templateJobConfig: UnifiedNodeConfig = {
  label: 'Template Job',
  icon: '📝',
  color: '#3F51B5',
  nodeType: 'template_job',
  category: 'compute',
  handles: {

    input: [

      { id: 'input', label: '', position: 'left' },

    ],


    output: [

      { id: 'output', label: '', position: 'right' },

    ],

  },
  defaults: {

  },
  customFields: templateJobFields,
};

export default templateJobConfig;