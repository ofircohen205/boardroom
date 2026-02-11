/**
 * Trade log table component for displaying backtest trades.
 */

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Trade } from "@/types/backtest";
import { ArrowDownIcon, ArrowUpIcon } from "lucide-react";

interface TradeLogProps {
  trades: Trade[];
}

export function TradeLog({ trades }: TradeLogProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (trades.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No trades executed in this backtest
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Type</TableHead>
            <TableHead className="text-right">Quantity</TableHead>
            <TableHead className="text-right">Price</TableHead>
            <TableHead className="text-right">Total</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {trades.map((trade, index) => (
            <TableRow key={index}>
              <TableCell className="font-medium">{formatDate(trade.date)}</TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  {trade.type === "BUY" ? (
                    <>
                      <ArrowUpIcon className="h-4 w-4 text-green-600 dark:text-green-400" />
                      <span className="font-medium text-green-600 dark:text-green-400">
                        BUY
                      </span>
                    </>
                  ) : (
                    <>
                      <ArrowDownIcon className="h-4 w-4 text-red-600 dark:text-red-400" />
                      <span className="font-medium text-red-600 dark:text-red-400">
                        SELL
                      </span>
                    </>
                  )}
                </div>
              </TableCell>
              <TableCell className="text-right tabular-nums">{trade.quantity}</TableCell>
              <TableCell className="text-right tabular-nums">
                {formatCurrency(trade.price)}
              </TableCell>
              <TableCell className="text-right tabular-nums font-medium">
                {formatCurrency(trade.total)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
