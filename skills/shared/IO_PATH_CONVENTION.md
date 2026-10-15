# Input/Output Path Convention (Unified for All .NET Skills)

This file removes ambiguity between "logical section names" and "physical on-disk paths"; it applies to all dotnet-* skills and dotnet-audit-pipeline.

## Two Execution Forms

| Form | Meaning |
| ---- | ---- |
| Pipeline merged | When orchestrated by dotnet-audit-pipeline, a single overall report is ultimately formed, but the structured artifact directories and files of each phase are still required to be physically created first by default |
| Single skill standalone | When only one skill is invoked, directories and files may be physically created following the suggested paths |

## Default Execution Mode (Mandatory On-Disk Persistence)

dotnet-security-audit-skill uses mandatory on-disk persistence by default, rather than keeping only logical sections.

By default, executing dotnet-audit-pipeline should physically create at least the following directories:

- codegraph/
- scan_audit/
- coverage_audit/
- design_intent/                # Design-intent summary (Phase 0.7 artifact; create the directory and write status even when there is no result)
- route_mapping/
- auth_audit/
- route_tracer/
- briefing/
- vuln_audit/
- vuln_poc/
- framework_audit/
- cross_analysis/
- vuln_report/
- exploit_chain/
- global_sink_fallback/
- review/
- quality/

If a phase produces nothing confirmable, the corresponding directory should still be created, and the reason ("no result / not executed / pending verification / environment-dependent") written in the directory's index file or phase file — rather than leaving the directory missing entirely.

## Phase Index Files and Empty-Result Files (Mandatory)

Each phase directory should by default contain at least one index file recording:

- which skills were invoked in this phase
- which files were actually generated
- which results are empty
- which results are only initial screening or partially complete

Recommended phase index files:

- scan_audit/index_{timestamp}.md
- coverage_audit/index_{timestamp}.md
- route_mapping/index_{timestamp}.md
- auth_audit/index_{timestamp}.md
- route_tracer/index_{timestamp}.md
- briefing/index_{timestamp}.md
- vuln_audit/index_{timestamp}.md
- vuln_poc/index_{timestamp}.md
- framework_audit/index_{timestamp}.md
- cross_analysis/index_{timestamp}.md
- review/index_{timestamp}.md
- vuln_report/index_{timestamp}.md
- quality/pipeline_execution_{timestamp}.md
- quality/api_coverage_gate_{timestamp}.md
- quality/quick_validation_{timestamp}.md (recommended: quick final check before delivery)
- quality/quick_validation_example_{timestamp}.md (recommended: training/regression reference example)
- quality/coverage_consistency_check_{timestamp}.md (recommended: cross-artifact field consistency check)
- quality/final_anchor_checklist_{timestamp}.md (recommended: final-anchor per-file checklist and summary)

If a directory has no explicit result, at least one of the following must still be created:

- index_{timestamp}.md: records the status "no result / not executed / pending verification / environment-dependent / initial screening"
- empty_result_{timestamp}.md: explains why this phase produced no formal finding or formal file

A directory existing without an index/explanation file is not allowed.

## Vulnerability Specialty Status Model (Mandatory)

dotnet-*-audit skills must use at least one of the following statuses during execution:

| Status | Meaning |
| ---- | ---- |
| NOT_RUN | Not executed; the reason must be stated |
| INITIAL_SCREENED | Initial screening done; only basic enumeration or coarse screening performed, evidence closure not yet completed |
| PARTIAL | Partially complete; specialty analysis entered, but trace, framework preconditions, or environment evidence not fully closed |
| COMPLETED | Completed; specialty conclusion output meeting current phase requirements is available |
| NOT_APPLICABLE | Not applicable; why it does not apply to this project or entry must be stated |

Constraints:

- Non-priority vulnerability types are allowed to remain at INITIAL_SCREENED or PARTIAL in a default execution, but they must not be completely unrecorded
- Even when no issue is found, it must be recorded that the skill executed with result NO_ISSUE or NO_FINDING
- The final report must be able to trace back the execution status and whether findings exist for every dotnet-*-audit skill
- The vulnerability index (`vuln_audit/index_{timestamp}.md`) must contain a `## Specialty Dispatch Verification` section: every ACTIVE specialty in `PHASE_STATUS` is checked one by one, in one of three states — `Triggered` (with artifact path) / `Negative Evidence` (NOT_APPLICABLE, with scope + rg pattern) / `Not Applicable` (with reason); bare "not triggered" / "not executed" wording is forbidden, and a missing row means a silently missed dispatch.
- The vulnerability index must also contain a `## Dimension Verification` section (parallel to "Specialty Dispatch Verification", effective 2026-09-20): every mechanism-extension dimension registered in the ledger is checked one by one in three states — `Covered` (with artifact section location) / `Negative Evidence` (with scope + rg pattern) / `Not Applicable` (with determination reason); bare "not covered" / "not mentioned" wording is forbidden, and a missing row means a silently missing dimension. Dual sources of truth for dimensions: registration source = the ledger (`docs/NewSkillRegistration.md`, Section 2, "Mechanisms Covered" field of each mechanism-extension entry); execution source = the dimension list snapshot in this appendix ("Dimension List (Execution Source Snapshot, 2026-09-21)"). New dimensions must be registered first (CLAUDE.md rule 0: "register before implementing") and synced into this snapshot before entering the mandatory enumeration list of specialties; specialties adding unregistered dimensions in their own body text is forbidden. The negative-evidence discipline for dimensions is the same as for specialty dispatch verification (scope + rg pattern, not vague assertions).

