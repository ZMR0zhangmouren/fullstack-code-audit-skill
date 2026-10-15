# Fullstack Final Report Fixed Template (Quality Section)

Purpose: provide the single source of truth template for the "Quality Report Section (Fixed)" in the fullstack-mode (dotnet + Node.js) final report, avoiding missing fields and criteria drift.

Inherited from: `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md` (structural single source of truth; BLOCKED semantics inherited verbatim).

Suggested embedding: `{project_name}_code_audit_{timestamp}.md`

## Fixed Template (Mandatory Fields)

```md
## Quality Report Section (Fixed)

### 1) Four Completion Status Declarations
- dotnet_api_coverage_status: {COMPLETE|PARTIAL}
- node_api_coverage_status: {COMPLETE|PARTIAL}
- contract_coverage_status: {COMPLETE|PARTIAL}
- audit_surface_status: {COMPLETED|PARTIAL|INITIAL_SCREENED}
- coverage_mode: {FULL|SAMPLE|INCREMENTAL}

### 2) Coverage Gate Summary
- dotnet_api_coverage_percent: {n}%
- node_api_coverage_percent: {n}%
- pipeline_execution: {COMPLETED|PARTIAL}
- gate_decision: {ALLOW_COMPLETED|FORCE_PARTIAL}
- gate_reason: {text}
- unmapped_routes_source: quality/unmapped_routes_{timestamp}.md (required if dotnet_api_coverage_status=PARTIAL or node_api_coverage_status=PARTIAL; otherwise write N/A)

### 2.1) Cross-Stack Contract Coverage Summary
- contract_coverage_percent: {n}%
- contract_matched_count: {n}
- contract_frontend_only_count: {n}
- contract_backend_only_count: {n}
- contract_map_source: cross/api_contract_map_{timestamp}.md (N/A forbidden; if contract_coverage_status=PARTIAL it must point to the actual artifact or a remapping plan)

### 2.2) Hidden Attack Surface List
- backend_only_attack_surface:
  - route: {path}
    method: {HTTP_METHOD}
    auth_status: {PUBLIC|AUTHENTICATED|UNKNOWN}
    in_trace_pool: {true|false}
    notes: {text}
  - ... (list all backend_only entries exhaustively)

### 2.3) Cross-Stack Exploit Chains
- cross_stack_exploit_chain_source: cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md
- cross_stack_chain_status: {COMPLETED|PARTIAL|PENDING}
- xtrace_chains:
  - XTRACE-{id}: {description}
    feasibility: {Confirmed Feasible|Inferred Feasible|Theoretically Feasible}
    linker_status: {EXECUTED|NOT_EXECUTED}
    notes: {text}
  - ...
- cross-stack-taint-linker delivered (ACTIVE): cross-stack chains are aggregated by it; when there are no cross-stack chains, record NOT_APPLICABLE with `empty_result` and keep `linker_status` as `NOT_EXECUTED`

### 3) Coverage Scope Statement (Must Be Retained)
- If coverage_mode=SAMPLE or dotnet_api_coverage_status=PARTIAL or node_api_coverage_status=PARTIAL:
  This report represents audit conclusions for "mapped entries" only; it does not represent conclusions for the full set of active APIs.
- If coverage_mode=INCREMENTAL:
  This report must declare the incremental baseline (changed commit range), affected file count / total file count, and reference both stacks' `quality/incremental_scope_{timestamp}.md` and `unmapped_routes_{timestamp}.md` artifacts; "full audit complete" wording is forbidden.
- If contract_coverage_status=PARTIAL:
  Cross-stack contract coverage in this report is incomplete; backend_only entries in the hidden attack surface list may not have been fully traced.

### 4) exploit-chain Coverage Scope Summary (Fixed)
- exploit_chain_source: exploit_chain/exploit_chains_{timestamp}.md
- exploit_chain_coverage_mode: {FULL|SAMPLE}
- exploit_chain_api_coverage_status: {COMPLETE|PARTIAL}
- exploit_chain_api_coverage_percent: {n}%
- exploit_chain_sampled_scope: {true|false}

### 4.5) Consistency Check Summary (Recommended)
- consistency_check_source: quality/coverage_consistency_check_{timestamp}.md (if it exists)
- consistency_check_status: {PASS|BLOCKED|N/A}
- exploit_chain_consistency_check_counts: {PASS:n, BLOCKED:n, N/A:n}

### 4.6) Final Anchor Check Result Reference (Recommended)
- final_anchor_checklist_source: quality/final_anchor_checklist_{timestamp}.md (if it exists)
- final_anchor_decision: {PASS|BLOCKED|PENDING|N/A}
- final_anchor_checklist_counts: {PASS:n, BLOCKED:n, PENDING:n}

### 5) Skill Usage Tracking & Findings Table (Mandatory)

The final report is output in English.
It must begin with a Skill usage and findings matrix covering all dotnet-* and node-* skills within this project's execution scope.

Recommended fields:

| skill_name       | skill_type | execution_status | findings_status    | primary_outputs                        | depends_on                    | notes |
| ---------------- | ---------- | ---------------- | ------------------ | -------------------------------------- | ----------------------------- | ----- |
| dotnet-sql-audit | vuln_audit | COMPLETED        | FOUND / NO_FINDING | vuln_audit/sql_*.md; vuln_poc/sql_*.md | route_tracer; framework_audit | -     |
| node-sql-audit   | vuln_audit | COMPLETED        | FOUND / NO_FINDING | vuln_audit/sql_*.md; vuln_poc/sql_*.md | route_tracer; framework_audit | -     |

Field explanations:

- skill_name: the specific skill name
- skill_type: framework_audit / vuln_audit / route_tracer / mapping / dependency_scan / contract_linker, etc.
- execution_status: NOT_RUN / INITIAL_SCREENED / PARTIAL / COMPLETED / NOT_APPLICABLE
- findings_status: FOUND / NO_FINDING / PENDING_VERIFICATION / ENVIRONMENT_DEPENDENT
- primary_outputs: files generated by or primarily consumed by this skill
- depends_on: the prerequisite phases or key artifacts it depends on
- notes: blocking reasons, review recommendations, environment limitations, evidence gaps

For "other vulnerability types": if only the grabber initial screening was run without completing the full specialty analysis, they must be explicitly marked INITIAL_SCREENED; if the specialty analysis was entered but the loop was not closed, they must be marked PARTIAL.

### 6) Vulnerability List Overview

**Severity Detail-Level Rules (Mandatory)**:
- Severity enum closure (2026-09-20): severity allows only the four values `C` / `H` / `M` / `L`; boundary cases use the upgrade-channel annotation format `L (suggest upgrade to M, reason: …)`; range values are forbidden ("L-M" is a counterexample and non-compliant; source of truth see the "Severity Enum Closure" section of `SEVERITY_RATING.md`).
- H severity + key M severity (confirmed exploitable / cross-stack chain closed): full detail block (fixed structure unchanged).
- Regular M severity: the detail block is compressed to "three evidence paragraphs + suggested fix", with sink details replaced by specialty artifact references.
- L severity: table row only (ID / severity / title / file:line / specialty artifact reference); no detail block.
- Pending / risk-pool items: enter only the risk pool table (§7 or the corresponding section); no details in the body.
- Detail-level reduction does not exempt traceability: every vulnerability must be locatable from the report to the specialty artifact (path + anchor).

(Reference vuln_audit/* and vuln_poc/* conclusions; fill vulnerability details per the vulnerability detail template)

### 7) Unclosed Traces / Pending-Evidence Risk Pool
(List route_id or SINK_ONLY synthetic IDs, missing evidence, and recommended actions)
```

