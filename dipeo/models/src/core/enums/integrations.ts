/**
 * External service integration enumerations
 */

export enum LLMService {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  GEMINI = 'gemini',
  BEDROCK = 'bedrock',
  VERTEX = 'vertex',
  DEEPSEEK = 'deepseek',
  OLLAMA = 'ollama'
}

export enum APIServiceType {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  GEMINI = 'gemini',
  BEDROCK = 'bedrock',
  VERTEX = 'vertex',
  DEEPSEEK = 'deepseek',
  OLLAMA = 'ollama',
  NOTION = 'notion',
  GOOGLE_SEARCH = 'google_search',
  SLACK = 'slack',
  GITHUB = 'github',
  JIRA = 'jira'
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