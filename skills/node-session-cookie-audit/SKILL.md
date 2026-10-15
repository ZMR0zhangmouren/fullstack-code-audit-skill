---
name: node-session-cookie-audit
description: Node.js session and cookie audit tool. Identifies risks such as JWT algorithm confusion, weak / hardcoded keys, missing cookie flags, and session lifecycle flaws; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js Session and Cookie Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to JWT signing / verification, cookie setting, session configuration, and session lifecycle
- If the project has secondary encapsulations such as AuthService, TokenManager, or SessionStore, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, serialization configuration, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **static-evidence-driven**: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- `jwt.verify` without pinned algorithms, exposing RS256→HS256 confusion or `alg:none` bypass risks
- Weak / hardcoded JWT keys, or insufficient key length
- Missing JWT expiration validation (`expiresIn` / `maxAge` not configured)
- Missing or misconfigured cookie triad (`HttpOnly` / `Secure` / `SameSite`)
- `express-session` using default names, weak secrets, or secure cookies not enabled
- `cookie-session` with weak signing keys or `signed` not enabled
- Incomplete logout: `req.session.destroy()` not called or client cookies not cleared

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites and configuration objects of `jwt.sign`, `jwt.verify`, `jsonwebtoken`, `jose`, `express-session`, `cookie-session`, `res.cookie(`, `sameSite`, `httpOnly`, `secure:`, `algorithms:`
- For each JWT call site record: algorithm options, key source, expiration, `aud`/`iss`/`sub` validation, and whether `none` is allowed
- For each Session / Cookie configuration point record: cookie flags, `secret`/`keys` sources, session name, expiration policy, and logout handling
- Check whether `jwt.verify` explicitly passes an `algorithms` array pinning the algorithm
- Check whether `jwt.sign` explicitly specifies `algorithm` and avoids `none`
- Check whether keys come from environment variables / KMS / Vault rather than hardcoded strings or short keys
- Check whether `res.cookie` sets `httpOnly`, `secure`, and `sameSite` simultaneously
- Check the length and source of the `express-session` `secret`, whether `name` is customized, and whether `cookie.secure` / `cookie.httpOnly` / `cookie.sameSite` are enabled
- Check whether `cookie-session` `keys` are strongly random and `signed` is `true`
- Check whether the session ID is regenerated after successful login (session fixation protection)
- Check whether the logout route calls `req.session.destroy()` and clears client cookies
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real JWT / Session / Cookie call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| algorithms array pinned | `jwt.verify(token, secret, { algorithms: ['HS256'] })` | Check whether verify / sign explicitly specifies the algorithm and rejects `none` | algorithm whitelist with none disabled → ✅ safe; `algorithms` not passed or `none` allowed → 🔴 high risk |
| Key from secure storage | Key from `process.env.JWT_SECRET` / KMS / Vault; sufficient length (HS256 ≥ 256 bits) | Check whether the key is hardcoded in source code or reversible | from secure storage with sufficient length → ✅ safe; hardcoded / short key / default secret → 🔴 high risk |
| Cookie triad complete | `res.cookie(name, value, { httpOnly: true, secure: true, sameSite: 'strict' })` | Check whether all cookie setting points configure HttpOnly, Secure, and SameSite simultaneously | all three correctly configured → ✅ safe; any missing → ⚠️ to be confirmed; all missing → 🔴 high risk |
| Session rotation / logout invalidation | `req.session.regenerate()` after login; `req.session.destroy()` + cookie clearing at logout | Check login / logout lifecycle handling | rotation at login and thorough logout → ✅ safe; no rotation or incomplete logout → ⚠️ to be confirmed |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: a JWT / Session / Cookie configuration flaw exists and is exploitable
- `Pending`: the context shows a suspicious pattern, but the configuration source, runtime value, or call chain is unclear
- `False Positive`: the configuration meets the security baseline, or the barrier has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found that the configuration flaw is exploitable → `Confirmed Vulnerability`
- Fixed security configuration / fail-close evidence is found → `False Positive`
- A key call chain or runtime configuration is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG` together with any of `EVID_NODE_SESS_JWT_ALG_PINNED`, `EVID_NODE_SESS_SECRET_SOURCE`, `EVID_NODE_SESS_COOKIE_FLAGS`, or `EVID_NODE_SESS_LIFECYCLE`, where the flaw is exploitable
- `jwt.verify` does not pass `algorithms`, or allows `none`, enabling RS256→HS256 confusion
- The JWT key is a hardcoded short string or publicly obtainable
- Cookies missing `HttpOnly` / `Secure` / `SameSite`, enabling XSS theft / CSRF carriage
- `express-session` uses the default `name`, a weak `secret`, or has secure cookie options disabled
- Logout does not call `req.session.destroy()`, leaving the server-side session valid

### ⚠️Pending Verification

- A configuration item (e.g., `secret`) references an environment variable, but whether the actual runtime value is strong enough cannot be confirmed
- Production / development branches affect the cookie `secure` setting, and the deployment environment cannot be confirmed statically
- A wrapper layer exists, and the actual options received by the underlying JWT library cannot be confirmed

### False Positive

- `jwt.verify` explicitly pins `algorithms` and rejects `none`
- The key comes from secure storage with length meeting algorithm requirements
- All cookies correctly set `HttpOnly` / `Secure` / `SameSite`
- The session ID is regenerated after login, and logout thoroughly destroys the session and clears client cookies

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct an RS256→HS256 algorithm confusion attack: sign a token using the public key as the HMAC key and submit it
- Construct an `alg:none` JWT and verify whether the server accepts it
- Construct expired / invalid-signature tokens and verify rejection logic
- Verify that cookies without `HttpOnly` can be read by scripts in XSS scenarios
- Verify whether cookies without `SameSite` are carried in cross-site requests
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Submit a correctly signed token and verify it passes normally
- Submit algorithm-confusion / `alg:none` / expired tokens and verify rejection
- Verify `Secure` cookies transmit normally over HTTPS and are not sent over HTTP

### Regression Testing

- Retest after remediation, confirming `algorithms` is pinned and `none` is rejected
- Retest the key rotation process, confirming no hardcoded keys were reintroduced
- Verify cookie flags and session lifecycle stay consistent in newly added routes

## Evidence References

- `EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG`
- `EVID_NODE_SESS_JWT_ALG_PINNED`
- `EVID_NODE_SESS_SECRET_SOURCE`
- `EVID_NODE_SESS_COOKIE_FLAGS`
- `EVID_NODE_SESS_LIFECYCLE`

## Output

- `node/vuln_audit/session-cookie_{timestamp}.md`
- `node/vuln_poc/session-cookie_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
