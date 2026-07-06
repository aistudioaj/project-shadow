# SHADOW PROJECT — MASTER HANDOFF
Last updated: June 2026 — Abu Dhabi
Owner: AJ | Technical & strategic partner: Claude

---

## THE ECOSYSTEM

| Product | Status | What it is |
|---|---|---|
| **Shadow** | LIVE — v35 pending upload | Personal AI OS for AJ. PWA at aistudioaj.github.io/project-shadow |
| **Arc** | SCOPED, PARKED | Standalone British-curriculum EdTech platform for AJ's three children. All 15 decisions locked (see ARC_SCOPE.md) |
| **Shadow Commercial** | Phase 4 concept | Multi-user GCC executive product, $99-499/month |

---

## BRAND — LOCKED

### Shadow
- Promise: **"One source. Total clarity."**
- Personality: discreet, precise, one step ahead, completely reliable, trusted confidant
- Tone: warm and direct, adaptive by context
- Colors: `#04060e` base · `#3b82f6` blue · `#a855f7` purple · `#22c55e` green
- Type: Playfair Display (display) · DM Sans (body) · DM Mono (data)

### Arc
- Promise: **"Prepared to learn. Informed to guide. Always."**
- White-first light mode. Navy `#0d1f3c` wordmark/headings only. Gold = achievement only.
- Year accents: Y3 amber `#d97706` · Y7 blue `#2756C5` · Y9 teal `#0d9488`

---

## CURRENT STATE — v35 (BUILT, AWAITING UPLOAD)

File: index.html — **303,480 bytes**. Model: `claude-opus-4-6`.

### What v35 contains (all of today's work)
1. **Council prompt overhaul (v33)** — AED default currency, today's date injected, stale-data flagging (>3 months), Challenger + Expander reviewer roles, no-homework rule, decisive verdicts, Perplexity sonar-pro
2. **Shadow Invest** — card in TREASURY, Profile Lite form (7 fields → shadow_profile table), 4 one-tap Council actions, profile injected into all Council calls
3. **Shadow's Read** — HOME brief card now synthesized by Claude (verdict + 3 implications), cached daily in localStorage
4. **Council follow-up hardening** — Tavily query capped 380 chars, auto-retry on model calls, model-tagged errors, conversation continuity (previous Q&A in context), prompt size caps
5. **Feedback loop** — thumbs up/down on Council answers → shadow_feedback; Insights agent in Council header analyzes patterns and recommends fixes
6. **Trade Desk** — six-agent paper trading pipeline (see below)

### The Council — architecture
Three-model orchestrated panel. Flow: detect task → Tavily live search → Lead drafts → Challenger + Expander review → Lead refines → VERDICT / ANALYSIS / RECOMMENDED ACTIONS / ALTERNATIVE.

| Model | Route | Leads |
|---|---|---|
| Claude Opus 4.6 | `?service=claude` | Strategy, Creative, Technical, Health |
| GPT-4o | `?service=openai` | Investment, Financial, Legal |
| Perplexity Sonar Pro | `?service=perplexity` | Research, Data, Architecture |

Access: HOME Council card · LIFE → Specialists (all cards redirect) · openShadowChat() redirects to openCouncil().

### Trade Desk — six-agent pipeline (paper money)
TREASURY → Shadow Invest → Trade Desk. Limits: max trade $13,500 · max position 10% · cash floor 20%.

| Stage | Agent | Power |
|---|---|---|
| 1 Analyst | Perplexity | Thesis with live data |
| 2 Portfolio Manager | GPT-4o | Sizing vs profile — can reject |
| 3 Risk Manager | Claude | Independent VETO, one revision loop |
| 4 Compliance | **Deterministic code** | Hard blocks: trade cap, position cap, cash floor, no-go list |
| 5 Trader | GPT-4o | Limit order construction |
| 6 Execution | Alpaca paper API | Places real order, simulated money |

Every stage logged to `shadow_trades` (audit trail). Live trading: NEVER autonomous — Phase 2 = one-tap human approval, only after months of paper record.

