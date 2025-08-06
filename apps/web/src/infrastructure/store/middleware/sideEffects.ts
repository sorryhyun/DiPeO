import { StateCreator, StoreMutatorIdentifier } from 'zustand';
import { UnifiedStore, MiddlewareContext, SideEffect } from '../types';

/**
 * Side effects middleware for handling async operations and external interactions
 */

// ===== Side Effect Registry =====

class SideEffectRegistry {
  private effects: Map<string, SideEffect[]> = new Map();

  register(actionPattern: string, effect: SideEffect): void {
    const existing = this.effects.get(actionPattern) || [];
    this.effects.set(actionPattern, [...existing, effect]);
  }

  unregister(actionPattern: string, effect: SideEffect): void {
    const existing = this.effects.get(actionPattern) || [];
    this.effects.set(
      actionPattern,
      existing.filter(e => e !== effect)
    );
  }

  getEffects(action: string): SideEffect[] {
    const effects: SideEffect[] = [];
    
    // Check for exact matches and patterns
    for (const [pattern, patternEffects] of this.effects.entries()) {
      if (this.matchesPattern(action, pattern)) {
        effects.push(...patternEffects);
      }
    }
    
    return effects;
  }

  private matchesPattern(action: string, pattern: string): boolean {
    // Support wildcards: "diagram.*" matches "diagram.addNode", "diagram.deleteNode", etc.
    if (pattern.includes('*')) {
      const regex = new RegExp(`^${  pattern.replace(/\*/g, '.*')  }$`);
      return regex.test(action);
    }
    return action === pattern;
  }
}

const registry = new SideEffectRegistry();

// ===== Common Side Effects =====

// Auto-save side effect
export const autoSaveSideEffect: SideEffect = {
  trigger: (context) => {
    // Trigger on any diagram or person modification
    return context.action.startsWith('diagram.') || 
           context.action.startsWith('person.');
  },
  execute: async (context) => {
    // Debounced save logic would go here
    console.log('[AutoSave] Triggered by:', context.action);
    // In real implementation, this would call GraphQL mutation
  },
};

// Analytics side effect
export const analyticsSideEffect: SideEffect = {
  trigger: (context) => {
    // Track specific user actions
    const trackedActions = [
      'diagram.addNode',
      'diagram.deleteNode',
      'execution.start',
      'execution.stop',
    ];
    return trackedActions.includes(context.action);
  },
  execute: async (context) => {
    console.log('[Analytics] Tracking:', context.action, context.payload);
    // Send to analytics service
  },
};

// Validation side effect
export const validationSideEffect: SideEffect = {
  trigger: (context) => {
    // Validate on diagram changes
    return context.action.startsWith('diagram.') && 
           !context.action.includes('Silent');
  },
  execute: async (context) => {
    console.log('[Validation] Checking diagram after:', context.action);
    // Run validation and update UI if needed
  },
};

// WebSocket notification side effect
export const websocketSideEffect: SideEffect = {
  trigger: (context) => {
    // Send updates for collaborative features
    return context.action.startsWith('diagram.') || 
           context.action.startsWith('execution.');
  },
  execute: async (context) => {
    console.log('[WebSocket] Broadcasting:', context.action);
    // Send update via WebSocket
  },
};

// ===== Middleware Implementation =====

type SideEffectsMiddleware = <
  T extends UnifiedStore,
  Mps extends [StoreMutatorIdentifier, unknown][] = [],
  Mcs extends [StoreMutatorIdentifier, unknown][] = []
>(
  initializer: StateCreator<T, Mps, Mcs, T>
) => StateCreator<T, Mps, Mcs, T>;

