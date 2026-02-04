import { Loader2, CheckCircle } from "lucide-react";
import type { AgentType } from "../types";

interface Props {
  agent: AgentType;
  title: string;
  isActive: boolean;
  isCompleted: boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
}

export function AgentPanel({ agent, title, isActive, isCompleted, data }: Props) {
  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">{title}</h3>
        {isActive && <Loader2 className="w-4 h-4 animate-spin text-blue-500" />}
        {isCompleted && <CheckCircle className="w-4 h-4 text-green-500" />}
      </div>

      {data && (
        <div className="text-sm space-y-1">
          {agent === "fundamental" && (
            <>
              <p>P/E: {data.pe_ratio?.toFixed(1) || "N/A"}</p>
              <p>Revenue Growth: {(data.revenue_growth * 100)?.toFixed(1)}%</p>
              <p>D/E: {data.debt_to_equity?.toFixed(2)}</p>
            </>
          )}
          {agent === "sentiment" && (
            <>
              <p>Sentiment: {data.overall_sentiment?.toFixed(2)}</p>
              <span className={`inline-block px-2 py-1 text-xs rounded ${data.overall_sentiment > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                {data.overall_sentiment > 0 ? "Positive" : "Negative"}
              </span>
            </>
          )}
          {agent === "technical" && (
            <>
              <p>Price: ${data.current_price?.toFixed(2)}</p>
              <p>RSI: {data.rsi?.toFixed(1)}</p>
              <span className="inline-block px-2 py-1 text-xs rounded bg-gray-100">{data.trend}</span>
            </>
          )}
          {agent === "risk" && (
            <>
              <p>Sector Weight: {(data.portfolio_sector_weight * 100)?.toFixed(1)}%</p>
              {data.veto ? (
                <span className="inline-block px-2 py-1 text-xs rounded bg-red-100 text-red-800">VETOED</span>
              ) : (
                <span className="inline-block px-2 py-1 text-xs rounded bg-green-100 text-green-800">Approved</span>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