---

## INFRASTRUCTURE

| Service | Detail |
|---|---|
| Live app | https://aistudioaj.github.io/project-shadow/ |
| Repo | github.com/aistudioaj/project-shadow |
| Worker | shadow-proxy.aistudio-aj.workers.dev — **PAID plan required** |
| Worker secrets | ANTHROPIC_KEY · OPENAI_KEY · PPLX_KEY · ELEVENLABS_KEY · TAVILY_KEY · ALPACA_KEY (pending) · ALPACA_SECRET (pending) |
| Worker version | v3 (adds `?service=alpaca` → paper-api.alpaca.markets) — pending deploy |
| Upload | python3 /Users/aistudio/Downloads/upload.py (edit MSG inside) |

### Supabase tables
Existing: shadow_briefs, shadow_memory, shadow_tasks, shadow_proactive_alerts, shadow_budget, shadow_reads, shadow_journal, shadow_travel, shadow_holdings, shadow_concierge, shadow_concierge_messages.
**New (SQL pending — run before testing v35):** shadow_profile, shadow_feedback, shadow_trades. RLS disabled on all.

---

## PENDING — AJ'S AT-HOME CHECKLIST

1. Alpaca account → paper keys → Cloudflare (`ALPACA_KEY`, `ALPACA_SECRET`, single-line paste)
2. Deploy worker_v3.js in Cloudflare
3. Run the 3 SQL blocks in Supabase (profile, feedback, trades)
4. Upload index.html v35 (verify 303,480 bytes first)
5. Test at `?v=35`: Shadow's Read → Profile Lite → Portfolio review → thumbs + Insights → Trade Desk run
6. Verify audit rows in shadow_trades and order in Alpaca dashboard

---

## KNOWN BUGS / OPEN ITEMS

1. ElevenLabs 401 — refresh ELEVENLABS_KEY in Cloudflare
2. Manifest.json 404 — PWA manifest missing
3. Concierge save button appends raw JSON before closing
4. HOME typography/identity — AJ wants a dedicated design session (logged, not urgent)
5. Council graceful degradation — proposed (one model fails → deliberation continues); not yet built
6. SHADOW_OPS.md playbook — agreed concept, to be committed to repo

---

## ROADMAP (COMMITTEE-APPROVED SEQUENCE)

| Phase | Content | Status |
|---|---|---|
| B | Shadow Invest: Trade Desk ✅ → real-estate radar → portfolio watchdog | IN PROGRESS |
| C | Shadow Health: AI workout scheduler → nutrition/supplements log → trends | NEXT |
| A | Full Shadow Profile → RAG (pgvector) → persona bible | AFTER C |
| D | Proactive layer: trigger rules engine, evening debrief, voice briefing | PLANNED |
| E | Council collaboration mode, document vault, Arc build | PLANNED |

Concierge booking: Phase 1 = execution-ready deep links → Phase 2 Duffel sandbox → live only with proper backend.

---

## GOVERNANCE — MANDATORY COMMITTEE (NO EXCEPTIONS)

All 7 for Arc decisions; core 3 (Technical, UX/UI, PM) for Shadow changes. Panel review BEFORE any code.

1 Technical Advisor · 2 UX/UI Advisor · 3 Product Manager · 4 Marketing & Comms · 5 EdTech SME · 6 British Curriculum Advisor · 7 Senior Strategic Advisor

Core principles: named personas per domain (Council model) · no-homework rule · AED default · one feature at a time · milestone snapshot after every confirmed working deploy.

---

## START-OF-SESSION CHECKLIST

1. `curl -s "https://raw.githubusercontent.com/aistudioaj/project-shadow/main/index.html" -o /tmp/index.html` — verify size matches last milestone
2. Test one Council question (verifies all three model keys)
3. 403 anywhere → re-paste key in Cloudflare FIRST, never code first
4. Read LESSONS_LEARNED.md before touching code
5. Panel review before any change

Journal reset word: "shadow" (lowercase)
