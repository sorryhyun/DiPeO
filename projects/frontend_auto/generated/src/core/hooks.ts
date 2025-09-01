// FILE: src/core/events.ts
import type { Appointment } from '@/core/contracts';
import type { AuthTokens } from '@/core/contracts';

/**
 * Typed Event Map for cross-app communication.
 * Modules may augment this interface via TS declaration merging to add new events.
 */
export interface EventMap {
  // Analytics and telemetry
  'analytics.track': { event: string; payload?: Record<string, any> };

  // User lifecycle
  'user.login': { userId: string; tokens?: AuthTokens };
  'user.logout': { userId?: string };

  // Appointments and healthcare domain
  'appointment.created': { appointmentId: string };
  'appointment.updated': { appointmentId: string; changes?: Partial<Appointment> };

  // Lab results
  'labresult.completed': { labId: string };

  // Extendable: other modules can declare module augmentation to add events
  [key: string]: any;
}

export type EventHandler<T> = (payload: T, meta?: { ts: string }) => void | Promise<void>;

/**
 * Lightweight, type-safe event bus.
 * - Synchronous emit: calls handlers in registration order; errors are logged but not thrown.
 * - Asynchronous emit: supports sequential or parallel execution.
 * - Handlers are stored per-event; iteration uses a snapshot to avoid mutation during emit.
 * - Returns unsubscribe function from on().
 */
class EventBus<EM extends Record<string, any> = EventMap> {
  private handlers: Map<keyof EM, Set<EventHandler<any>>> = new Map();

  on<K extends keyof EM>(event: K, handler: EventHandler<EM[K]>): () => void {
    let set = this.handlers.get(event);
    if (!set) {
      set = new Set<EventHandler<any>>();
      this.handlers.set(event, set);
    }
    set.add(handler as EventHandler<any>);
    // Return unsubscribe function
    return () => {
      set?.delete(handler as EventHandler<any>);
    };
  }

  off<K extends keyof EM>(event: K, handler?: EventHandler<EM[K]>): void {
    const set = this.handlers.get(event);
    if (!set) return;
    if (handler) {
      set.delete(handler as EventHandler<any>);
    } else {
      this.handlers.delete(event);
    }
  }

  async emit<K extends keyof EM>(
    event: K,
    payload: EM[K],
    options?: { async?: boolean; parallel?: boolean }
  ): Promise<void> {
    const handlers = Array.from(this.handlers.get(event) ?? []);
    if (handlers.length === 0) return;

    const ts = new Date().toISOString();

    const invoke = async (h: EventHandler<any>) => {
      try {
        await Promise.resolve(h(payload, { ts }));
      } catch (err) {
        // Best-effort logging; do not throw to avoid breaking app lifecycle
        // eslint-disable-next-line no-console
        console.error('[EventBus]', `Error in handler for event "${String(event)}"`, err);
      }
    };

    if (options?.async) {
      if (options.parallel) {
        // Parallel execution
        await Promise.all(handlers.map((h) => invoke(h))).catch((e) => {
          // Catch any unexpected errors from Promise.all
          // eslint-disable-next-line no-console
          console.error('[EventBus]', 'Parallel emit error', e);
        });
      } else {
        // Sequential asynchronous execution
        for (const h of handlers) {
          await invoke(h);
        }
      }
    } else {
      // Synchronous execution: fire and forget (errors logged inside)
      for (const h of handlers) {
        try {
          (h as any)(payload, { ts });
        } catch (err) {
          // eslint-disable-next-line no-console
          console.error('[EventBus]', 'Sync handler error', err);
        }
      }
    }
  }

  clear(): void {
    this.handlers.clear();
  }
}

/**
 * App-wide singleton event bus instance.
 * Consumers should import { eventBus, on, off, emit } from '@/core/events'
 */
export const eventBus = new EventBus<EventMap>();

/**
 * Convenience wrappers for consumer code.
 */
export const on = <K extends keyof EventMap>(
  event: K,
  handler: (payload: EventMap[K], meta?: { ts: string }) => void | Promise<void>
) => eventBus.on(event, handler as EventHandler<EventMap[K]>);

export const off = <K extends keyof EventMap>(
  event: K,
  handler?: (payload: EventMap[K], meta?: { ts: string }) => void | Promise<void>
) => eventBus.off(event, handler as any);

export const emit = <K extends keyof EventMap>(
  event: K,
  payload: EventMap[K],
  options?: { async?: boolean; parallel?: boolean }
) => eventBus.emit(event, payload, options);

/**
 * Factory to create ephemeral/event-scoped buses (useful for tests or feature-scoped communication)
 */
export function createEventBus<EM extends Record<string, any> = EventMap>(): EventBus<EM> {
  return new EventBus<EM>();
}

// Self-check markers
// [x] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)