## Canonical Names and Common Physical Paths

| Canonical Name | Common Physical Path | Description |
| ---- | ---- | ---- |
| codegraph_index_status_{timestamp}.md | codegraph/codegraph_index_status_{timestamp}.md | CodeGraph index status and metadata |
| codegraph_index_validation_{timestamp}.md | quality/codegraph_index_validation_{timestamp}.md | CodeGraph index quality validation results |
| scan_{filename}_{timestamp}.md | scan_audit/scan_{filename}_{timestamp}.md | Per-file security scan report (Phase 0.5, FULL/SAMPLE per file) |
| scan_{module}_{timestamp}.md | scan_audit/scan_{module}_{timestamp}.md | Module-aggregated scan report (INCREMENTAL mode) |
| scan_audit/index_{timestamp}.md | scan_audit/index_{timestamp}.md | Scan batch master index |
| coverage_{filename}_{timestamp}.md | coverage_audit/coverage_{filename}_{timestamp}.md | Per-file coverage backfill report (Phase 0.6) |
| backfill_{round}_{filename}_{timestamp}.md | coverage_audit/backfill_{round}_{filename}_{timestamp}.md | Coverage backfill round record |
| coverage_audit/index_{timestamp}.md | coverage_audit/index_{timestamp}.md | Coverage batch master index |
| controller_inventory_{timestamp}.md | route_mapping/controller_inventory_{timestamp}.md | Controller/action reconciliation list |
| routes_{timestamp}.md | route_mapping/routes_{timestamp}.md | HTTP / Hub / GraphQL / WCF entry list |
| params_{timestamp}.md | route_mapping/params_{timestamp}.md | Parameter structure corresponding to each entry |
| auth_mapping_{timestamp}.md | auth_audit/auth_mapping_{timestamp}.md | Static authentication bucketing |
| high_risk_routes_{timestamp}.md | cross_analysis/high_risk_routes_{timestamp}.md | High-risk entry set |
| sampled_high_risk_routes_{timestamp}.md | cross_analysis/sampled_high_risk_routes_{timestamp}.md | High-risk candidate entry set under sample mode (not exhaustive) |
| trace_batch_plan_{timestamp}.md | cross_analysis/trace_batch_plan_{timestamp}.md | Batched tracing plan |
| sink_suspect_dict_{timestamp}.md | cross_analysis/sink_suspect_dict_{timestamp}.md | Project-private SINK_SUSPECT parameter-name dictionary (pinyin/abbreviations/DTO deep fields/business terms; generated after Phase 1 parameter enumeration) |
| briefing_{sink_id}_{timestamp}.md | briefing/briefing_{sink_id}_{timestamp}.md | Candidate parameter list for a single sink (Phase 3.5) |
| briefing/index_{timestamp}.md | briefing/index_{timestamp}.md | Candidate parameter list batch master index |
| review_{sink_id}_{round}_{timestamp}.md | review/review_{sink_id}_{round}_{timestamp}.md | Per-sink per-round evidence quality check result (Phase 4.5); schema contains `evidence_spotcheck_count` / `evidence_spotcheck_failures` fields; REJECT may be annotated with `evidence_fabrication_suspected` |
| review/index_{timestamp}.md | review/index_{timestamp}.md | Quality-check batch master index |
| route_tracer/{route_id}/... | route_tracer/{route_id}/... | Tracing bucket artifacts |
| vuln_audit/{type}_{timestamp}.md | vuln_audit/{type}_{timestamp}.md | Vulnerability specialty artifact |
| vuln_audit/query_{timestamp}.md | vuln_audit/query_{timestamp}.md | Non-SQL query injection specialty artifact |
| vuln_audit/export_{timestamp}.md | vuln_audit/export_{timestamp}.md | Spreadsheet formula injection specialty artifact |
| vuln_audit/prompt_{timestamp}.md | vuln_audit/prompt_{timestamp}.md | AI prompt injection specialty artifact |
| vuln_poc/{type}_{timestamp}.md | vuln_poc/{type}_{timestamp}.md | Vulnerability specialty PoC / pending-verification PoC artifact |
| framework_audit/{name}_{timestamp}.md | framework_audit/{name}_{timestamp}.md | Framework specialty artifact |
| exploit_chains_{timestamp}.md | exploit_chain/exploit_chains_{timestamp}.md | Exploit chain aggregation report (includes coverage scope and consistency_check_status) |
| vuln_report/{project_name}_nuget_vuln_report_{timestamp}.md | vuln_report/{project_name}_nuget_vuln_report_{timestamp}.md | Dependency vulnerability report (header fields include `knowledge_cutoff_date` / `offline_report_source`, effective 2026-09-18) |
| index_{timestamp}.md | {stage}/index_{timestamp}.md | Phase index file recording execution status and artifact list |
| empty_result_{timestamp}.md | {stage}/empty_result_{timestamp}.md | Empty-result explanation file recording why there is no result |
| pipeline_execution_{timestamp}.md | quality/pipeline_execution_{timestamp}.md | Overall execution list and skill usage tracking |
| manifest_{run_id}.md | quality/manifest_{run_id}.md | Resume-from-breakpoint manifest (phase state machine, trace_status, execution_status, interruption point and next action; mandatory) |
| preflight_{timestamp}.md | quality/preflight_{timestamp}.md | Phase 0 preflight environment check (model enumeration probe / `.codegraph` upward resolution / dotnet SDK availability / credential availability declaration; degradation items go into manifest `gate_reason`, effective 2026-09-20) |
| incremental_scope_{timestamp}.md | quality/incremental_scope_{timestamp}.md | INCREMENTAL-mode change scope description (change baseline, changed file set, affected call chain expansion description) |
| api_coverage_gate_{timestamp}.md | quality/api_coverage_gate_{timestamp}.md | API coverage gate result (coverage percentage and unmapped list) |
| unmapped_routes_{timestamp}.md | quality/unmapped_routes_{timestamp}.md | Unmapped entry list and next-round remapping suggestions (mandatory when PARTIAL) |
| route_mapping_backfill_loop_{timestamp}.md | quality/route_mapping_backfill_loop_{timestamp}.md | Remapping loop round record (recommended) |
| quick_validation_{timestamp}.md | quality/quick_validation_{timestamp}.md | Final validation result (status consistency and declaration completeness) |
| quick_validation_example_{timestamp}.md | quality/quick_validation_example_{timestamp}.md | Final validation minimal example (training/regression reference) |
| coverage_consistency_check_{timestamp}.md | quality/coverage_consistency_check_{timestamp}.md | Cross-artifact field consistency check (gate/trace/exploit-chain/final report) |
| final_anchor_checklist_{timestamp}.md | quality/final_anchor_checklist_{timestamp}.md | Final-anchor per-file checklist (with PASS/BLOCKED/PENDING summary) |
| DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md | skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md | Final report quality section fixed template (single source of truth) |

