# .NET Route / Trace Output Templates

This file unifies the artifact formats of dotnet-route-mapper and dotnet-route-tracer, reducing format drift between skills and analysis batches.

## Usage Rules

- The output structure of route-mapper and route-tracer follows this file
- Specific fields may be supplemented per specialty, but the core sections and key fields defined here must not be removed
- If a project needs extra fields, append them in a compatible manner; do not change the semantics of existing primary keys
- The route_id in routes_{timestamp}.md, the route entries in params_{timestamp}.md, and the route_id in trace_{timestamp}.md must be consistent

## 1. route-mapper Output Templates

### 0. controller_inventory_{timestamp}.md (Gate Prerequisite)

Minimum sections:

- Title
- Generated at
- Analysis path
- Controller reconciliation table
- Unmapped controllers and reasons

Minimum fields per controller:

- controller_name
- controller_file
- route_prefix
- action_count
- mapped_actions
- in_route_mapping (Yes/No)
- in_auth_mapping (Yes/No)
- unmapped_reason

Reference skeleton:

```md
# {project_name} - Controller Inventory
Generated at: {timestamp}
Analysis path: {source_path}

## Controller Reconciliation Table
| controller_name | controller_file | route_prefix | action_count | mapped_actions | in_route_mapping | in_auth_mapping | unmapped_reason |
|---|---|---|---:|---:|---|---|---|

## Unmapped Controllers and Reasons
- ...
```

### 1. routes_{timestamp}.md

Minimum sections:

- Title
- Generated at
- Analysis path
- Route list (all)
- Count reconciliation (mandatory)

Minimum fields per route:

- route_id
- Entry type
- HTTP method or operation name
- Route path rule
- Route declaration style
- Controller / Action or equivalent handler identifier
- Handler
- Location
- Version
- Area
- Parameter overview
- Return template type

Reference skeleton:

```md
# {project_name} - Route & Entry Index (.NET)
Generated at: {timestamp}
Analysis path: {source_path}

## Route List (All)
=== [1] GET /api/v{version}/users/{id} ===
Entry type: HTTP
HTTP method: GET
Route path rule: /api/v{version}/users/{id}
Route declaration style: Attribute Routing
Controller: UsersController
Action: GetById
Handler: UsersController.GetById
Location: Controllers/UsersController.cs:line
Version: v{version}
Area: None
Parameter overview:
  Path: id, version
  Query: includeRoles
  Header: X-Tenant-Id
Return template type: JsonResult
```

### 1.1 Count Reconciliation Section (Mandatory)

After "Analysis path", the routes file header must append three lines:

declared_route_count: {declared total}
expanded_route_count: {expanded detail total rows}
count_self_check: PASS | FAIL

And append a "Count Reconciliation" section at the end of the file, listing the formula per controller (format: controller name: expanded count, ending with a Σ sum), explicitly writing out the verification process `declared total = Σ per-controller expanded counts (+ non-controller routes)`.
When count_self_check=FAIL, delivery to route-tracer / downstream phases is forbidden; fix the counts first before continuing.

### 2. params_{timestamp}.md

Minimum sections:

- Title
- Generated at
- Parameter details segmented by route_id or route title

Minimum fields per entry:

- Path parameter table
- Query parameter table
- Body / Form / Header / Cookie / File / Service / Custom Binder parameter tables
- Full request template

Reference skeleton:

````md
# {project_name} - Entry Parameter Structure (Per Entry)
Generated at: {timestamp}

=== Route: GET /api/v{version}/users/{id} ===
1) Path Parameters
| Parameter | Type/Constraint | Source | Required | Description |
|------|-----------|------|------|------|
| id | int | [FromRoute] / route template | Yes | User ID |

2) Query Parameters
| Parameter | Type | Source | Required | Description |
|------|------|------|------|------|
| includeRoles | bool | [FromQuery] | No | Whether to include roles |

5) Full Request Template
```http
GET /api/v1/users/123?includeRoles=true HTTP/1.1
Host: {host}
Authorization: Bearer {token}
X-Tenant-Id: {tenant}
Cookie: {cookie}
```
````

### 3. quality/route_mapper_validation_{timestamp}.md

Minimum sections:

