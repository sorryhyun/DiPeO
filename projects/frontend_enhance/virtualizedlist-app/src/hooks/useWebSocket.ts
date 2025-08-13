// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react';

export function useWebSocket(url: string, onMessage?: (payload: any) => void, enabled: boolean = true) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);

  useEffect(() => {
    if (!enabled) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    const onOpen = () => setConnected(true);
    const onClose = () => setConnected(false);
    const onErr = () => setConnected(false);

    ws.addEventListener('open', onOpen);
    ws.addEventListener('close', onClose);
    ws.addEventListener('error', onErr);
    ws.addEventListener('message', (evt) => {
      const data = JSON.parse(evt.data);
      setMessages((m) => [...m, data]);
      onMessage?.(data);
    });

    return () => {
      ws.removeEventListener('open', onOpen);
      ws.removeEventListener('close', onClose);
      ws.removeEventListener('error', onErr);
      ws.close();
    };
  }, [url, enabled]);

  return { connected, messages };
}