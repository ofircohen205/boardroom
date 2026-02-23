# Pipeline Parallel Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the dashboard to visually communicate that Fundamental, Sentiment, and Technical agents run in parallel (Phase 1), with Risk and Decision running sequentially after (Phase 2).

**Architecture:** Rewrite `AgentPipeline.tsx` to a two-phase row layout, then restructure `Dashboard.tsx` to group agent cards into the same two phases. Phase 2 content (pipeline row + agent cards) only appears after all Phase 1 agents complete, with a fade+slide animation.

**Tech Stack:** React 19, TypeScript, Tailwind CSS v4, shadcn/ui, lucide-react

---

## Context

**Design doc:** `docs/plans/2026-02-23-pipeline-parallel-redesign.md`

**Only 2 files change:**
- `frontend/src/components/AgentPipeline.tsx` — full rewrite
- `frontend/src/components/Dashboard.tsx` — restructure analysis section

**No backend changes. No changes to AgentPanel, DecisionCard, StockChart.**

**Key derived value used in both files:**
```ts
const allPhase1Complete =
  completedAgents.has('fundamental') &&
  completedAgents.has('sentiment') &&
  completedAgents.has('technical');
```

**Verification command (run after each task):**
```bash
cd frontend && npm run build 2>&1 | tail -20
```
TypeScript errors will show here. There is no automated UI test suite — verify visually in browser after both tasks.

---

## Task 1: Rewrite AgentPipeline.tsx

**Files:**
- Modify: `frontend/src/components/AgentPipeline.tsx`

**Step 1: Replace the file contents**

The new component renders two rows. Phase 1 row is always visible (once the component mounts). Phase 2 row fades in once `allPhase1Complete` is true.

```tsx
import {
  BarChart3,
  MessageSquare,
  TrendingUp,
  Shield,
  Gavel,
  Check,
  Loader2,
} from "lucide-react";
import type { AgentType } from "@/types";
import { cn } from "@/lib/utils";

interface Props {
  activeAgents: Set<AgentType>;
  completedAgents: Set<AgentType>;
  hasDecision: boolean;
}

const PHASE_1 = [
  { key: "fundamental" as AgentType, icon: BarChart3, label: "Fundamental" },
  { key: "sentiment" as AgentType, icon: MessageSquare, label: "Sentiment" },
  { key: "technical" as AgentType, icon: TrendingUp, label: "Technical" },
] as const;

const PHASE_2 = [
  { key: "risk" as AgentType, icon: Shield, label: "Risk" },
] as const;

function AgentNode({
  agentKey,
  icon: Icon,
  label,
  isActive,
  isComplete,
}: {
  agentKey: string;
  icon: React.ElementType;
  label: string;
  isActive: boolean;
  isComplete: boolean;
}) {
  return (
    <div className="flex flex-col items-center gap-3 min-w-[72px] relative z-10">
      <div
        className={cn(
          "relative flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-500 border-2 shadow-lg",
          isComplete && "bg-primary text-primary-foreground border-primary shadow-[0_0_25px_rgba(var(--primary),0.6)] scale-105",
          isActive && "bg-primary/20 text-primary border-primary animate-pulse-glow shadow-[0_0_20px_rgba(var(--primary),0.4)]",
          !isComplete && !isActive && "bg-muted/30 text-muted-foreground border-border",
        )}
      >
        {isComplete ? (
          <Check className="h-6 w-6" />
        ) : isActive ? (
          <Loader2 className="h-6 w-6 animate-spin" />
        ) : (
          <Icon className="h-5 w-5" />
        )}
      </div>
      <span
        className={cn(
          "hidden text-[10px] font-bold tracking-[0.2em] uppercase transition-colors sm:block",
          isComplete ? "text-primary text-glow" : isActive ? "text-foreground" : "text-muted-foreground/60",
        )}
      >
        {label}
      </span>
    </div>
  );
}

function ConnectingLine({ filled }: { filled: boolean }) {
  return (
    <div className="flex-1 h-[2px] bg-muted-foreground/20 relative overflow-hidden rounded-full mx-2 self-start mt-6">
      <div
        className={cn(
          "absolute inset-0 transition-all duration-1000 w-full origin-left bg-gradient-to-r from-primary to-primary/50",
          filled ? "scale-x-100" : "scale-x-0",
        )}
      />
    </div>
  );
}

export function AgentPipeline({ activeAgents, completedAgents, hasDecision }: Props) {
  const allPhase1Complete =
    completedAgents.has("fundamental") &&
    completedAgents.has("sentiment") &&
    completedAgents.has("technical");

  return (
    <div className="glass rounded-2xl px-8 py-6 border-border bg-card/80 backdrop-blur-xl space-y-4">

      {/* Phase 1 */}
      <div className="flex items-start gap-4">
        <div className="flex flex-col items-start gap-0.5 min-w-[72px] pt-1">
          <span className="text-[9px] font-black tracking-[0.25em] uppercase text-primary/70">Phase 1</span>
          <span className="text-[9px] tracking-wider uppercase text-muted-foreground/40">Parallel</span>
        </div>

        <div className="flex items-start flex-1">
          {PHASE_1.map((step, i) => (
            <div key={step.key} className="flex items-start flex-1">
              <AgentNode
                agentKey={step.key}
                icon={step.icon}
                label={step.label}
                isActive={activeAgents.has(step.key)}
                isComplete={completedAgents.has(step.key)}
              />
              {i < PHASE_1.length - 1 && (
                <ConnectingLine filled={completedAgents.has(step.key)} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Phase 2 — appears after Phase 1 completes */}
      <div
        className={cn(
          "flex items-start gap-4 transition-all duration-700 ease-out",
          allPhase1Complete ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3 pointer-events-none select-none",
        )}
      >
        <div className="flex flex-col items-start gap-0.5 min-w-[72px] pt-1">
          <span className="text-[9px] font-black tracking-[0.25em] uppercase text-primary/70">Phase 2</span>
          <span className="text-[9px] tracking-wider uppercase text-muted-foreground/40">Sequential</span>
        </div>

        <div className="flex items-start flex-1">
          {PHASE_2.map((step) => (
            <div key={step.key} className="flex items-start flex-1">
              <AgentNode
                agentKey={step.key}
                icon={step.icon}
                label={step.label}
                isActive={activeAgents.has(step.key)}
                isComplete={completedAgents.has(step.key)}
              />
              <ConnectingLine filled={completedAgents.has(step.key)} />
            </div>
          ))}

          {/* Decision node */}
          <div className="flex flex-col items-center gap-3 min-w-[72px] relative z-10">
            <div
              className={cn(
                "relative flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-500 border-2 shadow-lg",
                hasDecision && "bg-emerald-500 text-white border-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.6)] scale-110",
                !hasDecision && "bg-muted/30 text-muted-foreground border-border",
              )}
            >
              <Gavel className={cn("h-5 w-5", !hasDecision && "opacity-40")} />
            </div>
            <span
              className={cn(
                "hidden text-[10px] font-bold tracking-[0.2em] uppercase transition-colors sm:block",
                hasDecision ? "text-emerald-500" : "text-muted-foreground/60",
              )}
            >
              Decision
            </span>
          </div>
        </div>
      </div>

    </div>
  );
}
```

