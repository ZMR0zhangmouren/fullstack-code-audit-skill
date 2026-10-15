---
name: dotnet-review-agent
description: .NET code audit evidence quality-review phase Skill. Uses another model's perspective to check the evidence completeness of Taint reports, challenging natural-language conclusions on what grounds they hold. Does not take over Taint's tool calls or code context; only reviews whether the evidence in reports is sufficient.
---

# .NET Evidence Quality Review (ReviewAgent)

## Objective

Use **another model's perspective** to check the evidence completeness of Taint reports, reducing the probability of the model closing the case prematurely.

**ReviewAgent only looks at reports, not code (sole exception: targeted evidence spot checks under minimal read-only review authority).**

## Core Principles

- ReviewAgent **only reviews evidence; it does not re-audit**
- ReviewAgent **only looks at cleaned reports**, not the original code
- **Exception: minimal read-only review authority** — allowed, and only allowed, to spot-check the existence of specific `file:line` evidence cited in the report (using Grep/Read to open the cited location and verify the cited code fragment truly exists and matches the report's paraphrase); expanding this into a full code re-review is forbidden
- ReviewAgent **challenges natural-language conclusions on what grounds they hold**
- When evidence is missing, package the review feedback as modification requirements for Taint, sending Taint back to the original code context to continue investigating

## Inputs

- Cleaned audit report (code context and tool-call details removed; only conclusions and evidence chains retained)
- `briefing/briefing_{sink_id}_{timestamp}.md`: the candidate parameter checklist for the current sink
- Review history (to avoid repeatedly challenging the same issue)

## Invisible (Taking Over Taint's Responsibilities Is Forbidden)

- ❌ Taint's tool calls and code context
- ❌ Proactively reading code in full; ✅ only targeted spot checks at `file:line` cited by the report are allowed
- ❌ Reports of other sinks (only the current sink is reviewed)

## Review Checklist

For each sink, check item by item:

### A. Parameter Completeness

- [ ] **Every parameter** in the checklist has a conclusion (holds / excluded / pending verification)
- [ ] No parameter is missing (if the checklist has 6 parameters, the report must also have 6 conclusions)
- [ ] STRUCTURE_POSITION parameters are verified with priority

### B. Entry Point Completeness

- [ ] Entry point search is complete (no missed request parameter, header, or cookie sources)
- [ ] Indirect controllability has been verified (whether it comes from the database, cache, or config file)
- [ ] Second-order data chains have been considered (stored data triggered a second time)

### C. Barrier Verification Depth

- [ ] The barrier's **actual implementation has been analyzed** (not just the function name)
- [ ] Whether the barrier is invoked correctly (any missed parameters, any being skipped by conditional branches)
- [ ] Whether edge cases have been tested (e.g. Unicode bypass, case sensitivity issues)

### D. Data Flow Chain Completeness

- [ ] Key code positions from the write entry point to the sink have been covered
- [ ] Intermediate propagation nodes (transfer) have been recorded
- [ ] Branch conditions (if/switch/try-catch) have been analyzed

### E. Evidence Quality

- [ ] No use of "possibly" or "if" in place of evidence
- [ ] No conclusions without an analysis process
- [ ] Both establishment chains and exclusion chains exist
- [ ] The vulnerability detail explains both: why it is dangerous + why the other parameters are not dangerous

### F. Second-Order Propagation

- [ ] `source_write_entry` has been verified (can the attacker control the data through a real write boundary)
- [ ] `source_trigger_entry` has been verified (can the stored value reach the sink along the execution path)
- [ ] Database syntax has been verified (does it allow closing backticks to change the query structure)

### G. Evidence Authenticity Spot Check

- [ ] At least **5** key evidence citations are spot-checked per sink (priority: sink execution point, user input mapping point, at least 1 intermediate propagation node, at least 1 branch/barrier point, remediation suggestion citation point)
- [ ] Spot-check method: use Grep/Read to open the `file:line` cited by the report, verifying the cited code fragment **truly exists** and **is semantically consistent with the report's paraphrase**
- [ ] **Counter-evidence search**: for each key piece of evidence, attempt to search for counter-evidence (other branches in the same file, alternative call paths); when counter-evidence is found, PASS is not allowed — must REJECT with the counter-evidence location attached
- [ ] The spot-check scope is strictly limited to locations already cited by the report; expanding into a full code re-review is not allowed
- [ ] If a cited location does not contain that code, or the code is semantically inconsistent with the paraphrase → **directly REJECT**, and annotate `evidence_fabrication_suspected` in `missing_items`

## Output Schema

### review/review_{sink_id}_{round}_{timestamp}.md

| Field | Description |
|------|------|
| `sink_id` | Identifier of the reviewed sink |
| `round` | Review round |
| `review_status` | `PASS` / `REJECT` |
| `checked_items` | Checklist items checked (A–F) |
| `missing_items` | List of missing items |
| `review_suggestions` | Modification suggestions (packaged as modification requirements for Taint) |
| `establishment_chain_valid` | Whether the establishment chain is complete |
| `exclusion_chain_valid` | Whether the exclusion chain is complete |
| `evidence_spotcheck_count` | Number of evidence authenticity spot checks (PASS requires >= 5) |
| `evidence_spotcheck_failures` | List of spot-check inconsistencies (cited location / expected content / actual situation; fill "none" if none) |

### Review Feedback Examples

#### PASS Example

```
review_status: PASS
sink_id: SQL_001
checked_items: A, B, C, D, E, F, G
missing_items: none
review_suggestions: none
establishment_chain_valid: true
exclusion_chain_valid: true
evidence_spotcheck_count: 5
evidence_spotcheck_failures: none
```

#### REJECT Example

```
review_status: REJECT
sink_id: SQL_001
checked_items: A, B, D, E
checked_items: C(missing_barrier_implementation), F(missing_second_order)
missing_items:
  - C.1: barrier actual implementation for column_key not analyzed (only the function name was seen; implementation source not read)
  - F.1: source_write_entry not verified (can the attacker write column_key via the SaveFieldConfig interface)
  - G.1: evidence_fabrication_suspected — the report cites an escape call at Services/QueryBuilder.cs:88, but that line is actually a logging statement, semantically inconsistent with the paraphrase
review_suggestions:
  - Taint phase needs to read the actual implementation of `escape_like_literal()` and confirm the escaping logic
  - Taint phase needs to trace the write entry point of `column_key` and verify attacker controllability
  - Taint phase needs to re-verify the real code locations in QueryBuilder.cs and fix the evidence citations
establishment_chain_valid: false
exclusion_chain_valid: true
evidence_spotcheck_count: 2
evidence_spotcheck_failures:
  - cited location: Services/QueryBuilder.cs:88 | expected: escape_like_literal(column_key) call | actual: logging statement, no escaping logic
```

## Handoff with the Taint Phase

```
Taint outputs audit report
    → ReviewAgent reviews the evidence
    → If PASS: report enters the Report phase
    → If REJECT: review feedback packaged as Taint modification requirements
    → Taint returns to the original code context to continue investigating and gather more evidence
    → Updated report submitted to ReviewAgent again
    → Loop until PASS or maximum Review rounds reached
```

## Maximum Review Rounds

- Default maximum 3 rounds
- If still REJECT after more than 3 rounds, the report is marked `⚠️Pending Verification` with the evidence gaps found by ReviewAgent but not closed explained

## Anti-Patterns (Forbidden)

- ❌ **ReviewAgent re-auditing code**: apart from targeted spot checks at report citations, ReviewAgent only looks at reports and does not read code
- ❌ **ReviewAgent modifying conclusions**: it can only propose modification requirements, which are executed by the Taint phase
- ❌ **Passing review with "possibly"**: insufficient evidence must result in REJECT
- ❌ **Ignoring exclusion chains**: only verifying establishment chains without verifying why other parameters were excluded
- ❌ **Skipping spot checks and passing directly**: a sink marked PASS must have `evidence_spotcheck_count >= 5`

## Quality Gate

- [ ] Every sink has been reviewed by ReviewAgent
- [ ] Sinks marked PASS have complete establishment chains and exclusion chains
- [ ] Sinks marked PASS have completed evidence authenticity spot checks (`evidence_spotcheck_count >= 5`)
- [ ] Sinks marked REJECT have explicit modification requirements
- [ ] Sinks exceeding the maximum rounds are marked `⚠️Pending Verification` with the evidence gap records retained

## Output Paths

- `review/review_{sink_id}_{round}_{timestamp}.md`
- `review/index_{timestamp}.md` (batch master index)