- Coverage statistics
- Undetermined method or path combinations
- Conventional / attribute route conflict hints
- Parameter binding uncertainty items
- Entry list requiring further route-tracer confirmation

### 4. quality/api_coverage_gate_{timestamp}.md (Mandatory)

Minimum sections:

- Coverage statistics
- Unmapped controller list
- Unmapped action list
- Coverage conclusion and gate result

Minimum fields:

- active_controller_total
- mapped_controller_count
- mapped_action_count
- unique_path_count
- method_path_count
- unmapped_controllers
- unmapped_actions
- api_coverage_percent
- api_coverage_status (COMPLETE/PARTIAL)

Reference skeleton:

```md
# API Coverage Gate
Generated at: {timestamp}
coverage_mode: {FULL|SAMPLE}

## Coverage Statistics
- active_controller_total: {n}
- mapped_controller_count: {n}
- mapped_action_count: {n}
- unique_path_count: {unique path count}
- method_path_count: {(method,path) expansion total}
- api_coverage_percent: {n}%
- api_coverage_status: {COMPLETE|PARTIAL}

Note: both fields must match the routes file header; the sole consumption criterion for contract reconciliation is method_path_count.

## Unmapped Controller List
- ...

## Unmapped Action List
- ...

## Gate Result
- pipeline_execution_allowed_completed: {yes|no}
- reason: ...
```

### 4.5 quality/unmapped_routes_{timestamp}.md (Mandatory when `api_coverage_status=PARTIAL`)

Purpose: separately precipitate the "unmapped entry risk surface" so it is not drowned out by gate statistics fields.

Minimum fields:

- api_coverage_status
- unmapped_controller_count
- unmapped_action_count
- unmapped_controllers
- unmapped_actions
- next_backfill_batch

Reference skeleton:

```md
# Unmapped Routes Backlog
Generated at: {timestamp}
coverage_mode: {FULL|SAMPLE}
api_coverage_status: {COMPLETE|PARTIAL}

## Statistics
- unmapped_controller_count: {n}
- unmapped_action_count: {n}

## Unmapped Controllers
- {ControllerName} | {file} | {reason}

## Unmapped Actions
- {Controller}.{Action} | {method/path} | {reason}

## Next Backfill Batch Suggestions
- batch_001: {controller/action list}
- batch_002: {controller/action list}
```

### 4.6 quality/route_mapping_backfill_loop_{timestamp}.md (Recommended)

Purpose: record remapping loop rounds, avoiding "mapping ends early after discovering high-risk items".

Minimum fields:

- round
- mapped_controllers_delta
- mapped_actions_delta
- unmapped_remaining
- decision

Reference skeleton:

```md
# Route Mapping Backfill Loop
Generated at: {timestamp}

## Round 1
- mapped_controllers_delta: +8
- mapped_actions_delta: +42
- unmapped_remaining: 17
- decision: continue

## Round 2
- mapped_controllers_delta: +5
- mapped_actions_delta: +23
- unmapped_remaining: 12
- decision: continue

## Round N
- mapped_controllers_delta: +0
- mapped_actions_delta: +0
- unmapped_remaining: 0
- decision: stop (converged)
```

### 4.7 unmapped_routes Failure Counterexample (BLOCKED)

Purpose: train executors to recognize that when "entry coverage is incomplete and remapping is unfinished", subsequent phases must not be mistakenly written as deliverable.

```md
# Unmapped Routes Backlog (Blocked)
Generated at: 2026_06_25_20_40
coverage_mode: FULL
api_coverage_status: PARTIAL

## Statistics
- unmapped_controller_count: 2
- unmapped_action_count: 7

## Unmapped Controllers
- AdminController | Controllers/AdminController.cs | not covered by route mapping
- ExportController | Controllers/ExportController.cs | auth mapping not closed

## Unmapped Actions
- AdminController.DeleteUser | DELETE /api/admin/users/{id} | high-privilege entry not remapped
- ExportController.ExportZip | POST /api/export/zip | FILE/WRITE-risk entry not remapped

## Next Backfill Batch Suggestions
- batch_001: AdminController.*
- batch_002: ExportController.ExportZip, ExportController.ExportCsv

## Blocking Notes
- final_decision: BLOCKED
- reason: active API entry coverage is still PARTIAL, and key high-risk controllers have not completed remapping.
```

