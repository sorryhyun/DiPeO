import type { ExecutionID } from '../branded';

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
  maxReconnectAttempts?: number;
  maxReconnectInterval?: number;
  reconnectDecay?: number;
  debug?: boolean;
}

export interface MonitorSubscription {
  executionId: ExecutionID;
}