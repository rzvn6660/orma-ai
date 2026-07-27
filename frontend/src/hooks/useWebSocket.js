import { useState, useEffect, useRef } from 'react';

export const useWebSocket = (userId, onMessage) => {
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);
  const reconnectTimerRef = useRef(null);
  const isIntentionalCloseRef = useRef(false);
  
  // Store the latest onMessage callback without triggering a reconnect
  const onMessageRef = useRef(onMessage);
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    if (!userId) return;
    
    // Reset intentional close flag on mount
    isIntentionalCloseRef.current = false;

    const connect = () => {
      // Prevent duplicate connections
      if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
        return;
      }
      
      const token = localStorage.getItem('orma_token');
      const wsUrl = import.meta.env.VITE_API_BASE_URL 
        ? import.meta.env.VITE_API_BASE_URL.replace('http', 'ws') + `/api/notifications/ws/${userId}?token=${token}`
        : `ws://localhost:8000/api/notifications/ws/${userId}?token=${token}`;

      // Connect to WebSocket server
      ws.current = new WebSocket(wsUrl);
      
      ws.current.onopen = () => {
        console.log("Notification WebSocket Connected");
        setIsConnected(true);
        
        // Clear any existing reconnect timer when successfully connected
        if (reconnectTimerRef.current) {
          clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = null;
        }
      };
      
      ws.current.onclose = (event) => {
        setIsConnected(false);
        
        // Don't log expected shutdowns during React Strict Mode cleanup as errors
        if (isIntentionalCloseRef.current) {
          console.log("Notification WebSocket intentionally disconnected (React cleanup)");
          return;
        }

        console.warn(`Notification WebSocket Disconnected (Code: ${event.code}). Attempting reconnect...`);
        
        // Automatic reconnect only for genuine network failures (not intentional close)
        if (!reconnectTimerRef.current) {
          reconnectTimerRef.current = setTimeout(() => {
            reconnectTimerRef.current = null;
            connect();
          }, 3000); // 3 seconds reconnect delay
        }
      };

      ws.current.onerror = (error) => {
        // We do not close the socket here; onclose will fire subsequently if it's fatal
        console.error("WebSocket encountered an error:", error);
      };
      
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Dispatch global event for other components
          window.dispatchEvent(new CustomEvent('orma_websocket_message', { detail: data }));
          
          if (onMessageRef.current) {
            onMessageRef.current(data);
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };
    };

    connect();

    // Cleanup on unmount
    return () => {
      isIntentionalCloseRef.current = true;
      
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }

      if (ws.current) {
        const socket = ws.current;
        
        // Cleanly dispose of listeners to prevent memory leaks during rapid unmounts
        socket.onopen = null;
        socket.onmessage = null;
        socket.onerror = null;
        socket.onclose = null;
        
        /* 
         * React Strict Mode Behavior:
         * In development, React mounts, immediately unmounts, and remounts components.
         * If we call socket.close() while readyState is CONNECTING (0), the browser throws:
         * "WebSocket is closed before the connection is established."
         * To prevent this warning, we only call close() if the socket is already OPEN (1).
         * If it's CONNECTING, we assign a temporary onopen that closes it immediately,
         * ensuring it shuts down cleanly without throwing console errors.
         */
        if (socket.readyState === WebSocket.OPEN) {
          socket.close(1000, "Component unmounted");
        } else if (socket.readyState === WebSocket.CONNECTING) {
          socket.onopen = () => socket.close(1000, "Component unmounted");
        }
        
        ws.current = null;
      }
    };
  }, [userId]); // Only reconnect if userId changes

  return { isConnected };
};
