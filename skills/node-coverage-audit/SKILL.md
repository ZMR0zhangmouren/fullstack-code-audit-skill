---
name: node-coverage-audit
description: Node.js code audit coverage backfill phase skill. Receives risks and safe_regions output by the Scan phase, computes uncovered code fragments (gaps), and sends larger gaps back to the Scan phase for backfill. Not responsible for security judgments, only for coverage accountability tracking.
---

# Node.js Coverage Backfill (Coverage)

## Goal

Based on the `risks` and `safe_regions` output by the Scan phase, **compute uncovered code fragments (gaps)** and send larger gaps back to the Scan phase for backfill.

**Coverage is not a security proof; it is accountability tracking.**
The model must not just say "I have looked through it"; it must account for where it covered using risk regions and safe regions.

## Core Principles

- Coverage **does not judge whether semantics are complete**; it only computes physical coverage
- Coverage **does not prove code is safe**; it only tracks "what has not been looked at yet"
- Uncovered code fragments must be sent back to the Scan phase for backfill and must not be skipped

## Input

- `node/scan_audit/scan_{filename|module}_{timestamp}.md`: risks + safe_regions output by the Scan phase
- `node_source_path`: Node.js project source path
- `min_gap`: minimum gap threshold (default 10 lines)
- `max_rounds`: maximum backfill rounds (default 3 rounds)

## Algorithm Logic

### 1. Compute uncovered ranges

```
total file lines = actual code lines of the file (excluding blank lines and pure comment lines)
covered ranges = risks.line_range ∪ safe_regions.line_range
uncovered ranges = total file lines - covered ranges
```

### 2. Filter and merge gaps

- gaps smaller than `min_gap` lines are ignored (to avoid excessive backfill of tiny fragments)
- adjacent gaps (interval < 5 lines) are merged into one

### 3. Backfill loop

```
for round = 1 to max_rounds:
    gaps = find_uncovered_ranges(file, risks, safe_regions, min_gap)
    if gaps is empty or gaps identical to the previous round:
        break
    for each gap in gaps:
        send the gap back to the Scan phase, requesting a scan of that code segment
    update risks and safe_regions
```

### 4. Stop conditions

Backfill stops when any of the following holds:
- no gaps
- gaps unchanged from the previous round (converged)
- the `max_rounds` limit is reached
- the user explicitly terminates

## Output Schema

### 1. node/coverage_audit/coverage_{filename|module}_{timestamp}.md

Each file must have one coverage report output:

| Field | Description |
|------|------|
| `file_total_lines` | total file lines |
| `risks_count` | number of risks found |
| `safe_regions_count` | number of marked safe regions |
| `gaps` | list of uncovered fragments (each gap contains start_line, end_line, line_count) |
| `rounds_executed` | actual backfill rounds executed |
| `final_coverage_percent` | final coverage percentage |
| `stop_reason` | stop reason |

### 2. node/coverage_audit/backfill_{round}_{filename|module}_{timestamp}.md

Detailed record of each backfill round:

| Field | Description |
|------|------|
| `round` | backfill round |
| `gap_ranges` | gap ranges backfilled this round |
| `new_risks_found` | newly found risks this round |
| `new_safe_regions` | newly marked safe regions this round |
| `remaining_gaps` | gaps still remaining after backfill |

## Completion State Semantics (aligned with dotnet-coverage-audit)

- `COMPLETED`: `node/quality/api_coverage_gate_{timestamp}.md` exists and coverage reaches the gate (`api_coverage_percent=100%` in FULL mode), with no remaining gaps
- `PARTIAL`: gaps remain or `api_coverage_status=PARTIAL`; in this case the pipeline must persist `node/quality/unmapped_routes_{timestamp}.md` and continue the remapping loop
- `NOT_RUN`: this skill was not executed; the reason must be stated
- This skill **is not responsible for security judgments**; the completion state is only accountable for "coverage responsibility" and does not equal "code is safe"

## Handoff to Downstream Phases

```
Scan output (risks + safe_regions)
    → Coverage computes gaps
    → larger gaps sent back to Scan for backfill
    → update risks / safe_regions
    → Coverage outputs the final coverage report
    → handed to the Briefing phase to generate candidate parameter lists / routed to specialty audits by risk type
```

## Quality Gate

- [ ] Every file has a coverage_{filename|module}_{timestamp}.md output
- [ ] Gap computation is based on actual line number ranges, not estimates
- [ ] Backfill rounds do not exceed max_rounds
- [ ] The stop reason is explicitly recorded
- [ ] The final coverage percentage is computable
- [ ] The completion state declaration is consistent with the api_coverage_gate status (unmapped_routes persisted when PARTIAL)

## Output Paths

- `node/coverage_audit/coverage_{filename|module}_{timestamp}.md`
- `node/coverage_audit/backfill_{round}_{filename|module}_{timestamp}.md`
- `node/coverage_audit/index_{timestamp}.md` (batch master index)