**Step 2: Verify TypeScript compiles**

```bash
cd /Users/ofircohen/Projects/boardroom/frontend && npm run build 2>&1 | tail -20
```
Expected: no TypeScript errors related to `AgentPipeline.tsx`.

**Step 3: Commit**

```bash
git add frontend/src/components/AgentPipeline.tsx
git commit -m "feat: redesign AgentPipeline to two-phase parallel/sequential layout"
```

---

## Task 2: Restructure Dashboard.tsx analysis section

**Files:**
- Modify: `frontend/src/components/Dashboard.tsx`

**Step 1: Derive `allPhase1Complete` in the component**

Inside the `Dashboard` function, after the existing `isLoading` and `hasStarted` lines, add:

```ts
const allPhase1Complete =
  state.completedAgents.has("fundamental") &&
  state.completedAgents.has("sentiment") &&
  state.completedAgents.has("technical");
```

**Step 2: Replace the "Active Analysis View" block**

Find the comment `{/* Active Analysis View */}` (around line 171) and replace the entire block inside it (everything after `AgentPipeline` through the closing `</div>`) with the two-phase layout below.

The block to replace runs from just after the `AgentPipeline` component through to the closing `</div>` that wraps `{/* Agents Grid */}` and `{/* News Feed */}`.

Replace it with:

```tsx
{/* Phase 1 — Agent Cards (always visible once analysis starts) */}
<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
  <AgentPanel
    agent="fundamental"
    title="Fundamental"
    icon={BarChart3}
    isActive={state.activeAgents.has("fundamental")}
    isCompleted={state.completedAgents.has("fundamental")}
    isFailed={state.failedAgents.has("fundamental")}
    errorMessage={state.failedAgents.get("fundamental")}
    data={state.fundamental}
    index={0}
    onRetry={retry}
  />
  <AgentPanel
    agent="sentiment"
    title="Sentiment"
    icon={MessageSquare}
    isActive={state.activeAgents.has("sentiment")}
    isCompleted={state.completedAgents.has("sentiment")}
    isFailed={state.failedAgents.has("sentiment")}
    errorMessage={state.failedAgents.get("sentiment")}
    data={state.sentiment}
    index={1}
    onRetry={retry}
  />
  <AgentPanel
    agent="technical"
    title="Technical"
    icon={TrendingUp}
    isActive={state.activeAgents.has("technical")}
    isCompleted={state.completedAgents.has("technical")}
    isFailed={state.failedAgents.has("technical")}
    errorMessage={state.failedAgents.get("technical")}
    data={state.technical}
    index={2}
    onRetry={retry}
  />
</div>

{/* Phase 2 — Risk + Decision (appears after Phase 1 completes) */}
<div
  className={cn(
    "transition-all duration-700 ease-out space-y-6",
    allPhase1Complete ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4 pointer-events-none select-none hidden",
  )}
>
  {/* Quick Actions */}
  {(state.decision !== null || state.vetoed) && (
    <div className="flex justify-end">
      <Button
        variant="outline"
        size="sm"
        onClick={() => navigate(`/compare?ticker=${state.ticker}`)}
        className="gap-2"
      >
        <GitCompare className="w-4 h-4" />
        Compare with others
      </Button>
    </div>
  )}

  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    {/* Risk agent card */}
    <AgentPanel
      agent="risk"
      title="Risk"
      icon={Shield}
      isActive={state.activeAgents.has("risk")}
      isCompleted={state.completedAgents.has("risk")}
      isFailed={state.failedAgents.has("risk")}
      errorMessage={state.failedAgents.get("risk")}
      data={state.risk}
      index={3}
      onRetry={retry}
    />

    {/* Decision + Chart stacked */}
    <div className="flex flex-col gap-4">
      <DecisionCard
        decision={state.decision}
        vetoed={state.vetoed}
        vetoReason={state.risk?.veto_reason}
      />
      <div className="glass rounded-3xl overflow-hidden p-1 min-h-[240px] border-border">
        {state.technical?.price_history ? (
          <StockChart
            priceHistory={state.technical.price_history}
            ticker={state.ticker!}
            ma50={state.technical.ma_50}
            ma200={state.technical.ma_200}
            rsi={state.technical.rsi}
            bollingerUpper={state.technical.bollinger_upper}
            bollingerLower={state.technical.bollinger_lower}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground/20 text-sm font-mono uppercase tracking-widest">
            Market Data Unavailable
          </div>
        )}
      </div>
    </div>
  </div>

  {/* News Feed */}
  {state.sentiment && (
    <div className="glass rounded-xl p-6">
      <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
        <MessageSquare className="w-4 h-4" />
        Market Intelligence
      </h3>
      <NewsFeed
        newsItems={state.sentiment.news_items}
        socialMentions={state.sentiment.social_mentions}
      />
    </div>
  )}
</div>
```

**Step 3: Remove now-unused imports**

The `Zap` import in Dashboard.tsx header is still used. Double-check that all imports used in the new layout are present:
- `BarChart3`, `MessageSquare`, `TrendingUp`, `Shield`, `GitCompare` — already imported
- `AgentPanel`, `DecisionCard`, `StockChart`, `NewsFeed` — already imported

Remove any imports that are no longer referenced after the restructure (e.g. if `Zap` is actually unused now).

**Step 4: Verify TypeScript compiles**

```bash
cd /Users/ofircohen/Projects/boardroom/frontend && npm run build 2>&1 | tail -30
```
Expected: zero TypeScript errors.

**Step 5: Verify in browser**

Start the dev server and test manually:

```bash
cd /Users/ofircohen/Projects/boardroom/frontend && npm run dev
```

Check:
1. Before analysis: only the search bar shown (no pipeline, no cards)
2. After triggering analysis: Phase 1 pipeline row appears, 3 agent cards appear
3. While Phase 1 agents are running: their cards show the pulsing "ANALYZING" state
4. Once all 3 Phase 1 agents complete: Phase 2 pipeline row fades in, Risk card + Decision column animate in
5. Risk agent shows active then completes
6. Decision card shows the verdict

**Step 6: Commit**

```bash
git add frontend/src/components/Dashboard.tsx
git commit -m "feat: restructure dashboard into parallel Phase 1 and sequential Phase 2 layout"
```
