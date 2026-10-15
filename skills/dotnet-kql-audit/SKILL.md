---
name: dotnet-kql-audit
description: .NET KQL (Kusto Query Language) injection audit tool. Identifies KQL string concatenation and injection risks in the Azure Monitor Query SDK, Application Insights SDK, and Log Analytics API; outputs severity rating, PoC, and remediation recommendations.
---

# .NET KQL Injection Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the KQL-related grabbers of entry definitions, binding / conversion, precondition controls, sensitive operations, and security configuration
- If the project has secondary encapsulations such as KQL Builder, Query Helper, or LogAnalyticsClient, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement Azure Monitor configuration, serialization configuration, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- call sites of `LogsQueryClient.QueryWorkspaceAsync`, `QueryWorkspace`, `QueryResource`, and `MetricsQueryClient`, and sources of KQL query strings
- paths generating KQL via string concatenation, interpolated strings, StringBuilder, FormattableString, AppendFormat, and Join
- parameterization boundaries of `QueryWorkspace` / `QueryResource` / `QueryWorkspaceAsync` in the `Azure.Monitor.Query` SDK
- query construction points of `TelemetryClient.Query` / `AnalyticsClient` in `Microsoft.ApplicationInsights`
- call sites of `OperationalInsightsDataClient.Query` in `Microsoft.Azure.OperationalInsights` (legacy)
- whether "non-parameterizable" dynamic fragments such as dynamic table names, column names, where condition fragments, extend / project fields, and `| take` pagination fragments have whitelists
- KQL pipeline injection: injecting extra pipeline operations via `\n` (such as `| take 10000` becoming `| take 10000\n| union (traces | take 10000)`)
- unvalidated strings mixed into KQL operators such as `extend`, `project`, `where`, `contains`, `has`, and `startswith`
- whether multi-tenant and resource scope filters are bypassed by dynamic KQL
- whether exception handling, logs, and debug output expose complete KQL, query parameters, and workspace / resource IDs

## Enumeration Rules (Mandatory Refinement)

- Enumerate all KQL call points in classes inheriting Controller / ControllerBase, Services, Background Jobs, GraphQL Resolvers, and Hubs
- Search first: `LogsQueryClient`, `QueryWorkspace`, `QueryResource`, `MetricsQueryClient`, `QueryWorkspaceAsync`, `OperationalInsightsDataClient`, `AnalyticsClient`, `TelemetryClient.Query`
- Enumerate usage positions of string concatenation, interpolated strings, StringBuilder, FormattableString, AppendLine, Join, Format, and KQL helpers
- Separately enumerate "non-parameterizable fragments": dynamic table names, column names, where conditions, extend / project fields, `| take` / `| limit` pagination, and union / join target tables
- Enumerate the encapsulation chains of KQL Builder, Query Helper, LogAnalyticsClient, and custom KQL builders
- For each call point record: KQL source, parameter object source, upstream entry of the call stack, and whether it executes under resource scope filters / multi-tenant filters

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **KQL string concatenation** | Read the KQL query string construction source, confirming whether it comes from string concatenation / interpolation (such as `$"traces | where message contains '{input}'"`) | externally controllable input participating in KQL string concatenation → 🔴 high risk; fixed KQL template + SDK parameterized value slots → 🟠 parameterization boundary to be confirmed |
| **SDK parameterization boundary** | Confirm whether `QueryWorkspaceAsync` / `QueryResource` correctly use the SDK's parameterization capability instead of concatenating user input directly into KQL strings | SDK parameterization used correctly with no interpolation mixed in → ✅ safe; SDK called but the KQL string contains interpolation → ⚠️ to be confirmed |
| **Dynamic table name / column name whitelist** | Confirm whether dynamic table names, column names, extend / project fields, and `| take` / `| limit` pagination come from whitelist mappings | fail-close whitelist → ✅ safe; blacklist or no whitelist → 🔴 high risk; whitelist implementation not visible → ⚠️ to be confirmed |
| **KQL pipeline injection** | Confirm whether newlines can be appended to the constructed KQL string to add pipeline operations (such as injecting `\n| union (traces)`) | newline-appended pipelines allowed → 🔴 high risk; strict single query with no controllable pipeline slots → ✅ safe |
| **Operator controllability** | Confirm whether value slots in operators such as `where`, `contains`, `has`, `startswith`, `extend`, and `project` come from user-controllable input | value slots controllable without escaping / whitelist → 🔴 high risk; value slots from fixed constants or validated whitelists → ✅ safe |
| **Multi-tenant / resource scope filters** | Confirm whether multi-tenant / resource scope filters are bypassed by dynamic KQL (such as cross-workspace queries via union) | filters bypassable by dynamic KQL → 🔴 high risk; filters locked before query construction and not overridable by KQL → ✅ safe |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion as "Confirmed Safe" or "False Positive" is forbidden.**

