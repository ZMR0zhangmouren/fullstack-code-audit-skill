---
name: dotnet-ldap-audit
description: .NET LDAP injection audit tool. Identifies injection risks in DirectorySearcher, PrincipalContext, and custom LDAP Filter / DN string concatenation.
---

# .NET LDAP Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to LDAP filters, directory queries, binds, search bases, attribute mapping, and authentication bypass
- If the project has secondary encapsulations such as DirectoryService, AuthAdapter, PrincipalHelper, or SyncConnector, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align login / directory query entries, parameter sources, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement authentication integration, host configuration, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- string concatenation of DirectorySearcher.Filter: user input not escaping LDAP metacharacters (*, (, ), \, NUL)
- DN (Distinguished Name) concatenation: user input entering RDN components such as CN= and OU=
- filter parameter sources of PrincipalContext / PrincipalSearcher
- controllability of the filter and baseDN parameters of SearchRequest
- LDAP bind in login validation: user name injection causing authentication bypass
- filter construction in organization tree browsing, user search, and group membership queries
- LDAP queries and attribute mapping in SSO / SAML integration

## Evidence References

- EVID_LDAP_EXEC_POINT
- EVID_LDAP_FILTER_STRING_CONSTRUCTION
- EVID_LDAP_USER_PARAM_TO_FILTER_FRAGMENT

## Enumeration Rules (Mandatory Refinement)

- Enumerate DirectorySearcher, PrincipalSearcher, SearchRequest, SearchResponse, custom LDAP clients, and authentication services
- Search key fields such as Filter, DistinguishedName, baseDn, searchRoot, PrincipalContext, and group search first
- Enumerate LDAP queries and DN construction positions in login, user search, organization tree browsing, sync tasks, role mapping, and SSO integration
- For each LDAP call site record: filter source, escaping strategy, bind method, search scope, and how query results participate in authentication and authorization

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Filter string concatenation** | Read the construction source of `DirectorySearcher.Filter` or `SearchRequest.Filter`, confirming whether it comes from string concatenation / interpolation | user input participating in Filter concatenation without RFC 4515 escaping → 🔴 high risk; fixed Filter template + parameterized value slots → 🟠 value-slot boundary to be confirmed |
| **DN (Distinguished Name) concatenation** | Confirm whether user input enters the concatenation of RDN components such as CN=, OU=, and DC= | user input entering DN concatenation without RFC 4514 escaping → 🔴 high risk; fixed DN paths → ✅ safe |
| **RFC 4515 / 4514 escaping** | Read the escape function implementation source, confirming whether LDAP metacharacters (`*`, `(`, `)`, `\`, NUL) are handled | complete escaping and fail-close → ✅ safe; partial escaping or escaping before concatenation → ⚠️ bypassable; no escaping → 🔴 high risk |
| **Bind mode and authentication usage** | Distinguish authentication bind from search query scenarios; confirm whether the user name is controllable in bind scenarios | controllable user name in authentication bind → 🔴 high risk (authentication bypass); controllable Filter in search queries → 🟠 impact surface to be assessed |
| **Search scope and attribute whitelist** | Confirm whether `SearchScope` and query attributes come from user input and are restricted to the expected range | users can broaden the search scope or read sensitive attributes → 🔴 high risk; fixed scope with fail-close attribute whitelist → ✅ safe |
| **LDAP queries in SSO / SAML integration** | Confirm whether LDAP queries in SSO / SAML integration send external assertion / token content directly into the Filter | external assertion content entering the Filter directly → 🔴 high risk; validation layer present and fail-close → ✅ safe |

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

1. user-controllable input enters Filter / DN string concatenation positions directly, without RFC 4515 / 4514 escaping
2. LDAP metacharacters (`*`, `(`, `)`, `\`, NUL) enter Filter construction without escaping
3. in authentication bind scenarios, the user name comes from user-controllable input, enabling authentication bypass
4. the escape function is fail-open or silent-fallback, bypassable via encoding / double escaping
5. in nested / recursive structures (such as multi-layer DirectoryService wrappers), the top level has validation but sub-levels do not perform equivalent validation

### Pending

1. the context shows a suspicious pattern (such as a `DirectorySearcher` call), but the external input source is unclear (trace or call chain needs to be supplemented)
2. a barrier function (such as the RFC escape function) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
3. parameter passing in asynchronous / queue / event chains (such as background sync tasks) is not closed
4. LDAP query chains in SSO / SAML integration are complex, and the mapping from external assertions to the Filter is not fully closed

### False Positive

1. the final Filter / DN comes from fixed constants / enum mappings, and unknown input is refused execution (fail-close)
2. all recursive levels reuse the same RFC escape function, and the escape function is fail-close
3. user input enters only strictly escaped value slots, and escaping completes before string concatenation
4. search scope and attribute lists are fully fixed, and users cannot control query boundaries

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct LDAP injection payloads (such as `*)(uid=*))(&(uid=*`, `admin*)(objectClass=*`, `cn=admin\00`) and verify injection / authentication bypass really exists
- **Negative testing**: construct inputs intercepted by barriers (such as unescaped metacharacters properly escaped, illegal DN formats rejected) and verify the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (query point confirmation)**: the LDAP execution points and bind methods must be confirmed.
- 🔴 **CHECKPOINT B (filter mapping confirmation)**: the mapping from inputs to Filter / DN fragments must be given.
- 🔴 **CHECKPOINT C (escaping strategy confirmation)**: whether RFC escaping and whitelist strategies take effect must be stated.
- 🛑 **STOP**: if Filter controllability evidence is not closed, the conclusion is downgraded to `⚠️Pending Verification`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| LDAP execution point clear but input mapping unclear | complete the mapping from parameters to Filter / DN fragments | downgrade to `⚠️Pending Verification` |
| RFC escaping strategy unverifiable | verify the 4514 / 4515 encoding implementation and boundaries | no exploitable strong conclusion; give verification steps only |
| bind mode and query usage not distinguished | evaluate authentication / search / sync scenarios separately | adopt a conservative conclusion and retain pending items |

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

- Anti-pattern: judging injection upon hitting only an LDAP API. Correct practice: prove that input enters key Filter / DN fragments.
- Anti-pattern: ignoring RFC 4515 / 4514 escaping differences. Correct practice: clarify the escaping strategy and bypass surface.
- Anti-pattern: not verifying bind mode and query usage. Correct practice: distinguish the different risk semantics of authentication, search, and sync.
- Anti-pattern: writing "exploitable" with incomplete evidence. Correct practice: downgrade to `⚠️Pending Verification`.

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

- vuln_audit/ldap_{timestamp}.md
- Optional: vuln_poc/ldap_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
