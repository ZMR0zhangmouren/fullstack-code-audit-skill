---
name: node-nuxt-audit
description: Node.js Nuxt.js framework specialty audit tool. Performs white-box audits of Nuxt 3 — file-convention entries, Nitro server routes, the serverMiddleware / routeRules control plane, SSR hydration surface, and runtime configuration.
---

# Nuxt.js Framework Specialty Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the Nuxt-related grabbers of entry definitions (pages / file conventions, Nitro server / api routes, serverMiddleware), the nuxt.config configuration surface (routeRules / auth), SSR hydration, useFetch / useAsyncData data flows, and runtime configuration
- If the project has plugin / middleware secondary encapsulations, unified authentication wrapper layers, or custom Nitro handler factories, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align server / api / * and pages / entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (core input of this specialty: confirm serverMiddleware and route middleware coverage order)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to align anonymous entries, P0/P1 bucketing, and authentication coverage, including authentication within Nitro routes and auth module configuration)
- Optional: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` (used to cross-reference hydration data and useFetch data flows with specific entries and side-effect chains)
- Optional: `node/vuln_audit/*_{timestamp}.md` (used to corroborate with vulnerability specialties such as xss / session-cookie / file-upload)
- Optional: `cross/api_contract_map_{timestamp}.md` (used to align SSR hydration, BFF forwarding, or isomorphic parameter sources)

## Key Checks

- `nuxt.config` `serverMiddleware` / `routeRules` configuration: routeRules caching strategies caching sensitive data / authentication responses publicly
- Missing parameter binding and authentication in Nitro `server / api / *` route handlers (the framework does not authenticate by default; each handler needs explicit validation)
- `useFetch` / `useAsyncData` SSR data flows: server-fetched sensitive data entering the client payload verbatim
- `__NUXT__` hydration data containing sensitive information or unsanitized HTML → hydration injection surface (coordinating with `EVID_NODE_XSS_SSR_HYDRATION` of node-xss-audit)
- Middleware / plugin execution order: execution timing and short-circuit conditions of route middleware (middleware /) and Nitro server middleware
- auth module configuration: cookie / secret configuration and post-login ticket handling of modules such as `@nuxtjs/auth` / `nuxt-auth-utils`
- Server `server / api` vs client component data boundaries: client components directly requesting unsanitized endpoints, `$fetch` passing through to the backend

## Enumeration Rules (Mandatory Refinement)

### 1. Framework Boundary Layer

- Enumerate entry definition styles: pages / file conventions (page routes), server / api / * file conventions (Nitro route handlers), server / routes / *, serverMiddleware array configuration (nuxt.config)
- Enumerate route middleware: middleware / directory files and `definePageMeta({ middleware })` / `defineNuxtRouteMiddleware` mount points, named middleware execution order (global / local)
- Enumerate `routeRules` of `nuxt.config`: the `swr` / `isr` / `redirect` / `proxy` / `cors` configuration of each rule, path matching surfaces, and caching semantics (clues of cached sensitive data leakage)
- Identify request lifecycle boundaries: request → nitro server middleware → handler → SSR page data → `__NUXT__` hydration → browser
- Identify plugin execution order: plugins / directory plugins and the `app.vue` / `app.config` initialization chain

### 2. Runtime Configuration Layer

- Enumerate SSR rendering modes: `ssr: true/false`, `useFetch` / `useAsyncData` server data fetch points and `key` reuse, `payload` passing surfaces
- Enumerate hydration data surfaces: `__NUXT__` JSON (useState / useFetch results entering the payload), `dangerouslySetInnerHTML` / `v-html` usage points (coordinating with `EVID_NODE_XSS_SSR_HYDRATION` of node-xss-audit)
- Enumerate environment variable read points: `process.env`, `runtimeConfig` (public vs private fields), `.env*` file contents and sensitive items (secret, DB connection strings)
- Enumerate the `runtimeConfig` boundary of `nuxt.config`: public fields entering the client bundle, private fields visible only server-side
- Enumerate the Nitro configuration surface: `nitro.routeRules`, `nitro.prerender`, `nitro.output` deployment shapes (node-server / vercel / edge)

### 3. Precondition Control Plane Layer

- Enumerate authentication coverage: `@nuxtjs/auth` / `nuxt-auth-utils` module configurations (session / cookie / secret), explicit authentication logic within Nitro handlers (`getCookie` / `jwt.verify`), authentication in route middleware (`defineNuxtRouteMiddleware`)
- Identify missing authentication in Nitro routes: compare each handler for authentication logic invocation; mark uncovered `server / api / *` entries
- Enumerate serverMiddleware execution order: relative order with `server / api` routes, conditional allow branches (no uniform `next()`)
- Enumerate CORS and cache control surfaces: `routeRules.cors` configuration, `Access-Control-Allow-Origin` wildcard + `credentials`, `Cache-Control` headers of sensitive responses

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| serverMiddleware authentication | `serverMiddleware: [{ path: '/api', handler: authHandler }]` | Check the execution order of serverMiddleware relative to `server / api` routes and conditional allow branches | authentication before protected handlers and fail-close → ✅ safe; serverMiddleware mounted after routes or conditional allow → 🔴 high risk |
| hydration sanitization | useState / useFetch data serialized into the `__NUXT__` payload | Check whether hydration data contains sensitive information (tokens / internal paths / raw user data) and whether `v-html` output points are sanitized | hydration data minimized and output sanitized → ✅ safe; sensitive data entering hydration or unsanitized output → 🔴 high risk (coordinating with the xss specialty) |
| Nitro route authentication | explicit `getCookie` / `jwt.verify` validation within handlers | Check the authentication call chain of each `server / api / *` handler (including the real invocation of shared helpers) | all reachable handlers fail-close → ✅ safe; reachable handlers without authentication exist → 🔴 high risk |
| routeRules caching strategy | `routeRules: { '/api/profile': { swr: 3600 } }` | Check whether caching rules hit interfaces / pages containing sensitive data (user-level data, authentication responses) | sensitive surfaces not cached or cache keys isolated per user → ✅ safe; user-level / authentication data publicly cached → 🔴 high risk |

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

- `EVID_NODE_CFG_SSR_MODE` shows `__NUXT__` hydration / useFetch payload containing sensitive data or unsanitized HTML output, with reachable entries (coordinating with `EVID_NODE_XSS_SSR_HYDRATION` of the xss specialty)
- `EVID_NODE_CFG_MIDDLEWARE_ORDER` shows serverMiddleware / route middleware placed after protected handlers or conditionally allowing, with reachable `server / api` entries without authentication
- `EVID_NODE_CFG_SECURITY_SWITCH` shows routeRules configuring `swr` / `isr` public caching on user-level / authentication data interfaces, or CORS wildcard + `credentials` combination with a protected interface carrying cookies
- `EVID_NODE_CFG_RUNTIME_SETTING` shows keys / internal addresses stored in `runtimeConfig.public` or `NUXT_PUBLIC_`-style prefixed fields and entering the client bundle
- Parameter binding within a Nitro handler entering a sink directly without sanitization / validation → coordinate with the corresponding vulnerability specialty (nosql / cmd / ssrf) to confirm

### ⚠️Pending Verification

- serverMiddleware has conditional allow branches; not all path behaviors can be confirmed statically (`EVID_NODE_CFG_MIDDLEWARE_ORDER`)
- Whether routeRules caching actually caches sensitive responses depends on CDN / deployment layer behaviors and cache key design; the deployment environment needs joint confirmation
- The cookie / secret configuration of auth modules (`@nuxtjs/auth`, etc.) depends on version behaviors; not all session surfaces can be confirmed statically (`EVID_NODE_SESS_COOKIE_FLAGS`)
- Whether useFetch server data can be exploited for XSS depends on the frontend output context; joint confirmation with the xss specialty is needed

### False Positive

- serverMiddleware globally precedes all protected handlers and is fail-close (unauthenticated requests directly rejected)
- `__NUXT__` hydration contains only public data and output passes framework default escaping (no `v-html` / `dangerouslySetInnerHTML`)
- routeRules caching applies only to static public pages with cache keys isolated per user; sensitive data does not enter public caches
- `runtimeConfig.private` fields are correctly placed and do not enter the client bundle

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct paths bypassing serverMiddleware to request protected `server / api` handlers → should be rejected (401 / 403)
- Request SSR pages containing sensitive data → check whether the `__NUXT__` payload and HTML contain sensitive information or unsanitized output
- Send consecutive requests to swr-cached interfaces containing user data → verify whether different users' responses are mixed up in the public cache
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Legitimate requests with valid sessions / cookies pass through middleware normally into protected pages / handlers
- Normal SSR pages have complete hydration data without sensitive fields, and the frontend hydrates normally
- routeRules caching of static public pages works normally without data mixing

### Regression Testing

- Re-verify authentication coverage after middleware order or serverMiddleware configuration changes
- Newly added `server / api / *` handlers must be included in the authentication coverage list before retesting
- Retest cache leakage and configuration leakage surfaces after nuxt.config routeRules / runtimeConfig changes

## Evidence References

- `EVID_NODE_CFG_SSR_MODE` (SSR rendering mode and `__NUXT__` hydration surface configuration evidence)
- `EVID_NODE_CFG_MIDDLEWARE_ORDER` (serverMiddleware / route middleware order and short-circuit condition evidence)
- `EVID_NODE_CFG_SECURITY_SWITCH` (routeRules caching strategy and CORS configuration evidence)
- `EVID_NODE_CFG_RUNTIME_SETTING` (runtimeConfig / environment variable visibility evidence)
- `EVID_NODE_XSS_SSR_HYDRATION` (`__NUXT__` hydration injection surface, coordinating with node-xss-audit)
- `EVID_NODE_SESS_COOKIE_FLAGS` (auth module session / cookie configuration surface, coordinating with node-session-cookie-audit)
- `EVID_NODE_SSTI_RENDER_POINT` (custom rendering / template engine rendering surface, such as integrated template engines or custom Nitro rendering, coordinating with node-ssti-audit; regular SSR has no template engine surface and is low priority)

## Output

- `node/framework_audit/nuxt_{timestamp}.md`
- Must state: entry types and mount styles (pages / and server / api / * file conventions, serverMiddleware), middleware execution order and short-circuit conditions, SSR hydration surface (`__NUXT__` / useFetch payload), routeRules caching strategy and sensitive surfaces, runtimeConfig boundary, auth module configuration
- Must state environment differences: `ssr` switch branches, Nitro deployment shape (node-server / vercel / edge) differences, development / production configuration differences
- Consumption relationships: when affecting strong vulnerability conclusions, it must be explicitly stated how it is consumed by `node/route_tracer`, each `node-vuln-audit` specialty (xss / session-cookie / nosql / ssrf, etc.), and `node-audit-pipeline`
