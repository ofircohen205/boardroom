# Pipeline Parallel Redesign

**Date:** 2026-02-23
**Status:** Approved
**Scope:** Full dashboard redesign to reflect the parallel/sequential agent execution model

## Problem

The current `AgentPipeline` component renders a linear horizontal chain:

```
[Fundamental] → [Sentiment] → [Technical] → [Risk] → [Decision]
```

This implies all agents run sequentially. In reality the execution model is:

- **Phase 1 (parallel):** Fundamental, Sentiment, Technical run concurrently
- **Phase 2 (sequential):** Risk Manager runs after all Phase 1 agents complete
- **Phase 3:** Chairperson produces the final Decision

The agent cards grid (4-column) also doesn't communicate this grouping.

## Design

### Visual Metaphor: Two-Phase Row Layout

The pipeline bar and the agent cards both split into two labelled phases.

**Phase 2 is hidden until all Phase 1 agents complete**, then animates in (fade + slide down). This reinforces that Phase 2 only starts after Phase 1 fully finishes.

### AgentPipeline (progress bar)

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1   [Fundamental] ── [Sentiment] ── [Technical]      │
│  (parallel)                                                  │
│                                                              │
│  PHASE 2   [Risk] ──────────── [Decision]   ← conditional   │
│  (sequential)                                               │
└─────────────────────────────────────────────────────────────┘
```

- Phase 1 nodes share a horizontal connecting line that fills progressively
- Phase 2 row animates in (opacity + translateY) once all 3 Phase 1 agents are in `completedAgents`
- Same icon/color state machine as today: idle → pulsing active → complete (checkmark)

### Agent Cards (in Dashboard)

**Phase 1 — visible as soon as analysis starts:**
```
[Fundamental]  [Sentiment]  [Technical]   ← 3-column grid
```

**Phase 2 — animates in after all Phase 1 agents complete:**
```
[Risk Card]   [DecisionCard + StockChart]  ← 2-column grid
```

The right column of Phase 2 stacks DecisionCard above StockChart vertically.

### Transition Logic

`allPhase1Complete` = `completedAgents` contains all three of `fundamental`, `sentiment`, `technical`.

Both `AgentPipeline` and `Dashboard` use this derived boolean to conditionally render Phase 2 content with a CSS transition.

## Files Changed

| File | Change |
|---|---|
| `frontend/src/components/AgentPipeline.tsx` | Full rewrite — two-phase layout |
| `frontend/src/components/Dashboard.tsx` | Restructure analysis section into Phase 1 / Phase 2 blocks |

## Files Unchanged

- `frontend/src/components/AgentPanel.tsx` — no changes
- `frontend/src/components/DecisionCard.tsx` — no changes
- `frontend/src/components/StockChart.tsx` — no changes
- All backend files — no changes