## design_intent search_scope and Intent Sources (2026-09-18)

- Probe directory patterns (suffix match, recursive at any depth, excluding node_modules/bin/obj/dist/build/.next/.nuxt/coverage/.git):
  `**/docs/superpowers/specs/*.md`, `**/docs/superpowers/plans/*.md`, `**/docs/design/*.md`, `**/.superpowers/sdd/*/`, `**/docs/adrs/*.md` (whitelist enabled by default), `**/docs/rfcs/*.md` (whitelist enabled by default)
- The artifact's "Collection Status" section must contain a `search_scope` block (format see spec §2.3 code block)
- The negative-conclusion recheck protocol see `AUDIT_EXECUTION_COMMON.md` §9 rule ⑤

## Final Report Fixed Field Write-Back Sources (Recommended)

When the final report reuses `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md`, the following fields should keep a one-to-one mapping with the corresponding artifacts:

| Final Report Field | Recommended Source File | Write-Back Requirement |
| ---- | ---- | ---- |
| `consistency_check_source` | `quality/coverage_consistency_check_{timestamp}.md` | If the file exists, the path should be written back verbatim |
| `consistency_check_status` | `quality/coverage_consistency_check_{timestamp}.md` | Consistent with `final_status` |
| `exploit_chain_consistency_check_counts` | `exploit_chain/exploit_chains_{timestamp}.md` | Consistent with the exploit_chain overview table statistics |
| `final_anchor_checklist_source` | `quality/final_anchor_checklist_{timestamp}.md` | If the file exists, the path should be written back verbatim |
| `final_anchor_decision` | `quality/final_anchor_checklist_{timestamp}.md` | Consistent with `final_anchor_decision` in the checklist summary block |
| `final_anchor_checklist_counts` | `quality/final_anchor_checklist_{timestamp}.md` | Consistent with `checklist_pass_count / checklist_blocked_count / checklist_pending_count` |

Additional constraints:

- If `quality/final_anchor_checklist_{timestamp}.md` exists, the final report must not omit `4.6) Final Anchor Check Result Reference`
- If `final_anchor_decision = BLOCKED`, the final report must not use positive closing wording such as "deliverable", "finalization complete", or "final pass"
- If `api_coverage_status = PARTIAL`, `quality/unmapped_routes_{timestamp}.md` should also exist, and it is recommended to retain its blocking relationship in the final anchor or final report notes

### Final Field Reconciliation Static Mapping Template (P3)

| Field | Single Source of Truth | Consumer | Reconciliation Rule |
| ---- | ---- | ---- | ---- |
| api_coverage_status | quality/api_coverage_gate_*.md | Final report 2) Coverage Gate Summary, manifest | gate value = report value; inconsistency → FAIL |
| pipeline_execution | quality/pipeline_execution_*.md | manifest, quick_validation | When COMPLETED, gate must be COMPLETE and percent=100% (FULL) |
| dotnet_api_coverage_status and the other three declarations | Per-stack gate + cross/contract gate | Fullstack final report | Fields traceable (validate_audit.py check F) |
| contract_coverage_percent | cross/contract_coverage_gate_*.md | Fullstack report 2.1) | = matched/(matched+frontend_only+backend_only) |
| final_anchor_decision | quality/final_anchor_checklist_*.md | Final report 4.6 | PASS/BLOCKED/PENDING aligned field by field with summary counts |

- The three machine-check lines of final_anchor (pool count = unique ID count / statistics table = detail enumeration count / chain status decomposition) must be included in the checklist summary block

