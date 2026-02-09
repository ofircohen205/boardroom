import { useState, useCallback, useRef, useEffect } from "react";
import type { Market, WSMessage, AnalysisState } from "../types";
import type { ComparisonResult } from "../types/comparison";
import { useAuth } from "@/contexts/AuthContext";

const WS_BASE_URL = "ws://localhost:8000/ws/analyze";

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
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Effect to handle disconnection when token changes (e.g., logout)
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, [token]);

  const analyze = useCallback((ticker: string, market: Market = 'US', mode: string = 'standard') => {
    // If a socket is already open, close it before creating a new one.
    if (wsRef.current && wsRef.current.readyState < 2) { // OPEN or CONNECTING
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

    const wsUrl = `${WS_BASE_URL}?token=${token || ''}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({ ticker, market, mode }));
    };

    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);

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
    };

    ws.onclose = (event) => {
      setIsConnected(false);
      // If the close was unexpected, show an error.
      if (!event.wasClean) {
          setState((prev) => ({ ...prev, error: "Connection lost. Please try again." }));
      }
    };

    ws.onerror = (event) => {
      console.error("WebSocket error:", event);
      setState((prev) => ({ ...prev, error: "WebSocket connection failed" }));
      setIsConnected(false);
    };
  }, [token]); // Add token to dependency array

  const disconnect = useCallback(() => {
    if (wsRef.current) {
        wsRef.current.close(1000, "User disconnected"); // 1000 is a normal closure
    }
  }, []);

  const retry = useCallback(() => {
    if (state.ticker) {
      analyze(state.ticker, state.market);
    }
  }, [state.ticker, state.market, analyze]);

  const compareStocks = useCallback((tickers: string[], market: Market = 'US') => {
    // Close existing connection
    if (wsRef.current && wsRef.current.readyState < 2) {
      wsRef.current.close();
    }

    // Reset state
    setComparisonResult(null);
    setState((prev) => ({ ...prev, error: null }));

    const wsUrl = `${WS_BASE_URL}?token=${token || ''}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({ type: "compare", tickers, market }));
    };

    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);

      if (msg.type === "comparison_result") {
        setComparisonResult(msg.data as ComparisonResult);
      } else if (msg.type === "error") {
        setState((prev) => ({ ...prev, error: msg.data.message as string }));
      }
      // You can also handle intermediate agent_completed events here if needed
    };

    ws.onclose = (event) => {
      setIsConnected(false);
      if (!event.wasClean) {
        setState((prev) => ({ ...prev, error: "Connection lost. Please try again." }));
      }
    };

    ws.onerror = (event) => {
      console.error("WebSocket error:", event);
      setState((prev) => ({ ...prev, error: "WebSocket connection failed" }));
      setIsConnected(false);
    };
  }, [token]);

  return { state, comparisonResult, isConnected, analyze, compareStocks, disconnect, retry };
}
