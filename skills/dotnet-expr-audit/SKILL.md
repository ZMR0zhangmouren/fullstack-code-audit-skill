---
name: dotnet-expr-audit
description: .NET expression injection audit tool. Identifies expression evaluation risks in Roslyn Scripting, Dynamic LINQ, DataTable.Compute, and custom rule engines.
---

# .NET Expression Injection Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to script engines, expression interpreters, rule engines, Dynamic LINQ, and computed expressions
- If the project has secondary encapsulations such as RuleEngine, FormulaService, ScriptHost, or QueryExpressionBuilder, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align expression entries, parameter bindings, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement the host, rule engine registration, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- CSharpScript.EvaluateAsync / RunAsync: whether user input enters the expression string
- Dynamic LINQ (System.Linq.Dynamic.Core): Where / OrderBy / Select accepting string expressions
- DataTable.Compute / DataTable.Select: sources of the filter or expression parameters
- NCalc / custom rule engines: controllability of expression strings and sandbox restrictions
- expression entries in admin rule configuration, report formulas, marketing conditions, and workflow engines
- whether expression evaluation results enter sensitive semantics (database queries, file operations, reflective calls)
- sandbox policies: whether the allowed types / namespaces / methods are sufficiently strict

## Evidence References

- EVID_EXPR_EVAL_ENTRY
- EVID_EXPR_EXPR_CONTROL
- EVID_EXPR_EXEC_CHAIN_ENTRY

## Enumeration Rules (Mandatory Refinement)

- Enumerate Roslyn CSharpScript, DataTable.Compute, Dynamic LINQ, NCalc, custom rule engines, and workflow expression engines
- Search key fields such as evaluate, compile, script, expression, formula, rule, condition, where, and sort expression first
- Enumerate expression entries in admin rule configuration, report formulas, marketing rules, process engines, search sorting, and custom filters
- For each expression entry record: expression source, allowed types / functions, sandbox policy, and the sensitive semantics into which evaluation results flow

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Expression string controllability** | Read the expression string construction source, confirming whether it comes from user input (such as `CSharpScript.EvaluateAsync(userInput)`) | user input entering the expression string directly → 🔴 high risk; fixed expression template + only parameter values controllable → 🟠 parameter-slot boundary to be confirmed |
| **Sandbox / type whitelist** | Read `ScriptOptions` / custom sandbox configuration, confirming whether the allowed types, namespaces, and methods are fail-close | strict whitelist with unknown types rejected → ✅ safe; blacklist or unrestricted → 🔴 high risk; sandbox configuration not visible → ⚠️ to be confirmed |
| **Pre-evaluation validation** | Confirm whether whitelist, length limits, syntax restrictions, or AST validation exist before expression evaluation | validation present and fail-close → ✅ safe; length limits only without syntax restrictions → ⚠️ bypassable; no validation → 🔴 high risk |
| **Dynamic LINQ string expressions** | Confirm whether `Where` / `OrderBy` / `Select` of `System.Linq.Dynamic.Core` accept user-controllable strings | user-controllable without a whitelist → 🔴 high risk; fixed expression structure + value slots parameterized only → 🟠 to be confirmed |
| **DataTable.Compute / Select** | Confirm whether the expression / filter parameters of `Compute` or `Select` come from user input | user-controllable → 🔴 high risk; fixed expressions → ✅ safe |
| **Evaluation result sensitive semantics** | Trace whether expression evaluation results enter sensitive semantics such as database queries, file operations, permission checks, or command execution | entering sensitive semantics → 🔴 high-risk amplification; used for numeric computation only with results not echoed → 🟠 to be confirmed |

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

1. user-controllable input enters expression string evaluation directly (such as `CSharpScript.EvaluateAsync(userInput)`), without a sandbox / whitelist
2. `Where` / `OrderBy` / `Select` of `System.Linq.Dynamic.Core` accept user-controllable string expressions
3. the expression / filter parameters of `DataTable.Compute` / `DataTable.Select` come from user-controllable input
4. the sandbox / type whitelist is fail-open or silent-fallback, bypassable via dangerous types such as reflection, file operations, or process startup
5. in nested / recursive structures (such as multi-layer RuleEngine wrappers), the top level has validation but sub-levels do not perform equivalent validation
6. expression evaluation results enter sensitive semantics such as database queries, file operations, or permission checks