## Acceptance Points

- When `dotnet_api_coverage_status != COMPLETE` or `node_api_coverage_status != COMPLETE`, `pipeline_execution` must not be `COMPLETED`
- When `coverage_mode = SAMPLE`, `pipeline_execution` must not be `COMPLETED`
- When `dotnet_api_coverage_status = PARTIAL` or `node_api_coverage_status = PARTIAL`, `unmapped_routes_source` must not be N/A and must point to an actual artifact file
- When `contract_coverage_status = PARTIAL`, `contract_map_source` must not be N/A and must point to the actual `cross/api_contract_map_{timestamp}.md` artifact or a remapping plan file
- `contract_backend_only_count` must equal the total number of backend_only entries in the "Hidden Attack Surface List"
- `exploit_chain_consistency_check_counts` must be consistent with the `exploit_chain` overview table statistics
- If `consistency_check_status=BLOCKED`, `quick_validation.final_decision` must be linked to `BLOCKED`
- If `consistency_check_status=BLOCKED`, cross-stack exploit chain feasibility must not be written as "Confirmed Feasible"
- If `final_anchor_checklist_{timestamp}.md` exists, it is recommended that the final report write back its `final_anchor_decision` and PASS/BLOCKED/PENDING counts

## Minimal Example (Copyable)

