---
name: node-csrf-audit
description: Node.js CSRF audit tool. Identifies cross-site submission risks in express-session sameSite configuration, self-built token validation after csurf (deprecated), origin/referer comparison, and state-changing endpoints; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js CSRF Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to state-changing entries, token generation and validation, origin/referer comparison, cookie SameSite, and exemption lists
- If the project has secondary encapsulations such as CsrfMiddleware, FormGuard, MutationProtector, or AdminActionGuard, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align state-changing entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, serialization configuration, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- State-changing endpoints (POST/PUT/PATCH/DELETE) with no CSRF protection at all: no token, no origin validation, no second confirmation
- `csurf` was marked deprecated by npm in 2022; existing references must be checked; self-built token solutions need their generate-transport-validate loop and exemption list verified
- When `express-session`'s `cookie.sameSite` is not set explicitly, it relies on browser defaults (Lax since Chrome 80+); Lax is not equivalent to protection: old kernels / Safari behave inconsistently, GET side-effect entries exist, and subdomain cookie injection can still bypass it
- `sameSite: 'none'` must be paired with `secure:true`, and cross-site requests will carry cookies
- Origin/referer validation flaws: `indexOf`/`startsWith` substring matching, allowing empty origins, not comparing protocol and port
- The mitigating effect of JSON POST + `application/json` content-type restriction (HTML forms cannot forge that content type) must be assessed together with the CORS policy
- Next.js Server Actions' built-in protection (POST-only + Origin/Host comparison); scenarios where low versions or custom fetch/API Route paths bypass the built-in protection
- Coverage of non-HTML-form submission surfaces such as NestJS Guards, GraphQL Mutations, and multipart uploads; sensitive operations like password change / fund transfer lacking second confirmation

## Enumeration Rules (Mandatory Refinement)

- Enumerate all state-changing routes: `app.post(`, `app.put(`, `app.patch(`, `app.delete(`, `router.post(`, `@Post(`, `@Put(`, `@Mutation(`, Server Actions (`"use server"`)
- Search first for `csurf`, `csrf(`, `csrfToken`, `_csrf`, `csrf-csrf`, `doubleSubmit`, `req.headers.origin`, `req.headers.referer`, `Sec-Fetch-Site`, `sameSite`, `cookie.sameSite`
- For each state-changing entry record: authentication method (Cookie/session), token generation and validation locations, middleware mount scope and exemption list, content-type branches, and whether it is cross-site reachable
- Enumerate the initialization configuration of `express-session`/`cookie-session` and the actually issued values of explicit `sameSite` parameters in `res.cookie(...)`
- Enumerate whether sensitive operations (password change, fund transfer, binding email/phone) have an independent second factor with server-side re-verification
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real route handler functions

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| CSRF token validation | Self-built token (csrf-csrf double-submit cookie), global middleware | Check whether middleware covers all state-changing routes, the generate-transport-validate loop, and exemption list contents | full coverage and fail-close (no token → rejected) → ✅ safe; exemption list contains state-changing routes or only some routes mounted → 🔴 high risk; mount order after authentication unconfirmable → ⚠️ to be verified |
| Origin/referer validation | `req.headers.origin`/`req.headers.referer` compared against a Host whitelist | Check whether comparison is strict equality, whether empty origins are rejected, and whether substring matching exists | strict equality and empty origins rejected → ✅ safe; `indexOf`/`startsWith` substring matching or empty values allowed → ⚠️ bypassable |
| SameSite cookie | `cookie.sameSite` of `express-session`, explicit parameters of `res.cookie` | Read the session middleware configuration and the actual Set-Cookie issued values | `strict` → ✅ safe; explicit `lax` → ⚠️ (GET side effects / subdomain injection can still bypass); `none` or unset relying on browser defaults → 🔴 high risk |
| Content-type restriction | `express.json()` accepting only `application/json` | Confirm the endpoint is JSON-only with no form/multipart compatibility branch, and CORS is not loosened | JSON-only with strict CORS → ✅ mitigated; accepting form/urlencoded/multipart → 🔴 high risk |
| Second confirmation | Password change / fund transfer / binding operations require password re-entry or verification codes | Check whether sensitive operations have a server-side re-verified second factor | server-side re-verification → ✅ safe; frontend confirmation only → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: a credential-carrying cross-site state-changing entry appears to be missing all CSRF protections
- `Pending`: the context shows a suspicious pattern (e.g., only SameSite=Lax), but token validation, origin comparison, or middleware coverage is unclear
- `False Positive`: protection is verified fail-close (full token coverage / strict origin equality), or the entry is read-only GET

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found of a credential-carrying cross-site state-changing entry without effective protection → `Confirmed Vulnerability`
- Evidence of full token coverage / strict origin validation fail-close is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_CSRF_STATE_CHANGE_ENDPOINT` + `EVID_NODE_CSRF_TOKEN_CHECK` (validation missing or bypass branch exists), with no origin/referer validation and no second confirmation
- Cookie session with `sameSite:'none'` or unset (`EVID_NODE_CSRF_COOKIE_SAMESITE`), and token validation missing or bypassable
- Origin validation is a fail-open implementation with substring matching / empty origins allowed, and an attack page can carry cross-site requests through the validation

### ⚠️Pending Verification

- Token middleware exists, but the mount scope / middleware order (`EVID_NODE_CFG_MIDDLEWARE_ORDER`) cannot be confirmed to cover all state-changing routes
- Explicit `SameSite=Lax` is set, but GET side-effect entries or subdomain cookie injection scenarios need further evidence
- Next.js Server Actions built-in protection depends on the `next` version; the current version and custom fetch call paths cannot be confirmed

### False Positive

- Pure GET read-only endpoints with no state-changing side effects
- Token validation covers all routes and is fail-close (`EVID_NODE_CSRF_TOKEN_CHECK` + `EVID_NODE_CSRF_COOKIE_SAMESITE` dual evidence closed), with no bypass branches
- The endpoint accepts only `application/json` with strict origin validation and CORS not loosened; sensitive operations have additional server-side re-verification (`EVID_NODE_CSRF_SECOND_CONFIRM` as corroboration)

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct cross-site auto-submitting forms / `fetch` no-cors requests: carrying cookies to trigger unprotected state-changing endpoints
- Verify that cross-site POSTs succeed in causing side effects under a `sameSite:'none'` session
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Requests without a token / with a wrong token / with an expired token are rejected (fail-close)
- Requests with a forged `Origin: https://evil.com` and empty origins are rejected by origin validation
- Verify that `text/plain` / form submissions cannot reach business logic under content-type restrictions

### Regression Testing

- Retest after remediation, confirming token middleware still covers all state-changing routes
- Retest that newly added routes do not miss protection and the exemption list has not grown
- Verify SameSite / origin whitelist changes remain fail-close

## Evidence References

- `EVID_NODE_CSRF_STATE_CHANGE_ENDPOINT`
- `EVID_NODE_CSRF_TOKEN_CHECK`
- `EVID_NODE_CSRF_COOKIE_SAMESITE`
- `EVID_NODE_CSRF_SECOND_CONFIRM`
- Optional overlays: `EVID_NODE_SESS_COOKIE_FLAGS` (full cookie flags), `EVID_NODE_CFG_MIDDLEWARE_ORDER` (CSRF middleware mount order)

## Output

- `node/vuln_audit/csrf_{timestamp}.md`
- `node/vuln_poc/csrf_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