## final_anchor ↔ final_report 4.6 Minimal Reconciliation Example

Purpose: help executors quickly verify that the "final anchor checklist summary block" and the "final report 4.6 fields" are aligned, preventing a change in one place from being missed in the other.

### Checklist Summary Block (quality/final_anchor_checklist_{timestamp}.md)

```
## Summary
- checklist_pass_count: 3
- checklist_blocked_count: 2
- checklist_pending_count: 0
- final_anchor_decision: BLOCKED
```

### Final Report 4.6 Write-Back Fields (Must Correspond One-to-One with the Above)

```
### 4.6) Final Anchor Check Result Reference (Recommended)
- final_anchor_checklist_source: quality/final_anchor_checklist_{timestamp}.md
- final_anchor_decision: BLOCKED
- final_anchor_checklist_counts: {PASS:3, BLOCKED:2, PENDING:0}
```

Field mappings when reconciling:

| Final Report Field | Corresponding Checklist Field | Reconciliation Rule |
| ---- | ---- | ---- |
| `final_anchor_decision` | `final_anchor_decision` | Values must be completely identical |
| `final_anchor_checklist_counts.PASS` | `checklist_pass_count` | Numbers must match |
| `final_anchor_checklist_counts.BLOCKED` | `checklist_blocked_count` | Numbers must match |
| `final_anchor_checklist_counts.PENDING` | `checklist_pending_count` | Numbers must match |

Typical reconciliation failures (must not occur):

- Checklist writes `final_anchor_decision: BLOCKED`, final_report writes `final_anchor_decision: PASS`
- Checklist writes `checklist_blocked_count: 2`, final_report writes `{PASS:5, BLOCKED:0, PENDING:0}`
- final_report has `4.6` but `final_anchor_checklist_source` is empty
## Read Rules

When a skill says "read route_mapping/routes_*.md", in merged mode it should be understood as "read the route section in the overall report equivalent to routes_{timestamp}.md".

However, the default execution model of dotnet-security-audit-skill still requires physically creating the original artifacts first and then aggregating them via the pipeline; therefore the overall report must not replace the original phase files.

The execution matrix in the final report must be reversely mappable to index_{timestamp}.md or empty_result_{timestamp}.md under each phase directory.

## Coverage Gate and Completion Status Conventions (Mandatory)

- `coverage_mode` allows `FULL | SAMPLE | INCREMENTAL`; default `FULL`
- When `coverage_mode = INCREMENTAL`: `quality/incremental_scope_{timestamp}.md` must be persisted; when the change set (including expanded call chains) is 100% covered, `pipeline_execution=COMPLETED` is allowed, but the final report must declare `coverage_mode=INCREMENTAL`, the change baseline (commit range), and affected file count / total file count; "full audit complete" wording is forbidden
- Only when `api_coverage_status = COMPLETE` may the formal `cross_analysis/high_risk_routes_{timestamp}.md` be output
- If `api_coverage_status = PARTIAL` or `coverage_mode = SAMPLE`, `cross_analysis/sampled_high_risk_routes_{timestamp}.md` must be output
- If `api_coverage_status = PARTIAL`, `quality/unmapped_routes_{timestamp}.md` must be output
- If `api_coverage_status = PARTIAL` and the user has not explicitly terminated, the route mapping remapping loop must not end
- When `api_coverage_status != COMPLETE`, `pipeline_execution` in `quality/pipeline_execution_{timestamp}.md` must not be marked `COMPLETED`
- If `quality/final_anchor_checklist_{timestamp}.md` exists, the `final_anchor_checklist_source`, `final_anchor_decision`, and `final_anchor_checklist_counts` in the final report must be consistent with that file
- If `final_anchor_decision = BLOCKED`, the final report must not be written as "delivery passed" or an equivalent positive completion conclusion
- The final report must declare both `audit_surface_status` and `api_coverage_status`; a single "completed" must not substitute for them
- `cross_analysis/trace_batch_plan_{timestamp}.md` must satisfy the coverage mode thresholds:
	- FULL: `trace_batch_max_size` between 10–30
	- SAMPLE: `trace_batch_max_size` between 5–10, and must not exceed 10
	- SAMPLE: `planned_batch_count <= batch_count_upper_bound(=6)`; exceeding the limit requires re-planning
- If `quality/coverage_consistency_check_{timestamp}.md` exists and `final_status=BLOCKED`:
	- The chain feasibility in `exploit_chain/exploit_chains_{timestamp}.md` must not be labeled "confirmed feasible"
	- The `exploit_chain_consistency_check_counts` in the final report must reflect the BLOCKED count

## Route Count Dual-Field Criteria (Mandatory)

- `unique_path_count`: the number of unique paths after deduplication.
- `method_path_count`: the total count of (method, path) expansions; **the sole consumption criterion for cross-stack contract reconciliation**.
- Both fields must be written in the routes file header, controller_inventory / route_module_inventory, and api_coverage_gate; writing only one, or writing contradictory values, is a criteria violation (validate_audit.py WARN fallback).
- Historical artifacts without the dual fields are not held accountable; new artifacts must have both fields.

## PoC Placeholder Rules