## 2. route-tracer Output Templates

### 1. route_tracer/{route_id}/trace_{timestamp}.md

Minimum sections:

- Request template
- Entry & metadata
- Parameter entry points
- Binding chain
- Filters & middleware
- Business & DI chain
- Branch path tracing
- Parameter Controllability Matrix
- Sink Location
- Sink Summary
- Trace Completeness Statement
- Sink Evidence Type Checklist

Parameter Controllability Matrix minimum fields:

- Parameter name
- Binding source
- Converter / binder
- First validation point
- Final use point
- Controllability level
- Affected Sink

Sink Summary minimum fields:

- Sink type
- Specific API
- Code location
- Upstream parameters
- Whether encoding / whitelist / authorization / configuration protection applies
- Evidence strength

Reference skeleton:

````md
# Route Trace - {route_id}
Generated at: {timestamp}
Entry: GET /api/v1/users/123

## Request Template
```http
GET /api/v1/users/123?includeRoles=true HTTP/1.1
Host: {host}
Authorization: Bearer {token}
```

## Entry & Metadata
- Controller: UsersController
- Action: GetById
- Authorize: Policy=UserRead

## Parameter Entry Points
- id <- Route
- includeRoles <- Query

## Binding Chain
- [FromRoute] id -> int id

## Filters & Middleware
- AuthorizationFilter: UserReadPolicy
- Middleware: UseAuthentication -> UseAuthorization

## Business & DI Chain
- UsersController.GetById
- IUserService.GetById
- UserRepository.Load

## Parameter Controllability Matrix
| Parameter | Binding Source | Converter/Binder | First Validation Point | Final Use Point | Controllability Level | Affected Sink |
|------|------|------|------|------|------|------|
| id | Route | default binding | GetById guard | SqlCommand parameter | High | SQL |

## Sink Summary
| Sink Type | API | Code Location | Upstream Parameters | Protection | Evidence Strength |
|------|------|------|------|------|------|
| SQL | SqlCommand.ExecuteReader | Repository/UserRepository.cs:line | id | parameterized | COMPLETE |

## Trace Completeness Statement
- trace_status: COMPLETE
- Note: all six layers (Controller / Binder / Filter / Middleware / DI / Sink) are closed

## Sink Evidence Type Checklist
- The ## 9) section of dotnet-route-tracer/SKILL.md is the single source of truth (this file does not duplicate the EVID_* row table, to avoid drift between two places)
- This section heading and table header must exist; actual evidence rows for hit Sinks are copied from the corresponding rows of the tracer checklist

## Added: taint_nodes (key data role step-by-step records)

For each traced chain, records must be kept node by node, turning "thinking the model can gloss over" into "structure that must be accounted for".

### taint_nodes Field Definitions

| Node Type | Description | Required Fields |
|---------|------|---------|
| `source_write_entry` | Write entry: where dangerous data comes from and whether it is attacker-controllable | filepath, line_range, description, is_attacker_controllable |
| `source_trigger_entry` | Trigger entry: when it is read and who triggers it | filepath, line_range, description, trigger_condition |
| `storage_read` | Persistent storage read (database / cache / file / session) | filepath, line_range, description |
| `transfer` | Propagation node (assignment / passing / concatenation / conversion) | filepath, line_range, description |
| `barrier` | Security control point | line_range, barrier_type, actual_behavior, status (PASSED/FAILED/NOT_ANALYZED) |
| `sink` | Final execution point | filepath, line_range, description |

### taint_nodes Example

```json
{
  "taint_nodes": [
    {
      "taint_type": "source_write_entry",
      "filepath": "Controllers/ConfigController.cs",
      "line_range": "45-48",
      "description": "The user writes column_key via the SaveFieldConfig endpoint; business configuration admin permission required",
      "is_attacker_controllable": true
    },
    {
      "taint_type": "storage_read",
      "filepath": "Services/SearchService.cs",
      "line_range": "30-33",
      "description": "Reads column_key from the field_config table"
    },
    {
      "taint_type": "transfer",
      "filepath": "Services/SearchService.cs",
      "line_range": "40-44",
      "description": "column_key is concatenated into the SQL query condition"
    },
    {
      "taint_type": "barrier",
      "line_range": "40-44",
      "barrier_type": "column_whitelist",
      "actual_behavior": "No whitelist validation; column_key enters the column identifier position directly",
      "status": "FAILED"
    },
    {
      "taint_type": "sink",
      "filepath": "Services/SearchService.cs",
      "line_range": "45-48",
      "description": "SQL execution: column_key enters the column identifier position"
    }
  ]
}
```

