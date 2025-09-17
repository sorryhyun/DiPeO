/**
 * External service integration enumerations
 */

export enum LLMService {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  CLAUDE_CODE = 'claude-code',
  GOOGLE = 'google',
  GEMINI = 'gemini',
  OLLAMA = 'ollama'
}

/**
 * APIServiceType now only includes LLM providers.
 * External API providers (NOTION, GOOGLE_SEARCH, SLACK, etc.) are now
 * handled dynamically through the ProviderRegistry.
 */
export enum APIServiceType {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  GEMINI = 'gemini',
  OLLAMA = 'ollama',
  CLAUDE_CODE = "claude-code"
}

/**
 * @deprecated Use plain string provider ids resolved at runtime.
 * Kept only to avoid import breakages during transition.
 */
export type IntegrationProvider = string;

export enum ToolType {
  WEB_SEARCH = 'web_search',
  WEB_SEARCH_PREVIEW = 'web_search_preview',
  IMAGE_GENERATION = 'image_generation'
}

export enum ToolSelection {
  NONE = 'none',
  IMAGE = 'image',
  WEBSEARCH = 'websearch'
}

export enum AuthType {
  NONE = 'none',
  BEARER = 'bearer',
  BASIC = 'basic',
  API_KEY = 'api_key'
}

export enum RetryStrategy {
  NONE = 'none',
  LINEAR = 'linear',
  EXPONENTIAL = 'exponential',
  FIBONACCI = 'fibonacci',
  CONSTANT = 'constant',
  // Infrastructure-specific variants
  EXPONENTIAL_BACKOFF = 'exponential_backoff',
  LINEAR_BACKOFF = 'linear_backoff',
  FIXED_DELAY = 'fixed_delay'
}