- Real routes and parameters must be substituted into the request template
- Allowed session placeholders: {host}, {cookie}, {token}, {apiKey}, {jwt}
- When conditions are insufficient to construct a fully reproducible request, a pending-verification or environment-dependent PoC template must still be output in vuln_poc/{type}_{timestamp}.md; omitting the directory because full reproduction is impossible is not allowed

## Node.js and Cross-Stack Artifact Paths (Full-Stack Extension)

| Canonical Name | Physical Path | Description |
| ---- | ---- | ---- |
| stack_detect_{timestamp}.md | node/stack_detect/stack_detect_{timestamp}.md | Phase 0 node tech-stack detection (artifact key points include the embedded foreign-stack project ownership decision table, effective 2026-09-18) |
| route_module_inventory_{timestamp}.md | node/route_mapping/route_module_inventory_{timestamp}.md | Route module reconciliation list (mirrors controller_inventory) |
| routes_{timestamp}.md | node/route_mapping/routes_{timestamp}.md | node entry list |
| frontend_outbound_{timestamp}.md | node/route_mapping/frontend_outbound_{timestamp}.md | Frontend outbound endpoint collection artifact (node-route-mapper; structure includes its own `## Uncertain Method List` section, effective 2026-09-21) |
| params_{timestamp}.md | node/route_mapping/params_{timestamp}.md | Parameter structure |
| middleware_inventory_{timestamp}.md | node/route_mapping/middleware_inventory_{timestamp}.md | Middleware inventory (authentication surface) |
| route_mapping_index_{timestamp}.md | node/route_mapping/index_{timestamp}.md | node route mapping phase index |
| feature_api_map_{timestamp}.md | node/route_mapping/feature_api_map_{timestamp}.md | Feature↔API three-layer mapping (node-feature-api-mapper; view-layer reference, forbidden as EVID evidence source; accompanied by unmapped_feature_calls_{timestamp}.md when PARTIAL) |
| auth_mapping_{timestamp}.md | node/auth_audit/auth_mapping_{timestamp}.md | Static authentication bucketing |
| trace_{timestamp}.md | node/route_tracer/{route_id}/trace_{timestamp}.md | Single-route trace |
| trace_summary_{timestamp}.md | node/route_tracer/{route_id}/trace_summary_{timestamp}.md | Single-route trace summary |
| high_risk_routes_{timestamp}.md | node/cross_analysis/high_risk_routes_{timestamp}.md | High-risk entry set |
| trace_batch_plan_{timestamp}.md | node/cross_analysis/trace_batch_plan_{timestamp}.md | Batched tracing plan |
| global_sink_fallback_dir | node/global_sink_fallback/ | Global sink fallback directory |
| npm_audit_{timestamp}.md | node/vuln_scanner/npm_audit_{timestamp}.md | Dependency vulnerability scan (header fields include `knowledge_cutoff_date` / `offline_report_source`, effective 2026-09-18) |
| vuln_audit_{type}_{timestamp}.md | node/vuln_audit/{type}_{timestamp}.md | Vulnerability specialty artifact |
| vuln_audit_export_{timestamp}.md | node/vuln_audit/export_{timestamp}.md | Spreadsheet formula injection specialty artifact |
| vuln_audit_prompt_{timestamp}.md | node/vuln_audit/prompt_{timestamp}.md | AI prompt injection specialty artifact |
| vuln_poc_{type}_{timestamp}.md | node/vuln_poc/{type}_{timestamp}.md | Vulnerability specialty PoC |
| framework_audit_{name}_{timestamp}.md | node/framework_audit/{name}_{timestamp}.md | P2 framework specialty |
| exploit_chains_{timestamp}.md | node/exploit_chain/exploit_chains_{timestamp}.md | Exploit chain aggregation (ACTIVE, node-exploit-chain-audit) |
| codegraph_index_{timestamp}.md | node/codegraph/codegraph_index_{timestamp}.md | node CodeGraph index body (ACTIVE; record NOT_RUN when unavailable) |
| codegraph_index_status_{timestamp}.md | node/codegraph/codegraph_index_status_{timestamp}.md | node CodeGraph index status and metadata |
| scan_{filename|module}_{timestamp}.md | node/scan_audit/scan_{filename|module}_{timestamp}.md | Phase 0.5 risk scan (risks + safe_regions; discovery only, no determination) |
| coverage_{filename|module}_{timestamp}.md | node/coverage_audit/coverage_{filename|module}_{timestamp}.md | Phase 0.6 coverage backfill (gap calculation and backfill records) |
| briefing_{sink_id}_{timestamp}.md | node/briefing/briefing_{sink_id}_{timestamp}.md | Phase 3.5 candidate parameter list (sink parameter checklist) |
| cross_stack_exploit_chains_{timestamp}.md | cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md | Cross-stack exploit chains (stack_mode=BOTH; taint-linker XTRACE aggregation, written under {output_root}/cross/) |
| vuln_report_index_{timestamp}.md | node/vuln_report/index_{timestamp}.md | Vulnerability report index |
| api_coverage_gate_{timestamp}.md | node/quality/api_coverage_gate_{timestamp}.md | API coverage gate |
| unmapped_routes_{timestamp}.md | node/quality/unmapped_routes_{timestamp}.md | Unmapped entry list |
| manifest_{run_id}.md | node/quality/manifest_{run_id}.md | Resume-from-breakpoint manifest |
| preflight_{timestamp}.md | node/quality/preflight_{timestamp}.md | Phase 0 preflight environment check (model enumeration probe / `.codegraph` upward resolution / node runtime availability / credential availability declaration; degradation items go into manifest `gate_reason`, effective 2026-09-20) |
| cross_api_contract_map_{timestamp}.md | cross/api_contract_map_{timestamp}.md | Frontend-backend contract reconciliation (three buckets) |
| cross_contract_coverage_gate_{timestamp}.md | cross/contract_coverage_gate_{timestamp}.md | Contract coverage gate |
| cross_taint_links_{timestamp}.md | cross/cross_taint_links_{timestamp}.md | P2 cross-stack taint links |
| cross_consistency_findings_{timestamp}.md | cross/consistency_findings_{timestamp}.md | P2 two-side consistency |

