import { useCallback, useEffect, useRef, useState } from 'react';

const DEFAULT_WS_URL = 'ws://localhost:8000/ws';

function useWebSocket({ enabled, onOpen, onClose }) {
  const socketRef = useRef(null);
  const reconnectRef = useRef(null);
  const enabledRef = useRef(enabled);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [message, setMessage] = useState(null);

  const disconnect = useCallback(() => {
    if (reconnectRef.current) {
      clearTimeout(reconnectRef.current);
      reconnectRef.current = null;
    }

    if (socketRef.current) {
      socketRef.current.onopen = null;
      socketRef.current.onmessage = null;
      socketRef.current.onclose = null;
      socketRef.current.onerror = null;
      socketRef.current.close();
      socketRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const connect = useCallback(() => {
    if (!enabledRef.current) {
      return;
    }

    if (socketRef.current && (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setIsConnecting(true);
    const socket = new WebSocket(import.meta.env.VITE_WS_URL || DEFAULT_WS_URL);
    socketRef.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
      setIsConnecting(false);
      onOpen?.();
    };

    socket.onmessage = (event) => {
      try {
        setMessage(JSON.parse(event.data));
      } catch {
        setMessage({ error: 'Invalid WebSocket payload' });
      }
    };

    socket.onerror = () => {
      setIsConnected(false);
      setIsConnecting(false);
    };

    socket.onclose = () => {
      setIsConnected(false);
      setIsConnecting(false);
      onClose?.();

      if (enabledRef.current) {
        reconnectRef.current = setTimeout(connect, 3000);
      }
    };
  }, [onClose, onOpen]);

  const send = useCallback((payload) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(payload);
    }
  }, []);

  useEffect(() => {
    enabledRef.current = enabled;
    if (enabled) {
      connect();
      return () => {};
    }

    disconnect();
    return undefined;
  }, [connect, disconnect, enabled]);

  useEffect(() => () => disconnect(), [disconnect]);

  return {
    isConnected,
    isConnecting,
    message,
    send,
    connect,
    disconnect,
  };
}

export default useWebSocket;