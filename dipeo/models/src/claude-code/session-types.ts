export interface ClaudeCodeSession {
  sessionId: string;
  events: SessionEvent[];
  metadata: SessionMetadata;
}

export interface SessionEvent {
  type: 'user' | 'assistant' | 'summary';
  uuid: string;
  parentUuid?: string;
  timestamp: string;
  message: ClaudeCodeMessage;
  toolUse?: ToolUse;
  toolResult?: ToolResult;
}

export interface ClaudeCodeMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface SessionMetadata {
  startTime: string;
  endTime?: string;
  totalEvents: number;
  toolUsageCount: Record<string, number>;
  projectPath?: string;
}

export interface ToolUse {
  name: string;
  input: Record<string, any>;
}

export interface ToolResult {
  success: boolean;
  output?: string;
  error?: string;
}

export interface ConversationTurn {
  userEvent: SessionEvent;
  assistantEvent: SessionEvent;
  toolEvents: SessionEvent[];
}

export interface DiffPatchInput {
  filePath: string;
  oldContent?: string;
  newContent?: string;
  patch?: string;
}

export interface ClaudeCodeDiagramMetadata {
  sessionId: string;
  createdAt: string;
  eventCount: number;
  nodeCount: number;
  toolUsage: Record<string, number>;
}

export type ClaudeCodeEventType = 'user' | 'assistant' | 'summary' | 'tool_use' | 'tool_result';

export interface SessionStatistics {
  sessionId: string;
  totalEvents: number;
  userPrompts: number;
  assistantResponses: number;
  totalToolCalls: number;
  toolBreakdown: Record<string, number>;
  duration?: number;
  filesModified: string[];
  commandsExecuted: string[];
}

export interface SessionConversionOptions {
  outputDir?: string;
  format?: 'light' | 'native' | 'readable';
  autoExecute?: boolean;
  mergeReads?: boolean;
  simplify?: boolean;
  preserveThinking?: boolean;
}

export interface WatchOptions {
  interval?: number;
  autoConvert?: boolean;
  notifyOnNew?: boolean;
}
