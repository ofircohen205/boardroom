import type { Decision } from "../types";

interface Props {
  decision: Decision | null;
  vetoed: boolean;
  vetoReason?: string | null;
}

export function DecisionCard({ decision, vetoed, vetoReason }: Props) {
  if (vetoed) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <h2 className="text-xl font-bold text-red-700">Trade Vetoed</h2>
        <p className="text-red-600 mt-2">{vetoReason}</p>
      </div>
    );
  }

  if (!decision) return null;

  const actionColors = {
    BUY: "bg-green-500",
    SELL: "bg-red-500",
    HOLD: "bg-yellow-500",
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <div className="flex items-center gap-4 mb-4">
        <span className={`${actionColors[decision.action]} text-white text-lg px-4 py-2 rounded font-bold`}>
          {decision.action}
        </span>
        <span className="text-2xl font-bold">{(decision.confidence * 100).toFixed(0)}% confidence</span>
      </div>
      <p className="text-gray-700">{decision.rationale}</p>
    </div>
  );
}
