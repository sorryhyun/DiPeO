/**
 * Browser-specific stream manager for real-time execution updates
 * 
 * This manages streaming updates during execution, emitting them to UI components
 * through the execution store for real-time progress visualization.
 */

import { useExecutionStore } from '@/core/stores/executionStore';
import type { StreamManager } from './core/execution-engine';

export interface StreamUpdate {
  type: string;
  nodeId?: string;
  context?: Record<string, any>;
  total_cost?: number;
  memory_stats?: Record<string, any>;
  error?: string;
  output_preview?: string;
  message?: any;
  conversation_log?: string;
}

export class BrowserStreamManager implements StreamManager {
  private updateCallback?: (update: StreamUpdate) => void;

  constructor(updateCallback?: (update: StreamUpdate) => void) {
    this.updateCallback = updateCallback;
  }

  emit(update: StreamUpdate): void {
    // Call the update callback if provided
    if (this.updateCallback) {
      this.updateCallback(update);
    }
    
    // Also emit to global event system for conversation dashboard
    try {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('execution-update', {
          detail: { type: update.type, data: update }
        }));
      }
    } catch (error) {
      console.warn('Failed to dispatch execution update event:', error);
    }
  }

  isEnabled(): boolean {
    return true;
  }

  /**
   * Create a stream manager with execution store integration
   */
  static createWithStoreIntegration(): BrowserStreamManager {
    const updateCallback = (update: StreamUpdate) => {
      // Access store actions directly
      const store = useExecutionStore.getState();
      
      const timestamp = new Date().toISOString();
      console.log('[Stream Update]', timestamp, update.type, update.nodeId, `(${Date.now()})`);

      switch (update.type) {
        case 'node_start':
          if (update.nodeId) {
            console.log('[Stream] Starting node:', update.nodeId);
            store.addRunningNode(update.nodeId);
            store.setCurrentRunningNode(update.nodeId);
          }
          break;

        case 'node_complete':
          if (update.nodeId) {
            console.log('[Stream] Completing node:', update.nodeId);
            store.removeRunningNode(update.nodeId);
            store.setCurrentRunningNode(null);
          }
          break;

        case 'node_error':
          if (update.nodeId) {
            console.error(`Node error: ${update.nodeId}`, update.error);
            store.removeRunningNode(update.nodeId);
            store.setCurrentRunningNode(null);
          }
          break;

        case 'execution_complete':
          store.clearRunningNodes();
          store.setCurrentRunningNode(null);
          if (update.context) {
            store.setRunContext(update.context);
          }
          break;

        case 'execution_error':
          store.clearRunningNodes();
          store.setCurrentRunningNode(null);
          break;

        default:
          // Unknown update type - silently ignore
      }
    };

    return new BrowserStreamManager(updateCallback);
  }
}

/**
 * Create a stream manager for browser environment
 */
export function createStreamManager(updateCallback?: (update: StreamUpdate) => void): BrowserStreamManager {
  return new BrowserStreamManager(updateCallback);
}

/**
 * Create a stream manager with automatic store integration
 */
export function createStoreIntegratedStreamManager(): BrowserStreamManager {
  return BrowserStreamManager.createWithStoreIntegration();
}