# AXIOM — Claude Code Project Instructions

## Project
AXIOM is an EdTech platform built around **adaptive educational trajectory in real time**.

Initial focus:
- Web application
- Russian language
- Mathematics
- OGE preparation
- ~100 users for initial validation
- Fast, cost-efficient MVP
- Future B2C/B2B expansion

## Product principles
1. Do not build features merely because they are technically interesting.
2. Prefer the smallest implementation that validates a hypothesis.
3. AXIOM is not a generic AI chat.
4. Adaptive learning should use student state, skills, attempts, errors and progress.
5. Prefer deterministic/rule-based solutions on MVP when sufficient.
6. Do not introduce microservices without a real operational/scaling reason.
7. Do not prematurely optimize for hundreds of thousands of users.
8. Important decisions must be traceable to a user problem, evidence or measurable hypothesis.

## Engineering
Before modifying code:
- inspect relevant files and dependencies;
- understand existing patterns;
- check tests;
- preserve unrelated work;
- never overwrite user changes.

After significant changes:
- run tests;
- typecheck;
- lint;
- build;
- verify runtime where possible.

Never claim success without verification.

## Security
Treat student data as sensitive. Pay particular attention to authentication, authorization, RBAC, sessions, API validation, rate limits, secrets, logs, AI prompt injection and data leakage.

Never expose secrets or copy `.env` contents into documentation.

## AI
AI Tutor is an educational system, not merely a chatbot. Preserve educational context: student, topic, skill, task, attempt, error, knowledge state and learning objective.

For AI features evaluate:
- quality;
- latency;
- cost;
- safety;
- hallucination risk;
- evaluation.

## Documentation
Use:
- docs/audit/
- docs/product/
- docs/architecture/
- docs/business/
- docs/roadmap/
- docs/qa/
- docs/security/

## Change policy
Unless explicitly authorized:
**AUDIT MODE = no application source-code changes.**

First:
AUDIT → FINDINGS → OPTIONS → RECOMMENDATION → IMPLEMENTATION PLAN

Then wait for approval.

## Decision framework
Problem → Evidence → Options → Trade-offs → Cost → Benefit → Risk → Recommendation → Implementation

## Anti-overengineering
Always ask:
> Does this complexity solve a real problem at the current scale?

If not, prefer the simpler solution.

## Definition of Done
A feature is done only when implementation, relevant tests, verification and required documentation are complete.
