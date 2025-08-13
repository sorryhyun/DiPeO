import { useEffect, useState } from "react";

// Debounced value hook (shared utility)
export function useDebouncedValue<T>(value: T, delay = 250): T {
  const [debounced, setDebounced] = useState<T>(value);
  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

// Lightweight container size hook (optional helper)
export function useContainerSize<T extends HTMLElement = HTMLDivElement>(
  ref: React.RefObject<T>
): { height: number; width: number } {
  const [size, setSize] = useState({ height: 0, width: 0 });
  useEffect(() => {
    if (typeof window === "undefined") return;
    const el = ref.current;
    if (!el) return;
    const update = () =>
      setSize({ height: el.clientHeight, width: el.clientWidth });

    update();
    if (typeof ResizeObserver !== "undefined") {
      const ro = new ResizeObserver(update);
      ro.observe(el);
      return () => ro.disconnect();
    }
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, [ref]);
  return size;
}