### taint_nodes Acceptance Criteria

- [ ] Every traced chain has taint_nodes records
- [ ] source_write_entry and source_trigger_entry are distinguished (second-order scenarios)
- [ ] Every barrier has actual_behavior and status
- [ ] status can only be PASSED / FAILED / NOT_ANALYZED; omission is not allowed
- [ ] Nodes form a complete chain: source → [storage_read] → transfer → [barrier] → sink

### Relationship with Existing Fields

- `taint_nodes` is a structured supplement to the "Parameter Controllability Matrix" and "Sink Summary"
- The "Parameter Controllability Matrix" answers "where does the parameter come from and how controllable is it"
- `taint_nodes` answers "what role does the data play in the chain and what is the evidence for each role"
- Both must exist in the trace and complement each other
````

### 2. route_tracer/{route_id}/trace_summary_{timestamp}.md

A lightweight index for batch analysis. Minimum fields:

- route_id
- Entry identifier
- trace_status
- Key Sink types
- Key unclosed points
- Suggested vulnerability specialty handoff

## 3. Field Consistency Requirements

- route_id must keep the same identifier across routes, params, trace, trace_summary, and the final report
- Return template type, entry type, and handler identifiers must be semantically consistent between route-mapper and route-tracer
- trace_status allows only the three values COMPLETE, PARTIAL, UNRESOLVED
- Sink type naming should stay consistent with shared/DOTNET_SINK_REFERENCE.md and the classification used by the specific vuln_audit

## 4. high_risk_routes Output Constraints (Coverage Mode)

- When `coverage_mode=FULL` and `api_coverage_status=COMPLETE`, output `cross_analysis/high_risk_routes_{timestamp}.md`
- When `coverage_mode=SAMPLE` or `api_coverage_status=PARTIAL`, output `cross_analysis/sampled_high_risk_routes_{timestamp}.md`
- The sampled file header must contain:
  - `coverage_mode`
  - `api_coverage_status`
  - `controller_coverage_percent`
  - `auth_coverage_percent`
  - `disclaimer` (explicitly stating "reflects only high-risk candidates among currently mapped entries; does not represent the full set of high-risk entries across all active APIs")

### trace_batch_plan_{timestamp}.md Constraints (Coverage Mode Binding)

- `coverage_mode=FULL`:
  - `trace_batch_max_size` allowed range: 10–30
  - Default value: 10
  - Suggested batch-count reminder threshold: if `planned_batch_count > 20`, consider merging batches (soft constraint; forced re-planning not required)
- `coverage_mode=SAMPLE`:
  - `trace_batch_max_size` allowed range: 5–10
  - Default value: 8
  - Exceeding 10 is forbidden
  - `batch_count_upper_bound` fixed at 6 (total planned batches must not exceed 6)
- Each batch must carry fields:
  - `batch_id`
  - `coverage_mode`
  - `trace_batch_max_size`
  - `reason`
  - `route_ids`
- **Single-writer principle (2026-09-20, mandatory)**: trace_batch_plan / trace index files may only be written by the orchestration layer or a designated single batch writer; concurrent direct writes to the same file by multiple batches are forbidden; concurrent scenarios must use sharded naming `trace_batch_plan_{batch}.md`, with final merging handled by the orchestration layer — after merging, the formal artifact name is uniformly `trace_batch_plan_{timestamp}.md`

Reference skeleton:

```md
# Trace Batch Plan
Generated at: {timestamp}
coverage_mode: {FULL|SAMPLE}
batch_count_upper_bound: {6|N/A}
planned_batch_count: {n}

## Batch List
### batch_001
- coverage_mode: SAMPLE
- trace_batch_max_size: 8
- reason: sample mode prioritizes controlling batch size to reduce context loss and misjudgment risk
- route_ids:
  - HTTP:GET:/api/users/{id}
  - HTTP:POST:/api/orders/export
```

