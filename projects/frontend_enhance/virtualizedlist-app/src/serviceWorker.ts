// src/serviceWorker.ts
// Simple service worker registration scaffold. Adapt to your project setup.

export async function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    try {
      const reg = await navigator.serviceWorker.register('/service-worker.js');
      // You can add logging/telemetry here
      return reg;
    } catch (e) {
      // Progressive enhancement: swallow errors, degrade gracefully
      // eslint-disable-next-line no-console
      console.warn('ServiceWorker registration failed:', e);
    }
  }
  return null;
}