Rules:

- The node subtree fully mirrors the dotnet-side "mandatory on-disk persistence / phase index / empty-result explanation" conventions; when a phase produces nothing, the corresponding directory and index/explanation file should still be created.
- **Unified fullstack `run_timestamp` (2026-09-20, mandatory)**: in fullstack orchestrated execution, all `{timestamp}` occurrences in this document and in each sub-stack's canonical names take the `run_timestamp` generated by the fullstack orchestration layer and issued to both sub-stacks (format `YYYY_MM_DD_HH_mm`); it must be used for naming all artifacts of both sub-stacks (including the `{output_root}/dotnet/` and `{output_root}/node/` subtrees and fullstack-level quality/ and cross/ artifacts); independent per-sub-stack timestamps are forbidden; the difference between a sub-stack's actual start time and `run_timestamp` is only recorded in the mapping table of its `quality/manifest_*.md` and artifacts must not be named with sub-stack self-produced timestamps.
- **preflight naming alignment (2026-09-20)**: the `run_timestamp` clause above also applies to `preflight_{timestamp}.md` — under fullstack orchestration its `{timestamp}` always takes `run_timestamp`; naming with sub-stack self-produced timestamps is forbidden.
- When `api_coverage_status=PARTIAL`, `node/quality/unmapped_routes_{timestamp}.md` must be persisted and the route mapping remapping loop continues, unless the user explicitly accepts PARTIAL and terminates.
- The cross-stack exploit chain `cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md` is a formal fullstack-level artifact (stack_mode=BOTH): produced by cross-stack-taint-linker's XTRACE chain aggregation, written under `{output_root}/cross/`; when there are no cross-stack chains, record NOT_APPLICABLE with `empty_result_{timestamp}.md`; when `consistency_check_status=BLOCKED`, its feasibility determination also follows the degradation semantics, and `audit_surface_status=COMPLETED` takes the generation of this artifact as a precondition.

### Pending-Evidence Risk Pool Single Source of Truth (2026-09-18)

- Each artifact ends with a `## Pending Evidence Pool for This File` section, with row format: `| pool_id | Source Artifact | Source Stack | Associated Chain/Finding | Missing Evidence | Evidence-Supplementing Action | Responsibility Handoff |`; pool_id rule `PEND-{STACK}-{seq}` (e.g., `PEND-DOTNET-003`), globally unique within the source of truth
- Single source of truth: `quality/pending_pool_{timestamp}.md` (fullstack: `{output_root}/quality/`; same for single-stack), auto-aggregated as a final double-check at closing; the file header must contain `pool_total: {N}`, aggregation time, and the source artifact list
- The final report risk pool section and the `audit_surface_status` degradation basis consume only pending_pool counts and paths
- Row format extended with an eighth field "Closure Method" (2026-09-19): `| pool_id | Source Artifact | Source Stack | Associated Chain/Finding | Missing Evidence | Evidence-Supplementing Action | Responsibility Handoff | Closure Method |`
- Closure method three-value enum: `static-evidence` (closable purely statically) / `dynamic-unit` (executable in Phase 7 DYNAMIC_VERIFY(STATIC_UNIT)) / `needs-env` (requires a runtime environment; integration-level items tracked as separate projects)
- Entry status enum: `OPEN` / `DYNAMIC_VERIFIED` / `CLOSED` (effective 2026-09-21; `CLOSED` = closed within static audit or this execution phase — the evidence chain is already closed within the static audit or this execution phase, no need to enter the pending-evidence waiting flow; the closure method is still recorded per the three-value enum); aggregation counts by status buckets (`open_count` / `dynamic_verified_count` / `closed_count`), the `pool_total` scope unchanged; the orchestration layer's self-extended `closed_in_phase6_count` field is retired, unified under the `closed_count` scope (when the field appears in historical artifacts, aggregation treats it as `closed_count` with a note)
- Historical artifacts without the closure-method field: infer heuristically from the evidence-supplementing action text during aggregation (containing "dynamic verification / unit test / reproduce" → dynamic-unit; containing "tenant / credential / environment / running instance" → needs-env; everything else → static-evidence), and note the number of inferred rows in the aggregation file
- Dynamic verification report registration (2026-09-19): `quality/dynamic_verify_report_{timestamp}.md` (Phase 7 DYNAMIC_VERIFY(STATIC_UNIT) artifact; fullstack: `{output_root}/quality/`; same for single-stack; node mirror `node/quality/dynamic_verify_report_{timestamp}.md`)
- Dynamic verification scratch project directory registration (2026-09-19): `quality/dynamic_verify_scratch/` (the only temporary test project directory in the repository where writes are allowed; per-case `case_{pool_id}/` + `run_{pool_id}.log`; node mirror `node/quality/dynamic_verify_scratch/`)
- **One ID per row (2026-09-20, mandatory)**: both the `## Pending Evidence Pool for This File` section and the `pending_pool_{timestamp}.md` aggregation file are **one ID per row**; alias merging is forbidden (the same pool_id written on one row under multiple aliases/variants). When one pending-evidence item relates to multiple targets (multiple chains / multiple findings / multi-file evidence): split the targets into separate rows (reusing the same pool_id or deriving child sequence numbers per the rule), or enumerate them separated by commas in the "Associated Chain/Finding" column; an alias-merged row (e.g., `PEND-DOTNET-003 aka P3`) is a criteria violation and must not be counted in aggregation or report statistics.
- **Three counting formulas (2026-09-20, sole criteria)**: ① `pool_total` = number of unique pool_ids (row count after deduplicating by pool_id, independent of status buckets; the sum of bucket counts must equal pool_total); ② the "Findings Statistics Table" count in each artifact = the actual number of enumerated detail blocks (if the table says N, the body must have N enumerated blocks, named one by one); ③ `closed` count = sum of non-false-positive non-pending items (closed = all entries − false positives − pending; pending includes both OPEN and DYNAMIC_VERIFIED statuses). When self-reported values disagree with the formula values, the difference reason must be explicitly written (which row / which entry causes the deviation); silently picking one is forbidden; the difference reason lands in the "Criteria Notes" section of the `pending_pool_{timestamp}.md` aggregation file header (2026-09-21).
- **Chain status criteria (2026-09-21, registered companion to formula ③)**: chain status four-value enum — `closed` = evidence chain closed and neither false positive nor pending; `open` = not closed; `false_positive` = evidence refuted; `pending` = suspended in the pending-evidence pool (the part of open already registered into pending_pool; under formula ③ criteria, pending count is the same set as open, closed = all − false positives − pending). Mapping with exploit-chain four states (sole criteria for chain status decomposition):

