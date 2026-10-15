---
name: node-nextjs-audit
description: Node.js Next.js framework specialty audit tool. Performs white-box audits of Next.js applications — the App / Pages Router entry surface, middleware control plane, SSR hydration surface, image optimization, and runtime configuration.
---

# Next.js Framework Specialty Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the Next.js-related grabbers of entry definitions (app/ and pages/ file conventions, API Routes / Route Handlers), middleware matchers, rewrites / redirects, SSR hydration, environment variables, and image optimization configuration
- If the project has custom servers (custom server rewriting getServerSideProps / middleware), secondary-encapsulated data fetching hooks, or unified authentication wrapper layers, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align pages / api and app / api entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (core input of this specialty: confirm the coverage of middleware.ts and the effective surface of matchers)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to align anonymous entries, P0/P1 bucketing, and authentication coverage, including cookie validation within middleware and authentication within API routes)
- Optional: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` (used to cross-reference hydration data, next / image remote sources with specific entries and side-effect chains)
- Optional: `node/vuln_audit/*_{timestamp}.md` (used to corroborate with vulnerability specialties such as xss / ssrf / open-redirect / session-cookie)
- Optional: `cross/api_contract_map_{timestamp}.md` (used to align SSR hydration, BFF forwarding, or isomorphic parameter sources)

## Key Checks

- `middleware.ts` without `matcher` configured: the ambiguity of middleware intercepting everything or allowing everything when no matcher is configured, and matchers missing protected paths (reachable entries skipping authentication)
- `next.config.js` `rewrites` / `redirects` targets containing user-controllable fragments → open redirect / SSRF clues (coordinating with the node-open-redirect / node-ssrf specialties)
- Missing authentication in API Routes (pages / api) and Route Handlers (app / api): no route-level authentication, relying on frontend-hidden entries
- `__NEXT_DATA__` / RSC hydration data containing sensitive information or unsanitized HTML → hydration injection surface (coordinating with `EVID_NODE_XSS_SSR_HYDRATION` of node-xss-audit)
- `NEXT_PUBLIC_*` prefixed environment variables misused for keys / internal addresses → browser bundle and source-visible leakage
- `next / image` remote sources without `remotePatterns` whitelist configured or overly broad configuration → image optimization proxy SSRF clues
- Server component vs client component boundaries: sensitive logic (keys, authentication decisions) placed inside `'use client'` leading to frontend exposure
- edge runtime permission surface: sensitive operations or reliance on untrusted environment variables within middleware / edge functions

## Enumeration Rules (Mandatory Refinement)

### 1. Framework Boundary Layer

- Enumerate entry definition styles: app / directory file conventions (`page.tsx` / `layout.tsx` / `route.ts` / `middleware.ts`) and pages / directory conventions (`pages / api / *` API Routes, `getServerSideProps` / `getStaticProps` file exports)
- Enumerate the `export default` logic and `matcher` configuration of `middleware.ts` (or `middleware.js`): missing matchers, path prefixes missed by matcher arrays, boundaries of matchers using regex
- Enumerate `rewrites` / `redirects` configurations of `next.config.js`: target sources (hardcoded / environment variables / user input), `has` / `missing` conditions, wildcard matching surfaces
- Enumerate server component vs client component boundaries: `'use client'` directive files, `use server` / Server Actions exposure surfaces, RSC data serialization surfaces (non-serializable objects / functions passed through)
- Identify request lifecycle boundaries: request → middleware → route handler / page → hydration payload → browser

### 2. Runtime Configuration Layer

- Enumerate SSR rendering modes: `getServerSideProps` / `getStaticProps` / `getInitialProps`, `generateStaticParams`, `output: 'standalone'`, ISR (`revalidate`) configuration
- Enumerate hydration data surfaces: `__NEXT_DATA__` JSON, RSC payload, `dangerouslySetInnerHTML` usage points, server data injected into HTML without sanitization (coordinating with `EVID_NODE_XSS_SSR_HYDRATION` of node-xss-audit)
- Enumerate environment variable read points: `process.env`, `NEXT_PUBLIC_` prefixed variables (browser-side visible), `.env*` file contents and sensitive items (secret, token, DB connection strings)
- Enumerate image optimization configuration: `remotePatterns` / `domains` of `next / image`, custom `loader` configurations, image request forwarding surfaces (SSRF clues, coordinating with node-ssrf-audit)
- Enumerate edge runtime: entries / middleware with `export const runtime = 'edge'`, edge environment variable visibility and permission amplification surfaces

### 3. Precondition Control Plane Layer

- Enumerate authentication coverage: cookie / token validation in middleware (`cookies()` / `req.cookies`, jwt.verify), whether API Route authentication logic is per-route or a shared helper, `@auth` / NextAuth configuration
- Identify missing authentication in API Routes / Route Handlers: compare the route list with authentication logic coverage; mark uncovered `pages / api / *` and `app / api / *` entries
- Enumerate CORS configuration: `headers()` dynamic response headers, `headers` static configuration of `next.config`, `Access-Control-Allow-Origin` wildcard + `credentials` combination
- Enumerate Server Actions exposure surfaces: whether `'use server'` exported actions bypass frontend authentication, missing parameter validation

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| middleware matcher coverage | `export const config = { matcher: ['/api/:path*', '/dashboard/:path*'] }` | Check whether the matcher covers all protected entries; when no matcher is configured, confirm the intent of global middleware effectiveness; compare matcher expressions with the route list | matcher covers all protected surfaces with fail-close logic → ✅ safe; matcher missing paths or no matcher causing authentication ambiguity → 🔴 high risk |
| SSR hydration sanitization | server data serialized into `__NEXT_DATA__` / RSC payload | Check whether hydration data contains sensitive information (tokens / internal paths / raw user data) and whether HTML output points are sanitized | hydration data minimized and HTML output sanitized → ✅ safe; sensitive data entering hydration or unsanitized output → 🔴 high risk (coordinating with the xss specialty) |
| API Route authentication | API Routes / Route Handlers explicitly calling authentication helpers | Check each entry of `pages / api` and `app / api` for authentication logic invocation (including the real call chain of shared helpers) | all reachable entries fail-close → ✅ safe; reachable entries without authentication exist → 🔴 high risk |
| image remote source whitelist | `images.remotePatterns` explicitly declared in `next.config` | Check `next / image` usage points and the `remotePatterns` configuration, confirming whether remote sources are whitelist-constrained | fixed whitelist with tightened protocol / host → ✅ safe; no whitelist or overly broad wildcards → ⚠️ to be confirmed (SSRF clue) |

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

- `EVID_NODE_CFG_SSR_MODE` shows sensitive data entering the SSR / hydration surface (`__NEXT_DATA__` / RSC payload) or unsanitized HTML output, with reachable entries (coordinating with `EVID_NODE_XSS_SSR_HYDRATION` of the xss specialty)
- `EVID_NODE_CFG_MIDDLEWARE_ORDER` shows `middleware.ts` without a matcher or with matchers missing protected paths, and reachable API entries without authentication exist (configuration missing + entry reachable)
- `EVID_NODE_CFG_RUNTIME_SETTING` shows keys / internal addresses stored under the `NEXT_PUBLIC_*` prefix and referenced by components or client-side code
- `next / image` remote sources without `remotePatterns` configured or with overly broad wildcards, with user-controllable image URL input points (`EVID_NODE_SSRF_URL_CONSTRUCTION`)
- `rewrites` / `redirects` targets containing user-controllable fragments without target validation → open redirect / SSRF clues (`EVID_NODE_CFG_SECURITY_SWITCH`)

### ⚠️Pending Verification

- Middleware authentication has conditional allow branches (missing cookie falls through to a default page rather than rejection); not all path behaviors can be confirmed statically (`EVID_NODE_CFG_MIDDLEWARE_ORDER`)
- Whether `next / image` remote sources can actually be attacker-controlled depends on the upstream source of image URLs; tracing is needed for confirmation
- Server Actions (`'use server'`) parameter validation depends on runtime framework behaviors; not all validation gaps can be confirmed statically
- Whether hydration data can be exploited for XSS depends on the frontend output context (`dangerouslySetInnerHTML` vs safe interpolation); joint confirmation with the xss specialty is needed

### False Positive

- `middleware.ts` matcher explicitly covers all protected entries with fail-close authentication logic (rejection on failure)
- Hydration data contains only public data and all HTML output passes framework default escaping (no `dangerouslySetInnerHTML`)
- `NEXT_PUBLIC_*` contains only non-sensitive public configuration (such as site names, public API endpoints), with no keys / internal information
- `next / image` `remotePatterns` is a fixed whitelist with tightened protocol / host, and image URLs have no controllable input points (`EVID_NODE_SSRF_ALLOWLIST`)

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct paths bypassing the matcher (such as case variations, trailing slashes, double encoding) to request protected APIs → should be rejected (401 / 403)
- Request SSR pages containing sensitive data → check whether the hydration payload and HTML contain sensitive information or unsanitized output
- Construct a malicious `?url=` triggering the `next / image` proxy → should be rejected by the whitelist rather than issuing a request
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Legitimate requests with valid cookies / tokens pass through middleware normally into protected pages / APIs
- Normal SSR pages have complete hydration data without sensitive fields, and the frontend hydrates normally
- Whitelisted image sources load normally without proxy wrongful rejection

### Regression Testing

- Re-verify authentication coverage and bypass surfaces after matchers add / change paths
- Newly added API Routes / Route Handlers must be included in the authentication coverage list before retesting
- Retest open redirect and image SSRF surfaces after `next.config` (rewrites / redirects / images) changes

## Evidence References

- `EVID_NODE_CFG_SSR_MODE` (SSR rendering mode and hydration surface configuration evidence)
- `EVID_NODE_CFG_MIDDLEWARE_ORDER` (middleware matcher and middleware order evidence)
- `EVID_NODE_CFG_RUNTIME_SETTING` (NEXT_PUBLIC_ environment variables and runtime configuration evidence)
- `EVID_NODE_CFG_SECURITY_SWITCH` (CORS wildcard + credentials, rewrites target validation switch evidence)
- `EVID_NODE_XSS_SSR_HYDRATION` (`__NEXT_DATA__` / RSC hydration injection surface, coordinating with node-xss-audit)
- `EVID_NODE_SSRF_URL_CONSTRUCTION` and `EVID_NODE_SSRF_ALLOWLIST` (next / image remote sources and image proxy SSRF surface, coordinating with node-ssrf-audit)
- `EVID_NODE_SSTI_RENDER_POINT` (custom rendering / template engine rendering surface, such as custom servers or dynamic template output, coordinating with node-ssti-audit; regular SSR has no template engine surface and is low priority)

## Output

- `node/framework_audit/nextjs_{timestamp}.md`
- Must state: entry types and mount styles (app / and pages / file conventions, API Routes / Route Handlers, middleware), matcher coverage and uncovered entries, SSR hydration surface (`__NEXT_DATA__` / RSC), rewrites / redirects target sources, NEXT_PUBLIC_ leaked items, next / image remote source configuration, edge runtime exposure surface
- Must state environment differences: development / production build differences (`NODE_ENV` branches), `output: 'standalone'` deployment shape, ISR caching behavior
- Consumption relationships: when affecting strong vulnerability conclusions, it must be explicitly stated how it is consumed by `node/route_tracer`, each `node-vuln-audit` specialty (xss / ssrf / open-redirect / session-cookie, etc.), and `node-audit-pipeline`
