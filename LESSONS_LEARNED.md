# SHADOW — LESSONS LEARNED
Hard-won knowledge. Read before touching code. Every item here cost real time.

---

## CODE & FILE INTEGRITY

1. **JS inside `<script src="...">` tags is silently ignored.** Browsers discard inline content when src is present. The Council was invisible for hours because its JS was injected inside the Supabase script tag. ALL injected JS goes in its own `<script>` block before `</body>`.
2. **Non-ASCII characters in JS are fatal.** Em dashes, emojis, arrows inside string literals cause silent or hard crashes. Validate every script block: `node --check` + zero non-ASCII scan before EVERY upload.
3. **Duplicate function definitions break everything.** Grep for duplicates after every injection (`function (\w+)\(` counter).
4. **Function must be defined before it is called** — renderConciergeBrief before triggerConciergeBrief. Order regressions are silent.
5. **CSS/HTML injection can fail silently.** Heredocs with Unicode markers match zero occurrences without error. ALWAYS assert the anchor string exists, then verify the change landed after writing.
6. **Exact-string replaces only.** Use assert-on-anchor Python replaces; never regex-guess against a 270KB file.
7. **Dark text on dark background looks like a broken feature.** The Council "didn't open" for a session — it was open with #1e293b text on #04060e. Check contrast before debugging logic.

## DEPLOY & FILE HANDLING

8. **Stale file uploads are the #1 recurring failure.** The upload script grabs whatever index.html is in Downloads. Procedure: DELETE old file → download fresh → VERIFY BYTE SIZE in Finder matches what Claude stated → upload → curl the raw GitHub URL and verify size again.
9. **Always fetch the live file fresh at session start** and before any edit. Local /tmp copies go stale within a session — my own /tmp was silently reverted once mid-session.
10. **Work can exist locally and never ship.** v33 sat unuploaded for a day while we discussed features. Every build ends with: file presented + byte size stated + MSG string given.
11. **Milestone discipline:** snapshot after every confirmed-working deploy. Revert to last confirmed MILESTONE, not last edit.

## API KEYS & SERVICES

12. **ANTHROPIC_KEY resets periodically.** 403 = re-paste key in Cloudflare FIRST. Never debug code first.
13. **API keys must be pasted as one unbroken line.** Perplexity's key spans lines when copied; line breaks → "Invalid header value".
14. **Perplexity: use the GENERAL API key**, not the search-specific one (that one returns 401 invalid_api_key).
15. **Gemini is blocked in the UAE** ("Country, region, or territory not supported"). Perplexity Sonar Pro is the replacement — and it's better for research anyway (built-in live search).
16. **OpenAI requires billing credits** — quota error means top up at platform.openai.com, not a code problem.
17. **Cloudflare free plan rate-limits after 3-4 rapid requests.** Worker MUST stay on paid plan ($5/month).
18. **Worker "Unknown service" = the route isn't deployed.** Verify with Ctrl+F in the deployed code editor, then Deploy again — the editor showing code does not mean it is deployed.
19. **Tavily queries have a length limit.** "Go deeper on: [long prompt]" overflowed it. Cap search queries at 380 chars.

## AI ORCHESTRATION

20. **Multi-model calls need retry.** One transient 429/500 killed entire Council deliberations. One retry after 1.2s fixed 90% of failures.
21. **Tag errors with the failing model** — `[gpt4o] failed after retry: ...` turns an hour of guessing into a 10-second diagnosis.
22. **Follow-ups need explicit conversation context.** Stateless calls made "Go deeper" start cold. Inject previous Q + final position (truncated) into context.
23. **Cap prompt segments on chains.** Drafts + reviews accumulate; truncate (2500/1200 chars) in refine steps.
24. **Prompt quality is 80% of output quality.** The Council's jump came from prompt engineering (roles, currency, freshness, no-homework), not model changes.
25. **Compliance/safety rules belong in deterministic code, not AI.** Models hallucinate; `if (notional > limit) block` does not. Trade Desk stage 4 is code on purpose.
26. **JSON from models needs defensive parsing.** Strip fences, slice first `{` to last `}`, try/catch (tdJSON pattern).

## PRODUCT & PROCESS

27. **Diagnose before coding. Never guess.** Error pattern → root cause → fix. Every "same shit" moment traced to skipping this.
28. **Panel review before every change — no exceptions.** Random suggestions without committee sign-off are forbidden and have caused regressions.
29. **One feature at a time.** Parallel changes = untraceable failures.
30. **The design renderer has limits** — mockups that lean on gradients/glows disappoint. Design within what actually renders; get AJ's sign-off on the full page, not fragments.
31. **AJ's standing preferences:** information analyzed, never raw (Shadow's Read principle) · decisive single-position verdicts · AED default · premium feel, minimal clutter · named personas per domain.
32. **Autonomous real-money execution from a client-side PWA is a hard no.** Paper first, human approval gate second, proper backend before any live money. The committee's honesty on this is a feature, not friction.
