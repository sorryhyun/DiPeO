// types/index.ts


/* ---------- Primitives ---------- */
export type ID = string;
export interface Vec2 { x: number; y: number }

export type Dict<V = unknown> = Record<string, V>;
export type Nullable<T> = T | null;
export type DeepPartial<T> = { [K in keyof T]?: DeepPartial<T[K]> };

/* ---------- API layer ---------- */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface RequestConfig<B = unknown, Q = Dict, H extends Dict<string> = Dict<string>> {
  url: string;
  method?: HttpMethod;
  body?: B;
  query?: Q;
  headers?: H;
  signal?: AbortSignal;
}

interface ApiMeta { filename?: string; path?: string }

export type ApiResponse<T = unknown> =
  | ({ success: true; data: T } & ApiMeta)
  | ({ success: false; error: string } & ApiMeta);

/* ---------- Diagram domain ---------- */
export const NodeKinds = [
  'start', 'job', 'person_job', 'condition', 'endpoint', 'db', 'notion',
  'person_batch_job', 'user_response',
] as const;
export type NodeKind = typeof NodeKinds[number];

export interface Node<D = Dict, K extends NodeKind = NodeKind> {
  id: ID;
  kind: K;
  pos: Vec2;
  data: D;
}

/** Lightweight edge between nodes */
export interface Arrow<M = Dict> {
  id: ID;
  source: ID;
  target: ID;
  meta?: M;
}

export interface ApiKey {
  id: ID;
  service: string;
  key: string;
}

export interface Diagram {
  id: string;
  name: string;
  description?: string;
  nodes: Node[];
  arrows: Arrow[];
  persons: Person[];
  apiKeys: ApiKey[];
  metadata?: Dict;
}

/* Person / Memory */
export interface Person {
  id: ID;
  name: string;
  avatarUrl?: string;
}

export interface ConversationMessage {
  id?: ID;
  role: 'user' | 'assistant' | 'system';
  personId: ID;
  content: string;
  timestamp?: string;
  tokenCount?: number;
  nodeLabel?: string;
}

export interface Page<T = unknown> {
  items: T[];
  total: number;
  hasMore: boolean;
}

export type PersonMemoryState = Page<ConversationMessage> & {
  visible: number;
  forgotten: number;
};

/* ---------- Runtime / Execution ---------- */
export type MessageHandler = (message: WSMessage) => void;

export interface ExecutionOptions {
  mode?: 'monitor' | 'headless' | 'check';
  debug?: boolean;
  delay?: number;
  continueOnError?: boolean;
  allowPartial?: boolean;
  debugMode?: boolean;
}

export interface ExecutionState<C = Dict> {
  id: ID;
  running: ID[];
  completed: ID[];
  skipped: ID[];
  paused: ID[];
  context: C;
  errors: Dict<string>;
  isRunning: boolean;
  startedAt?: string;
  endedAt?: string;
  totalTokens?: number;
}

export interface WebSocketHooks {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (e: Event) => void;
  onMessage?: (ev: MessageEvent) => void;
}

export interface WebSocketClientOptions extends WebSocketHooks {
  url?: string;
  protocols?: string[];
  reconnectInterval?: number;
  maxReconnect?: number;
}

/* Event helpers */
export type EventPayload<T extends string, P = undefined> =
  P extends undefined ? { type: T } : { type: T; payload: P };

export type NodeExecutionEvent =
  | EventPayload<'node_start', { nodeId: ID }>
  | EventPayload<'node_progress', { nodeId: ID; message?: string }>
  | EventPayload<'node_complete', { nodeId: ID; output: unknown }>
  | EventPayload<'node_error', { nodeId: ID; error: string }>
  | EventPayload<'node_paused', { nodeId: ID }>
  | EventPayload<'node_resumed', { nodeId: ID }>
  | EventPayload<'node_skipped', { nodeId: ID }>;

/* ---------- UI ---------- */
export const Views = ['diagram','memory','execution','conversation'] as const;
export type View = typeof Views[number];

export interface UIState {
  selected?: { id: ID; kind: 'node' | 'arrow' | 'person' };
  active: View;
  monitorMode: boolean;
  propertyPanelOpen: boolean;
  contextMenu?: { pos: Vec2; nodeId?: ID };
}

/* Canvas */
export interface CanvasState {
  zoom: number;
  center: Vec2;
  dragging: boolean;
  connecting: boolean;
}

export interface PropertyPanelState {
  open: boolean;
  dirty: boolean;
  errors: Dict<string>;
}

/* Field Configuration */
export type FieldType = 
  | 'text' 
  | 'select' 
  | 'textarea' 
  | 'checkbox' 
  | 'number'
  | 'boolean'
  | 'string'
  | 'file'
  | 'person'
  | 'maxIteration'
  | 'personSelect'
  | 'variableTextArea'
  | 'labelPersonRow'
  | 'row'
  | 'custom';

export interface FieldConfig<T = unknown> {
  name: string;
  label: string;
  type: FieldType;
  placeholder?: string;
  required?: boolean;
  options?: Array<{ value: string; label: string }> | (() => Array<{ value: string; label: string }>);
  rows?: number;
  hint?: string;
  min?: number;
  max?: number;
  acceptedFileTypes?: string;
  disabled?: boolean;
  conditional?: {
    field: string;
    values: T[];
    operator?: 'equals' | 'notEquals' | 'includes';
  };
  className?: string;
  dependsOn?: string[];
}

/* ---------- Errors ---------- */
export class AgentDiagramError extends Error {
  constructor(message: string, readonly details?: Dict) {
    super(message);
    this.name = new.target.name;
  }
}
export class DependencyError extends AgentDiagramError {}
export class MaxIterationsError extends AgentDiagramError {}
export class ConditionEvaluationError extends AgentDiagramError {}

export type WSMessage = { type: string; [key: string]: any }; // Basic WS message


// Only export non-conflicting API types
export {
  type ApiClientOptions,
  type DiagramSaveRequest,
  type DiagramSaveResponse,
  type ConvertRequest,
  type ConvertResponse,
  type HealthResponse,
  type ExecutionCapabilitiesResponse
} from './api';
