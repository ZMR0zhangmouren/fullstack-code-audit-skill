---
name: node-open-redirect-audit
description: Node.js open redirect audit tool. Identifies controllable redirect targets such as res.redirect(req.query.url) and Next.js redirect, plus normalization bypass risks with ///, \, and %2F; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js Open Redirect Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to redirect call sites, returnTo/redirect_uri parameters, target allowlists, and normalization variants
- If the project has secondary encapsulations such as RedirectHelper, LoginFlowService, NavigationGuard, or CallbackResolver, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align redirect entries, redirect parameters, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement authentication boundaries of login / logout / callback entries)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Targets taken directly from request parameters: `res.redirect(req.query.url)` / `res.redirect(req.body.returnTo)`
- Next.js `next/navigation` `redirect()` (Server Actions / Route Handlers) and `res.redirect` in `pages/api`
- `returnTo` / `next` / `continue` / `redirect_uri` / `callbackUrl` parameters in login / logout / OAuth callbacks
- Normalization bypass variants: `///evil.com`, `//evil.com`, `\evil.com`, `https:%2F%2F`, `\/\/evil.com`, `javascript:`, `data:`
- Whether the allowlist implementation is fail-close: out-of-whitelist falls back to a fixed page / throws, versus passing the raw value through
- Relative-path validation such as `startsWith('/')` that does not exclude protocol-relative (`//`) and backslash (`/\`) variants
- Scenarios where `req.headers.host` / `X-Forwarded-Host` participate in concatenating the redirect domain
- Payment callbacks, invitation links, and deep-link redirects carrying sensitive parameters such as tokens / codes off-site

## Enumeration Rules (Mandatory Refinement)

- Enumerate all redirect call sites: `res.redirect(`, `res.location(`, `res.writeHead(302`, `statusCode = 302`, `redirect(` (next/navigation), `successRedirect` (passport)
- Search first for `returnTo`, `returnUrl`, `redirect_uri`, `callbackUrl`, `req.query.next`, `req.query.redirect`, `req.query.continue`, `req.query.callback`
- Enumerate validation implementations: `new URL(`, `startsWith('/')`, `startsWith('http')`, `includes('http')`, allowlist array / Map comparison, and default fallback branches
- Enumerate business scenarios such as login, logout, OAuth callbacks, payment callbacks, invitation links, deep-link redirects, and error redirects
- For each redirect point record: target source, decode count, validation logic and comparison position, and sensitive parameters carried after the redirect

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Target allowlist | Domain whitelist array / Map comparison | Read the whitelist implementation source, confirming whether out-of-whitelist falls back to a fixed page or throws | fail-close (fallback to homepage / rejection) → ✅ safe; fail-open (allow by default / pass raw value through) → 🔴 high risk |
| Relative-path validation | `startsWith('/')` excluding `//` and `/\` | Verify validation executes after decoding and covers protocol-relative and backslash variants | all variants excluded → ✅ safe; `startsWith('/')` only → ⚠️ bypassable via `//evil.com`, `/\evil.com` |
| URL normalization | Parsing with `new URL()` and comparing `hostname` | Check whether `decodeURIComponent` precedes parsing, and whether comparison is structural or string-level | comparison after parsing → ✅ safe; string-level comparison → ⚠️ bypassable via encoded variants such as `https:%2F%2F` |
| Protocol restriction | http/https only | Enumerate whether `javascript:`/`data:`/`vbscript:` are explicitly rejected | explicitly rejected → ✅ safe; unrestricted → 🔴 high risk |
| Host header concatenation | `req.headers.host` / `X-Forwarded-Host` concatenating the redirect domain | Check whether the Host comes from a forgeable request header without validation | fixed domain constant → ✅ safe; direct request-header use → ⚠️ to be verified (depends on reverse-proxy overrides) |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter the redirect target slot directly
- `Pending`: the context shows a suspicious pattern, but the target source, allowlist behavior, or normalization chain is unclear
- `False Positive`: the target comes from fixed constants / enum mappings, or the allowlist has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found that externally controllable input enters the redirect target slot → `Confirmed Vulnerability`
- Fixed whitelist mapping / fail-close evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_REDIRECT_CALL` + `EVID_NODE_REDIRECT_TARGET_CONTROL`: the target comes directly from a request parameter with no validation, or fail-open validation
- An allowlist / relative-path validation exists but is bypassable via `//evil.com`, `\evil.com`, or encoded variants (`EVID_NODE_REDIRECT_ALLOWLIST_VALIDATE` + `EVID_NODE_REDIRECT_ENCODING_BYPASS` corroborate the reachable bypass path)
- The redirect chain carries login tickets / authorization codes to an external domain, and the validation is bypassable

### ⚠️Pending Verification

- The target source is partially controllable (e.g., only the Host header participates in concatenation), but reverse-proxy overrides and forgery feasibility cannot be confirmed
- An allowlist exists, but evidence of the decode count, `new URL` parsing order, and comparison position is insufficient
- A Next.js Route Handler redirect point exists, but the parameter source needs trace closure

### False Positive

- The redirect target comes from fixed constants / route names (e.g., `res.redirect('/dashboard')`)
- The allowlist is fail-close (out-of-whitelist always falls back to a fixed page), and normalization executes after decoding (`EVID_NODE_REDIRECT_ALLOWLIST_VALIDATE` + `EVID_NODE_REDIRECT_ENCODING_BYPASS` dual evidence closed)

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct `?next=//evil.com`, `?next=\/\/evil.com`, `?next=https:%2F%2Fevil.com`, `?next=javascript:alert(1)` and verify the actual redirect destination
- Verify whether codes / tokens are exfiltrated after tampering with the OAuth callback `redirect_uri`
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Out-of-whitelist domains and non-relative paths are rejected (fail-close)
- The `data:`/`javascript:` protocols are explicitly rejected
- Verify out-of-whitelist targets fall back to a fixed page rather than passing the raw value through

### Regression Testing

- Retest after remediation, confirming normalization variants (double slashes / backslashes / encoding) remain blocked
- Newly added redirect points integrate the unified validation function and remain fail-close
- Verify whitelist changes do not introduce wildcard subdomain allowances

## Evidence References

- `EVID_NODE_REDIRECT_CALL`
- `EVID_NODE_REDIRECT_TARGET_CONTROL`
- `EVID_NODE_REDIRECT_ALLOWLIST_VALIDATE`
- `EVID_NODE_REDIRECT_ENCODING_BYPASS`
- Optional overlay: `EVID_NODE_CFG_SECURITY_SWITCH` (framework / gateway-level redirect security switches)

## Output

- `node/vuln_audit/open_redirect_{timestamp}.md`
- `node/vuln_poc/open_redirect_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
