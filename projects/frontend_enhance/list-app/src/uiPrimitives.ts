// src/uiPrimitives.ts
"use client";

export const t = (key: string, fallback?: string) => {
  // Simple stub; replace with your i18n library hook (e.g., react-i18next)
  // Return fallback if provided, else the key
  return fallback ?? key;
};

// Small token-based class helpers (you can swap to clsx/macro if desired)
export const cx = (...classes: (string | false | null | undefined)[]) =>
  classes.filter(Boolean).join(" ");

export const UI = {
  loader: "inline-block w-4 h-4 border-2 border-current border-t-transparent animate-spin",
  emptyState: "text-gray-500",
  errorState: "text-red-600",
} as const;