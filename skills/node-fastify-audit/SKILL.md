---
name: node-fastify-audit
description: Node.js Fastify framework specialty audit tool. Performs white-box audits of the framework boundary, runtime configuration, and control plane of Fastify applications — JSON schema validation, hook chains, encapsulation contexts, and error handling.
---

# Fastify Framework Specialty Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the Fastify-related grabbers of route schema validation, hook chains, encapsulation (register) isolation, static directories, and plugin configuration
- If the project has Fastify secondary encapsulations such as plugin wrappers, decorators (decorate), or shared schema reuse, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (core input of this specialty: confirm hook chain order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to align anonymous entries, P0/P1 bucketing, and preHandler authentication coverage)
- Optional: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` (used to cross-reference weak schema validation / hook risks with specific entries and side-effect chains)
- Optional: `node/vuln_audit/*_{timestamp}.md` (used to corroborate with vulnerability specialties such as nosql / xss / session-cookie)
- Optional: `cross/api_contract_map_{timestamp}.md` (used to align BFF forwarding or isomorphic parameter sources)

## Key Checks

- Missing route-level JSON schema: `schema.body/params/query` undefined → parameters passing through to handlers with weak validation (fail-open)
- ajv configuration: `coerceTypes` enabled causing type-coercion bypass of validation; `removeAdditional` not enabled, letting extra fields enter handlers
- Hook chain order flaws: `onRequest` / `preHandler` not short-circuiting via `reply.send`, or registered in an encapsulated child context, or the authentication hook being overridden by later hooks at the same level
- Encapsulation context (`fastify.register`) isolation flaws: authentication hooks registered on the root instance failing to take effect in child encapsulations
- `@fastify/static` root directory controllable, `index` / `list` options enabled, or placed before authentication → directory exposure
- Content type parsing: non-JSON Content-Type falling back to the default parser (weak validation bypassing schema.body)
- `@fastify/cors` wildcard + `credentials` combination; missing `@fastify/rate-limit`
- Missing `setErrorHandler` → default error responses (stacks and internal paths in non-production environments)

## Enumeration Rules (Mandatory Refinement)

### 1. Framework Boundary Layer

- Enumerate entry definition styles: `fastify.get/post/route({ method, url, handler })`, `fastify.register(plugin, options)` plugin mounting, `fastify.all` catch-all
- Enumerate hook chain registration: `onRequest` → `preParsing` → `preValidation` → `preHandler` → handler → `onSend` → `onResponse`, annotating the short-circuit condition of each layer (direct return via `reply.send`, `return reply.code(...).send(...)`)
- Enumerate encapsulation contexts: plugin isolation boundaries of `fastify.register`, hook and decorator scopes of the root instance / child encapsulated instances
- Enumerate static directories: the `root` source of `@fastify/static` (hardcoded / environment variables / user input), `index`, `list`, `prefix` options, and position relative to authentication hooks
- Identify request lifecycle boundaries: request → hook chain → handler → onSend → response; annotate `reply.send` output points (for the XSS specialty)

### 2. Runtime Configuration Layer

- Enumerate `process.env`, `dotenv`, `.env` read points and sensitive items (secret, token, DB connection strings)
- Enumerate JSON schema validation configuration: `schema.body/params/query/response` definitions of each route, `ajv.customOptions` (`coerceTypes` / `removeAdditional`), `attachValidation` weakened mode
- Enumerate content type parsing: `addContentTypeParser` custom parsers, non-JSON fallback paths, `contentTypeParser` overrides
- Enumerate plugin configurations: `@fastify/cookie` (signed / secure), `@fastify/cors`, `@fastify/rate-limit`, `@fastify/session`, `fastify-helmet`
- Enumerate security headers and CORS configuration: `@fastify/helmet`, `@fastify/cors({ origin, credentials })`
- If secondary encapsulations such as plugin wrappers or shared schema reuse exist, they must be unwrapped layer by layer to the real route / hook call sites

### 3. Precondition Control Plane Layer

- Enumerate authentication coverage: `jwt.verify` / custom authentication in `preHandler`, `@fastify/auth`, whether the `onRequest` global authentication hook is registered on the root instance or only in child encapsulations
- Identify route-level authentication gaps: compare the route list with authentication hook coverage; mark uncovered routes and `fastify.all` catch-all routes
- Enumerate rate limiting: `@fastify/rate-limit` configuration and its linkage with the `request.ip` source (reverse-proxy IP forgery bypassing rate limits)
- Enumerate request size limits: global `bodyLimit` configuration, route-level `bodyLimit`, upload limits (`@fastify/multipart` limits)

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| schema validation | route defines `schema: { body: {...} }` | Check whether each route defines schema.body / params / query and whether ajv options are weakened | schema explicit with `coerceTypes` off → ✅ safe; schema missing or `attachValidation` weakening → 🔴 weak validation (fail-open) |
| hook order | `onRequest` / `preHandler` authentication followed by `done()` / `reply.send` short-circuit | Check the position of the authentication hook relative to the handler along the hook chain and its short-circuit conditions | authentication hook before the handler with unconditional passage → ✅ safe; authentication mounted after the handler / not registered → 🔴 high risk |
| encapsulation isolation | root instance registers a global authentication `onRequest` hook | Check whether the registration context (root / child encapsulation) of the authentication hook covers all routes | root-instance global coverage or fail-close within child encapsulations → ✅ safe; incomplete child encapsulation coverage → ⚠️ to be confirmed |
| error handling | `fastify.setErrorHandler((err, req, reply) => ...)` | Check whether a custom error handler is set and whether responses contain stacks / internal paths | custom handler with sanitized responses → ✅ safe; missing → 🔴 default stack leakage (fail-open) |

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

- A route does not define `schema.body/params/query` with reachable entries, and external input passes straight into the handler (`EVID_NODE_CFG_SECURITY_SWITCH`)
- `coerceTypes` enabled or `attachValidation` weakening, with type coercion / silent passthrough on validation failure (`EVID_NODE_CFG_RUNTIME_SETTING`)
- `setErrorHandler` missing, and default error responses output stacks and internal paths (`EVID_NODE_CFG_ERR_HANDLER`)
- The authentication hook is registered in a child encapsulation leaving uncovered routes, or the `onRequest` hook does not short-circuit to allow non-whitelist requests (`EVID_NODE_CFG_MIDDLEWARE_ORDER`)
- `@fastify/cors` wildcard + `credentials` combination, with a protected interface carrying cookies

### ⚠️Pending Verification

- Encapsulation context isolation unclear: the authentication hook is registered on the root instance but `fastify.register` child instances have overriding behavior, and the effective scope on all routes cannot be confirmed statically
- ajv options such as `coerceTypes` are injected through plugin encapsulation, and the actually compiled effective configuration cannot be confirmed statically
- Non-JSON Content-Type fallback paths depend on the headers actually sent by clients, and not all fallback scenarios can be enumerated statically
- Whether error responses leak stacks depends on the runtime `NODE_ENV` value, which cannot be confirmed statically

### False Positive

- Each route explicitly defines `schema` and the ajv configuration is fail-close (unknown fields rejected / stripped)
- The authentication hook is globally registered on the root instance `onRequest` and intercepts unconditionally
- `setErrorHandler` is registered and responses are sanitized (no stacks / internal paths)
- CORS not wildcarded and not carrying `credentials`; `@fastify/static` root fixed and placed after authentication

## Testing Recommendations (Mandatory)

### Positive Testing

- Request a protected route without authentication → should be rejected (401 / 403), verifying hook chain coverage
- Construct a body violating the schema (wrong type / extra fields) → should return 400 rather than entering the handler
- Trigger an exception request → the response should be a sanitized error page without stacks / internal paths
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Legitimate requests pass through the complete hook chain (authentication + rate limit + schema validation) and return normally
- Boundary-value requests conforming to the schema work and are not wrongly rejected
- In production mode (`NODE_ENV=production`), error responses do not leak stacks

### Regression Testing

- Re-verify authentication coverage and schema validation after hook chain order or encapsulation structure changes
- Newly added routes must be included in the schema / authentication coverage list before retesting
- Retest stack leakage and 400 / 413 behavior after error handler / content type parser changes

## Evidence References

- `EVID_NODE_CFG_SECURITY_SWITCH`
- `EVID_NODE_CFG_RUNTIME_SETTING`
- `EVID_NODE_CFG_ERR_HANDLER`
- `EVID_NODE_CFG_MIDDLEWARE_ORDER`
- `EVID_NODE_NOSQL_TYPE_COERCE_GUARD` (weak schema validation scenarios, coordinating with node-nosql-audit)
- `EVID_NODE_SESS_COOKIE_FLAGS` (@fastify/cookie / session configuration surface, coordinating with node-session-cookie-audit)

## Output

- `node/framework_audit/fastify_{timestamp}.md`
- Must state: route entries and schema validation coverage (including the missing list), hook chain order and short-circuit conditions, encapsulation context isolation, static directory exposure surface, runtime configuration (ajv / bodyLimit / CORS / rate-limit), authentication coverage and uncovered routes
- Must state environment differences: `NODE_ENV` branches, `request.ip` reverse-proxy dependencies, production / development configuration differences
- Consumption relationships: when affecting strong vulnerability conclusions, it must be explicitly stated how it is consumed by `node/route_tracer`, each `node-vuln-audit` specialty (nosql / xss / session-cookie, etc.), and `node-audit-pipeline`
