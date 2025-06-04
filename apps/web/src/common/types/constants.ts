// Constants

export const DEFAULT_MAX_TOKENS = 4096;
export const DEFAULT_TEMPERATURE = 0.7;
export const DEFAULT_MAX_ITERATIONS = 100;
export const DEFAULT_EXECUTION_TIMEOUT = 300000; // 5 minutes

export const SUPPORTED_DOC_EXTENSIONS = new Set([
  '.txt', '.md', '.docx', '.pdf'
]);

export const SUPPORTED_CODE_EXTENSIONS = new Set([
  '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.jsx', '.tsx'
]);