## Two-Phase Determination (Mandatory)

Follow the two-phase determination process of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

1. **Phase 1 (interim conclusion)**: mark each hit as `Confirmed Vulnerability Candidate` / `Pending` / `False Positive` first
2. **Phase 2 (mandatory evidence chasing)**:
   - if Phase 1 is `Confirmed Vulnerability Candidate` → all relevant items of the Barrier verification matrix must be completed before `Confirmed` may be marked
   - if Phase 1 is `Pending` → chase at least one more hop of the call chain or downstream parser downward, until a determination can be made
   - if Phase 2 still cannot close → remain `Pending`, and explicitly record which hop of evidence is missing

## Determination Rules (Mandatory Refinement)

### Confirmed Vulnerability

At least one of the following conditions holds:

1. user-controllable input enters KQL string concatenation / interpolation positions directly, with no barrier validation
2. dynamic table names, column names, extend / project fields, and `| take` pagination fragments have no whitelist or the whitelist is fail-open
3. the constructed KQL string allows newline-appended pipeline operations, making pipeline injection feasible
4. value slots of operators such as `where` / `contains` / `has` come from user-controllable input without escaping / whitelists
5. in nested / recursive structures (such as multi-layer KQL Builder wrappers), the top level has validation but sub-levels do not perform equivalent validation

### Pending

1. the context shows a suspicious pattern (such as a `QueryWorkspaceAsync` call), but the external input source is unclear (trace or call chain needs to be supplemented)
2. a barrier function (such as a KQL parameterization wrapper) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
3. parameter passing in asynchronous / queue / event chains (such as background tasks periodically querying Log Analytics) is not closed
4. SDK parameterization and string concatenation are mixed, and the specific usage path at the current call site cannot be confirmed

### False Positive

1. the final KQL query comes from fixed constants / template mappings, and unknown input is refused execution (fail-close)
2. all recursive levels reuse the same fail-close whitelist validator (table names / column names / extend fields)
3. user input enters only SDK parameterized value slots, and the KQL string template is fully fixed with no interpolation
4. multi-tenant / resource scope filters are locked before query construction and cannot be overridden by KQL

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct KQL injection payloads (such as `evil' | union (traces)`, `message contains 'x'\n| union (traces | take 100)`, and illegal extend fields) and verify injection really exists
- **Negative testing**: construct inputs intercepted by barriers (such as out-of-whitelist table names, illegal column names, and non-parameterized value slots) and verify the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Evidence References (Mandatory)

- EVID_KQL_EXEC_POINT
- EVID_KQL_STRING_CONSTRUCTION
- EVID_KQL_USER_PARAM_TO_KQL_FRAGMENT

## Execution Checkpoints

🔴 **STOP — the following two items must be verified before outputting conclusions; neither may be missing:**

1. **trace-gate check**: if `route_tracer/{route_id}/trace_{timestamp}.md` **does not exist or trace_status=PARTIAL/UNRESOLVED**, all conclusions must be downgraded to `⚠️Pending Verification`; outputting `✅Confirmed Exploitable` is forbidden.
2. **EVID completeness check**: if EVID_KQL_EXEC_POINT / EVID_KQL_STRING_CONSTRUCTION / EVID_KQL_USER_PARAM_TO_KQL_FRAGMENT are not all satisfied, outputting high-risk (🔴) level conclusions is forbidden.

🔴 **STOP — when any of the following situations is found, it must be annotated separately in the output and must not be silently skipped:**

- dynamic fragments (table names / column names / extend fields / where conditions) without whitelist protection → list a separate `⚠️ Whitelist Missing Risk`
- multi-tenant / resource scope filters bypassed by dynamic KQL → list a separate `⚠️ Filter Bypass Risk`
- complete KQL or query parameters leaked in exceptions / logs → list a separate `⚠️ Information Disclosure Risk`

## Resource References & Reachability Validation (Mandatory)

