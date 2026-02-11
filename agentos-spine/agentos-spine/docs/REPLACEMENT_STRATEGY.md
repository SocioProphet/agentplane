# Replacement strategy (provider + contract tests)

We adopt components quickly **without getting trapped** by:

1) Defining a stable interface (e.g., MeaningGraphAPI, KnowledgeBaseAPI)
2) Writing contract tests against the interface
3) Adopting an initial provider (AD4M, Fortemi, Inbox Zero, etc.) behind an adapter
4) Building a permissive replacement that passes the same contract tests

## Priorities

Replace-first:
- Fortemi (BUSL)

Use-now, replace-if-needed:
- AD4M (boxed behind MeaningGraphAPI)
- Inbox Zero (GPL/AGPL lane; boxed behind MailOpsAPI)

Security-boxed:
- Desktop automation (Agent-S)
- Anything with marketplace/skills ingestion (must be allowlisted)
