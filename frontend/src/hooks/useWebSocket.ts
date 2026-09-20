// AquaGuard AI - Enhanced WebSocket Hook (Phase 8)
// Supports multiple WS channels + message history + typed events
import { useEffect, useRef, useState, useCallback } from 'react';

export type WSStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WSOptions {
  maxHistory?: number;      // keep last N messages
  reconnectMs?: number;     // reconnect delay
}

export function useWebSocket<T = unknown>(url: string, options: WSOptions = {}) {
  const { maxHistory = 50, reconnectMs = 3000 } = options;
  const ws        = useRef<WebSocket | null>(null);
  const reconnect = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [status,      setStatus]      = useState<WSStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<T | null>(null);
  const [history,     setHistory]     = useState<T[]>([]);
  const [connectedAt, setConnectedAt] = useState<Date | null>(null);
  const [msgCount,    setMsgCount]    = useState(0);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    setStatus('connecting');
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => {
      setStatus('connected');
      setConnectedAt(new Date());
    };

    socket.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as T;
        setLastMessage(data);
        setMsgCount(c => c + 1);
        setHistory(h => [...h.slice(-(maxHistory - 1)), data]);
      } catch {
        // non-JSON message ignored
      }
    };

    socket.onerror = () => setStatus('error');

    socket.onclose = () => {
      setStatus('disconnected');
      reconnect.current = setTimeout(connect, reconnectMs);
    };
  }, [url, maxHistory, reconnectMs]);

  const disconnect = useCallback(() => {
    if (reconnect.current) clearTimeout(reconnect.current);
    ws.current?.close();
    ws.current = null;
    setStatus('disconnected');
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { status, lastMessage, history, connectedAt, msgCount };
}
