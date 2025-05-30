// Common UI constants
export const GRID_SIZE = 20;
export const SNAP_THRESHOLD = 10;

// Export/Import formats
export const EXPORT_FORMATS = {
  json: 'application/json',
  yaml: 'application/x-yaml',
  uml: 'text/plain',
} as const;

// API service types
export const API_SERVICES = {
  openai: 'openai',
  claude: 'claude',
  gemini: 'gemini',
  grok: 'grok',
} as const;

// Execution states
export const EXECUTION_STATES = {
  idle: 'idle',
  running: 'running',
  paused: 'paused',
  completed: 'completed',
  error: 'error',
} as const;