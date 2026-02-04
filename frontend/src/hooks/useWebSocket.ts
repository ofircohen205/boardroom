import { useState, useCallback, useRef } from "react";
import type { Market, WSMessage, AnalysisState } from "../types";

const WS_URL = "ws://localhost:8000/ws/analyze";

export function useWebSocket() {
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
    vetoed: false,
    error: null,
  });
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const analyze = useCallback((ticker: string, market: Market) => {
    // Reset state
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
      vetoed: false,
      error: null,
    });

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({ ticker, market }));
    };

    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);

      setState((prev) => {
        const newState = { ...prev };

        switch (msg.type) {
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

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = () => {
      setState((prev) => ({ ...prev, error: "WebSocket connection failed" }));
    };
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
  }, []);

  return { state, isConnected, analyze, disconnect };
}
