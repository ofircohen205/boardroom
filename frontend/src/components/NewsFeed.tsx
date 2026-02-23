import type { NewsItem, SocialMention } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Newspaper, ExternalLink, Hash } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  newsItems: NewsItem[];
  socialMentions: SocialMention[];
}

export function NewsFeed({ newsItems, socialMentions }: Props) {
  const allItems = [
    ...newsItems.map((n) => ({
      ...n,
      type: "news" as const,
      sentimentScore: n.sentiment,
    })),
    ...socialMentions.map((s) => ({
      ...s,
      type: "social" as const,
      title: s.content.slice(0, 120),
      sentimentScore: 0,
    })),
  ];

  if (allItems.length === 0) return null;

  return (
    <Card className="glass animate-fade-up border-primary/20">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b border-border bg-muted/30">
        <CardTitle className="flex items-center gap-2 text-sm font-bold tracking-widest uppercase text-muted-foreground">
          <Newspaper className="h-4 w-4 text-primary" />
          Market Intelligence
        </CardTitle>
        <span className="text-[10px] font-mono px-2 py-1 rounded-full bg-muted/30 text-muted-foreground border border-border">
          {allItems.length} EVENTS
        </span>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[280px]">
          <div className="flex flex-col">
            {allItems.slice(0, 12).map((item, i) => (
              <a
                key={i}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-start gap-4 px-6 py-4 transition-all hover:bg-muted/30 border-b border-border last:border-0"
              >
                {/* Type indicator */}
                <div
                  className={cn(
                    "mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border transition-colors",
                    item.type === "news"
                      ? "bg-blue-500/10 border-blue-500/20 text-blue-400 group-hover:border-blue-500/50"
                      : "bg-pink-500/10 border-pink-500/20 text-pink-400 group-hover:border-pink-500/50",
                  )}
                >
                  {item.type === "news" ? (
                    <Newspaper className="h-3 w-3" />
                  ) : (
                    <Hash className="h-3 w-3" />
                  )}
                </div>

                <div className="min-w-0 flex-1 space-y-1.5">
                  <p className="text-sm font-medium leading-relaxed group-hover:text-primary transition-colors">
                    {item.title}
                  </p>
                  <div className="flex items-center gap-3">
                    <Badge
                      variant="outline"
                      className="text-[9px] px-2 py-0 h-4 border-border bg-muted/30 text-muted-foreground group-hover:border-border/80"
                    >
                      {item.source}
                    </Badge>
                    {item.type === "news" && item.sentimentScore !== 0 && (
                      <span
                        className={cn(
                          "text-[10px] font-mono font-bold tabular-nums",
                          item.sentimentScore > 0
                            ? "text-emerald-400"
                            : "text-rose-400",
                        )}
                      >
                        {item.sentimentScore > 0 ? "BULLISH" : "BEARISH"} {" "}
                        {Math.abs(item.sentimentScore).toFixed(2)}
                      </span>
                    )}
                  </div>
                </div>

                <ExternalLink className="mt-1 h-3 w-3 shrink-0 text-muted-foreground/40 opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" />
              </a>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