## 5. Minimal Sample Artifact Pack (New, for Regression Alignment)

Purpose: quickly verify "coverage gate semantics are implemented per the unified criteria".

Suggested directory: `quality/minimal_sample_pack_{timestamp}/`

It should contain at least the following 3 example files:

1. `route_mapping/controller_inventory_{timestamp}.md`
2. `quality/api_coverage_gate_{timestamp}.md`
3. `cross_analysis/sampled_high_risk_routes_{timestamp}.md`

### Example A: controller_inventory_{timestamp}.md

```md
# DemoProject - Controller Inventory
Generated at: 2026_06_24_10_30
Analysis path: /repo/demo

## Controller Reconciliation Table
| controller_name | controller_file | route_prefix | action_count | mapped_actions | in_route_mapping | in_auth_mapping | unmapped_reason |
|---|---|---|---:|---:|---|---|---|
| UsersController | Controllers/UsersController.cs | /api/users | 6 | 6 | Yes | Yes | |
| OrdersController | Controllers/OrdersController.cs | /api/orders | 5 | 4 | Yes | No | auth mapping pending |

## Unmapped Controllers and Reasons
- None
```

### Example B: quality/api_coverage_gate_{timestamp}.md

```md
# API Coverage Gate
Generated at: 2026_06_24_10_30
coverage_mode: SAMPLE

## Coverage Statistics
- active_controller_total: 2
- mapped_controller_count: 2
- mapped_action_count: 10
- api_coverage_percent: 90%
- api_coverage_status: PARTIAL

## Unmapped Controller List
- None

## Unmapped Action List
- OrdersController.ExportCsv

## Gate Result
- pipeline_execution_allowed_completed: no
- reason: api_coverage_status=PARTIAL
```

### Example C: cross_analysis/sampled_high_risk_routes_{timestamp}.md

```md
# Sampled High Risk Routes
Generated at: 2026_06_24_10_30
coverage_mode: SAMPLE
api_coverage_status: PARTIAL
controller_coverage_percent: 100%
auth_coverage_percent: 80%
disclaimer: reflects only high-risk candidates among currently mapped entries; does not represent the full set of high-risk entries across all active APIs.

## Route Candidates
| route_id | method | path | source_bucket | reason |
|---|---|---|---|---|
| HTTP:GET:/api/users/{id} | GET | /api/users/{id} | P1 | insufficient authorization granularity (potential IDOR) |
| HTTP:POST:/api/orders/export | POST | /api/orders/export | SINK_SUSPECT | FILE/WRITE-related parameters controllable |
```

Acceptance points:

- The `timestamp` of the three files should be identical
- The sampled file must carry a `disclaimer`
- The `api_coverage_status` of the gate and the sampled file must be consistent

## 6. quick_validation_{timestamp}.md (Final Validation Template)

Purpose: quickly verify consistency among "gate status, artifact completeness, and report declarations" before delivery.

Suggested path: `quality/quick_validation_{timestamp}.md`

Minimum fields:

- timestamp
- coverage_mode
- api_coverage_status
- pipeline_execution
- checklist_results
- final_decision

Reference skeleton:

```md
# Quick Validation
Generated at: 2026_06_24_11_15

## Run Context
- coverage_mode: SAMPLE
- api_coverage_status: PARTIAL
- pipeline_execution: PARTIAL

## Checklist
- [x] route_mapping/controller_inventory_{timestamp}.md exists
- [x] quality/api_coverage_gate_{timestamp}.md exists
- [x] cross_analysis/sampled_high_risk_routes_{timestamp}.md exists (SAMPLE/PARTIAL)
- [x] cross_analysis/trace_batch_plan_{timestamp}.md satisfies `planned_batch_count <= 6` under SAMPLE
- [x] quality/pipeline_execution_{timestamp}.md is consistent with the gate status
- [x] The final report contains the dual completion status declarations
- [x] The final report contains the coverage scope statement
- [x] The final report contains the exploit-chain coverage scope summary, consistent with `exploit_chain/exploit_chains_{timestamp}.md`
- [x] (Recommended) quality/coverage_consistency_check_{timestamp}.md persisted, with no conflicting blocking items

## Field Conflict Location (if coverage_consistency_check exists)
- consistency_check_status: PASS
- conflicts_count: 0
- Conflict summary: none (if there are conflicts, write "conflicting field | source file | fix suggestion")

## Conclusion
- final_decision: PASS
- notes: no blocking items; deliverable
```