### Pending

1. the context shows a suspicious pattern (such as an `EvaluateAsync` call), but the external input source is unclear (trace or call chain needs to be supplemented)
2. a barrier function (such as sandbox configuration) exists, but whether the current branch invokes it and whether the configuration takes effect cannot be confirmed
3. parameter passing in asynchronous / queue / event chains (such as background rule engines) is not closed
4. expression sources are complex (such as read from the database / cache), and whether they can be influenced by users cannot be confirmed

### False Positive

1. the final expression comes from fixed constants / enum mappings, and unknown input is refused execution (fail-close)
2. all recursive levels reuse the same fail-close type whitelist / sandbox validator
3. user input enters only numeric parameter slots, the expression structure is fully fixed, and there is no string interpolation
4. expression evaluation executes in a strict sandbox that forbids access to all dangerous types and methods

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct expression injection payloads (such as `File.ReadAllText("/etc/passwd")`, `Process.Start("calc")`, `1; DROP TABLE`) and verify expression execution really exists
- **Negative testing**: construct inputs intercepted by barriers (such as out-of-sandbox types, overlong expressions, illegal syntax) and verify the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (evaluation entry confirmation)**: the real expression evaluation APIs must be located first.
- 🔴 **CHECKPOINT B (controllability confirmation)**: whether the expression string or parameter context is controllable must be confirmed.
- 🔴 **CHECKPOINT C (execution chain confirmation)**: whether evaluation results enter sensitive semantics must be stated.
- 🛑 **STOP**: if there are only expression keyword hits without execution chain evidence, the conclusion is downgraded to `⚠️Pending Verification`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| real evaluation APIs not located | return to the entry to complete Evaluate / Compile call evidence | downgrade to `⚠️Pending Verification`, retaining the hit point |
| expression controllability unprovable | trace the input-to-expression-string / context mapping | only output pending paths; make no strong conclusion |
| evaluation result destination unknown | trace to sensitive semantics such as database / files / permission checks | if still unclosed, maintain a conservative risk description |

🔴 **STOP: when any fallback triggers, outputting "Confirmed Injection" is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Mandatory shared indexes: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber source) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: persistence paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from directories are forbidden.
- Evidence consistency validation: if graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: confirm at least once before submission that key referenced files are accessible (such as `DOTNET_AUDIT_GRABBER_INDEX.md` and `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Execute at least 2 typical test cases before each output (one happy path + one boundary / ambiguity scenario), and record expected vs actual differences.
- `full_test >= 1` is required by default; if only `dry_run` is possible, `confidence=LOW` must be marked in the conclusion, with a supplementary test plan and owner given.
- Pass criteria: key fields complete, evidence chains traceable, conclusion levels consistent with gate status; if any fails, marking "passed / deliverable" is forbidden.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `input constraints` → `execution steps` → `output and acceptance`; missing layers or cross-layer mixing are forbidden.
- A single paragraph is recommended not to exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into the single-source-of-truth section.
- AI-style filler and empty connectives are forbidden (such as "first / second / finally / in summary / to put it simply / in other words"); rewrite them into executable statements upon discovery.

## Quality Gate & Assessment Consistency (Mandatory)

- Execute the minimal gate self-check before output: `input completeness`, `key evidence hit`, and `output path valid` must all be PASS.
- If any of `key evidence missing`, `chain not closed`, or `consistency_check_status=BLOCKED` exists, the conclusion must be downgraded to `BLOCKED`; outputting "Confirmed Exploitable / Deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

- Anti-pattern: judging injection upon hitting only the `expression` keyword. Correct practice: confirm the evaluation API and the controllable expression string.
- Anti-pattern: ignoring sandbox / whitelist configuration. Correct practice: verify accessible types and function boundaries.
- Anti-pattern: not tracing where evaluation results go. Correct practice: complete the follow-up chain to sensitive semantics.
- Anti-pattern: strong conclusions with insufficient evidence. Correct practice: downgrade to `⚠️Pending Verification` and list the missing evidence.

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

- vuln_audit/expr_{timestamp}.md
- Optional: vuln_poc/expr_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
