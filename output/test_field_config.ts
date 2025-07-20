// Generated field configuration for hook
export const hookFields = [
  {
    name: 'hook_type',
    type: 'enum',
    required: True,
    defaultValue: 'shell'
  }{{#unless @last}},{{/unless}}
  {
    name: 'command',
    type: 'string',
    required: False,
    defaultValue: ''
  }{{#unless @last}},{{/unless}}
];