- Mandatory shared indexes: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber source) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: persistence paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from directories are forbidden.
- Evidence consistency validation: if graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: confirm at least once before submission that key referenced files are accessible (such as `DOTNET_AUDIT_GRABBER_INDEX.md` and `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Every skill maintains at least 2 typical test cases (one happy path + one complex scenario) and annotates the case IDs in the results.
- Each evaluation round executes `full_test` on at least 1 case; if limited to `dry_run`, `dry_run_reason` and a supplementary test plan must be recorded.
- Pass criteria must simultaneously satisfy: `intent achieved`, `key evidence hit`, and `output format compliant`; if any is not met, "pass" must not be given.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `input constraints` → `execution steps` → `output and acceptance`; missing layers or cross-layer mixing are forbidden.
- A single paragraph is recommended not to exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into the single-source-of-truth section.
- AI-style filler and empty connectives are forbidden (such as "first / second / finally / in summary / to put it simply / in other words"); rewrite them into executable statements upon discovery.

## Quality Gate & Assessment Consistency (Mandatory)

- Execute the minimal gate self-check before output: `input completeness`, `key evidence hit`, and `output path valid` must all be PASS.
- If any of `key evidence missing`, `chain not closed`, or `consistency_check_status=BLOCKED` exists, the conclusion must be downgraded to `BLOCKED`; outputting "Confirmed Exploitable / Deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

| # | Anti-pattern | Why it is wrong | Correct practice |
|---|---|---|---|
| 1 | **Outputting ✅Confirmed without a trace** | static grabbers alone cannot prove parameter controllability and execution paths | downgrade to `⚠️Pending Verification`, stating the missing evidence |
| 2 | **Judging SDK parameterized interfaces as safe directly** | `QueryWorkspaceAsync(workspace, $"traces | where message contains '{userInput}'")` is still an injection risk; SDK parameterization ≠ KQL without injection | check whether the KQL string is mixed in via interpolation, not just the SDK call pattern |
| 3 | **Searching only one call layer and ignoring the wrapper chain** | the business layer calls KQL Builder, and KQL Builder calls `QueryWorkspaceAsync` — the vulnerability sits at the bottom layer | the enumeration rules require tracing to the final execution point |
| 4 | **Treating dynamic table names / column names / extend fields as low risk and ignoring them** | table / column name injection enables union-based attacks and cross-table data leakage | non-parameterizable fragments must be enumerated separately with whitelist recommendations |
| 5 | **Ignoring KQL pipeline injection** | KQL uses `|` pipeline operations; injecting `\n| union (traces)` enables cross-table queries | enumeration must check whether newlines can be appended to the constructed KQL string to add pipelines |

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (KQL execution entry confirmation)**: KQL execution entries and SDK / native call boundaries must be confirmed.
- 🔴 **CHECKPOINT B (KQL string construction confirmation)**: KQL strings must be confirmed as parameter-bound rather than string concatenation / interpolation.
- 🔴 **CHECKPOINT C (high-risk KQL fragment confirmation)**: high-risk fragments such as dynamic table names, column names, extend / project fields, and pipeline appends must be confirmed.
- 🛑 **STOP**: if parameterization evidence and the execution chain are not closed, outputting a "no injection risk" conclusion is forbidden.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| trace incomplete or missing | supplement route_tracer evidence and align route_id | downgrade to `⚠️Pending Verification`; Confirmed Exploitable is forbidden |
| parameter-to-KQL-fragment mapping unclosed | complete the string construction and execution point chain evidence | no high-risk confirmation; give verification steps only |
| dynamic fragment whitelist evidence insufficient | verify table name / column name / extend field whitelist logic item by item | conservatively mark high-risk pending items |

🔴 **STOP: when any fallback triggers, outputting "no injection risk" is forbidden.**

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion levels: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose one of three; blank is forbidden).
- Minimum evidence set: at least the five items `Entry Point`, `Controllable Parameter`, `Key Call`, `Security Boundary`, and `Missing Evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softened wording is forbidden: such as "may be at risk / suggested attention / depends on the situation / most likely"; when evidence is insufficient, `⚠️Pending Verification` and the next evidence-supplementing action must be explicitly written.

Minimal output fragment (directly reusable):

```md
- Hit ID: M{hash} (file path fragment + line number + sequence, used for cross-phase tracking and regression alignment)
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameter=...; key call=...; security boundary=...; missing evidence=none
- test_id: T{hash} (associated test case)
- Next action: if gaps exist, supplement the parameter-propagation evidence of trace_id=...
```

## Output

- vuln_audit/kql_{timestamp}.md
