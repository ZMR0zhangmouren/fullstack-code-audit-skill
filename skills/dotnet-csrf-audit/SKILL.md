---
name: dotnet-csrf-audit
description: .NET CSRF audit tool. Identifies missing Antiforgery protection, validation bypasses, and inconsistent configuration risks at state-changing entries.
---

# .NET CSRF Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to Antiforgery, cookie authentication, cross-site submission, state-changing entries, and exception whitelists
- If the project has secondary encapsulations such as CsrfHelper, AjaxWrapper, MutationGateway, or AdminActionService, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align state-changing entries, parameter sources, and `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to supplement authentication state, anonymous entries, and permission boundaries)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- whether state-changing endpoints (POST / PUT / PATCH / DELETE) have Antiforgery validation enabled
- the risk of API controllers not enabling Antiforgery by default (cookie authentication + API combination)
- whether endpoints marked with [IgnoreAntiforgeryToken] truly have no state-changing side effects
- Content-Type bypass: exploitation scenarios where text/plain does not trigger CORS preflight
- the Antiforgery token transmission and validation mechanism in SPA / Ajax scenarios
- CSRF protection of Blazor Server events, SignalR Hub methods, and GraphQL Mutations
- the possibility of subdomain cookie injection causing token override

## Evidence References

- EVID_CSRF_STATE_CHANGE_HANDLER_EXEC
- EVID_CSRF_TOKEN_SOURCE
- EVID_CSRF_TOKEN_VERIFY
- EVID_CSRF_BYPASS_BRANCH

## Enumeration Rules (Mandatory Refinement)

- Enumerate all state-changing endpoints: POST, PUT, PATCH, DELETE, GraphQL Mutations, Blazor Server events, and side-effect Hub methods
- Search ValidateAntiForgeryToken, AutoValidateAntiforgeryToken, IgnoreAntiforgeryToken, IAntiforgery, and cookie auth + API combination usage positions first
- Enumerate frontend forms, Ajax, SPA, GraphQL, SignalR, iframe submissions, file uploads, and multipart request paths
- For each state-changing entry record: authentication method, token source, validation location, exception rules, content-type branches, and whether it is cross-site reachable

## Barrier Verification Matrix (Mandatory)

Evaluate per the fail-close three-level standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Level | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Level 1 | state-changing entry reachable | entries such as POST / PUT / PATCH / DELETE / Mutation / Hub exist and can be cross-site triggered | BLOCKED → not a state-changing entry; the specialty ends |
| Level 2 | token validation chain complete | the three segments of token generation, transmission, and validation have complete evidence with no breaks | BLOCKED → conclusion downgraded to `⚠️Pending Verification / Environment-Dependent` |
| Level 3 | bypass branches not achievable | no effective content-type / whitelist / framework branch bypass paths | PARTIAL → only output bypass hypotheses and verification steps |

## Two-Phase Determination Process (Mandatory)

- **Phase 1 (initial screening hit)**: hit a state-changing entry + token source controllable or missing, and output `hit ID: M{hash}`.
- **Phase 2 (refined confirmation)**:
  1. back-trace the three-segment chain of token generation - transmission - validation;
  2. check the bypass conditions of [IgnoreAntiforgeryToken] / content-type branches / whitelist exceptions;
  3. if all three-level Barriers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priorities (Mandatory)

1. **Confirmed Vulnerability**: state-changing entry reachable + token validation chain broken or completely missing + bypass branch achievable. Output `Confirmed Vulnerability`.
2. **Pending**: the entry is reachable but part of the token chain evidence is missing, or the bypass conditions depend on a specific environment. Output `Pending`.
3. **False Positive / No Risk**: the entry is not state-changing (e.g., a pure GET read-only), or the token validation chain is complete with no bypassable branches. Output `False Positive` with the determination basis.

## Testing Recommendations and Minimal Trigger Conditions (Mandatory)

- **Minimal trigger conditions**:
  - a state-changing request entry exists (POST / PUT / PATCH / DELETE / Mutation / Hub)
  - the request can carry the target site's cookies (SameSite = None / Lax or subdomain injection)
  - no effective Antiforgery token validation exists, or the validation is bypassable
- **Test case suggestions**:
  - Happy Path: normal requests with tokens are accepted; requests without tokens are rejected
  - Boundary / ambiguity: Content-Type: text/plain bypassing preflight, subdomain cookie override, state-changing side effects of whitelisted endpoints
- Each hit output appends `hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (state-changing entry confirmation)**: side-effect entries (POST / PUT / PATCH / DELETE / Mutation / Hub) must be locked first.
- 🔴 **CHECKPOINT B (token chain confirmation)**: three-segment evidence of token generation, transmission, and server-side validation must be given.
- 🔴 **CHECKPOINT C (bypass branch confirmation)**: whether content-type / exception whitelist / framework branches can bypass validation must be explicit.
- 🛑 **STOP**: if the token validation chain is incomplete, the conclusion is downgraded to `⚠️Pending Verification / Environment-Dependent`; outputting Confirmed CSRF is forbidden.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| state-changing entry identification incomplete | complete the list of POST / PUT / PATCH / DELETE / Mutation / Hub entries | retain high-risk entries as pending first; give no strong conclusion |
| token generation - transmission - validation chain broken | complete the three-segment evidence separately and verify branch conditions | downgrade the conclusion to `⚠️Pending Verification / Environment-Dependent` |
| whitelist / content-type bypass evidence insufficient | verify whitelist items and request type branches item by item | only output suspicious bypass paths and verification steps |

🔴 **STOP: when any fallback triggers, outputting "Confirmed CSRF" is forbidden.**

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

- Anti-pattern: treating "logged-in state exists" as "CSRF does not hold". Correct practice: check whether cross-site requests can carry credentials.
- Anti-pattern: ignoring side-effect entries of JSON / API / Mutation / Hub. Correct practice: cover all state-changing surfaces.
- Anti-pattern: not verifying the token generation - transmission - validation loop. Correct practice: all three segments of evidence are indispensable.
- Anti-pattern: not auditing exception whitelists. Correct practice: verify whitelist boundaries and bypass conditions item by item.

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion levels: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose one of three; blank is forbidden).
- Minimum evidence set: at least the five items `Entry Point`, `Controllable Parameter`, `Key Call`, `Security Boundary`, and `Missing Evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softened wording is forbidden: such as "may be at risk / suggested attention / depends on the situation / most likely"; when evidence is insufficient, `⚠️Pending Verification` and the next evidence-supplementing action must be explicitly written.

Minimal output fragment (directly reusable):

```md
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameter=...; key call=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement the parameter-propagation evidence of trace_id=...
```

## Output

- vuln_audit/csrf_{timestamp}.md
- Optional: vuln_poc/csrf_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
