# SHADOW — IDEAS DUMP
Running log of ideas, decisions, and future directions. Nothing here is lost.

---

## SHIPPED ✅

- **The Council** — three-model orchestrated panel (Claude lead/strategy, GPT-4o investment/legal, Perplexity research). VERDICT / ANALYSIS / ACTIONS / ALTERNATIVE. Live.
- **Council prompt overhaul** — AED default, date injection, stale-data flagging, Challenger + Expander reviewer roles, no-homework rule, decisive verdicts.
- **Shadow Invest v1** — Profile Lite (7 fields) + 4 one-tap Council actions; profile injected into every Council call.
- **Shadow's Read** — HOME brief synthesized to verdict + 3 implications, cached daily. Principle: analysis in, information out.
- **Feedback loop** — thumbs on every Council answer + Insights agent that mines feedback for fix recommendations.
- **Trade Desk** — six-agent institutional pipeline on Alpaca paper: Analyst → PM → Risk (veto) → Compliance (code) → Trader → Execution, full audit trail.
- **HOME redesign** — brief → 2 intel cards → Council → concierge → priorities, 24px rhythm, Ask Shadow bar removed.
- **Arc brand + full scope** — locked, parked (see ARC_SCOPE.md).

## LOGGED PRINCIPLES (PERMANENT)

- **Named personas per function** — every dimension gets a character with name, personality, domain expertise. The Council is the model. Applies to Shadow Health, Invest, Concierge, Arc tutors.
- **RAG architecture** — index all data (memories, journal, briefs, concierge, Arc progress) in Supabase pgvector; retrieve only relevant chunks per query. Cuts tokens/cost, improves relevance at scale. Tracked architectural priority.
- **No-homework rule** — outputs are decisions, not research assignments.
- **Analyzed, not raw** — every surface synthesizes meaning for AJ, never dumps data.

## NEXT UP (COMMITTEE-SEQUENCED)

1. **Real estate radar** — saved criteria; Shadow monitors UAE listings/launches weekly, surfaces only deals meeting ROI thresholds.
2. **Portfolio watchdog** — concentration alerts, threshold breaches, earnings lookaheads → morning brief.
3. **Shadow Health** — AI workout scheduler (adapts to Body Battery/sleep/calendar), nutrition + supplements log (photo logging via Claude vision), body measurements, health trends with proactive flags.
4. **Full Shadow Profile** — deep onboarding in ME tab; foundational memory. Highest-leverage single feature.
5. **Persona bible** — write the named specialists (Invest advisor, Health coach, Concierge, Arc tutors) as reusable system prompts.
6. **Council graceful degradation** — one model fails → deliberation continues (lead fallback to Claude, single-reviewer mode, noted in output).
7. **SHADOW_OPS.md** — ops playbook committed to repo: deploy checklist, key resets, error patterns. Tool-agnostic documentation, not an AI governor.

## FUTURE / PARKED

- **Trade Desk Phase 2** — one-tap human approval gate → live execution only after months of paper record + proper backend with limits and kill switches. Never autonomous live money from client-side PWA.
- **TradingView MCP as Analyst input** — desktop-bound chart-reading bridge could enrich the Analyst desk when AJ works from laptop w/ Claude Code. Analysis only; execution stays Alpaca. Phase 3 enhancement.
- **Concierge real bookings** — Phase 1 execution-ready deep links (exact flight/hotel, pre-filled, AJ pays on airline page) → Phase 2 Duffel sandbox → live only with tokenized-payment backend.
- **Proactive trigger engine** — deterministic rules + cheap scheduled calls: lease expiries, school fees, HRV-drop + heavy-calendar burnout warnings, renewal lookaheads.
- **Evening debrief** — 6pm counterpart to morning brief.
- **Voice briefing** — Arthur reads the brief (fix ElevenLabs 401 first).
- **Council collaboration mode** — invite lawyer/advisor into one deliberation context; scoped access only; legal/privacy design needed (who sees what, who owns outputs).
- **Document vault** — upload contracts/statements; Council cites them (long-context use case).
- **Shadow Commercial** — multi-user GCC product, $99-499/mo; Trade Desk architecture is the flagship story.
- **Fable 5 usage doctrine** — expensive frontier models are for design-time (prompts, architecture, personas written once), not runtime. Runtime stays on Opus/GPT-4o/Sonar.

## DESIGN DEBT (ACKNOWLEDGED, AWAITING DEDICATED SESSION)

- HOME typography and page identity — AJ: "missing an identity, very dull." Larger editorial brief verdict, intentional color accents, weightier numbers. Do NOT piecemeal; one dedicated design session with full-page sign-off.
- Concierge save button JSON leak.
- Manifest.json 404 (PWA installability).
