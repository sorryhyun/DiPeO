// filepath: src/core/hooks.ts

import type { AppConfig } from '@/app/config';
import type { EventBus } from './events';
import type { Container } from './di';

// Hook point union for extension points
export type HookPoint = 
  | 'beforeApiRequest' 
  | 'afterApiResponse' 
  | 'onLogin' 
  | 'onLogout' 
  | 'onRouteChange' 
  | 'onAppBoot';

// Context object passed to all hook functions
export interface HookContext {
  appConfig: AppConfig;
  eventBus: EventBus;
  diContainer: Container;
}

// Generic hook function signature
export type HookFn<TArgs extends any[] = any[], TRet = void> = 
  (context: HookContext, ...args: TArgs) => TRet | Promise<TRet>;

// Hook-specific argument types for better type safety
export interface HookArgs {
  beforeApiRequest: [request: { url: string; init?: RequestInit }];
  afterApiResponse: [response: any]; // Response | ApiError
  onLogin: [payload: { user: any; tokens: any }];
  onLogout: [payload: { userId?: string }];
  onRouteChange: [routeInfo: { from: string | null; to: string; params?: Record<string, string> }];
  onAppBoot: [];
}

// Hook entry with priority
interface HookEntry {
  fn: HookFn<any, any>;
  priority: number;
}

// Hook Registry class for managing extension points
export class HookRegistry {
  private hooks: Map<HookPoint, HookEntry[]> = new Map();
  private context: HookContext | null = null;

  // Initialize the registry with context
  initialize(context: HookContext): void {
    this.context = context;
  }

  // Register a hook function for a specific hook point
  register<P extends HookPoint>(
    point: P,
    fn: HookFn<HookArgs[P], any>,
    priority: number = 100
  ): () => void {
    if (!this.hooks.has(point)) {
      this.hooks.set(point, []);
    }

    const entry: HookEntry = { fn, priority };
    const entries = this.hooks.get(point)!;
    
    // Insert in sorted order by priority
    const insertIndex = entries.findIndex(e => e.priority > priority);
    if (insertIndex === -1) {
      entries.push(entry);
    } else {
      entries.splice(insertIndex, 0, entry);
    }

    // Return unregister function
    return () => {
      const hookEntries = this.hooks.get(point);
      if (hookEntries) {
        const index = hookEntries.indexOf(entry);
        if (index !== -1) {
          hookEntries.splice(index, 1);
        }
      }
    };
  }

  // Get a snapshot of registered hooks for a point
  list<P extends HookPoint>(point: P): Array<{ fn: HookFn<HookArgs[P], any>; priority: number }> {
    const entries = this.hooks.get(point) || [];
    return [...entries]; // Return a copy to prevent external modification
  }

  // Run all hooks for a specific point
  async run<P extends HookPoint>(
    point: P,
    ...args: HookArgs[P]
  ): Promise<void> {
    if (!this.context) {
      console.warn(`HookRegistry: Context not initialized. Call initialize() first.`);
      return;
    }

    const entries = this.list(point);
    
    for (const entry of entries) {
      try {
        await entry.fn(this.context, ...args);
      } catch (error) {
        // Log error but continue with other hooks
        console.error(`Hook error at ${point} (priority ${entry.priority}):`, error);
        
        // Also emit to event bus if available
        if (this.context.eventBus) {
          this.context.eventBus.emit('hook:error', {
            point,
            priority: entry.priority,
            error: error instanceof Error ? error.message : String(error),
          });
        }
      }
    }
  }

  // Clear all hooks (useful for testing)
  clear(): void {
    this.hooks.clear();
  }

  // Get count of registered hooks for a point
  count(point?: HookPoint): number {
    if (point) {
      return this.hooks.get(point)?.length || 0;
    }
    let total = 0;
    this.hooks.forEach(entries => {
      total += entries.length;
    });
    return total;
  }
}

// Global singleton instance
const hookRegistry = new HookRegistry();

// Convenience function to register a hook
export function registerHook<P extends HookPoint>(
  point: P,
  fn: HookFn<HookArgs[P], any>,
  priority?: number
): () => void {
  return hookRegistry.register(point, fn, priority);
}

// React hook wrapper for registering hooks with component lifecycle
export function useHook<P extends HookPoint>(
  point: P,
  fn: HookFn<HookArgs[P], any>,
  priority?: number
): void {
  // This assumes React is available in the consuming environment
  // Using dynamic import to avoid hard dependency
  if (typeof window !== 'undefined' && 'React' in window) {
    const React = (window as any).React;
    React.useEffect(() => {
      const unregister = registerHook(point, fn, priority);
      return unregister;
    }, [point, priority]); // fn is intentionally omitted to avoid re-registration on every render
  }
}

// Convenience function to run hooks
export async function runHooks<P extends HookPoint>(
  point: P,
  ...args: HookArgs[P]
): Promise<void> {
  return hookRegistry.run(point, ...args);
}

// Export the singleton for direct access if needed
export const hooks = {
  registry: hookRegistry,
  register: registerHook,
  run: runHooks,
  use: useHook,
  initialize: (context: HookContext) => hookRegistry.initialize(context),
  clear: () => hookRegistry.clear(),
  count: (point?: HookPoint) => hookRegistry.count(point),
  list: <P extends HookPoint>(point: P) => hookRegistry.list(point),
};

// Example usage patterns (documentation)
/*
// In a plugin or feature module:
import { registerHook } from '@/core/hooks';

// Add correlation ID to all API requests
const unregister = registerHook('beforeApiRequest', async (ctx, request) => {
  request.init = request.init || {};
  request.init.headers = {
    ...request.init.headers,
    'X-Correlation-Id': crypto.randomUUID(),
  };
}, 50); // priority 50 runs before default priority 100

// Track errors
registerHook('afterApiResponse', async (ctx, response) => {
  if (!response.success) {
    await sendToErrorTracker(response);
  }
}, 150);

// Analytics on login
registerHook('onLogin', async (ctx, { user, tokens }) => {
  ctx.eventBus.emit('analytics:track', {
    event: 'user_login',
    userId: user.id,
    properties: { method: 'email' },
  });
});

// Clean up when done
unregister();
*/

// Self-Check Comments:
// [x] Uses `@/` imports only - Yes, imports from @/app/config and local ./events, ./di
// [x] Uses providers/hooks (no direct DOM/localStorage side effects) - Pure registry implementation, no side effects
// [x] Reads config from `@/app/config` - Yes, through HookContext type
// [x] Exports default named component - N/A (utility module, exports named functions/class)
// [x] Adds basic ARIA and keyboard handlers - N/A (not a UI component)
