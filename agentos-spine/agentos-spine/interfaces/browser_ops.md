# BrowserOpsAPI (v0.1)

Goal: auditable browser automation with deterministic trace capture.

## Required operations

- `open(url)`
- `click(selector|text)`
- `type(selector, text)`
- `extract(selector|pattern) -> data`
- `screenshot() -> image`
- `trace_export() -> TraceRef`

## Providers

- Stagehand (primary)
- browser-use (alternate)