| exploit-chain Status | Chain Status Criteria |
| ---- | ---- |
| ✅ Confirmed | closed |
| ⚠️ Pending Verification / 🔍 Environment-Dependent | open |
| ❌ Not Exploitable | false_positive |

Status name alignment (2026-09-21): in formula ③ context, `pending` is synonymous and same-set with `open` in these criteria (the part of open already registered into pending_pool) — formula ③ "closed = all entries − false positives − pending" is exactly "closed = all entries − false positives − open"; when verifying formula ③ against exploit-chain artifacts, the open rows in the four-state decomposition are the pending rows.
- **Pool rows before references (2026-09-20, mandatory)**: before any artifact (including the final report, exploit_chain, statistics tables, risk pool sections) references a pool_id, that pool_id must already be registered in this file's `## Pending Evidence Pool for This File` section or the `pending_pool_{timestamp}.md` aggregation file (pool rows precede references); referencing an unregistered pool_id is a criteria violation — register the row first, then reference.
- **Schema extensions must be registered first (2026-09-20)**: any extension or change to the pending-pool row format (eight fields), closure-method three-value enum, entry status enum, or pool_id naming rule must be registered in this section of this document first (register before implementing), and must not land new fields in artifacts before the documentation is updated.

### Dimension List (Execution Source Snapshot, 2026-09-21)

Snapshot date: 2026-09-21. This list is the **execution source of truth** for the "Dimension Verification" section (vulnerability specialty status model section) and the mandatory specialty enumeration list: external execution environments (without a `docs/` directory) can enumerate all dimensions by reading this appendix. New dimensions must be registered in the ledger first (`docs/NewSkillRegistration.md` Section 2, register before implementing) and synced into this snapshot; when packaging for delivery, reconcile this snapshot against the ledger (manual consistency check record). Completeness criteria for the list = all audit-quality mechanism entries in the ledger (categories A and B combined; sync upon addition; drift between the list and the ledger is forbidden).

Dimensions fall into two categories with different three-state/two-state disciplines (**items whose category is unclear default to category B**, interpreted strictly: register more rather than miss any):

#### Category A: Vulnerability Mechanism Dimensions (three states; negative-evidence discipline includes scope + rg pattern)

Three states per item: `Covered` (with artifact section location) / `Negative Evidence` (NOT_APPLICABLE, with scope + rg pattern) / `Not Applicable` (with determination reason); bare "not covered" / "not mentioned" wording is forbidden.

| # | Dimension | Owning Specialty (Mechanism Extension Landing Point) |
| ---- | ---- | ---- |
| A1 | Account enumeration · error-response consistency | dotnet-auth-audit (node-auth-audit symmetric) |
| A2 | Audit integrity tampering | dotnet-logging-audit (node symmetric) |
| A3 | Audit availability flooding | dotnet-logging-audit (node symmetric) |
| A4 | Signed-request replay protection (nonce/timestamp/replay cache freshness) | dotnet-crypto-audit + dotnet-webapi-audit (node symmetric) |
| A5 | Integer overflow (numeric boundaries) | dotnet-logic-audit (node symmetric) |
| A6 | Configuration exposure three dimensions: configuration exposure / response information disclosure / secret exposure boundary | dotnet-config-audit (node symmetric) |
| A7 | Supply chain knowledge cutoff + offline source (`knowledge_cutoff_date` / `offline_report_source`) | dotnet-vuln-scanner / node-vuln-scanner |
| A8 | Dynamic verification four-zero red lines (zero credentials / zero network / zero services / zero writes outside scratch directory) | pipeline Phase 7 DYNAMIC_VERIFY(STATIC_UNIT) |

