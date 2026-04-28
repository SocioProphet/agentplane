# Software Operational Risk Receipt Linkage Example

This example shows the **minimum linkage shape** for connecting `agentplane` execution evidence to the typed software operational risk lane.

## Scenario

A bundle run is allowed, but the execution surface is marked `watch` because a live upstream provider status signal indicates elevated recent instability.

## Example linkage set

- `UpstreamWatchItem`  
  `urn:srcos:upstream-watch:provider:openai-codex`
- `SoftwareOperationalIncident`  
  `urn:srcos:oprisk-incident:openai-codex-unresponsive-2026-03-09`
- `SoftwareOperationalScenarioRun`  
  `urn:srcos:oprisk-scenario-run:devtools-agent-baseline-2026-q2`
- `ReserveScenarioReport`  
  `urn:srcos:oprisk-reserve-report:devtools-agent-2026-q2`
- `SoftwareOperationalAnalysisBundle`  
  `urn:srcos:oprisk-analysis-bundle:devtools-agent-2026-q2`

## How the execution evidence would read

### Validation phase

- Bundle validates structurally.
- Validation notes that execution depends on a watched upstream provider.
- The validation evidence references the `UpstreamWatchItem` ID.

### Placement phase

- Placement chooses a lower-risk execution surface or records that no safer surface exists.
- The placement evidence carries the watch-item reference and notes concentration implications.

### Run phase

- Run completes but records degraded performance or elevated risk state.
- The run evidence may reference both the watch item and a relevant historical incident if that incident materially informs the operational state.

### Review phase

- Session review links the execution evidence to the scenario-run and reserve/report objects used for governance analysis.
- This makes the governance chain explicit: live upstream watch → execution evidence → scenario analysis → reserve/report output.

## Why this example exists

The first useful step is not a whole new artifact schema family.
It is making sure the current evidence artifacts can point to the operational-risk objects that now exist upstream in the typed contract lane.
