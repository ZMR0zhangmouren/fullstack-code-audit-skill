---
name: dotnet-coverage-audit
description: .NET code audit coverage re-inspection phase Skill. Takes the risks and safe_regions output by the Scan phase, computes uncovered code fragments (gaps), and sends larger gaps back to the Scan phase for re-inspection. Does not make security judgments; only tracks coverage accountability.
---

# .NET Coverage Re-Inspection (Coverage)

## Objective

Based on the `risks` and `safe_regions` output by the Scan phase, **compute uncovered code fragments (gaps)** and send larger gaps back to the Scan phase for re-inspection.

**Coverage is not a security proof; it is accountability tracking.**
The model must not just say "I finished reading"; it must account for what it covered using risk regions and safe regions.

## Core Principles

- Coverage **does not judge whether semantics are complete**; it only computes physical coverage
- Coverage **does not prove code is safe**; it only tracks "what has not been looked at yet"
- Uncovered code fragments must be sent back to the Scan phase for re-inspection; skipping is not allowed

## Inputs

- `scan_audit/scan_{filename}_{timestamp}.md`: risks + safe_regions output by the Scan phase
- `source_path`: project source code path
- `min_gap`: minimum gap threshold (default 10 lines)
- `max_rounds`: maximum re-inspection rounds (default 3 rounds)

## Algorithm Logic

### 1. Compute Uncovered Ranges

```
Total file lines = actual code lines of the file (excluding blank lines and pure comment lines)
Covered ranges = risks.line_range ∪ safe_regions.line_range
Uncovered ranges = Total file lines - Covered ranges
```

### 2. Filter and Merge Gaps

- Gaps smaller than `min_gap` lines are ignored (to avoid over-inspecting tiny fragments)
- Adjacent gaps (separated by < 5 lines) are merged into one

### 3. Re-Inspection Loop

```
for round = 1 to max_rounds:
    gaps = find_uncovered_ranges(file, risks, safe_regions, min_gap)
    if gaps is empty or gaps are identical to the previous round:
        break
    for each gap in gaps:
        send the gap back to the Scan phase, requiring that code range to be scanned
    update risks and safe_regions
```

### 4. Stop Conditions

Stop re-inspection when any of the following holds:
- No gaps
- Gaps unchanged from the previous round (converged)
- `max_rounds` limit reached
- User explicitly terminates

## Output Schema

### 1. coverage_audit/coverage_{filename}_{timestamp}.md

A coverage report must be output for each file:

| Field | Description |
|------|------|
| `file_total_lines` | Total lines of the file |
| `risks_count` | Number of risks found |
| `safe_regions_count` | Number of marked safe regions |
| `gaps` | List of uncovered fragments (each gap contains start_line, end_line, line_count) |
| `rounds_executed` | Number of re-inspection rounds actually executed |
| `final_coverage_percent` | Final coverage percentage |
| `stop_reason` | Reason for stopping |

### 2. coverage_audit/backfill_{round}_{filename}_{timestamp}.md

Detailed record of each re-inspection round:

| Field | Description |
|------|------|
| `round` | Re-inspection round |
| `gap_ranges` | Gap ranges re-inspected in this round |
| `new_risks_found` | Newly found risks in this round |
| `new_safe_regions` | Newly marked safe regions in this round |
| `remaining_gaps` | Gaps still remaining after re-inspection |

## Handoff to Downstream Phases

```
Scan output (risks + safe_regions)
    → Coverage computes gaps
    → Large gaps sent back to Scan for re-inspection
    → Update risks / safe_regions
    → Coverage outputs final coverage report
    → Handed to the AttackSurface phase for routing by risk type
```

## Quality Gate

- [ ] Each file has a coverage_{filename}_{timestamp}.md output
- [ ] Gap computation is based on actual line number ranges, not estimates
- [ ] Re-inspection rounds do not exceed max_rounds
- [ ] Stop reason is explicitly recorded
- [ ] Final coverage percentage is computable

## Output Paths

- `coverage_audit/coverage_{filename}_{timestamp}.md`
- `coverage_audit/backfill_{round}_{filename}_{timestamp}.md`
- `coverage_audit/index_{timestamp}.md` (batch master index)
