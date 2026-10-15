---
name: dotnet-open-redirect-audit
description: .NET open redirect audit tool. Identifies target address control risks in Redirect, LocalRedirect, ReturnUrl, Challenge callbacks, and post-login redirects.
---

# .NET Open Redirect Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to ReturnUrl, Redirect, navigation targets, external address whitelists, and proxy prefix handling
- If the project has secondary encapsulations such as RedirectHelper, LoginFlowService, NavigationGuard, or CallbackResolver, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align redirect entries, ReturnUrl parameters, and `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to supplement authentication boundaries of login / logout / challenge entries)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Redirect(url) where the url source is a request parameter without IsLocalUrl validation
- redirect_uri / post_logout_redirect_uri validation in OAuth / OIDC callbacks
- ReturnUrl / next / continue parameters in login / logout flows
- whether LocalRedirect truly restricts local redirects (PathBase impact)
- controllability of redirect addresses after Challenge / SignOut
- target address validation in payment callbacks, invitation links, and deep-link redirects
- protocol restrictions: whether javascript: / data: / protocol-relative URLs are allowed

## Evidence References

- EVID_REDIR_OUTPUT_POINT
- EVID_REDIR_DEST_SOURCE_MAPPING
- EVID_REDIR_DEST_VALIDATION_NORMALIZATION

## Enumeration Rules (Mandatory Refinement)

- Enumerate all Redirect, LocalRedirect, RedirectToAction, Challenge, SignOut, and returnUrl / next / continue / callback parameter handling logic
- Search IsLocalUrl, redirect_uri, post_logout_redirect_uri, ReturnUrl, redirectTo, callbackUrl, and PathBase-related code first
- Enumerate business scenarios such as login, logout, authentication callbacks, payment callbacks, invitation links, deep-link redirects, and error redirects
- For each redirect point record: target source, validation logic, external identity provider constraints, proxy header impact, and whether sensitive tickets are carried

Evidence suggestions: reuse the path normalization approach of XSS / CFG, and state the target validation branches in the report.

## Barrier Verification Matrix (Mandatory)

Evaluate per the fail-close three-level standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Level | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Level 1 | redirect point exists with controllable target source | redirect points such as Redirect / Challenge / SignOut / ReturnUrl exist and the target parameter is user-controllable | BLOCKED → target source uncontrollable; the specialty ends |
| Level 2 | validation logic bypassable | IsLocalUrl / allowlist / protocol restrictions have bypass possibilities (double slashes / encoding / backslashes / javascript:, etc.) | BLOCKED → conclusion downgraded to `⚠️Pending Verification / Environment-Dependent` |
| Level 3 | redirect consequence reaches sensitive operations | the redirect can cause credential leakage, unauthorized access, or sensitive operation execution | PARTIAL → only output bypass hypotheses and verification steps |

## Two-Phase Determination Process (Mandatory)

- **Phase 1 (initial screening hit)**: hit a redirect output point + target source from user input, and output `hit ID: M{hash}`.
- **Phase 2 (refined confirmation)**:
  1. back-trace the target address source and parameter mapping chain;
  2. verify the bypass conditions of IsLocalUrl / allowlist / protocol restrictions / normalization logic (double slashes, encoding, backslashes, PathBase impact);
  3. assess whether the redirect can reach sensitive endpoints or leak credentials;
  4. if all three-level Barriers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priorities (Mandatory)

1. **Confirmed Vulnerability**: redirect point exists + target source controllable + validation bypassable + reaches sensitive operations. Output `Confirmed Vulnerability`.
2. **Pending**: the redirect point and target mapping exist, but validation bypass conditions or proxy / PathBase impact evidence is insufficient. Output `Pending`.
3. **False Positive / No Risk**: the target source is uncontrollable (hardcoded / internally generated), or the validation logic is strict with complete normalization. Output `False Positive` with the determination basis.

## Testing Recommendations and Minimal Trigger Conditions (Mandatory)

- **Minimal trigger conditions**:
  - a redirect point exists (Redirect / LocalRedirect / Challenge / SignOut)
  - the redirect target source contains user-controllable input (ReturnUrl / next / continue / callback parameters)
  - the target validation logic has bypass possibilities (missing IsLocalUrl, incomplete whitelist, no protocol restrictions)
- **Test case suggestions**:
  - Happy Path: normal local path redirects succeed; external URLs are intercepted
  - Boundary / ambiguity: `//evil.com`, `\\evil.com`, `javascript:alert(1)`, URL encoding bypasses, PathBase prefix bypasses
- Each hit output appends `hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (redirect point confirmation)**: real redirect output points such as Redirect / Challenge / SignOut must be confirmed.
- 🔴 **CHECKPOINT B (target mapping confirmation)**: the target address source and parameter mapping must be given.
- 🔴 **CHECKPOINT C (validation chain confirmation)**: whether IsLocalUrl / allowlist / protocol restrictions actually execute must be confirmed.
- 🛑 **STOP**: if the target validation branch cannot be confirmed, the conclusion is downgraded to `⚠️Pending Verification / Environment-Dependent`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| redirect target source chain incomplete | complete the mapping from parameters to Redirect / Challenge outputs | downgrade to `⚠️Pending Verification / Environment-Dependent` |
| normalization / protocol restriction evidence insufficient | verify double slashes, encoding, backslashes, and scheme branches | no exploitable strong conclusion; give verification paths only |
| proxy / PathBase impact unclear | align the final redirect target under the deployment chain | assess conservatively and retain pending items |

🔴 **STOP: when any fallback triggers, outputting "Confirmed Exploitable" is forbidden.**

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

- Anti-pattern: judging a vulnerability directly upon seeing Redirect(url). Correct practice: confirm whether the target source is controllable first.
- Anti-pattern: checking IsLocalUrl only without normalization verification. Correct practice: cover bypasses such as double slashes, encoding, and backslashes.
- Anti-pattern: ignoring proxy and PathBase impact. Correct practice: verify the final redirect target per the deployment boundary.
- Anti-pattern: strong conclusions with an incomplete evidence chain. Correct practice: downgrade to `⚠️Pending Verification / Environment-Dependent`.

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

- vuln_audit/redir_{timestamp}.md
- Optional: vuln_poc/redir_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
