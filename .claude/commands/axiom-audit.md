# /axiom-audit

Run the complete AXIOM audit defined in `AXIOM_AUDIT.md`.

Start in AUDIT / PLAN mode.

Do not modify application source code.

First:
1. Check git status.
2. Map repository and stack.
3. Read `CLAUDE.md`.
4. Find project documentation.
5. Determine how the app is run/tested.
6. Inspect the live MVP:
   https://axiom-mvp.relaxdev.ru

Then execute all phases in `AXIOM_AUDIT.md`.

Cross-check:
DOCUMENTATION vs CODE vs LIVE MVP.

Mark unknown facts as UNKNOWN rather than guessing.

Create all requested documentation artifacts.

At the end create:
- `docs/AXIOM-STRATEGIC-AUDIT-V2.md`
- `docs/AXIOM-DECISION-MEMO.md`

Then STOP.

Do not implement application changes until the project owner explicitly approves the implementation plan.

Final response must contain:
- overall score;
- top 10 critical findings;
- top 10 recommendations;
- recommended design direction;
- recommended architecture;
- recommended business model;
- first 10 implementation tasks;
- biggest risks;
- paths to all created documents.
