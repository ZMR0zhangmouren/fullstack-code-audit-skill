---
name: node-express-audit
description: Node.js Express framework specialty audit tool. Performs white-box audits of the framework boundary, runtime configuration, and control plane of Express applications — entry registration, middleware chains, static directories, and runtime configuration.
---

# Express Framework Specialty Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the Express-related grabbers of entry definitions (app / express.Router registration), middleware chain order, static directories, parsers, and session / security header configuration
- If the project has Express secondary encapsulations such as createApp(), middleware combiners, or route factories, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (core input of this specialty: confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to align anonymous entries, P0/P1 bucketing, and authentication coverage)
- Optional: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` (used to cross-reference middleware / parser risks with specific entries and side-effect chains)
- Optional: `node/vuln_audit/*_{timestamp}.md` (used to corroborate with vulnerability specialties such as ssti / xss / session-cookie)
- Optional: `cross/api_contract_map_{timestamp}.md` (used to align SSR, BFF forwarding, or isomorphic parameter sources)

## Key Checks

- Middleware chain order flaws: authentication / security middleware registered after routes; static directories or sensitive routes executing before authentication
- Missing error middleware or not using the 4-argument signature: Express default error handler outputs stacks and internal paths outside production (fail-open)
- `express.static` root directory controllable, `dotfiles` / directory listing enabled, or placed before authentication → arbitrary file reads / directory exposure
- `express.json` / `express.urlencoded` without `limit` / `type` configured → oversized request bodies or wrong Content-Type parsing surface
- Overly broad `trust proxy` configuration → `req.ip` forgeable, bypassing IP whitelists and rate limits
- view engine (ejs / pug / handlebars) rendering user-controllable templates or unescaped data → coordinate with node-ssti-audit
- Missing helmet, CORS wildcard + `credentials` combination → missing security headers / arbitrary cross-origin
- Route-level authentication missing: passport / express-jwt not covering some routers or dynamically registered routes

## Enumeration Rules (Mandatory Refinement)

### 1. Framework Boundary Layer

- Enumerate entry definition styles: `app.get/post/put/delete/all`, `app.use`, `express.Router()` and `router.get/post/use`, dynamic route registration (`forEach` / loop `app.use`, `app.use(router)` mounting, `app.all('*')` catch-all)
- Enumerate middleware chain order and short-circuit conditions: record the `app.use` chain in registration order; whether `next()` is called, conditional allow branches, chain breakpoints after `res.end()` / `res.send()`
- Enumerate static directories: the `root` source of `express.static(root, options)` (hardcoded / environment variables / user input), `dotfiles`, `index`, the `serve-index` middleware, and position relative to authentication middleware
- Identify request lifecycle boundaries: req → middleware → handler → response; annotate direct `res.send` concatenation output points (for the XSS specialty)
- Identify framework default behaviors: 404 catch-all, default error handling (stack leakage surface), `NODE_ENV` branch behavior

### 2. Runtime Configuration Layer

- Enumerate `process.env`, `dotenv`, `.env` read points and sensitive items (secret, token, DB connection strings)
- Enumerate body parsing configuration: `express.json({ limit, type })`, `express.urlencoded`, `raw` / `text` parsers
- Enumerate `app.set('trust proxy', ...)` configuration values and `req.ip` / `req.ips` usage points
- Enumerate view engine: `app.set('view engine')`, `app.set('views')`, `res.render` call sites (coordinate with node-ssti-audit)
- Enumerate session and cookie configuration: `express-session` (`secret` / `cookie` options / `name`), `cookie-parser` (`signed` key)
- Enumerate security headers and CORS configuration: helmet, `cors({ origin, credentials })`, CSP, HSTS
- If secondary encapsulations such as createApp(), middleware combiners, or route factories exist, they must be unwrapped layer by layer to the real `app.use` / route call sites

### 3. Precondition Control Plane Layer

- Enumerate authentication coverage: whether `passport.initialize()` / `passport.authenticate`, `express-jwt`, or custom auth middleware are globally `app.use` or mounted only on some routes
- Identify route-level authentication gaps: compare the route list with authentication middleware coverage; mark uncovered routers and dynamically registered routes
- Enumerate rate limiting: `express-rate-limit` configuration and its linkage with `trust proxy` (IP forgery bypassing rate limits)
- Enumerate request size limits: body `limit`, and `limits` / `fileFilter` of upload middleware such as multer

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Middleware order | `app.use(auth)` registered before `app.use(routes)` | List middleware item by item in registration order; check the position of authentication / security middleware relative to routes and static directories, and short-circuit conditions | authentication before protected surfaces with unconditional passage → ✅ safe; authentication mounted after routes or conditionally allowing → 🔴 high risk |
| Parser limits | `express.json({ limit: '1mb', type: 'application/json' })` | Check body parser `limit` / `type` configuration and mount points | explicit `limit` with tightened `type` → ✅ safe; `limit` not configured or `type: '*/*'` → ⚠️ to be confirmed |
| Authentication coverage | `app.use(requireAuth)` or per-route `authMiddleware` | Compare the route / middleware list with authentication coverage, including dynamically registered routes | global or per-route fail-close → ✅ safe; reachable unauthenticated routes exist → 🔴 high risk |
| Error handling | `app.use((err, req, res, next) => ...)` 4-argument signature | Check whether a 4-argument error middleware is registered and whether responses contain stacks / internal paths | custom error middleware with sanitized responses → ✅ safe; missing or non-4-argument signature → 🔴 default stack leakage (fail-open) |
| Static directory exposure | `express.static(path.join(__dirname, 'public'))` | Check the `root` source, `dotfiles` / `index` options, and position relative to authentication middleware | `root` fixed with no directory listing and placed after authentication → ✅ safe; `root` controllable or directory exposed → 🔴 high risk |

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