#### Category B: Audit Quality Mechanism Dimensions (two states: implemented / not applicable with reason; registration-style evidence)

These dimensions describe the audit process's own failure chains and do not use the "rg negative evidence" three-state discipline; per item, register one of two states — `Implemented` (with registration-style evidence location) / `Not Applicable` (with reason).

| # | Dimension | Landing Point |
| ---- | ---- | ---- |
| B1 | Preflight environment check (model enumeration / `.codegraph` upward resolution / SDK & runtime / credential availability declaration) | Both pipelines Phase 0 |
| B2 | run_timestamp unified issuance (fullstack orchestration layer issues; sub-stacks forbidden from self-producing) | IO unified fullstack run_timestamp clause |
| B3 | Dimension verification itself (mandatory `## Dimension Verification` section in index) | IO vulnerability specialty status model section |
| B4 | Pending-pool eight fields (including closure method and one-ID-per-row discipline) | IO pending-evidence risk pool single source of truth section |
| B5 | Specialty dispatch verification (three states in index `## Specialty Dispatch Verification` section) | IO vulnerability specialty status model section |
| B6 | Milestone write-back (manifest milestone line format single source of truth) | PHASE_STATUS |
| B7 | Method-level pairing (node route-mapper forbids conservative dual-method upper bound flowing downstream) | node-route-mapper |
| B8 | Embedded foreign-stack three-state ownership decision table | Both pipelines Phase 0 stack_detect |
| B9 | Phase 0.7 recursive search_scope (six patterns + directory enumeration discipline) | Both pipelines Phase 0.7 |
| B10 | Phase 6 execution order constraint (P1-5: contract-mapper first, consistency-audit / taint-linker started in dependency order) | fullstack-audit-pipeline Phase 6 |
| B11 | Wait-timeout formula (FULL mode `estimated minutes = 2 + (total files / 1000) × 8`; rounding and total-file-count scope see PHASE_STATUS clause) | PHASE_STATUS wait-timeout formula clause |

### Preflight Artifact Template (2026-09-21)

`quality/preflight_{timestamp}.md` (node mirror `node/quality/preflight_{timestamp}.md`) has the following fixed structure; custom formats are forbidden:

```md
# Preflight Environment Check
run_id: {project_name}_{run_timestamp}
run_timestamp: {YYYY_MM_DD_HH_mm}

## Four-Item Determination Table
| Item | Result (PASS/FAIL/DEGRADED) | Probe Method and Scope | Conclusion and Impact |
| ---- | ---- | ---- | ---- |
| Model enumeration | PASS | Probe the available model list of the execution environment | Designated model available; execute per plan |
| .codegraph upward resolution | DEGRADED | Resolve `.codegraph/` upward from source_path layer by layer (including x/y/.codegraph nesting levels) | No existing index located; build index in Phase 0; fall back to static analysis |
| SDK & runtime | DEGRADED | dotnet SDK / node runtime and package manager availability (including version and target-framework compatibility notes) | SDK unavailable; static audit continues with registration; build-dependent checks degraded |
| Credential availability | PASS | Declare the available credential scope for this execution (write "none" explicitly when there are no credentials) | None (Phase 7 dynamic verification and integration-level evidence supplementation not applicable; four-zero red lines as precondition) |

## Degradation Item List
- {degraded item} | reason | registration location: manifest gate_reason | affected phase: {N}
- None
```

Key writing points for the four items:

- **Model enumeration**: list the detected available models; when the designated model is unavailable, degrade per the available list and register in both this table and manifest `gate_reason`; silently switching models is forbidden
- **`.codegraph` upward resolution**: state the resolution starting point, the number of levels traversed upward, and the determination result of each level; when not located, the conclusion must include the wording "fall back to static analysis", not just "not found"
- **SDK & runtime**: the dotnet side includes SDK version and target-framework compatibility; the node side includes node/npm/pnpm/yarn and package managers; unavailability means DEGRADED with registration; the static audit path is unaffected
- **Credential availability**: enumerate available credential types and scope item by item; write "none" explicitly when there are no credentials, and note the relationship to Phase 7 dynamic verification (STATIC_UNIT four-zero red lines unaffected) and needs-env evidence-supplementation items
- **Cascade rules (2026-09-21)**: SDK / runtime unavailable → static audit continues, degradation registered into manifest `gate_reason` (subsequent static phases not blocked); no credentials → static audit unaffected, only Phase 7 dynamic verification and needs-env integration-level supplementation items degraded — the four-zero red lines are a precondition self-check and are not relaxed or waived because of missing credentials

In fullstack orchestration mode, `{run_timestamp}` always takes the orchestration-layer-issued value; sub-stack self-production is forbidden (see the "Unified fullstack run_timestamp" clause); any degradation item must also be registered into `quality/manifest_{run_id}.md`'s `gate_reason`.
