import { useState, useEffect, useRef } from 'react';

// Singleton socket connection manager to prevent duplicate connections per tab
let globalSocket = null;
let activeUserId = null;
let reconnectTimer = null;
const listeners = new Set();

const notifyListeners = (data) => {
  listeners.forEach(fn => {
    try {
      fn(data);
    } catch (err) {
      console.error('[ORMA WS] Listener callback error:', err);
    }
  });
};

const getWsUrl = (userId) => {
  const token = localStorage.getItem('orma_token');
  const base = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000');
  const wsPrefix = base.startsWith('https') ? base.replace(/^https/, 'wss') : base.replace(/^http/, 'ws');
  return `${wsPrefix}/api/notifications/ws/${userId}?token=${token}`;
};

const setupGlobalSocket = (userId) => {
  if (!userId) return;
  if (globalSocket && activeUserId === userId && (globalSocket.readyState === WebSocket.OPEN || globalSocket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  // Close old socket if switching users
  if (globalSocket) {
    try {
      globalSocket.onclose = null;
      globalSocket.close();
    } catch (_) {}
    globalSocket = null;
  }

  activeUserId = userId;
  const url = getWsUrl(userId);
  
  try {
    const ws = new WebSocket(url);
    globalSocket = ws;

    ws.onopen = () => {
      console.log(`[ORMA WS] Connected | user_id: ${userId}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log(`[ORMA WS EVENT] type: ${data.type} | alert_id: ${data.alert_id || data.id || 'N/A'} | elder: ${data.elder_name || data.elder_id || 'N/A'} | status: ${data.status || 'N/A'}`);
        
        // Dispatch global window event for all listeners and cross-component subscribers
        window.dispatchEvent(new CustomEvent('orma_websocket_message', { detail: data }));
        notifyListeners(data);
      } catch (err) {
        console.error('[ORMA WS] Error parsing message:', err);
      }
    };

    ws.onerror = (err) => {
      console.warn('[ORMA WS] WebSocket error:', err);
    };

    ws.onclose = (event) => {
      if (globalSocket === ws) {
        globalSocket = null;
      }
      // Reconnect after 3s if still on same user
      if (activeUserId === userId && !reconnectTimer) {
        reconnectTimer = setTimeout(() => {
          reconnectTimer = null;
          setupGlobalSocket(userId);
        }, 3000);
      }
    };
  } catch (err) {
    console.error('[ORMA WS] Connection failed:', err);
  }
};

export const useWebSocket = (userId, onMessage) => {
  const [isConnected, setIsConnected] = useState(() => Boolean(globalSocket && globalSocket.readyState === WebSocket.OPEN));
  const onMessageRef = useRef(onMessage);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    if (!userId) return;

    setupGlobalSocket(userId);

    const listenerWrapper = (data) => {
      if (onMessageRef.current) {
        onMessageRef.current(data);
      }
    };

    listeners.add(listenerWrapper);

    const checkStatus = () => {
      setIsConnected(Boolean(globalSocket && globalSocket.readyState === WebSocket.OPEN));
    };

    const statusInterval = setInterval(checkStatus, 2000);

    return () => {
      listeners.delete(listenerWrapper);
      clearInterval(statusInterval);
    };
  }, [userId]);

  return { isConnected };
};