- `EVID_NODE_CFG_MIDDLEWARE_ORDER` shows authentication middleware placed after routes / static directories, with protected entries reachable (configuration missing + entry reachable)
- The 4-argument error middleware is missing, and when `NODE_ENV !== 'production'` the default error response outputs stacks and internal paths (`EVID_NODE_CFG_ERR_HANDLER`)
- The `express.static` root source is controllable or exposes sensitive directories, with an accessible URL (`EVID_NODE_CFG_SECURITY_SWITCH`)
- CORS wildcard + `credentials: true` combination, with a protected interface carrying cookies (`EVID_NODE_CFG_SECURITY_SWITCH`)
- The body parser has no `limit` with reachable entries, and there are oversized request / wrong Content-Type handling paths (`EVID_NODE_CFG_RUNTIME_SETTING`)

### ⚠️Pending Verification

- Middleware coverage unclear: authentication middleware has conditional allow branches (`next()` not uniformly called), and not all paths can be confirmed statically
- `trust proxy` depends on the deployment environment (whether the reverse proxy sets `X-Forwarded-For`), and `req.ip` trustworthiness cannot be confirmed statically
- helmet is only enabled at the entry app.js, but independent instances of sub-app mounting / secondary encapsulation cannot be confirmed statically
- Whether error responses leak stacks depends on the runtime `NODE_ENV` value, which cannot be confirmed statically

### False Positive

- Authentication middleware is global `app.use` before all routes and fail-close (unauthenticated requests directly rejected)
- The 4-argument error middleware is registered and the response content is sanitized (no stacks / internal paths)
- helmet enabled at all mount points, CORS not wildcarded and not carrying `credentials`
- `express.static` root hardcoded and fixed, placed after authentication

## Testing Recommendations (Mandatory)

### Positive Testing

- Request a protected route without authentication → should be rejected (401 / 403), verifying authentication coverage
- Construct an over-limit body (exceeding `limit`) request → should return 413 rather than entering the handler
- Trigger an exception request → the response should be a sanitized error page without stacks / internal paths
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Legitimate requests pass through the complete middleware chain (authentication + rate limit + parsing) and return normally
- Body / upload requests within normal limits work and are not wrongly rejected
- In production mode (`NODE_ENV=production`), error responses do not leak stacks

### Regression Testing

- Re-verify authentication coverage and static directory position after middleware order changes
- Newly added routes must be included in the authentication coverage list before retesting
- Retest stack leakage and 413 behavior after error middleware / body parser changes

## Evidence References

- `EVID_NODE_CFG_MIDDLEWARE_ORDER`
- `EVID_NODE_CFG_SECURITY_SWITCH`
- `EVID_NODE_CFG_ERR_HANDLER`
- `EVID_NODE_CFG_RUNTIME_SETTING`
- `EVID_NODE_SESS_COOKIE_FLAGS` (express-session / cookie-parser configuration surface, coordinating with node-session-cookie-audit)
- `EVID_NODE_SSTI_RENDER_POINT` (view engine rendering surface, coordinating with node-ssti-audit)

## Output

- `node/framework_audit/express_{timestamp}.md`
- Must state: entry types and mount styles (app / router / dynamic registration), middleware chain order and short-circuit conditions, static directory exposure surface, runtime configuration (body limit / trust proxy / session / CORS / view engine), authentication coverage and uncovered routes
- Must state environment differences: `NODE_ENV` branches, `trust proxy` deployment dependencies, production / development configuration differences
- Consumption relationships: when affecting strong vulnerability conclusions, it must be explicitly stated how it is consumed by `node/route_tracer`, each `node-vuln-audit` specialty (ssti / xss / session-cookie / file-upload, etc.), and `node-audit-pipeline`