Determination rules:

- Whenever a status conflict appears (e.g., `api_coverage_status=PARTIAL` but `pipeline_execution=COMPLETED`), `final_decision` must be `BLOCKED`
- In SAMPLE mode, if the coverage scope statement is missing, `final_decision` must be `BLOCKED`
- If `consistency_check_status=BLOCKED`, `final_decision` must be `BLOCKED`

## 7. quick_validation_example_{timestamp}.md (Minimal Example)

Purpose: provide first-time recipients a "directly copyable" quick validation persistence sample.

Suggested path: `quality/quick_validation_example_{timestamp}.md`

Reference skeleton:

```md
# Quick Validation Example
Generated at: 2026_06_24_12_10

## Run Context
- coverage_mode: SAMPLE
- api_coverage_status: PARTIAL
- api_coverage_percent: 88%
- pipeline_execution: PARTIAL

## Checklist
- [x] route_mapping/controller_inventory_2026_06_24_12_10.md exists
- [x] quality/api_coverage_gate_2026_06_24_12_10.md exists
- [x] cross_analysis/sampled_high_risk_routes_2026_06_24_12_10.md exists
- [x] cross_analysis/trace_batch_plan_2026_06_24_12_10.md satisfies SAMPLE thresholds (5–10)
- [x] cross_analysis/trace_batch_plan_2026_06_24_12_10.md satisfies SAMPLE batch count upper bound (planned_batch_count <= 6)
- [x] exploit_chain/exploit_chains_2026_06_24_12_10.md has passed through the coverage scope
- [x] The final report has declared "covers only the mapped-entry sample scope"
- [x] The final report has written the exploit-chain coverage scope summary with fields consistent with the exploit_chain file
- [x] quality/coverage_consistency_check_2026_06_24_12_10.md has verified key field consistency, with no blocking conflicts

## Conclusion
- final_decision: PASS
- notes: SAMPLE-mode validation passed; may serve as a phase deliverable.
```

Usage requirements:

- `quick_validation_example` is for examples and training; it does not replace the formal `quick_validation` artifact
- Timestamps and file names in the example may be replaced per actual execution, but the field structure must not be reduced

### quick_validation Failure Counterexample (Count Reconciliation Failure, BLOCKED)

Purpose: train executors to recognize the blocking scenario where "statuses look consistent but counts are not".

```md
# Quick Validation Example (Blocked)
Generated at: 2026_06_25_16_40

## Run Context
- coverage_mode: SAMPLE
- api_coverage_status: PARTIAL
- pipeline_execution: PARTIAL

## Checklist
- [x] quality/coverage_consistency_check_2026_06_25_16_40.md persisted
- [ ] Final report `exploit_chain_consistency_check_counts` consistent with the exploit_chain overview table (failed)

## Field Conflict Location (if coverage_consistency_check exists)
- consistency_check_status: BLOCKED
- conflicts_count: 1
- Conflict summary: exploit_chain_consistency_check_counts.BLOCKED | final_report vs exploit_chain/exploit_chains_2026_06_25_16_40.md | re-count and write back to the final report

## Conclusion
- final_decision: BLOCKED
- notes: count reconciliation failed; delivery forbidden.
```

## 8. coverage_consistency_check_{timestamp}.md (Cross-Artifact Consistency Check)

**Dual-stack isomorphism (mandatory)**: dotnet (`quality/coverage_consistency_check_{timestamp}.md`) and node (`node/quality/coverage_consistency_check_{timestamp}.md`) must produce same-named independent files, with structure per this section. If merging into another quality file is truly necessary, the merged file must contain the marker lines `MERGED_FROM: coverage_consistency_check_{timestamp}.md` and `MERGE_REASON: {merge reason}`, and the merged-away file path must still be registered in the manifest; having neither an independent file nor a marker line is treated as a missing artifact.

Purpose: uniformly check key fields across gate/trace/exploit-chain/final report, locate conflict sources, and give fix suggestions.

Suggested path: `quality/coverage_consistency_check_{timestamp}.md`

Minimum fields:

