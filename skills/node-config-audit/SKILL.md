---
name: node-config-audit
description: Node.js configuration security audit tool. Identifies risks such as missing helmet, CORS wildcard + credentials, overly broad trust proxy, hardcoded secrets in .env, and verbose production error pages; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js Configuration Security Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to framework entry configuration, security middleware, environment variables, and security switches
- If the project has secondary encapsulations such as setupSecurity, applyMiddleware, config/index.js, or env.js, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **static-evidence-driven**: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`
- Responsibility boundary: session, cookie, and JWT session configuration details belong to `node-session-cookie-audit`; this specialty covers the framework and runtime configuration surface

## Key Checks

- Missing helmet or only partially mounted: security headers such as CSP, HSTS, and X-Frame-Options absent by default
- The dangerous combination `cors({ origin: '*', credentials: true })`; origin echoing + credentials reflecting arbitrary domains
- Overly broad `app.set('trust proxy', true)`: `req.ip` can be forged via `X-Forwarded-For`, affecting rate limiting and audit attribution
- `.env` committed to the repository, secrets hardcoded in source, dotenv loading development defaults in production
- Express default error pages outputting stacks when `NODE_ENV !== 'production'`; debug switches, Swagger / OpenAPI, GraphQL Playground, and pino-pretty diagnostic surfaces exposed in production
- Production security switches in `next.config` (devIndicators, source maps, headers) and `nuxt.config` (devtools, ssr)
- NestJS `ConfigModule.forRoot` default values and dead environment branch conditions

## Enumeration Rules (Mandatory Refinement)

- Enumerate framework entries and configuration files: `app.js` / `server.js` / `main.ts` / `config/` / `.env*` / `next.config.*` / `nuxt.config.*`
- rg searches: `helmet`, `cors(`, `origin`, `credentials`, `trust proxy`, `dotenv`, `process.env`, `NODE_ENV`, `app.set(`, `swagger`, `playground`, `devtools`, `devtool`, `sourcemap`
- For each configuration point record: configuration location, runtime code, impact surface, environment conditional branches (NODE_ENV), and whether it is a security switch
- Verify middleware mount order: whether helmet / cors / rate limit take effect globally before routes, and whether route-level overrides exist
- Identify environment variable fallback defaults: fail-open patterns such as `process.env.X || 'dev-secret'`
- If configuration goes through secondary encapsulation (a config middleware layer), it must be unwrapped layer by layer to the actually effective values

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Environment branch | `process.env.NODE_ENV` checks | Confirm whether dangerous configurations are strictly confined to production conditions | effective only in development with rejection by default → ✅ safe; missing or inverted condition → 🔴 high risk |
| Security middleware | helmet / cors / rate limit | Verify mount order and parameters (origin whitelist, credentials) | mounted globally with CORS tightened → ✅ safe; `origin:'*'` + `credentials:true` → 🔴 high risk |
| Proxy trust | `app.set('trust proxy', N)` | Verify trusted hop counts against the real proxy topology | specific hop counts or trusted network segments → ✅ safe; `true` trusting all → 🔴 high risk |
| Secret source | dotenv / environment injection / key management services | Trace secret declaration locations and default fallback values | environment injection without weak defaults → ✅ safe; source literals or .env committed → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: a dangerous configuration switch appears to take effect outside the development environment, or missing security middleware affects sensitive endpoints
- `Pending`: the context shows a suspicious pattern, but the external input source, barrier behavior, or call chain is unclear
- `False Positive`: the input comes from fixed constants / enum mappings, or the barrier has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found that externally controllable input enters the Sink position → `Confirmed Vulnerability`
- Fixed whitelist mapping / fail-close evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_CFG_SECURITY_SWITCH` + `EVID_NODE_CFG_RUNTIME_SETTING`: `cors({ origin: '*', credentials: true })` in effect, or helmet missing with no alternative security headers in production
- `EVID_NODE_CFG_ERR_HANDLER`: verbose error pages in non-production environments, with stacks and internal paths returned to clients
- `EVID_NODE_CFG_RUNTIME_SETTING`: `.env` committed to the repository or secrets hardcoded in source, without environment isolation and rotation
- `EVID_NODE_CFG_MIDDLEWARE_ORDER`: overly broad `trust proxy` allowing `req.ip` forgery, affecting rate limiting and audit attribution

### ⚠️Pending Verification

- helmet / cors configuration points are hit, but the production deployment shape (whether the reverse proxy adds security headers) is unknown
- `.env` files exist, but whether they are committed to the repository or whether CI injects real values cannot be confirmed
- `next.config` / `nuxt.config` security switches are hit, but the rendering mode and deployment target are unconfirmed

### False Positive

- Dangerous configurations take effect only under the `NODE_ENV=development` branch, with production failing closed by default
- helmet mounted globally, CORS whitelist tightened, and secrets injected via environment or key management services
- `trust proxy` specifies concrete hop counts and all upstreams are trusted gateways

## Testing Recommendations (Mandatory)

### Positive Testing

- Send a preflight request with `Origin: https://evil.example` and credentials to verify the CORS wildcard combination allows it
- Forge `X-Forwarded-For` to verify the `req.ip` trust surface and rate-limit bypass; trigger an uncaught exception to verify the verbose error page
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Under `NODE_ENV=production`, verify helmet headers are complete, error pages carry no stack, and diagnostic surfaces return 404
- Out-of-whitelist Origin requests are rejected by CORS; startup fails when secrets are missing (fail-close)

### Regression Testing

- Retest after remediation, confirming middleware order is not regressed by new routes
- Retest that environment branches remain tightened for production under container variable misconfiguration; newly added endpoints inherit the global security middleware by default

## Evidence References

- `EVID_NODE_CFG_SECURITY_SWITCH`
- `EVID_NODE_CFG_RUNTIME_SETTING`
- `EVID_NODE_CFG_MIDDLEWARE_ORDER`
- `EVID_NODE_CFG_SSR_MODE`
- `EVID_NODE_CFG_ERR_HANDLER`

## Output

- `node/vuln_audit/config_{timestamp}.md`
- `node/vuln_poc/config_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)

## Mechanism Extension: Security Configuration Exposure and Response Information Disclosure (2026-09-14 Ledger Round)

### Mechanism Description and Boundary

This extension covers two exposure chains:

- **Internal information disclosure chain**: route / configuration request → documentation / configuration / metadata response → internal information exposure. Unauthorized requesters obtain internal implementation details, deployment configuration, and middleware information from responses.
- **Secret leakage chain**: response field → secret material → credential leakage. Responses directly carry credential material such as connection strings, private keys, and access keys.

Ledger boundary (verbatim): findings of secret material take the secret exposure path first; publicly and intentionally exposed API documentation is not judged a vulnerability.

### Key Checks and Enumeration Grabbers

Record for each hit: file, line number, endpoint / response point, and exposed content type.

- **Configuration / metadata endpoints**: routes such as `/debug` / `/config` exporting `process.env` or configuration objects, `/health` (detailed health checks exposing dependency information), unauthorized `server-status` / metrics endpoints, full exposure of `swagger` / openapi documentation, downloadable `.env` / `config.json` static files, production source maps (`.js.map`) exposure.
- **Error response disclosure**: express error middleware leaking `err.stack` (e.g., `app.use((err, req, res, next) => res.status(500).json({ error: err.message, stack: err.stack }))`), verbose error pages not conditioned on environment, error responses carrying internal paths / dependency versions.
- **Secret patterns in responses**: connection strings (`mongodb://` / `postgres://` containing passwords), `-----BEGIN PRIVATE KEY-----` / `-----BEGIN RSA PRIVATE KEY-----`, AKIA-style access keys, JWTs hardcoded in responses or frontend configuration, hardcoded API keys.

### Verification Matrix

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Endpoint access control** | Issue unauthorized requests to configuration / metadata endpoints, confirming whether authentication + authorization is required | unauthorized rejected or only intentionally public documentation → ✅ safe; unauthorized access to internal information → 🔴 high-risk candidate |
| **Production error page convergence** | Trigger an exception under production configuration, confirming the response is a unified error page without stack / configuration / internal path details | unified convergence → ✅ safe; leaking stacks / configuration / internal paths → 🔴 high-risk candidate |
| **Secret pattern scanning and response interception** | Scan response bodies for secret patterns such as connection strings, private key headers, AKIA, and JWTs, and trace their paths into responses | no secrets in responses → ✅ safe; detectable with locatable source → 🔴 high-risk candidate |
| **Public documentation whitelist** | Confirm whether exposed documentation endpoints are intentionally public (e.g., publicly available API documentation), excluding by intentionality | intentionally public → not a vulnerability; unintentionally public → ⚠️ to be confirmed |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion as "Confirmed Safe" or "False Positive" is forbidden.**

### Determination Rules

Confirmation requires closing EVIDs per path:

**The internal information path** must close both of the following EVIDs, both indispensable:

1. **Endpoint exposure surface closure**: evidence of unauthorized accessible surface of route / configuration / metadata endpoints (`EVID_NODE_CFG_SENSITIVE_ENDPOINT_EXPOSURE`).
2. **Actual internal information disclosure closure**: evidence that responses actually expose internal implementation / deployment configuration, not merely endpoint existence (`EVID_NODE_CFG_INTERNAL_INFO_DISCLOSURE`).

**The secret path** replaces the second ID with a third: evidence of credential leakage with secret material detected in responses (`EVID_NODE_CFG_SECRET_MATERIAL_IN_RESPONSE`).

🔴 **Confirmation threshold (ledger verbatim): it must be proven that response content actually exposes internal information or secret material; confirmation based solely on endpoint existence or suspected field names is forbidden; publicly and intentionally exposed API documentation is not judged a vulnerability.**

### Testing Recommendations

- **Positive**: access configuration / metadata endpoints without authorization and confirm internal information is obtained; scan responses to confirm secret patterns are detectable.
- **Negative**: after authentication + authorization convergence, unified production error pages, and secret-in-response interception, the issue is no longer exploitable.
- **Regression**: when new metadata / diagnostic endpoints are added (including health checks, metrics, and configuration export), re-verify access control and the intentional-public whitelist.

### Evidence References

- `EVID_NODE_CFG_SENSITIVE_ENDPOINT_EXPOSURE`: evidence of unauthorized accessible surface of route / configuration / metadata endpoints (first ID shared by both paths)
- `EVID_NODE_CFG_INTERNAL_INFO_DISCLOSURE`: evidence that responses actually expose internal implementation / deployment configuration (second ID of the internal information path)
- `EVID_NODE_CFG_SECRET_MATERIAL_IN_RESPONSE`: evidence of credential leakage with secret material detected in responses (second ID replacement of the secret path)