```md
## Quality Report Section (Fixed)

### 1) Four Completion Status Declarations
- dotnet_api_coverage_status: PARTIAL
- node_api_coverage_status: COMPLETE
- contract_coverage_status: PARTIAL
- audit_surface_status: PARTIAL
- coverage_mode: SAMPLE

### 2) Coverage Gate Summary
- dotnet_api_coverage_percent: 88%
- node_api_coverage_percent: 100%
- pipeline_execution: PARTIAL
- gate_decision: FORCE_PARTIAL
- gate_reason: dotnet_api_coverage_status=PARTIAL
- unmapped_routes_source: quality/unmapped_routes_2026_08_22_10_20.md

### 2.1) Cross-Stack Contract Coverage Summary
- contract_coverage_percent: 75%
- contract_matched_count: 45
- contract_frontend_only_count: 5
- contract_backend_only_count: 10
- contract_map_source: cross/api_contract_map_2026_08_22_10_20.md

### 2.2) Hidden Attack Surface List
- backend_only_attack_surface:
  - route: /api/v1/admin/legacy-sync
    method: POST
    auth_status: AUTHENTICATED
    in_trace_pool: false
    notes: not referenced by the frontend; included in the pending-evidence risk pool
  - route: /internal/health/detailed
    method: GET
    auth_status: PUBLIC
    in_trace_pool: true
    notes: entered the trace pool; waiting for route-tracer closure

### 2.3) Cross-Stack Exploit Chains
- cross_stack_exploit_chain_source: cross/exploit_chain/cross_stack_exploit_chains_2026_08_22_10_20.md
- cross_stack_chain_status: PENDING
- xtrace_chains:
  - XTRACE-001: frontend login form → Node.js BFF → dotnet AuthService token generation
    feasibility: Inferred Feasible
    linker_status: EXECUTED
    notes: taint-linker has linked the cross-stack taint chain; dynamic re-verification pending

### 3) Coverage Scope Statement (Must Be Retained)
- This report represents audit conclusions for "mapped entries" only; it does not represent conclusions for the full set of active APIs.
- Cross-stack contract coverage in this report is incomplete; backend_only entries in the hidden attack surface list may not have been fully traced.

### 4) exploit-chain Coverage Scope Summary (Fixed)
- exploit_chain_source: exploit_chain/exploit_chains_2026_08_22_10_20.md
- exploit_chain_coverage_mode: SAMPLE
- exploit_chain_api_coverage_status: PARTIAL
- exploit_chain_api_coverage_percent: 88%
- exploit_chain_sampled_scope: true

### 4.5) Consistency Check Summary (Recommended)
- consistency_check_source: quality/coverage_consistency_check_2026_08_22_10_20.md
- consistency_check_status: PASS
- exploit_chain_consistency_check_counts: {PASS:3, BLOCKED:0, N/A:1}

### 4.6) Final Anchor Check Result Reference (Recommended)
- final_anchor_checklist_source: quality/final_anchor_checklist_2026_08_22_10_20.md
- final_anchor_decision: PASS
- final_anchor_checklist_counts: {PASS:5, BLOCKED:0, PENDING:0}

### 5) Skill Usage Tracking & Findings Table (Mandatory)
(Fill in skill_name / skill_type / execution_status / findings_status / primary_outputs / depends_on / notes)

### 6) Vulnerability List Overview
(Reference vuln_audit/* and vuln_poc/*)

### 7) Unclosed Traces / Pending-Evidence Risk Pool
(List route_id / SINK_ONLY and recommended actions)
```

## BLOCKED Minimal Example (Count Reconciliation Failure)

Purpose: train executors to recognize the blocking scenario where "final report fields are written out, but consistency counts are still not deliverable".

