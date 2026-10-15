---
name: dotnet-session-cookie-audit
description: .NET session, cookie, and JWT audit tool. Identifies cookie flags, authentication ticket rotation, JWT validation parameter, and logout cleanup flaws.
---

# .NET Session / Cookie / JWT Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to sessions, cookies, JWTs, ticket attributes, renewal, logout, and cross-site behavior
- If the project has secondary encapsulations such as TokenService, CookieHelper, SessionManager, or AuthCookieFactory, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align login, logout, and ticket update entries with `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to supplement authentication state, anonymous entries, and permission boundaries)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

Key checks:

- cookie flags: HttpOnly, Secure, SameSite, Domain, Path, IsEssential, Persistent, SlidingExpiration, and cross-subdomain sharing policies
- whether authentication tickets, session ids, correlation cookies, and antiforgery tokens are rotated after login, privilege escalation, 2FA completion, tenant switching, and impersonation
- consistency of ASP.NET Core Identity, CookieAuthentication, SessionMiddleware, DataProtection key rings, and distributed cache sessions
- TokenValidationParameters, signature algorithms, kid selection, key rotation, issuer / audience, exp / nbf, clock skew, and refresh token management
- boundary issues when JWTs, cookies, sessions, remember-me, external login callbacks, device trust, and stateless APIs are mixed
- whether logout cleans up client cookies, server-side sessions, refresh tokens, server caches, SignalR connection states, and background persistent sessions

## Key Checks

- cookie flags: whether HttpOnly, Secure, and SameSite are correctly configured
- session fixation: whether the Session ID / authentication ticket is rotated after login
- JWT validation: signature algorithm whitelist, exp / nbf / iss / aud validation, ClockSkew settings
- logout cleanup: whether cookies, sessions, and refresh tokens are all invalidated
- refresh tokens: storage location, rotation policy, and revocation mechanism
- cross-domain / cross-subdomain cookie sharing: session leakage caused by overly broad Domain settings
- remember me / persistent cookies: security and revocability of long-term tickets
- sliding expiration: whether SlidingExpiration causes sessions to never expire

## Evidence References

- EVID_SESS_COOKIE_FLAGS
- EVID_SESS_TICKET_REGEN_ROTATION
- EVID_SESS_JWT_VERIFY_CLAIMS
- EVID_SESS_LOGOUT_CLEAR

## Enumeration Rules (Mandatory Refinement)

- Enumerate all CookieAuthentication, SessionMiddleware, Identity, JwtBearer, RefreshToken, RememberMe, and Persistent Cookie configurations and usage points
- Search HttpOnly, SecurePolicy, SameSite, ExpireTimeSpan, SlidingExpiration, SaveTokens, TokenValidationParameters, and refresh token tables / caches first
- Enumerate ticket update paths after login, privilege escalation, tenant switching, 2FA completion, external login callbacks, and password resets
- For each session mechanism record: ticket type, storage location, rotation timing, logout cleanup path, and whether it is shared across subdomains / applications

## Barrier Verification Matrix (Mandatory)

Evaluate per the fail-close three-level standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Level | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Level 1 | session / cookie / JWT mechanism exists and is actually used | CookieAuthentication / SessionMiddleware / JwtBearer exist and are actually used in the authentication flow | BLOCKED → no session / cookie / JWT usage; the specialty ends |
| Level 2 | security attributes missing or misconfigured | HttpOnly / Secure / SameSite missing, TokenValidationParameters loose, SlidingExpiration never expiring | BLOCKED → security attributes correctly configured; the conclusion is downgraded |
| Level 3 | rotation / logout cleanup flaws enabling session fixation or hijacking | tickets not rotated after login privilege escalation, logout not cleaning client / server / refresh tokens | PARTIAL → only output potential risks and verification steps |

## Two-Phase Determination Process (Mandatory)

- **Phase 1 (initial screening hit)**: hit CookieAuthentication / SessionMiddleware / JwtBearer + security attribute configuration + rotation / logout paths, and output `hit ID: M{hash}`.
- **Phase 2 (refined confirmation)**:
  1. back-trace the login → ticket generation → transmission → validation → logout cleanup chain;
  2. verify security attribute configurations such as cookie flags, TokenValidationParameters, and SlidingExpiration;
  3. assess the completeness of ticket rotation after login privilege escalation and logout cleanup (client / server / refresh tokens);
  4. if all three-level Barriers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priorities (Mandatory)

1. **Confirmed Vulnerability**: session mechanism used + security attributes missing + rotation / logout cleanup flaws enabling exploitation. Output `Confirmed Vulnerability`.
2. **Pending**: the session mechanism exists but security attribute or rotation / logout evidence is partially missing. Output `Pending`.
3. **False Positive / No Risk**: session mechanism security attributes complete (HttpOnly / Secure / SameSite / Strict), TokenValidationParameters strict, and rotation and logout cleanup complete. Output `False Positive` with the determination basis.

## Testing Recommendations and Minimal Trigger Conditions (Mandatory)

- **Minimal trigger conditions**:
  - CookieAuthentication / SessionMiddleware / JwtBearer usage exists
  - cookie flags missing or TokenValidationParameters loose
  - or tickets not rotated after login privilege escalation, or refresh tokens not cleaned at logout
- **Test case suggestions**:
  - Happy Path: normal login / logout flows with complete ticket rotation and cleanup
  - Boundary / ambiguity: cross-site requests carrying SameSite=None cookies, SlidingExpiration never expiring, JWT none / HS256 algorithm confusion, and missing refresh token reuse detection
- Each hit output appends `hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Evidence References

- EVID_SESS_COOKIE_FLAGS
- EVID_SESS_TICKET_REGEN_ROTATION
- EVID_SESS_JWT_VERIFY_CLAIMS
- EVID_SESS_LOGOUT_CLEAR

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (ticket attribute confirmation)**: key security attributes of cookies / JWTs / sessions must be confirmed.
- 🔴 **CHECKPOINT B (rotation and renewal confirmation)**: ticket rotation behavior after login, privilege escalation, and tenant switching must be confirmed.
- 🔴 **CHECKPOINT C (logout cleanup confirmation)**: both client-side and server-side sessions must be confirmed invalidated.
- 🛑 **STOP**: if rotation or logout evidence is not closed, the conclusion is downgraded to `⚠️Pending Verification`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| ticket attribute evidence incomplete | complete cookie / JWT / session security attribute configurations | downgrade to `⚠️Pending Verification` |
| rotation chain after login privilege escalation unclosed | trace the session / token rotation execution points | no "session secure" strong conclusion |
| logout cleanup chain missing (client / server) | complete cookie / session / refresh token revocation evidence | assess conservatively and list pending evidence |

🔴 **STOP: when any fallback triggers, outputting "no session risk" is forbidden.**

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

- Anti-pattern: judging session security based only on cookie flags. Correct practice: also verify rotation, revocation, and logout cleanup.
- Anti-pattern: ignoring refresh token lifecycles. Correct practice: verify storage, rotation, revocation, and reuse detection.
- Anti-pattern: treating cross-subdomain sharing as acceptable by default. Correct practice: restrict Domain / Path to the minimal scope.
- Anti-pattern: declaring "no session risk" with insufficient evidence. Correct practice: downgrade to `⚠️Pending Verification`.

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

- vuln_audit/sess_{timestamp}.md
- Optional: vuln_poc/sess_{timestamp}.md (if reproducible requests, configuration verification steps, or environment-dependent verification chains can be constructed)
