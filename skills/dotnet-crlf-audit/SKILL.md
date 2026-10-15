---
name: dotnet-crlf-audit
description: .NET CRLF and response splitting audit tool. Identifies control character injection risks in output points such as Response.Headers, Set-Cookie, and Location.
---

# .NET CRLF Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to headers, cookies, log newlines, response splitting, and proxy passthrough
- If the project has secondary encapsulations such as ResponseHelper, HeaderBuilder, CookieManager, or LogFormatter, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align output entries, parameter sources, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement the host server, proxy boundaries, and response handling control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- positions in Response.Headers.Append / Add where the value source is user input
- user-controllable content in Set-Cookie values, Location headers, and Content-Disposition file names
- proxy passthrough headers (X-Forwarded-*) written to responses unfiltered
- scenarios where download file names come from the database or request parameters without `\r\n` filtering
- positions where user data is embedded in custom security headers
- the default interception behavior of host servers (Kestrel / IIS / Nginx) against CRLF and possible bypasses

## Evidence References

- EVID_CRLF_OUTPUT_POINT
- EVID_CRLF_USER_INPUT_INTO_HEADER_COOKIE
- EVID_CRLF_CONTROL_CHAR_FILTERING_ENCODING

## Enumeration Rules (Mandatory Refinement)

- Enumerate all Response.Headers writes, Set-Cookie, Location, Content-Disposition, custom downloads, and reverse-proxy passthrough header logic
- Search HeaderDictionary, Append, Add, SetCookieHeaderValue, FileDownloadName, and redirect location key calls first
- Enumerate positions where user input, file names, log IDs, proxy headers, and database fields enter headers
- For each header output point record: field name, value source, filtering logic, host server interception behavior, and the possible response pollution type

Evidence suggestions: focus on recording the output point, user input mapping, and control character filtering behavior.

## Barrier Verification Matrix (Mandatory)

Evaluate per the fail-close three-level standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Level | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Level 1 | output point exists and user input reachable | output points such as Response.Headers / Set-Cookie / Location / Content-Disposition exist and their value sources include user input | BLOCKED → no user input mapping; the specialty ends |
| Level 2 | control characters injectable | control characters such as `\r\n` are not effectively filtered or encoded and can reach the output point | BLOCKED → conclusion downgraded to `⚠️Pending Verification / Environment-Dependent` |
| Level 3 | proxy / host does not intercept | Kestrel / IIS / reverse proxies have no default interception of headers containing control characters, or the interception is bypassable | PARTIAL → only output environment-dependent conclusions and reproduction suggestions |

## Two-Phase Determination Process (Mandatory)

- **Phase 1 (initial screening hit)**: hit a header / cookie / location output point + user input mapping, and output `hit ID: M{hash}`.
- **Phase 2 (refined confirmation)**:
  1. back-trace the input → header value → control character filtering chain;
  2. verify control character residues in the raw value, after one decode, and after double decoding;
  3. check the default interception behavior of the Kestrel / IIS / proxy layers;
  4. if all three-level Barriers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priorities (Mandatory)

1. **Confirmed Vulnerability**: output point exists + user input reaches directly + control characters unfiltered + proxy / host does not intercept. Output `Confirmed Vulnerability`.
2. **Pending**: the output point and user input mapping exist, but filtering logic or proxy behavior evidence is insufficient. Output `Pending`.
3. **False Positive / No Risk**: the output point has no user input mapping, or control characters are effectively filtered and the proxy layer strictly intercepts. Output `False Positive` with the determination basis.

## Testing Recommendations and Minimal Trigger Conditions (Mandatory)

- **Minimal trigger conditions**:
  - a header / cookie / location output point exists
  - the output value contains user-controllable input (request parameters, file names, proxy headers, database fields)
  - control characters such as `\r\n` can reach the output point unfiltered
- **Test case suggestions**:
  - Happy Path: normal header values output correctly, and requests containing `\r\n` are intercepted or filtered
  - Boundary / ambiguity: double-encoding bypass, Unicode line separators (`\u2028` / `\u2029`), proxy passthrough header injection
- Each hit output appends `hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (output point confirmation)**: the real write-out points of headers / cookies / locations must be confirmed first.
- 🔴 **CHECKPOINT B (character chain confirmation)**: a three-segment evidence of `input -> header value -> control character filtering` must be given.
- 🔴 **CHECKPOINT C (proxy semantics confirmation)**: the differences in how Kestrel / IIS / proxy layers handle illegal headers must be stated.
- 🛑 **STOP**: if there are only keyword hits without output mapping evidence, the conclusion is downgraded to `⚠️Pending Verification`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| cannot close the input-to-header / cookie output mapping | complete the chain evidence from parameter sources to output APIs | downgrade to `⚠️Pending Verification`, retaining the suspicious point |
| control character filtering inconsistent with decode paths | verify the raw value, one decode, and double decode simultaneously | evaluate conservatively per the worst path; give no strong conclusion |
| proxy / host interception behavior unclear | record layer by layer, distinguishing Kestrel, IIS, and reverse proxies | only output environment-dependent conclusions and reproduction suggestions |

🔴 **STOP: when any fallback triggers, outputting "CRLF does not hold" is forbidden.**

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

- Anti-pattern: equating a header write point hit directly with a valid vulnerability. Correct practice: supplement input mapping and control character filtering evidence.
- Anti-pattern: ignoring encoding and double-decode paths. Correct practice: verify both raw values and decoded values.
- Anti-pattern: not distinguishing default interception capabilities of hosts / proxies. Correct practice: clarify the real behavior of the deployment chain.
- Anti-pattern: writing "no risk" with insufficient evidence. Correct practice: downgrade to `⚠️Pending Verification`.

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

- vuln_audit/crlf_{timestamp}.md
- Optional: vuln_poc/crlf_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