```md
## Quality Report Section (Fixed)

### 1) Four Completion Status Declarations
- dotnet_api_coverage_status: PARTIAL
- node_api_coverage_status: COMPLETE
- contract_coverage_status: PARTIAL
- audit_surface_status: PARTIAL
- coverage_mode: SAMPLE

### 2) Coverage Gate Summary
- dotnet_api_coverage_percent: 88%
- node_api_coverage_percent: 100%
- pipeline_execution: PARTIAL
- gate_decision: FORCE_PARTIAL
- gate_reason: dotnet_api_coverage_status=PARTIAL
- unmapped_routes_source: quality/unmapped_routes_2026_08_22_18_10.md

### 2.1) Cross-Stack Contract Coverage Summary
- contract_coverage_percent: 75%
- contract_matched_count: 45
- contract_frontend_only_count: 5
- contract_backend_only_count: 10
- contract_map_source: cross/api_contract_map_2026_08_22_18_10.md

### 2.2) Hidden Attack Surface List
- backend_only_attack_surface:
  - route: /api/v1/admin/legacy-sync
    method: POST
    auth_status: AUTHENTICATED
    in_trace_pool: false
    notes: not referenced by the frontend; included in the pending-evidence risk pool
  - route: /internal/health/detailed
    method: GET
    auth_status: PUBLIC
    in_trace_pool: true
    notes: entered the trace pool; waiting for route-tracer closure

### 2.3) Cross-Stack Exploit Chains
- cross_stack_exploit_chain_source: cross/exploit_chain/cross_stack_exploit_chains_2026_08_22_18_10.md
- cross_stack_chain_status: PENDING
- xtrace_chains:
  - XTRACE-001: frontend login form → Node.js BFF → dotnet AuthService token generation
    feasibility: Theoretically Feasible (count reconciliation failed; automatically downgraded)
    linker_status: EXECUTED
    notes: consistency_check_status=BLOCKED → feasibility downgraded; "Confirmed Feasible" wording forbidden

### 3) Coverage Scope Statement (Must Be Retained)
- This report represents audit conclusions for "mapped entries" only; it does not represent conclusions for the full set of active APIs.
- Cross-stack contract coverage in this report is incomplete; backend_only entries in the hidden attack surface list may not have been fully traced.

### 4) exploit-chain Coverage Scope Summary (Fixed)
- exploit_chain_source: exploit_chain/exploit_chains_2026_08_22_18_10.md
- exploit_chain_coverage_mode: SAMPLE
- exploit_chain_api_coverage_status: PARTIAL
- exploit_chain_api_coverage_percent: 88%
- exploit_chain_sampled_scope: true

### 4.5) Consistency Check Summary (Recommended)
- consistency_check_source: quality/coverage_consistency_check_2026_08_22_18_10.md
- consistency_check_status: BLOCKED
- exploit_chain_consistency_check_counts: {PASS:3, BLOCKED:0, N/A:1}

### 4.6) Final Anchor Check Result Reference (Recommended)
- final_anchor_checklist_source: quality/final_anchor_checklist_2026_08_22_18_10.md
- final_anchor_decision: BLOCKED
- final_anchor_checklist_counts: {PASS:3, BLOCKED:1, PENDING:1}

### 5) Skill Usage Tracking & Findings Table (Mandatory)
(Fill in skill_name / skill_type / execution_status / findings_status / primary_outputs / depends_on / notes)

### 6) Vulnerability List Overview
(Reference vuln_audit/* and vuln_poc/*)

### 7) Unclosed Traces / Pending-Evidence Risk Pool
(List route_id / SINK_ONLY and recommended actions)
```

#### BLOCKED Example Determination Notes (Apply Only to the BLOCKED Minimal Example Above)

- If `consistency_check_status=BLOCKED`, this example is not deliverable
- If `exploit_chain_consistency_check_counts` is inconsistent with the exploit_chain overview table statistics, the final report must be written back first, and then `quick_validation` must be re-run
- If any BLOCKED exists, exploit-chain conclusions must not be written as "Confirmed Feasible"
- If contract reconciliation is blocked (`contract_coverage_gate` determined as BLOCKED, e.g., `contract_map_source` points to an empty file), or when `consistency_check_status=BLOCKED`, the contract coverage conclusion is downgraded to PARTIAL per the gate determination; `contract_coverage_status` among the four declarations must not be COMPLETE

## Vulnerability Detail Template (Mandatory)

> Used in **### 6) Vulnerability List Overview** of the **Fixed Template (Mandatory Fields)**.

### Per-Vulnerability Detail Structure (Mandatory)

Each vulnerability must follow the following structure (written into the vulnerability detail paragraph of the overall report):

```markdown
### [{severity prefix}-{type code}-{sequence number}] {risk title}

| Item | Information |
|------|------|
| Severity | {🔴/🟠/🟡/🔵} (CVSS {score}) |
| Reachability (R) | {0-3} - {reason} |
| Impact (I) | {0-3} - {reason} |
| Exploitation Complexity (C) | {0-3} - {reason} |
| Exploitability | ✅ Confirmed / ⚠️ Pending Verification / ❌ Not Exploitable / 🔍 Environment-Dependent |
| Location | {file path}:{line number} ({function/method}) |

#### Data Flow Chain (Source → Sink)
```

(Write assignment/passing/concatenation/validation/branches line by line per route; omission is forbidden)

#### Exploit Preconditions

- Authentication requirement: {none / login required / specific permission required}
- Input controllability: {fully controllable / conditionally controllable / not controllable}
- Trigger conditions: {branch / exception / environment dependency}

#### Verification PoC (Executable Request Mandatory)

```http
{HTTP Method} {full path and query/body} HTTP/1.1
Host: {host}
{necessary headers/session/JWT/cookie}

{Payload}
```

#### Suggested Fix

```
- Focus on "code replacement suggestions" (give key points of the safe way to write it)
- Provide search statements for "how to search the code for missed fixes" (in bash/rg form)
```
