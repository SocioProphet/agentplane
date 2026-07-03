# MailOpsAPI (v0.1)

Goal: email triage and automation behind a swappable contract.

## Required operations

- `sync()`
- `triage_queue() -> threads`
- `classify(thread_id) -> labels`
- `draft(thread_id, intent) -> draft`
- `apply(thread_id, actions)`

## Providers

- Inbox Zero (boxed service)
- MailOps-Core (planned permissive replacement)
