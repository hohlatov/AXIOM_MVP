# AXIOM — MASTER AUDIT DIRECTIVE

## Mission
Perform a complete audit of AXIOM as a product, codebase, running application, architecture, AI system and business.

Live MVP:
https://axiom-mvp.relaxdev.ru

Compare:
**DOCUMENTATION vs CODE vs LIVE MVP**

Do not assume existing implementation is correct.

## Phase 0 — Safety
1. Check working directory and git status.
2. Identify stack, entry points and package manifests.
3. Find CLAUDE.md, README, env examples, migrations, Docker/config files.
4. Do not delete or overwrite user work.
5. Do not modify production data.
6. Do not expose secrets.

## Phase 1 — Repository discovery
Map frontend, backend, database, auth, AI, API, state, routes, tests, deployment, analytics and infrastructure.

Create:
`docs/audit/01-project-map.md`

## Phase 2 — Runtime audit
Run the application if possible. Check install, dev server, build, tests, lint, typecheck and migrations.

Test:
Landing → Registration → Login → Onboarding → Diagnostic → Dashboard → Practice → Answer → Error → AI Tutor → Progress

Record runtime/console/API errors, broken links, dead buttons, incorrect states, loading states, empty states and mobile issues.

Create:
`docs/audit/02-runtime-audit.md`

## Phase 3 — Live MVP
Inspect landing, onboarding, auth, dashboard, diagnostic, practice, AI Tutor, progress, pricing and responsive/mobile UX.

Compare live behavior with local code.

Create:
`docs/audit/03-live-vs-code.md`

## Phase 4 — Documentation gap analysis
Find all project documentation and compare:
DOCUMENTATION vs CODE vs LIVE MVP

Statuses:
IMPLEMENTED / PARTIAL / MISSING / CONTRADICTED / OUTDATED / UNKNOWN

Create:
`docs/audit/04-documentation-gap-analysis.md`

## Phase 5 — Product audit
Answer:
- What is AXIOM?
- Who is it for?
- What problem does it solve?
- Why return tomorrow?
- Why pay?
- Why AXIOM instead of ChatGPT?
- Why instead of Решу ОГЭ?
- Why instead of an online school?
- What is defensible?

Create:
`docs/product/01-product-audit.md`

## Phase 6 — UX/UI audit
Audit information architecture, onboarding, dashboard, navigation, diagnostic, practice, AI Tutor, progress, pricing, mobile, accessibility, cognitive load, CTA and feedback.

Score important screens 0–10.

Create:
`docs/product/02-ux-ui-audit.md`

## Phase 7 — Design directions
Develop at least 3 distinct concepts, such as AI-first, Exam-first and Adaptive-first.

For each assess dashboard, navigation, onboarding, core flow, visual direction, pros/cons, complexity, retention and monetization.

Choose one recommended direction.

Create:
`docs/product/03-design-directions.md`

## Phase 8 — Killer feature
Generate at least 5 candidates. Score user value, business value, effort, risk, retention, monetization and defensibility. Choose one.

Create:
`docs/product/04-killer-feature.md`

## Phase 9 — Adaptive Learning Engine
Design:
Student Model → Knowledge State → Skill Graph → Recommendation Engine → Task Selection → Attempt → Error Analysis → Knowledge Update → Next Recommendation

Separate MVP, Launch and Advanced/Scale. Avoid unnecessary ML on MVP.

Create:
`docs/architecture/adaptive-learning-engine.md`

## Phase 10 — AI Tutor
Audit model, prompts, context, memory, RAG, embeddings, vector DB, grounding, hallucinations, safety, prompt injection, latency, cost and evaluation.

Explicitly decide whether RAG is justified for MVP.

Define modes:
Explain, Hint, Socratic, Check Answer, Error Analysis, Simplify, Exam Mode.

Create:
`docs/architecture/ai-tutor.md`

## Phase 11 — OGE knowledge model
Build:
Topic → Skill → Subskill → Prerequisite → Task Type → Error Pattern → Explanation → Practice

Verify current OGE requirements using authoritative/current sources when external research is needed.

Create:
`docs/product/oge-knowledge-graph.md`

## Phase 12 — Feature audit
Classify current features:
KEEP / CHANGE / REMOVE / POSTPONE / NEW

Use:
P0 Critical / P1 High / P2 Useful / P3 Later

Create:
`docs/product/05-feature-prioritization.md`

## Phase 13 — Architecture
Audit frontend, backend, database, auth, AI, storage, infrastructure, observability, analytics and security.

Do not introduce microservices by default.

Create:
`docs/architecture/01-current-architecture.md`

## Phase 14 — Three-stage architecture
Design:
- Stage 1: Current MVP, ~100 users
- Stage 2: Commercial launch, ~1,000–10,000
- Stage 3: Scale, 10,000 → 100,000 → 500,000+

Define frontend, backend, DB, cache, queue, AI, RAG, storage, analytics, monitoring, security, CI/CD and infrastructure.

State explicit scaling triggers.

Create:
`docs/architecture/02-target-architecture.md`

## Phase 15 — Database
Audit PostgreSQL: schema, tables, PK/FK, constraints, indexes, normalization, RLS, migrations and query patterns.

Pay attention to users, students, subjects, topics, skills, tasks, attempts, errors, knowledge_state, recommendations, AI conversations, subscriptions, payments and analytics.

Create:
`docs/architecture/03-database-design-v2.md`

## Phase 16 — API
Audit/propose method, path, request, response, auth, validation, errors and rate limits.

