// FILE: src/core/events.ts

import type { User, Patient, Appointment, AuthTokens } from '@/core/contracts'
import { isDevelopment } from '@/app/config'

// Event map and typing
export type EventMap = {
  'analytics.track': { event: string; payload?: Record<string, any> }
  'user.login': { userId: string; tokens?: AuthTokens }
  'user.logout': { userId?: string }
  'appointment.created': { appointmentId: string }
  'appointment.updated': { appointmentId: string; changes?: Partial<Appointment> }
  'labresult.completed': { labId: string }
  // Module augmentation can extend this interface to add new events
  [key: string]: any
}

// Generic event handler type
export type EventHandler<T> = (payload: T, meta?: { ts: string }) => void | Promise<void>

// Lightweight, typed EventBus
export class EventBus<EM extends Record<string, any> = EventMap> {
  private handlers: Map<string, Set<EventHandler<any>>> = new Map()

  on<K extends keyof EM>(event: K, handler: EventHandler<EM[K]>): () => void {
    const key = event as string
    let set = this.handlers.get(key)
    if (!set) {
      set = new Set<EventHandler<any>>()
      this.handlers.set(key, set)
    }
    set.add(handler as EventHandler<any>)
    // Return unsubscribe helper
    return () => {
      set?.delete(handler as EventHandler<any>)
    }
  }

  off<K extends keyof EM>(event: K, handler?: EventHandler<EM[K]>): void {
    const key = event as string
    const set = this.handlers.get(key)
    if (!set) return
    if (handler) {
      set.delete(handler as EventHandler<any>)
    } else {
      set.clear()
    }
  }

  async emit<K extends keyof EM>(
    event: K,
    payload: EM[K],
    options?: { async?: boolean; parallel?: boolean }
  ): Promise<void> {
    const key = event as string
    const handlers = Array.from(this.handlers.get(key) ?? [])
    const ts = new Date().toISOString()

    // Internal wrapper to execute a single handler with error catching
    const runHandler = async (h: EventHandler<EM[K]>) => {
      try {
        const res = (h as any)(payload, { ts })
        if (res && typeof (res as any).then === 'function') {
          await (res as Promise<void>)
        }
      } catch (err) {
        if (isDevelopment) {
          // eslint-disable-next-line no-console
          console.error('EventBus handler error', { event, payload, error: err })
        }
      }
    }

    if (handlers.length === 0) return

    const runSequential = !(options?.parallel)
    // If parallel requested, run all in parallel
    if (options?.parallel) {
      await Promise.all(handlers.map((h) => runHandler(h as EventHandler<any>)))
      return
    }

    // If async flag requested, await each handler in sequence (but not fire-and-forget)
    if (options?.async) {
      for (const h of handlers) {
        await runHandler(h as EventHandler<any>)
      }
      return
    }

    // Default: fire-and-forget synchronous-ish emission
    for (const h of handlers) {
      try {
        const res = (h as any)(payload, { ts })
        if (res && typeof (res as any).then === 'function') {
          // Attach a catch to prevent unhandled rejections
          (res as Promise<void>).catch((err) => {
            if (isDevelopment) {
              // eslint-disable-next-line no-console
              console.error('EventBus async handler error (fire-and-forget)', { event, payload, error: err })
            }
          })
        }
      } catch (err) {
        if (isDevelopment) {
          // eslint-disable-next-line no-console
          console.error('EventBus handler error (fire-and-forget)', { event, payload, error: err })
        }
      }
      if (!runSequential) break
    }
  }

  clear(): void {
    this.handlers.clear()
  }
}

// Factory to create ephemeral buses if needed
export function createEventBus<EM extends Record<string, any> = EventMap>(): EventBus<EM> {
  return new EventBus<EM>()
}

// Singleton instance for app-wide usage
export const eventBus = createEventBus<EventMap>()

// Convenience exports wrapping the singleton
export const on = <K extends keyof EventMap>(
  event: K,
  handler: EventHandler<EventMap[K]>
): (() => void) => eventBus.on(event, handler)

export const off = <K extends keyof EventMap>(
  event: K,
  handler?: EventHandler<EventMap[K]>
): void => eventBus.off(event, handler)

export const emit = <K extends keyof EventMap>(
  event: K,
  payload: EventMap[K],
  options?: { async?: boolean; parallel?: boolean }
): Promise<void> => eventBus.emit(event, payload, options)

// Optional: allow module augmentation for new events
// declare module '@/core/events' {
//   interface EventMap {
//     'myplugin.event': { data: string; ok?: boolean }
//   }
// }

// Self-check comments
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)