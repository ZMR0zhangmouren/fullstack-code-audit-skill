---
name: node-koa-audit
description: Node.js Koa framework specialty audit tool. Performs white-box audits of the framework boundary, runtime configuration, and control plane of Koa applications — onion-model middleware chains, ctx passing, body parsing, and error handling.
---

# Koa Framework Specialty Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the Koa-related grabbers of middleware chains (onion model), ctx data passing, body parsing, static directories, and session / security header configuration
- If the project has Koa secondary encapsulations such as app.use combiners, middleware factories, or ctx enhancement extensions, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (core input of this specialty: confirm onion chain registration order and `await next()` short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to align anonymous entries, P0/P1 bucketing, and authentication middleware coverage)
- Optional: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` (used to cross-reference ctx data flow / middleware risks with specific entries and side-effect chains)
- Optional: `node/vuln_audit/*_{timestamp}.md` (used to corroborate with vulnerability specialties such as xss / session-cookie / file-upload)
- Optional: `cross/api_contract_map_{timestamp}.md` (used to align BFF forwarding or isomorphic parameter sources)

## Key Checks

- Onion-model short-circuit flaws: authentication / security middleware not calling `await next()` or registered after routes → subsequent middleware and handlers skipping authentication entirely
- `ctx.onerror` default handling: without custom error catching, non-production environments output stacks and internal paths to responses by default (fail-open)
- `koa-body` / `koa-bodyparser` without size limits (the default 1mb needs confirmation) or overly broad multipart configuration → oversized request bodies / wrong Content-Type parsing surface
- `koa-static` root directory controllable, `index` / `hidden` options enabled, or placed before authentication → directory exposure / sensitive file reads
- CORS wildcard (`@koa/cors` `origin: '*'`) combined with `credentials` → arbitrary cross-origin cookie carriage
- `koa-session` configuration flaws: default `key`, `signed` not enabled, `cookie.secure` unset, improper rolling renewal policy
- `ctx.state` global shared data injection points and downstream consumption surfaces (coordinating with vuln specialties)
- `ctx.request.body` accessed before the parser is mounted → undefined silently passing through (fail-open)

## Enumeration Rules (Mandatory Refinement)

### 1. Framework Boundary Layer

- Enumerate middleware chain registration: record onion layers of `app.use(...)` in registration order; annotate whether each layer calls `await next()` and whether there are conditional short-circuits (direct return via `return ctx.body = ...`)
- Enumerate route access styles: `koa-router` (`router.get/post`, `router.allowedMethods`), `@koa/router`, custom route dispatch middleware
- Enumerate static directories: the `root` source of `koa-static(root, options)` (hardcoded / environment variables / user input), `index`, `hidden`, `defer` options, and position relative to authentication middleware
- Identify request lifecycle boundaries: request → outer onion layer → handler → inner onion layer → response; annotate `ctx.body` direct assignment output points (for the XSS specialty)
- Identify framework default behaviors: 404 catch-all, `ctx.onerror` default error handling (stack leakage surface)

### 2. Runtime Configuration Layer

- Enumerate `process.env`, `dotenv`, `.env` read points and sensitive items (secret, token, DB connection strings)
- Enumerate body parsing configuration: `koa-bodyparser({ limit, onerror })`, `koa-body` (multipart / limits / formidable options), parser mount positions
- Enumerate ctx data binding: injection points of `ctx.query`, `ctx.params`, `ctx.request.body`, `ctx.headers`, `ctx.state`
- Enumerate session configuration: `koa-session` (`key` / `signed` / `cookie.secure` / `rolling` / store), cookie options
- Enumerate security headers and CORS configuration: helmet / koa-helmet, `@koa/cors`, CSP, HSTS
- If secondary encapsulations such as middleware combiners or ctx enhancement exist, they must be unwrapped layer by layer to the real `app.use` / parser call sites

### 3. Precondition Control Plane Layer

- Enumerate authentication coverage: whether `passport` (ctx.state.user), `koa-jwt`, or custom authentication middleware are mounted globally at the outer onion layer or only on some routes
- Identify route-level authentication gaps: compare the route list with authentication middleware coverage; mark uncovered routes and dynamically registered routes
- Enumerate rate limiting: configurations such as `koa-ratelimit` and their linkage with the `ctx.ip` source (reverse-proxy IP forgery bypassing rate limits)
- Enumerate request size limits: body `limit`, multipart upload limits (`maxFileSize` / `maxFields` of `formidable`)

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Onion order | authentication middleware `app.use` before routes and `await next()` passage | List middleware layer by layer in registration order; check the position of the authentication layer relative to the route layer and whether `await next()` is unconditional | authentication as the outermost layer with no bypass after passage → ✅ safe; authentication mounted after routes or conditional short-circuit → 🔴 high risk |
| Parser limits | `koa-bodyparser({ limit: '1mb' })` | Check body parser `limit` / multipart options and mount positions | explicit `limit` with tightened multipart restrictions → ✅ safe; `limit` not configured or multipart unrestricted → ⚠️ to be confirmed |
| Authentication coverage | outer-layer global authentication middleware or per-route `koa-jwt` | Compare the route list with authentication middleware coverage, including dynamically registered routes | global or per-route fail-close → ✅ safe; reachable unauthenticated routes exist → 🔴 high risk |
| onerror stack leakage | custom `app.on('error')` / error middleware catching and sanitizing responses | Check whether the `ctx.onerror` default behavior is overridden and whether responses contain stacks / internal paths | errors caught and responses sanitized → ✅ safe; relying on `ctx.onerror` default output → 🔴 stack leakage (fail-open) |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Risk Candidate`: missing framework configuration or control plane may allow external input to bypass, privilege escalation, or sensitive information exposure
- `Pending`: the context shows a suspicious pattern, but the entry coverage, barrier behavior, or call chain is unclear
- `False Positive`: the configuration has fail-close explicitly enabled, or the risk point is already covered by another control plane

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found linking the framework control plane to a specific entry / sink → `Confirmed Risk`
- Fixed whitelist mapping / fail-close evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_CFG_MIDDLEWARE_ORDER` shows authentication middleware registered after routes or a short-circuit layer without `await next()`, with protected entries reachable
- The `ctx.onerror` default behavior is not overridden, and error responses output stacks and internal paths (`EVID_NODE_CFG_ERR_HANDLER`)
- The `koa-static` root source is controllable or `index` / `hidden` expose directories, with an accessible URL (`EVID_NODE_CFG_SECURITY_SWITCH`)
- `@koa/cors` wildcard + `credentials` combination, with a protected interface carrying cookies (`EVID_NODE_CFG_SECURITY_SWITCH`)
- The body parser is not mounted or has no `limit`, while handlers directly consume `ctx.request.body` (silent undefined passthrough / oversized request bodies entering parsing) (`EVID_NODE_CFG_RUNTIME_SETTING`; for the koa-body multipart configuration surface see `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG`)

### ⚠️Pending Verification

- Onion chain coverage unclear: authentication middleware has conditional short-circuit branches (no uniform `await next()`), and not all paths can be confirmed statically
- `ctx.ip` / rate limiting depends on the deployment environment (whether the reverse proxy passes through the source IP), which cannot be confirmed statically
- `koa-session`'s `signed` / `cookie.secure` are enabled only in the production branch (HTTPS condition), and the deployment environment cannot be confirmed statically
- Whether error responses leak stacks depends on the runtime `NODE_ENV` value, which cannot be confirmed statically

### False Positive

- The authentication middleware is the outermost onion layer with unconditional `await next()` passage, rejecting unauthenticated requests directly
- Custom `app.on('error')` / error middleware is registered and responses are sanitized (no stacks / internal paths)
- CORS not wildcarded and not carrying `credentials`; helmet / koa-helmet enabled at all mount points
- `koa-static` root hardcoded and fixed, `index: false`, and placed after authentication

## Testing Recommendations (Mandatory)

### Positive Testing

- Request a protected route without authentication → should be rejected (401 / 403), verifying onion chain coverage
- Construct over-limit body / over-limit multipart requests → should return 413 / 400 rather than entering the handler
- Trigger an exception request → the response should be a sanitized error page without stacks / internal paths
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Legitimate requests pass through the complete onion chain (authentication + rate limit + parsing) and return normally
- Body / upload requests within normal limits work and are not wrongly rejected
- In production mode (`NODE_ENV=production`), error responses do not leak stacks

### Regression Testing

- Re-verify authentication coverage and static directory position after onion layer registration order changes
- Newly added routes must be included in the authentication coverage list before retesting
- Retest stack leakage and 413 behavior after error handling / body parser changes

## Evidence References

- `EVID_NODE_CFG_MIDDLEWARE_ORDER`
- `EVID_NODE_CFG_ERR_HANDLER`
- `EVID_NODE_CFG_SECURITY_SWITCH`
- `EVID_NODE_CFG_RUNTIME_SETTING`
- `EVID_NODE_SESS_COOKIE_FLAGS` (koa-session configuration surface, coordinating with node-session-cookie-audit)
- `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG` (koa-body multipart configuration surface, coordinating with node-file-upload-audit)

## Output

- `node/framework_audit/koa_{timestamp}.md`
- Must state: onion middleware chain registration order and short-circuit conditions, ctx data binding and `ctx.state` injection surface, static directory exposure surface, runtime configuration (body limit / session / CORS), authentication coverage and uncovered routes
- Must state environment differences: `NODE_ENV` branches, `ctx.ip` reverse-proxy dependencies, production / development configuration differences
- Consumption relationships: when affecting strong vulnerability conclusions, it must be explicitly stated how it is consumed by `node/route_tracer`, each `node-vuln-audit` specialty (xss / session-cookie / file-upload, etc.), and `node-audit-pipeline`
