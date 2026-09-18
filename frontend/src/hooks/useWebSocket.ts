import { useEffect, useRef, useState, useCallback } from 'react';

type WSStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export function useWebSocket(url: string) {
  const ws = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<WSStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<unknown>(null);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    setStatus('connecting');
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => setStatus('connected');
    socket.onmessage = (e) => {
      try { setLastMessage(JSON.parse(e.data)); }
      catch { setLastMessage(e.data); }
    };
    socket.onerror = () => setStatus('error');
    socket.onclose = () => {
      setStatus('disconnected');
      setTimeout(connect, 3000); // auto-reconnect
    };
  }, [url]);

  const disconnect = useCallback(() => {
    ws.current?.close();
    ws.current = null;
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { status, lastMessage };
}
