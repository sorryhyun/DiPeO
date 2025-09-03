// FILE: src/core/events.ts

import { User, Patient, Appointment, ApiResult } from '@/core/contracts'

// Core Events: Typed EventBus for cross-module communication.
// This module purposely avoids circular imports by exporting the bus from here
// and letting other modules import { eventBus, on, off, emit } from this file.

export type EventMap = {
  'analytics.track': { event: string; payload?: Record<string, any> }
  'user.login': { userId: string; tokens?: { accessToken?: string; refreshToken?: string } }
  'user.logout': { userId?: string }
  'appointment.created': { appointmentId: string }
  'appointment.updated': { appointmentId: string; changes?: Partial<Appointment> }
  'labresult.completed': { labId: string }
  // Allow augmentation by other modules:
  [key: string]: any
}

export type EventHandler<T> = (payload: T, meta?: { ts: string }) => void | Promise<void>

class EventBus<EM extends Record<string, any> = EventMap> {
  private handlers = new Map<string, Set<EventHandler<any>>>()

  on<K extends keyof EM>(event: K, handler: EventHandler<EM[K]>): () => void {
    const key = String(event)
    let set = this.handlers.get(key)
    if (!set) {
      set = new Set<EventHandler<any>>()
      this.handlers.set(key, set)
    }
    set.add(handler as EventHandler<any>)
    // unsubscribe function
    return () => this.off(event, handler)
  }

  off<K extends keyof EM>(event: K, handler?: EventHandler<EM[K]>): void {
    const key = String(event)
    const set = this.handlers.get(key)
    if (!set) return
    if (!handler) {
      // remove all handlers for this event
      this.handlers.delete(key)
      return
    }
    set.delete(handler as EventHandler<any>)
    if (set.size === 0) this.handlers.delete(key)
  }

  async emit<K extends keyof EM>(
    event: K,
    payload: EM[K],
    options?: { async?: boolean }
  ): Promise<void> {
    const key = String(event)
    const set = this.handlers.get(key)
    if (!set || set.size === 0) return

    const ts = new Date().toISOString()
    const snapshot = Array.from(set)

    // If explicit async mode requested, await handlers sequentially
    if (options?.async) {
      for (const handler of snapshot) {
        try {
          await (handler as EventHandler<any>)(payload, { ts })
        } catch (err) {
          // Swallow to avoid breaking app flow; log for dev/debugger
          try {
            // eslint-disable-next-line no-console
            console.error('[EventBus] async handler error', err)
          } catch {
            // ignore
          }
        }
      }
      return
    }

    // Default: fire-and-forget with promise handling to avoid unhandled rejections
    for (const handler of snapshot) {
      try {
        const r = (handler as EventHandler<any>)(payload, { ts })
        if (r && typeof (r as any).then === 'function') {
          (r as Promise<any>).catch((e) => {
            try {
              // eslint-disable-next-line no-console
              console.error('[EventBus] handler promise rejection', e)
            } catch {
              // ignore
            }
          })
        }
      } catch (err) {
        try {
          // eslint-disable-next-line no-console
          console.error('[EventBus] handler error', err)
        } catch {
          // ignore
        }
      }
    }
  }

  clear(): void {
    this.handlers.clear()
  }
}

// Singleton instance for app-wide usage
export const eventBus = new EventBus<EventMap>()

// Convenience bindings
export const on = eventBus.on.bind(eventBus)
export const off = eventBus.off.bind(eventBus)
export const emit = eventBus.emit.bind(eventBus)

// Self-Check
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)