- timestamp
- compared_files
- consistency_matrix
- conflicts
- final_status

Reference skeleton:

```md
# Coverage Consistency Check
Generated at: 2026_06_24_14_20

## Compared Files
- quality/api_coverage_gate_2026_06_24_14_20.md
- cross_analysis/trace_batch_plan_2026_06_24_14_20.md
- exploit_chain/exploit_chains_2026_06_24_14_20.md
- DemoProject_code_audit_2026_06_24_14_20.md

## Consistency Matrix
| Field | gate | trace_batch_plan | exploit_chain | final_report | Consistency |
|---|---|---|---|---|---|
| coverage_mode | SAMPLE | SAMPLE | SAMPLE | SAMPLE | PASS |
| api_coverage_status | PARTIAL | N/A | PARTIAL | PARTIAL | PASS |
| api_coverage_percent | 88% | N/A | 88% | 88% | PASS |
| planned_batch_count | N/A | 5 | N/A | 5 | PASS |
| exploit_chain_sampled_scope | N/A | N/A | true | true | PASS |

## Conflicts (If Any)
- None

## Conclusion
- final_status: PASS
- notes: key fields consistent; deliverable.
```

Determination rules:

- When any key field conflicts and affects conclusion semantics, `final_status` must be `BLOCKED`
- When `final_status=BLOCKED`, a "conflicting field + source file + fix suggestion" triple must be given

Closing checklist (recommended to check item by item):

- [ ] Skill list count reconciliation: the skill counts declared in README/CLAUDE.md match the actual counts under `skills/` on disk (check the dotnet and node families separately)
- The static mapping for field reconciliation takes the "Final Field Reconciliation Static Mapping Template" of IO_PATH_CONVENTION.md as its source of truth

## 9. Final Report Fixed Template (Extracted)

To reduce field drift caused by multi-place maintenance, the fixed final report fragments have been extracted to:

- `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md`

Usage constraints:

- The final report quality section must take that file as the single source of truth
- If template fields change, update that file first, then sync the consumers (pipeline/README/CLAUDE)

Quick acceptance:

- The PASS/BLOCKED/N/A of `exploit_chain_consistency_check_counts` must be consistent with the `exploit_chain` overview table statistics
- If `consistency_check_status=BLOCKED`, `quick_validation.final_decision` must be linked to `BLOCKED`

## 10. exploit-chain BLOCKED Failure Counterexample (Count Reconciliation Failure)

Purpose: train executors to recognize the scenario where "the exploit chain file itself also needs degraded wording, not just fixing the final report".

```md
# Exploit Chains Example (Blocked)
Generated at: 2026_06_25_19_20
coverage_mode: SAMPLE
api_coverage_status: PARTIAL
api_coverage_percent: 88%

## Chain Overview Table
| Chain ID | Entry Point | Final Target | Steps | Minimum Privilege | Overall Complexity | Feasibility | Bottleneck Node | coverage_mode | api_coverage_status | sampled_scope | consistency_check_status |
|---|---|---|---:|---|---|---|---|---|---|---|---|
| CHAIN-001 | GET /api/users/{id} | Admin token leakage | 2 | no authentication | medium | Inferred Feasible | AUTH-002 | SAMPLE | PARTIAL | true | BLOCKED |

## consistency_check Count Statistics
- consistency_check_counts: {PASS:0, BLOCKED:1, N/A:0}

## Chain Details
- consistency_check_source: quality/coverage_consistency_check_2026_06_25_19_20.md
- consistency_check_status: BLOCKED
- Degradation statement: this chain has been downgraded because consistency count reconciliation failed; no "Confirmed Feasible" determination is provided for now.
- Fix suggestion: fix the count difference between final_report and the exploit_chain overview table first, then re-run in the order `final_report -> consistency_check -> quick_validation -> exploit_chain`.
```

## 11. final_anchor_checklist_{timestamp}.md (Minimal Example)

Purpose: provide the closing phase a copyable sample of "per-file checking + summary determination + blocking source location".

Suggested path: `quality/final_anchor_checklist_{timestamp}.md`

### final_anchor PASS Minimal Example

