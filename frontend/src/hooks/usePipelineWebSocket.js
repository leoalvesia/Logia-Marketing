import { useEffect, useRef, useCallback, useState } from "react";
import { usePipelineStore } from "@/stores/pipelineStore";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

// Backoff sequence: 1s, 2s, 4s, 8s, 30s (capped)
const BACKOFF_DELAYS = [1000, 2000, 4000, 8000, 30000];
const HEARTBEAT_INTERVAL_MS = 30_000;

export function usePipelineWebSocket(sessionId) {
  const ws = useRef(null);
  const heartbeatTimer = useRef(null);
  const reconnectTimer = useRef(null);
  const retryCount = useRef(0);
  const offlineQueue = useRef([]);
  const isMounted = useRef(true);

  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const setPipelineState = usePipelineStore((s) => s.setPipelineState);
  const handleWsMessage = usePipelineStore((s) => s.handleWsMessage);

  const clearHeartbeat = () => {
    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
      heartbeatTimer.current = null;
    }
  };

  const startHeartbeat = useCallback(() => {
    clearHeartbeat();
    heartbeatTimer.current = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ type: "ping" }));
      }
    }, HEARTBEAT_INTERVAL_MS);
  }, []);

  const flushOfflineQueue = useCallback(() => {
    while (offlineQueue.current.length > 0) {
      const msg = offlineQueue.current.shift();
      ws.current?.send(JSON.stringify(msg));
    }
  }, []);

  const connect = useCallback(() => {
    if (!sessionId || !isMounted.current) return;

    setConnectionStatus(retryCount.current > 0 ? "reconnecting" : "connecting");

    const socket = new WebSocket(`${WS_URL}/ws/pipeline/${sessionId}`);
    ws.current = socket;

    socket.onopen = () => {
      if (!isMounted.current) return;
      console.log("[WS] connected:", sessionId);
      retryCount.current = 0;
      setConnectionStatus("connected");
      startHeartbeat();
      flushOfflineQueue();
    };

    socket.onmessage = (event) => {
      if (!isMounted.current) return;
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "pong") return; // heartbeat ack
        const { state, data } = msg;
        if (state) setPipelineState(state);
        if (handleWsMessage) handleWsMessage(msg);
      } catch {
        // malformed message — ignore
      }
    };

    socket.onclose = () => {
      if (!isMounted.current) return;
      console.log("[WS] disconnected:", sessionId);
      clearHeartbeat();
      setConnectionStatus("disconnected");

      // Exponential backoff reconnect
      const delay =
        BACKOFF_DELAYS[Math.min(retryCount.current, BACKOFF_DELAYS.length - 1)];
      retryCount.current += 1;

      reconnectTimer.current = setTimeout(() => {
        if (isMounted.current) connect();
      }, delay);
    };

    socket.onerror = (err) => {
      console.error("[WS] error:", err);
      socket.close();
    };
  }, [sessionId, setPipelineState, handleWsMessage, startHeartbeat, flushOfflineQueue]);

  useEffect(() => {
    isMounted.current = true;
    connect();
    return () => {
      isMounted.current = false;
      clearHeartbeat();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect]);

  const send = useCallback((data) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    } else {
      // Queue message to send once reconnected
      offlineQueue.current.push(data);
    }
  }, []);

  return { send, connectionStatus };
}