export const sideEffectsMiddleware: SideEffectsMiddleware = (config) => (set, get, api) => {
  // Track current action for context
  let currentAction: string | null = null;
  let currentPayload: unknown = null;

  // Wrap set function to intercept actions
  const wrappedSet = (partial: any, replace?: any, action?: any) => {
    // Extract action info if available
    if (typeof action === 'object' && action && 'type' in action) {
      currentAction = action.type as string;
      currentPayload = 'payload' in action ? action.payload : partial;
    } else if (typeof action === 'string') {
      currentAction = action;
      currentPayload = partial;
    }

    // Call original set with proper arguments
    if (replace === undefined) {
      (set as any)(partial);
    } else if (action === undefined) {
      (set as any)(partial, replace);
    } else {
      (set as any)(partial, replace, action);
    }

    // Execute side effects after state update
    if (currentAction) {
      const context: MiddlewareContext = {
        action: currentAction,
        payload: currentPayload,
        timestamp: Date.now(),
      };

      const effects = registry.getEffects(currentAction);
      
      // Execute all matching side effects
      Promise.all(
        effects
          .filter(effect => effect.trigger(context))
          .map(effect => effect.execute(context).catch(error => {
            console.error(`[SideEffect] Error in ${currentAction}:`, error);
          }))
      );
    }

    // Reset action tracking
    currentAction = null;
    currentPayload = null;
  };

  return config(wrappedSet as any, get, api);
};

// ===== Side Effect Hooks =====

export function useSideEffect(
  actionPattern: string,
  effect: SideEffect
): void {
  // Register on mount, unregister on unmount
  // This would use React.useEffect in actual implementation
  registry.register(actionPattern, effect);
}

export function registerGlobalSideEffect(
  actionPattern: string,
  effect: SideEffect
): () => void {
  registry.register(actionPattern, effect);
  return () => registry.unregister(actionPattern, effect);
}

// ===== Debounced Side Effects =====

export function createDebouncedSideEffect(
  effect: SideEffect,
  delay: number
): SideEffect {
  let timeoutId: NodeJS.Timeout | null = null;

  return {
    trigger: effect.trigger,
    execute: async (context) => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      return new Promise((resolve) => {
        timeoutId = setTimeout(async () => {
          await effect.execute(context);
          resolve();
        }, delay);
      });
    },
  };
}

// ===== Throttled Side Effects =====

export function createThrottledSideEffect(
  effect: SideEffect,
  interval: number
): SideEffect {
  let lastExecutionTime = 0;
  let pendingExecution: (() => Promise<void>) | null = null;
  let timeoutId: NodeJS.Timeout | null = null;

  return {
    trigger: effect.trigger,
    execute: async (context) => {
      const now = Date.now();
      const timeSinceLastExecution = now - lastExecutionTime;

      if (timeSinceLastExecution >= interval) {
        lastExecutionTime = now;
        return effect.execute(context);
      } else {
        // Schedule execution for later
        pendingExecution = () => effect.execute(context);
        
        if (!timeoutId) {
          const remainingTime = interval - timeSinceLastExecution;
          timeoutId = setTimeout(async () => {
            if (pendingExecution) {
              lastExecutionTime = Date.now();
              await pendingExecution();
              pendingExecution = null;
            }
            timeoutId = null;
          }, remainingTime);
        }
      }
    },
  };
}

// ===== Conditional Side Effects =====

export function createConditionalSideEffect(
  condition: (state: UnifiedStore) => boolean,
  effect: SideEffect,
  getState: () => UnifiedStore
): SideEffect {
  return {
    trigger: (context) => {
      // Check both the effect's trigger and the additional condition
      return effect.trigger(context) && condition(getState());
    },
    execute: effect.execute,
  };
}

// ===== Register default side effects =====

export function registerDefaultSideEffects(): void {
  // Register debounced auto-save
  registerGlobalSideEffect(
    'diagram.*',
    createDebouncedSideEffect(autoSaveSideEffect, 1000)
  );

  // Register throttled analytics
  registerGlobalSideEffect(
    '*',
    createThrottledSideEffect(analyticsSideEffect, 5000)
  );

  // Register immediate validation
  registerGlobalSideEffect('diagram.*', validationSideEffect);

  // Register WebSocket updates
  registerGlobalSideEffect('*', websocketSideEffect);
}