```md
# Final Anchor Checklist
Generated at: 2026_06_25_21_10

- [x] 1. `quality/api_coverage_gate_2026_06_25_21_10.md` exists and `api_coverage_status` confirmed
- [x] 2. `quality/coverage_consistency_check_2026_06_25_21_10.md` exists and `final_status` confirmed
- [x] 3. `quality/quick_validation_2026_06_25_21_10.md` exists and `final_decision` confirmed
- [x] 4. `exploit_chain/exploit_chains_2026_06_25_21_10.md` exists and chain feasibility wording reviewed
- [x] 5. `DemoProject_code_audit_2026_06_25_21_10.md` has written back the final conclusion and consistency counts

## Summary
- checklist_pass_count: 5
- checklist_blocked_count: 0
- checklist_pending_count: 0
- final_anchor_decision: PASS
- pool_check: PASS
- stat_check: PASS
- chain_check: PASS

## BLOCKED Source File Summary (If Any)
- None
```

### final_anchor BLOCKED Minimal Example

```md
# Final Anchor Checklist
Generated at: 2026_06_25_21_30

- [x] 1. `quality/api_coverage_gate_2026_06_25_21_30.md` exists and `api_coverage_status` confirmed
- [x] 2. `quality/coverage_consistency_check_2026_06_25_21_30.md` exists and `final_status` confirmed
- [ ] 3. `quality/quick_validation_2026_06_25_21_30.md` exists and `final_decision` confirmed (failed)
- [x] 4. `exploit_chain/exploit_chains_2026_06_25_21_30.md` exists and chain feasibility wording reviewed
- [ ] 5. `DemoProject_code_audit_2026_06_25_21_30.md` has written back the final conclusion and consistency counts (failed)

## Summary
- checklist_pass_count: 3
- checklist_blocked_count: 2
- checklist_pending_count: 0
- final_anchor_decision: BLOCKED
- pool_check: PASS
- stat_check: FAIL
- chain_check: FAIL

## BLOCKED Source File Summary (If Any)
- quality/quick_validation_2026_06_25_21_30.md | final_decision | consistency_check_status=BLOCKED
- DemoProject_code_audit_2026_06_25_21_30.md | exploit_chain_consistency_check_counts | inconsistent with exploit_chain overview table statistics
```

Usage requirements:

- If `checklist_blocked_count > 0`, `final_anchor_decision` must be `BLOCKED`
- If `quality/final_anchor_checklist_{timestamp}.md` exists, the final report `4.6` fields must be consistent with its summary block
- If `final_anchor_decision=BLOCKED`, the final report must not write "deliverable / passed / closing complete"

### Machine Verification (Count = Enumeration Count, 2026-09-20)

In addition to manual line-by-line checking at closing, the following three machine-verification lines must be executed with results recorded (formula criteria take the "Three Counting Formulas" in the pending-evidence risk pool section of `IO_PATH_CONVENTION.md` as the sole source of truth; the three lines' results are recorded in the summary block above as the fields `pool_check` / `stat_check` / `chain_check`, with values PASS/FAIL):

- [ ] Pool count = unique ID count: the `pool_total` of `pending_pool_{timestamp}.md` equals the row count after deduplicating by pool_id (one ID per row, no alias-merged rows; the sum of status buckets = pool_total)
- [ ] Findings statistics table = detail block enumeration count: the counts in each artifact's "Findings Statistics Table" equal the actual number of enumerated detail blocks, traceable item by item
- [ ] Chain status decomposition self-consistent: the exploit_chain chain status decomposition satisfies `closed + open + false_positive = total chains` (closed = sum of non-false-positive non-pending items); when not satisfied, `final_anchor_decision` must be `BLOCKED`

## Uncovered Attack Surface Risk Summary (Mandatory for PARTIAL/SAMPLE)

| Reachability \ Sensitive Operation | Read/Write | Admin | Funds/Data Export | Total |
| ---- | ---- | ---- | ---- | ---- |
| Anonymous reachable | {n} | {n} | {n} | {n} |
| Authenticated reachable | {n} | {n} | {n} | {n} |
| Intranet/role reachable | {n} | {n} | {n} | {n} |

- Uncovered entry list summary: {Top N routes/methods/paths}
- Residual risk range: {highest possible level per SEVERITY_RATING and its basis}
- Suggestion: {backfill batches or reasons for accepting the statement}