Create:
`docs/architecture/04-api-spec-v2.md`

## Phase 17 — Security
Audit minors, personal data, authentication, authorization, RBAC, sessions, API security, AI abuse, secrets, logs and data leakage.

Priorities:
CRITICAL / HIGH / MEDIUM / LOW

Create:
`docs/security/security-audit.md`

## Phase 18 — QA
Audit tests and define unit, integration, API, E2E, AI evaluation and useful visual regression.

Create:
`docs/qa/test-strategy.md`

## Phase 19 — Analytics
Define North Star Metric, activation, retention, revenue, learning and AI metrics.

Core events include signup, login, onboarding_completed, diagnostic_started/completed, task_started/completed/failed, hint_used, AI_opened, AI_message, subscription_started/cancelled.

Create:
`docs/product/analytics-spec.md`

## Phase 20 — Business model
Re-evaluate freemium, subscription, annual, family, B2B and hybrid models. Do not accept prior pricing assumptions without analysis.

Create:
`docs/business/business-model-v2.md`

## Phase 21 — Competition
Research current competitors including Фоксфорд, Учи.ру, Skysmart, Умскул, Тетрика, Решу ОГЭ, ChatGPT and relevant current competitors.

Use current sources and dates for changing facts.

Create:
`docs/business/competitive-analysis.md`

## Phase 22 — TAM/SAM/SOM
Recalculate from evidence. For every number show source, date, formula, assumptions and confidence. Do not invent data.

Create:
`docs/business/market-sizing.md`

## Phase 23 — Three-year financial model
Build Year 1 monthly and Years 2–3 with appropriate granularity.

Scenarios:
Conservative / Base / Optimistic

Include revenue, AI/API, hosting, DB, storage, development, salaries, marketing, legal, accounting, taxes, payment processing, support, content, teachers and contingency.

Calculate:
MRR, ARR, ARPU, CAC, LTV, churn, gross margin, contribution margin, burn, runway and break-even.

Create:
`docs/business/financial-model-v2.md`

## Phase 24 — Unit economics
Calculate economics by Free, Basic, Pro, Family and B2B. Include AI, infrastructure, support and payment costs. Test whether ~1,000 ₽/month is viable.

## Phase 25 — GTM
Plan pre-launch, first 100, 1,000, 10,000 and 100,000 users across VK, Telegram, YouTube, SEO, influencers, teachers, tutors, schools and referral.

Create:
`docs/business/gtm-strategy.md`

## Phase 26 — Roadmap
Build:
NOW → MVP → MVP+ → Launch → V1 → Scale

Every feature gets priority, value, effort, risk and dependencies.

Create:
`docs/roadmap/product-roadmap-v2.md`

## Phase 27 — 90-day plan
Create an executable 90-day plan with task, priority, role, dependencies, expected result and KPI.

Create:
`docs/roadmap/90-day-plan.md`

## Phase 28 — Technical debt
Create:
`docs/architecture/technical-debt.md`

Include problem, location, impact, risk, effort, priority and recommendation.

## Phase 29 — Investor view
Evaluate why now, why AXIOM, market, moat, defensibility, copyability, data advantage, path to 100k users and plausible exit.

Create:
`docs/business/investor-analysis.md`

## Phase 30 — Red team
Try to disprove product-market fit, pricing, retention, financial assumptions, AI value, adaptive-learning advantage, technical assumptions and market assumptions.

Create:
`docs/audit/final-red-team.md`

## Phase 31 — Final report
Create:
`docs/AXIOM-STRATEGIC-AUDIT-V2.md`

Include:
Executive Summary, Current State, Product, UX/UI, Design, Killer Feature, Adaptive Learning, AI Tutor, OGE Model, Features, Architecture, Database, API, Security, QA, Analytics, Business Model, Competition, TAM/SAM/SOM, Pricing, Financial Model, Unit Economics, GTM, Roadmap, 90-Day Plan, Technical Debt, Risks, Investor View, Red Team and Final Recommendation.

Create:
`docs/AXIOM-DECISION-MEMO.md`

Answer:
1. What stays?
2. What changes?
3. What is removed?
4. What is added?
5. What happens first?
6. What must NOT be built now?
7. AXIOM in 3 months?
8. AXIOM in 12 months?
9. Target architecture?
10. Business model?
11. North Star Metric?
12. Biggest risk?
13. Biggest opportunity?
14. Next action?

## Final scoring
Score:
Product /10
UX /10
UI /10
Technology /10
Architecture /10
AI /10
Adaptive Learning /10
Security /10
Business /10
Monetization /10
Market /10
Competitive Advantage /10
Scalability /10
Investor Readiness /10
Overall /10

## Critical implementation rule
During audit:
**DO NOT modify application source code.**

Only documentation may be created/updated under the documented audit/product/architecture/business/roadmap/qa/security directories.

After audit, STOP and report findings, recommendations, affected files, complexity and risks.

Wait for explicit approval before implementation.

## No fake success
Never say "done" without verification. After implementation run relevant tests, lint, typecheck, build and runtime checks.

## Subagents
If available, parallelize independent research:
- Frontend/UX
- Backend/API
- Database
- AI
- Security
- QA
- Business

Then reconcile all findings as Principal Architect.

## External research
For changing business facts use current sources and record source/date/confidence.

## MVP principle
Do not build a huge ecosystem prematurely. The MVP must prove:
diagnosis → weakness detection → personalized trajectory → practice → error understanding → adaptation → AI help → return → willingness to pay.
