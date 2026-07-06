# ARC — CONFIRMED SCOPE
A Shadow satellite product · British curriculum EdTech platform
Status: FULLY SCOPED AND PARKED. Build starts the moment AJ says go.

---

## BRAND

- **Name:** Arc — trajectory, momentum, works ages 7-14. Arabic transliteration clean.
- **Promise:** "Prepared to learn. Informed to guide. Always."
- **Born from AJ's pain:** never again searching for study materials, exam dates, revision sheets, or cramming on exam eve.
- **Parent link:** "A Shadow product" footer credit + shared typography only. Own identity otherwise.
- **Visual:** white-first light mode. Navy #0d1f3c wordmark/headings only — never dark surfaces on child screens. Gold = achievement only (badges, streaks, rewards). Benchmarked against Duolingo / Khan Academy / Quizlet: white space first, progress always visible, immediate feedback, bite-sized sessions, gamification that teaches.
- **Year accents:** Y3 amber #d97706 · Y7 blue #2756C5 · Y9 teal #0d9488
- **Type:** Playfair Display · DM Sans · DM Mono
- **Domain:** GitHub Pages first → arclearn.io / arc.education later (arc.ai premium/taken).

## THE FIFTEEN LOCKED DECISIONS

| # | Decision |
|---|---|
| 1 | Build order: **admin dashboard first**, then child UIs |
| 2 | **AI-powered living question bank** — grows with curriculum, child performance, term, exams |
| 3 | 1 hour/day: Y3 = 3x20min · Y7 = 2x30min · Y9 = 1x60min (or 2x30) |
| 4 | Sibling leaderboard: **projects only** — academic scores stay private per child |
| 5 | Launch subjects: **Maths, Science, English** |
| 6 | Phase 2 subjects: History, Geography, Social Studies, GL Assessment (verbal + non-verbal) |
| 7 | Phase 3: Arabic + Islamic Studies (with RTL UI) |
| 8 | Wife access: simplified view toggle inside AJ account, **own separate PIN** — children have easy access to her devices; admin must never be compromised through them |
| 9 | Hosting: GitHub Pages for now |
| 10 | **No mascot** — one premium design language across all ages; experience adapts, brand doesn't. Y3 warm/celebratory · Y7 clear/motivating · Y9 focused/exam-ready |
| 11 | English only — Arabic unlocks with Islamic Studies (built properly, not bolted on) |
| 12 | Notifications: proactive — daily child reminders, weekly parent reports, **calendar-driven exam prep** that ramps intensity gradually as exams approach |
| 13 | **School circular integration** — dedicated email; Arc parses circulars → extracts exam dates, deadlines, events → auto-updates calendar → triggers prep plans → alerts AJ with actions taken |
| 14 | **Document upload** — three types: curriculum docs (syllabus, past papers, mark schemes), school docs (circulars, timetables, teacher feedback), child work (Arc reviews and gives feedback) |
| 15 | **Multi-LLM verification** — Phase 1 Claude only; Phase 2 second model verifies answers (definitive check for Maths/Science, criteria alignment for English); disagreements flagged to AJ, never delivered unresolved. Children's education must not depend on one model that might hallucinate |

## THE THREE CHILDREN

| Child | Year | Age | Accent | Focus |
|---|---|---|---|---|
| 1 | Year 9 | 13-14 | Teal | GCSE runway — structured revision, exam mode |
| 2 | Year 7 | 11-12 | Blue | Secondary foundations — consistency over intensity |
| 3 | Year 3 | 7-8 | Amber | Core literacy/numeracy — short, encouraging, never "homework" |

## ACCESS MODEL (THREE TIERS)

- **AJ (full admin):** all-children dashboard w/ traffic lights, per-child completion/scores/streaks/weak areas, assignment + target control, calendar + circulars, document upload, alerts, stats pushed to Shadow morning brief.
- **Wife (simplified, PIN-protected):** three cards, traffic light each, last active + streak + weekly %, one-tap message AJ. Zero admin controls.
- **Children (own logins, username + PIN):** own content only, no sibling academic visibility, projects leaderboard, age-adapted experience.

## CONTENT ENGINE

Four types: **Exercises** (5-15 Q, auto-scored, adaptive) · **Revision sheets** (15-25 Q, curriculum-aligned) · **Projects** (multi-step guided, leaderboard) · **Interactive tutor** (Socratic — asks back, never hands answers; topic-bounded).
Named tutor personas per year group (Shadow persona principle).
GL Assessment: dedicated timed practice mode, tracked separately.
Session shape: warm-up 2min → main block → feedback + score → streak/reward.

## TECHNICAL STACK

| Component | Choice |
|---|---|
| Frontend | PWA — separate repo `arc-platform` |
| DB | Supabase — NEW project, fully separate from Shadow |
| AI | Claude (claude-sonnet-4-6 class) via dedicated Cloudflare Worker (paid) |
| Auth | Supabase Auth — child username+PIN, parent email+password |
| Circulars | Dedicated email + parsing job |
| Notifications | Email (Resend) → push in Phase 2 |

### Tables
arc_children · arc_users · arc_sessions · arc_assignments · arc_questions · arc_responses · arc_progress · arc_calendar · arc_circulars · arc_documents · arc_achievements · arc_shadow_sync · arc_notifications

### Shadow integration
Daily job writes compact per-child stats to Shadow memory → surfaces in morning brief ("Y9: 85% this week, weak Geography. Y3: missed 2 sessions."). Tutor card in Shadow LIFE links to Arc admin.

## BUILD PHASES

1. **Foundation:** repo + Supabase + Worker · AJ admin dashboard (traffic lights) · child auth · basic exercise engine · Maths/Science/English · Shadow stats integration
2. **Intelligence:** year-adapted child UIs · revision sheets · academic calendar + circular parsing · proactive exam-prep engine · document upload · wife view · streaks + notifications
3. **Verification & expansion:** second-LLM verifier · GL mode · projects + leaderboard · humanities subjects
4. **Arabic & polish:** RTL, Arabic + Islamic Studies, full gamification, push

## GOVERNANCE

Every Arc decision requires ALL SEVEN committee members. No exceptions.
