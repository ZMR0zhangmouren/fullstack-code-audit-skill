---
name: dotnet-tpl-audit
description: .NET template injection audit tool. Identifies controllable template name or template content risks in Razor Runtime Compilation, custom template engines, email templates, and dynamic view resolution.
---

# .NET Template Injection Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to template sources, runtime compilation, partial templates, email templates, and preview rendering
- If the project has secondary encapsulations such as TemplateRenderer, MailComposer, PreviewEngine, or ViewCompiler, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align template entries, parameter bindings, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement Razor, email template, or runtime compilation control planes)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Razor Runtime Compilation: whether users can control template content or template paths
- third-party template engines (RazorLight, Scriban, Fluid, DotLiquid): controllability of template sources
- email templates: template content loaded from databases / CMS and editable by admins
- CMS / low-code platforms: compilation and execution permissions of user-defined templates
- service container access within templates: whether arbitrary service methods can be invoked via templates
- Include / Import / Partial: file inclusion caused by controllable template paths
- template compilation cache: cache poisoning or persistent backdoor risks

## Evidence References

- EVID_TPL_ENGINE_RENDER_OR_PARSE_ENTRY
- EVID_TPL_TEMPLATE_OR_EXPR_CONTROL
- EVID_TPL_EXEC_CHAIN_ENTRY

## Enumeration Rules (Mandatory Refinement)

- Enumerate Razor Runtime Compilation, custom ViewEngines, email templates, CMS templates, export templates, notification templates, and low-code template engines
- Search key names such as template, view, layout, partial, render, compile, razor, liquid, scriban, and mustache first
- Enumerate template names, template paths, template content, helpers, include / import, model objects, and service container access capabilities
- For each template entry record: template source, compilation method, runtime permissions, output landing point, and whether user-controllable templates or expressions exist

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Template source controllability** | Confirm whether template content / template paths come from user-controllable input (such as user uploads, admin backend editing, or URL parameters specifying template names) | user-controllable template content / paths without a sandbox → 🔴 high risk; only admins can edit and admins are trusted → 🟠 to be confirmed; templates fully fixed → ✅ safe |
| **Runtime compilation permissions** | Confirm whether runtime compilation of Razor Runtime Compilation or third-party template engines is enabled, and the execution permissions of the compiled code | runtime compilation enabled with controllable templates → 🔴 high risk; runtime compilation disabled → ✅ safe; compilation in a sandbox → 🟠 sandbox strength to be confirmed |
| **Helper / function whitelist** | Confirm whether the helpers, functions, and service containers accessible in templates are fail-close whitelists | fail-close whitelist → ✅ safe; no whitelist or blacklist mode → 🔴 high risk; whitelist not visible → ⚠️ to be confirmed |
| **Include / Import / Partial path restrictions** | Confirm whether include / import / partial paths in templates come from user-controllable input and are confined to the template directory | controllable paths without base-directory locking → 🔴 high risk; fixed paths or sandbox locking → ✅ safe |
| **Template compilation cache security** | Confirm whether the template compilation cache can be poisoned (e.g., user-controllable templates written to the cache are later triggered by other users) | cache keys associated with user input and templates controllable → 🔴 high risk; cache isolated and templates fixed → ✅ safe |
| **Output landing and echo** | Confirm whether template rendering results enter output surfaces perceivable by attackers, such as email sending, PDF generation, or page display | entering attacker-perceivable output surfaces → 🔴 high-risk amplification; internal previews or admin-visible only → 🟠 to be confirmed |

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

1. user-controllable input enters template content / template paths directly, with no sandbox / whitelist restrictions
2. runtime compilation is enabled with controllable template content, allowing arbitrary C# code execution
3. the helper / function whitelist is fail-open or silent-fallback, and templates can call dangerous functions (such as file operations or command execution)
4. include / import / partial paths come from user-controllable input without base-directory locking (file inclusion)
5. in nested / recursive structures (such as multi-layer TemplateRenderer wrappers), the top level has validation but sub-levels do not perform equivalent validation
6. the template compilation cache can be poisoned by user-controllable templates

### Pending

1. the context shows a suspicious pattern (such as a `RenderTemplate` call), but the template source is unclear (trace or call chain needs to be supplemented)
2. a barrier function (such as the helper whitelist) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
3. parameter passing in asynchronous / queue / event chains (such as background email rendering) is not closed
4. runtime compilation configuration is scattered across multiple places, and whether it is enabled cannot be confirmed

### False Positive

1. the final template comes from fixed constants / enum mappings, and unknown input is refused execution (fail-close)
2. all recursive levels reuse the same fail-close template whitelist validator
3. runtime compilation is disabled, and templates are pre-compiled with fully fixed content
4. template rendering results do not enter any attacker-perceivable output surface

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct template injection payloads (such as `@(new System.Diagnostics.ProcessStartInfo("calc"))`, `{% include '/etc/passwd' %}`, and custom helper calls performing file operations) and verify template execution really exists
- **Negative testing**: construct inputs intercepted by barriers (such as out-of-whitelist helpers, illegal template paths, and overlong templates) and verify the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (template engine identification)**: engines such as Razor / Scriban / Handlebars and their rendering entries must be confirmed.
- 🔴 **CHECKPOINT B (data flow confirmation)**: whether user input enters template statements, helpers, or expression evaluation must be confirmed.
- 🔴 **CHECKPOINT C (isolation and whitelist confirmation)**: helper whitelists, function disabling, and sandbox boundaries must be confirmed.
- 🛑 **STOP**: if template execution capability and input controllability are not both determined, no "not exploitable" conclusion may be drawn.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| template entry clear but controllability unclear | complete the mapping evidence of template name / content sources | downgrade to `⚠️Pending Verification` |
| helper / include capability boundaries unclear | verify whitelists and disabling strategies | no "not exploitable" strong conclusion |
| rendering result destination unknown | trace to output surfaces such as pages / emails / exports | assess conservatively and retain pending items |

🔴 **STOP: when any fallback triggers, outputting "not exploitable" is forbidden.**

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

- Anti-pattern: judging template injection upon seeing only a template engine. Correct practice: confirm whether template content / template names are controllable.
- Anti-pattern: ignoring include / import and helper capabilities. Correct practice: evaluate the callable surface and sandbox boundaries.
- Anti-pattern: not tracing where rendering products go. Correct practice: confirm whether they enter emails, pages, or executable consumption chains.
- Anti-pattern: writing "not exploitable" with incomplete evidence. Correct practice: downgrade and list the missing evidence.

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

- vuln_audit/tpl_{timestamp}.md
- Optional: vuln_poc/tpl_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
