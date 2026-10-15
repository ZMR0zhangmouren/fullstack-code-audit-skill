---
name: node-review-agent
description: Node.js code audit evidence quality-check phase skill. Uses another model's perspective to check the evidence completeness of Taint reports, probing what natural-language conclusions are based on. It does not take over Taint's tool calls or code site work; it only reviews whether the evidence in reports is sufficient.
---

# Node.js Evidence Quality Check (ReviewAgent)

## Goal

Use **another model's perspective** to check the evidence completeness of Taint reports, reducing the probability of the model closing prematurely.

**ReviewAgent only looks at reports, not code (the only exception: evidence spot checks under minimal read-only re-verification rights).**

## Core Principles

- ReviewAgent **only reviews evidence and does not re-audit**
- ReviewAgent **only looks at sanitized reports**, not the original code
- **Exception: minimal read-only re-verification rights** — it is allowed, and only allowed, to perform existence spot checks on specific `file:line` evidence cited in reports (using Grep / Read to open the cited location and verify that the cited code fragment really exists and is semantically consistent with the report's paraphrase); expanding this into a full code re-review is forbidden
- ReviewAgent **probes what natural-language conclusions are based on**
- When evidence is missing, the review feedback is packaged as modification requirements for Taint, sending Taint back to the original code context to continue investigating

## Input

- The sanitized audit report (code sites and tool call details removed; only conclusions and evidence chains retained)
- `node/briefing/briefing_{sink_id}_{timestamp}.md`: the candidate parameter checklist of the current sink (when the node-side briefing is not delivered, substitute with the parameter controllability matrix in `node/route_tracer/**`)
- Review history (to avoid re-probing the same question)

## Input Dependencies

- `node/route_tracer/**`: route-tracer batched tracing artifacts (including the parameter controllability matrix), serving as the substitute source of candidate parameter lists when briefing is not delivered
- `node/vuln_audit/*`: vulnerability specialty audit artifacts (the source of the reports being reviewed)
- `node/auth_audit/auth_mapping_*.md`: authentication and authorization mapping (the basis for reviewing AUTH-class sinks)
- `node/quality/api_coverage_gate_*.md`: API coverage gate (confirming whether the sink under review is within the coverage scope)
- When the above dependencies are missing, record `execution_status=NOT_RUN` with the missing reason in `node/review/index_{timestamp}.md`
- Evidence references follow the EVID_NODE_* namespace of `shared/EVIDENCE_POINT_IDS.md`; Sink type determination follows `shared/NODE_SINK_REFERENCE.md`

## Invisible (Taking Over Taint Responsibilities Is Forbidden)

- ❌ Taint's tool calls and code sites
- ❌ Proactively reading code in full; ✅ only targeted re-verification at `file:line` cited by reports is allowed
- ❌ Reports of other sinks (only the current sink is reviewed)

## Quality Check Checklist

For each sink, check item by item:

### A. Parameter Completeness

- [ ] **Every parameter** in the checklist has a conclusion (holds / excluded / pending verification)
- [ ] No parameter is missed (a checklist with 6 parameters must have 6 conclusions in the report)
- [ ] STRUCTURE_POSITION parameters are verified with priority

### B. Entry Completeness

- [ ] Entry search is complete (no missed request parameter, header, or cookie sources)
- [ ] Indirect controllability has been verified (whether it comes from the database, cache, or configuration files)
- [ ] Second-order data chains have been considered (triggered secondarily after storage)

### C. Barrier Verification Depth

- [ ] The barrier **actual implementation has been analyzed** (not just the function name)
- [ ] Whether the barrier is invoked correctly (no missing parameters, not skipped by conditional branches)
- [ ] Whether boundary cases have been tested (such as Unicode bypasses and case issues)

### D. Data Flow Chain Completeness

- [ ] Key code locations from the write entry to the sink have been covered
- [ ] Intermediate propagation nodes (transfer) have been recorded
- [ ] Branch conditions (if / switch / try-catch) have been analyzed

### E. Evidence Quality

- [ ] No "maybe" or "if" used in place of evidence
- [ ] No conclusions without analysis process
- [ ] Both the establishment chain and the exclusion chain exist
- [ ] Vulnerability details state both: why it is dangerous + why the other parameters are not dangerous

### F. Second-Order Propagation

- [ ] `source_write_entry` has been verified (whether the attacker can control the data through a real write boundary)
- [ ] `source_trigger_entry` has been verified (whether the saved value can reach the sink along the execution path)
- [ ] The database syntax has been verified (whether it allows closing backticks to change the query structure)

### G. Evidence Authenticity Spot Check

- [ ] Each sink has at least **5** key evidence references spot-checked (priorities: sink execution point, user input mapping point, at least 1 intermediate propagation node, at least 1 branch / barrier point, remediation recommendation reference point)
- [ ] Spot check method: use Grep / Read to open the `file:line` cited by the report and verify that the cited code fragment **really exists** and is **semantically consistent with the report's paraphrase**
- [ ] **Counter-evidence search**: for each key piece of evidence, attempt to search for counter-evidence (other branches in the same file, alternative call paths); when counter-evidence is found, PASS is not allowed — REJECT with the counter-evidence location attached
- [ ] The spot check scope is strictly limited to locations already cited by the report and must not expand into a full code re-review
- [ ] When a cited location does not contain the code, or the code does not match the paraphrase semantics → **REJECT directly**, and annotate `evidence_fabrication_suspected` in `missing_items`

## Output Schema

### node/review/review_{sink_id}_{round}_{timestamp}.md

| Field | Description |
|------|------|
| `sink_id` | the identifier of the sink under review |
| `round` | review round |
| `review_status` | `PASS` / `REJECT` |
| `checked_items` | checked checklist items (A–F) |
| `missing_items` | list of missing items |
| `review_suggestions` | modification suggestions (packaged as modification requirements for Taint) |
| `establishment_chain_valid` | whether the establishment chain is complete |
| `exclusion_chain_valid` | whether the exclusion chain is complete |
| `evidence_spotcheck_count` | number of evidence authenticity spot checks (PASS must be >= 5) |
| `evidence_spotcheck_failures` | list of spot-check inconsistencies (cited location / expected content / actual situation; write "none" when empty) |

### Sample Review Feedback

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
  - C.1: the actual implementation of the column_key barrier has not been analyzed (only the function name seen; implementation source not read)
  - F.1: source_write_entry not verified (whether the attacker can write column_key through the SaveFieldConfig endpoint)
  - G.1: evidence_fabrication_suspected — the report cites an escaping call at services/queryBuilder.js:88, but that line is actually a logging statement, inconsistent with the paraphrase
review_suggestions:
  - The Taint phase needs to read the actual implementation of `escape_like_literal()` and confirm the escaping logic
  - The Taint phase needs to trace the write entry of `column_key` and verify attacker controllability
  - The Taint phase needs to re-verify the real code locations in queryBuilder.js and correct the evidence references
establishment_chain_valid: false
exclusion_chain_valid: true
evidence_spotcheck_count: 2
evidence_spotcheck_failures:
  - cited location: services/queryBuilder.js:88 | expected: escape_like_literal(column_key) call | actual: logging statement, no escaping logic
```

## Handoff with the Taint Phase

```
Taint outputs the audit report
    → ReviewAgent reviews the evidence
    → if PASS: the report enters the Report phase
    → if REJECT: review feedback is packaged as modification requirements for Taint
    → Taint returns to the original code context to continue investigating and supplementing evidence
    → the updated report is submitted to ReviewAgent again
    → the loop continues until PASS or the maximum review round is reached
```

## Maximum Review Rounds

- Default maximum 3 rounds
- When still REJECT after more than 3 rounds, the report is marked `⚠️Pending Verification` with the evidence gaps found by ReviewAgent but not closed stated

## Anti-Patterns (Forbidden)

- ❌ **ReviewAgent re-auditing code**: except for targeted spot checks at report citations, ReviewAgent only looks at reports and does not read code
- ❌ **ReviewAgent modifying conclusions**: it can only raise modification requirements, executed by the Taint phase
- ❌ **Passing the review with "maybe"**: insufficient evidence must be REJECTed
- ❌ **Ignoring the exclusion chain**: only verifying the establishment chain without verifying why the other parameters are excluded
- ❌ **Skipping spot checks and passing directly**: sinks that PASS must have `evidence_spotcheck_count >= 5`

## Quality Gate

- [ ] Every sink has been reviewed by ReviewAgent
- [ ] Sinks that PASS must have complete establishment and exclusion chains
- [ ] Sinks that PASS must have completed evidence authenticity spot checks (`evidence_spotcheck_count >= 5`)
- [ ] Sinks that are REJECTed have explicit modification requirements
- [ ] Sinks exceeding the maximum rounds are marked `⚠️Pending Verification` with evidence gap records retained

## Output Paths

- `node/review/review_{sink_id}_{round}_{timestamp}.md`
- `node/review/index_{timestamp}.md` (batch master index)
