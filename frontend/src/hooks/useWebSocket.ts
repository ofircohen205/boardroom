import { useState, useCallback, useRef, useEffect } from "react";
import type { Market, WSMessage, AnalysisState } from "../types";
import type { ComparisonResult } from "../types/comparison";
import { useAuth } from "@/contexts/AuthContext";

const WS_BASE_URL = "ws://localhost:8000/ws/analyze";

// Connection states
export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "reconnecting";

// Reconnection config
const INITIAL_RETRY_DELAY = 1000; // 1 second
const MAX_RETRY_DELAY = 30000; // 30 seconds
const MAX_RETRY_ATTEMPTS = 5;
const BACKOFF_MULTIPLIER = 2;

export function useWebSocket() {
  const { token } = useAuth();
  const [state, setState] = useState<AnalysisState>({
    ticker: null,
    market: "US",
    fundamental: null,
    sentiment: null,
    technical: null,
    risk: null,
    decision: null,
    activeAgents: new Set(),
    completedAgents: new Set(),
    failedAgents: new Map(),
    vetoed: false,
    error: null,
  });
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  const [latestNotification, setLatestNotification] = useState<Record<string, unknown> | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCountRef = useRef(0);
  const retryDelayRef = useRef(INITIAL_RETRY_DELAY);
  const shouldReconnectRef = useRef(false);
  const lastRequestRef = useRef<{ type: string; data: Record<string, unknown> } | null>(null);

  // Backward compatibility - isConnected derived from connectionStatus
  const isConnected = connectionStatus === "connected";

  // Clear reconnection timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Reset reconnection state
  const resetReconnectState = useCallback(() => {
    retryCountRef.current = 0;
    retryDelayRef.current = INITIAL_RETRY_DELAY;
    shouldReconnectRef.current = false;
    clearReconnectTimeout();
  }, [clearReconnectTimeout]);

  // Calculate next retry delay with exponential backoff
  const getNextRetryDelay = useCallback(() => {
    const delay = Math.min(retryDelayRef.current, MAX_RETRY_DELAY);
    retryDelayRef.current *= BACKOFF_MULTIPLIER;
    return delay;
  }, []);

  // Attempt to reconnect - stored in ref to avoid circular dependency
  const attemptReconnectRef = useRef<(() => void) | null>(null);

  const attemptReconnect = useCallback(() => {
    if (attemptReconnectRef.current) {
      attemptReconnectRef.current();
    }
  }, []);

  // Setup WebSocket handlers
  const setupWebSocket = useCallback(
    (ws: WebSocket, onMessage: (msg: WSMessage) => void) => {
      ws.onopen = () => {
        console.log("WebSocket connected");
        setConnectionStatus("connected");
        resetReconnectState();

        // Send the pending request
        if (lastRequestRef.current) {
          ws.send(JSON.stringify(lastRequestRef.current.data));
        }
      };

      ws.onmessage = (event) => {
        const msg: WSMessage = JSON.parse(event.data);

        // Handle notification messages separately (not tied to analysis session)
        if (msg.type === "notification") {
          console.log("Notification received:", msg.data);
          setLatestNotification(msg.data);
          return;
        }

        onMessage(msg);
      };

      ws.onclose = (event) => {
        console.log("WebSocket closed", event.code, event.reason);
        setConnectionStatus("disconnected");

        // Only attempt reconnection if:
        // 1. The close was unexpected (not clean)
        // 2. Reconnection is enabled
        // 3. We have a request to retry
        if (!event.wasClean && shouldReconnectRef.current && lastRequestRef.current) {
          console.log("Connection lost unexpectedly, will attempt reconnection...");
          setState((prev) => ({
            ...prev,
            error: `Connection lost. Reconnecting... (Attempt ${retryCountRef.current + 1}/${MAX_RETRY_ATTEMPTS})`,
          }));
          attemptReconnect();
        }
      };

      ws.onerror = (event) => {
        console.error("WebSocket error:", event);
        setConnectionStatus("disconnected");

        // Don't set error here - let onclose handle reconnection
        // The error will be set if max retries are reached
      };
    },
    [resetReconnectState, attemptReconnect]
  );

  // Effect to handle disconnection when token changes (e.g., logout)
  useEffect(() => {
    return () => {
      shouldReconnectRef.current = false;
      clearReconnectTimeout();
      wsRef.current?.close();
    };
  }, [token, clearReconnectTimeout]);

  const analyze = useCallback(
    (ticker: string, market: Market = "US", mode: string = "standard") => {
      // Close existing connection
      if (wsRef.current && wsRef.current.readyState < 2) {
        shouldReconnectRef.current = false;
        clearReconnectTimeout();
        wsRef.current.close();
      }

      // Reset state for new analysis
      setState({
        ticker,
        market,
        fundamental: null,
        sentiment: null,
        technical: null,
        risk: null,
        decision: null,
        activeAgents: new Set(),
        completedAgents: new Set(),
        failedAgents: new Map(),
        vetoed: false,
        error: null,
      });

      // Enable reconnection for this request
      shouldReconnectRef.current = true;
      lastRequestRef.current = {
        type: "analyze",
        data: { ticker, market, mode },
      };

      // If this is a retry, keep the existing retry count
      // Otherwise, reset it
      if (connectionStatus !== "reconnecting") {
        retryCountRef.current = 0;
        retryDelayRef.current = INITIAL_RETRY_DELAY;
      }

      const wsUrl = `${WS_BASE_URL}?token=${token || ""}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      setConnectionStatus("connecting");

      setupWebSocket(ws, (msg: WSMessage) => {
        setState((prev) => {
          // Ignore messages from a previous analysis session
          if (prev.ticker !== ticker) return prev;

          const newState = { ...prev };

          switch (msg.type) {
            case "analysis_started":
              newState.activeAgents = new Set();
              newState.completedAgents = new Set();
              newState.failedAgents = new Map();
              break;
            case "agent_started":
              if (msg.agent) {
                newState.activeAgents = new Set(prev.activeAgents).add(msg.agent);
              }
              break;

            case "agent_completed":
              if (msg.agent) {
                newState.activeAgents = new Set(prev.activeAgents);
                newState.activeAgents.delete(msg.agent);
                newState.completedAgents = new Set(prev.completedAgents).add(msg.agent);

                switch (msg.agent) {
                  case "fundamental":
                    newState.fundamental = msg.data as unknown as typeof newState.fundamental;
                    break;
                  case "sentiment":
                    newState.sentiment = msg.data as unknown as typeof newState.sentiment;
                    break;
                  case "technical":
                    newState.technical = msg.data as unknown as typeof newState.technical;
                    break;
                  case "risk":
                    newState.risk = msg.data as unknown as typeof newState.risk;
                    break;
                }
              }
              break;

            case "agent_error":
              if (msg.agent) {
                newState.activeAgents = new Set(prev.activeAgents);
                newState.activeAgents.delete(msg.agent);
                newState.failedAgents = new Map(prev.failedAgents);
                newState.failedAgents.set(msg.agent, msg.data.error as string);
              }
              break;

            case "veto":
              newState.vetoed = true;
              break;

            case "decision":
              newState.decision = msg.data as unknown as typeof newState.decision;
              break;

            case "error":
              newState.error = msg.data.message as string;
              break;
          }

          return newState;
        });
      });
    },
    [token, connectionStatus, setupWebSocket, clearReconnectTimeout]
  );

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearReconnectTimeout();
    lastRequestRef.current = null;

    if (wsRef.current) {
      wsRef.current.close(1000, "User disconnected");
    }
  }, [clearReconnectTimeout]);

  const retry = useCallback(() => {
    if (state.ticker) {
      // Reset retry count for manual retry
      retryCountRef.current = 0;
      retryDelayRef.current = INITIAL_RETRY_DELAY;
      analyze(state.ticker, state.market);
    }
  }, [state.ticker, state.market, analyze]);

  const compareStocks = useCallback(
    (tickers: string[], market: Market = "US") => {
      // Close existing connection
      if (wsRef.current && wsRef.current.readyState < 2) {
        shouldReconnectRef.current = false;
        clearReconnectTimeout();
        wsRef.current.close();
      }

      // Reset state
      setComparisonResult(null);
      setState((prev) => ({ ...prev, error: null }));

      // Enable reconnection for this request
      shouldReconnectRef.current = true;
      lastRequestRef.current = {
        type: "compare",
        data: { tickers, market },
      };

      // Reset retry state for new request
      if (connectionStatus !== "reconnecting") {
        retryCountRef.current = 0;
        retryDelayRef.current = INITIAL_RETRY_DELAY;
      }

      const wsUrl = `${WS_BASE_URL}?token=${token || ""}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      setConnectionStatus("connecting");

      setupWebSocket(ws, (msg: WSMessage) => {
        if (msg.type === "comparison_result") {
          setComparisonResult(msg.data as unknown as ComparisonResult);
        } else if (msg.type === "error") {
          setState((prev) => ({ ...prev, error: msg.data.message as string }));
        }
        // You can also handle intermediate agent_completed events here if needed
      });
    },
    [token, connectionStatus, setupWebSocket, clearReconnectTimeout]
  );

  // Setup the actual reconnect implementation after analyze and compareStocks are defined
  useEffect(() => {
    attemptReconnectRef.current = () => {
      if (!shouldReconnectRef.current || !lastRequestRef.current) {
        return;
      }

      if (retryCountRef.current >= MAX_RETRY_ATTEMPTS) {
        console.warn(`Max reconnection attempts (${MAX_RETRY_ATTEMPTS}) reached`);
        setState((prev) => ({
          ...prev,
          error: "Connection failed after multiple attempts. Please refresh the page.",
        }));
        setConnectionStatus("disconnected");
        shouldReconnectRef.current = false;
        return;
      }

      retryCountRef.current++;
      const delay = getNextRetryDelay();

      console.log(
        `Reconnecting... Attempt ${retryCountRef.current}/${MAX_RETRY_ATTEMPTS} (delay: ${delay}ms)`
      );

      setConnectionStatus("reconnecting");

      reconnectTimeoutRef.current = setTimeout(() => {
        const request = lastRequestRef.current;
        if (request?.type === "compare") {
          compareStocks(request.data.tickers as string[], request.data.market as Market);
        } else if (request?.data) {
          analyze(request.data.ticker as string, request.data.market as Market, request.data.mode as string);
        }
      }, delay);
    };
  }, [analyze, compareStocks, getNextRetryDelay]);

  return {
    state,
    comparisonResult,
    isConnected,
    connectionStatus,
    latestNotification,
    analyze,
    compareStocks,
    disconnect,
    retry,
  };
}
