---
name: node-graphql-audit
description: Node.js GraphQL framework specialty audit tool. Performs white-box audits of GraphQL schema and resolver parameter sources, introspection switches, depth / complexity limits, resolver-level authentication, error formatting, and runtime configuration.
---

# GraphQL Framework Specialty Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the GraphQL-related grabbers of schema / type definitions, resolver parameter sources (context / args), introspection and playground switches, depth / complexity limits, error formatting, and authentication guard configuration
- If the project has schema stitching / federation gateways, resolver factories, or unified authentication wrappers (custom directives / `graphql-shield` rules), they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align GraphQL entry endpoints with `route_id`; this specialty's entry usually converges to a single `/graphql` endpoint)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm the authentication coverage order of the middleware preceding the `/graphql` endpoint)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (core input of this specialty: align anonymous entries, P0/P1 bucketing, and resolver-level authentication coverage)
- Optional: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` (used to cross-reference the data flow from resolver parameters to sinks with specific entries)
- Optional: `node/vuln_audit/*_{timestamp}.md` (used to corroborate with vulnerability specialties such as nosql / expr / cmd / ssrf — the injection surface within resolvers)
- Optional: `cross/api_contract_map_{timestamp}.md` (used to align BFF forwarding or isomorphic parameter sources)

## Key Checks

- Schema definitions and resolver parameter sources: the `args` / `context` parsing surface of resolvers, with parameters passing through into queries / command execution (in-resolver injection, coordinating with the node-nosql / node-expr specialties)
- Introspection switch: introspection not disabled in production → schema structure and internal field names leaked (attack surface expansion)
- Missing depth / complexity limits: `graphql-depth-limit` / `maxDepth` / `complexity` not configured → deep nesting / batch queries / alias abuse DoS
- Missing resolver-level authentication: field-level guards (`graphql-shield` / custom directives) not covering some query / mutation, or authentication relying only on frontend-hidden fields
- Error stack leakage: `formatError` / `formattedErrors` not sanitized, error responses containing stacks and internal paths (coordinating with `EVID_NODE_CFG_ERR_HANDLER`)
- `graphql-playground` / GraphiQL enabled in production → interactive query surface exposure
- Batch query and alias abuse: `__typename` injection, batch field aliases amplifying server-side costs (cache bypass)

## Enumeration Rules (Mandatory Refinement)

### 1. Framework Boundary Layer

- Enumerate entry definition styles: `GraphQLModule.forRoot` (@nestjs/graphql) / `ApolloServer` / `express-graphql` / `mercurius` (Fastify) mount points and endpoint paths, gateway / federation subgraph boundaries (`@key` / `@external` directives)
- Enumerate schema definitions: type / query / mutation definitions in SDL files or code-first (`@ObjectType` / `@Field` / `@Resolver`), custom directive (`@auth` / `@requireRole`, etc.) mount surfaces
- Enumerate resolver parameter sources: `args` extraction, `context` (`req` / `user` / `db`) resolution, `@Parent` / `@Info` field selection surfaces, paths where parameters pass through into sinks
- Identify request lifecycle boundaries: HTTP request → GraphQL parsing (parse / validate / execute) → resolver chain (field-level, expanded by depth) → response
- Identify batching surfaces: `batch` / `batching` configuration, alias and repeated field selections (repeated resolver execution amplification surface)

### 2. Runtime Configuration Layer

- Enumerate introspection configuration: the `introspection: true/false` switch, environment branches (on in development / off in production), `playground: true` configuration of playground / GraphiQL
- Enumerate depth / complexity limits: `validationRules` (`graphql-depth-limit`, `graphql-validation-complexity`), `maxDepth` / `maxComplexity` / `requestDidStart` plugins, `maxQueryDepth` (Mercurius)
- Enumerate error formatting: whether `formatError` / `formattedErrors` / `customFormatErrorFn` sanitize stacks and internal paths, the `includeStacktraceInErrorResponses` switch (Apollo)
- Enumerate resolver cost control: default field resolvers (`defaultFieldResolver`), N+1 queries within resolvers (without DataLoader) amplification surface
- Enumerate environment variable read points: schema paths / endpoint configurations, `process.env` sensitive items, runtime build branches

### 3. Precondition Control Plane Layer

- Enumerate resolver-level authentication coverage: `graphql-shield` rules (`rule` / `shield` middleware), custom auth directives, `@UseGuards` (nestjs/graphql), the source of `user` injection in context (JWT verification points)
- Identify field-level authentication gaps: compare all query / mutation / fields of the schema with authentication rule coverage; mark uncovered resolvers and nested fields
- Enumerate pre-resolution interception surfaces: Apollo plugins (`requestDidStart` / `didResolveOperation`), HTTP-layer middleware authentication (auth preceding the `/graphql` endpoint) and its superposition with in-resolver authentication
- Enumerate rate limiting and request size limits: `graphql-rate-limit` / throttler configurations, single request size limits, persisted query whitelists

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| introspection switch | `introspection: false` (production) | Check the environment branches and production values of the introspection / playground configuration | disabled in production with development / production configuration isolation → ✅ safe; introspection or playground enabled in production → 🔴 high risk |
| depth limits | `validationRules: [depthLimit(10)]` | Check whether depth / complexity validation rules are registered and their thresholds, comparing against the actual nesting depth of the schema | explicit depth limits with reasonable thresholds → ✅ safe; missing or excessively large thresholds → ⚠️ to be confirmed (DoS surface) |
| resolver authentication | `graphql-shield` shield middleware / `@UseGuards(GqlAuthGuard)` | Compare all query / mutation / fields of the schema with authentication rule coverage, including nested fields and dynamic schemas | all resolvers fail-close → ✅ safe; reachable unauthenticated resolvers / fields exist → 🔴 high risk |
| error formatting | `formatError: (err) => sanitized` | Check whether error formatting sanitizes stacks / internal paths and whether `includeStacktraceInErrorResponses` is off | custom formatting with sanitization → ✅ safe; default output of stacks / internal paths → 🔴 leakage (fail-open) |

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

- `EVID_NODE_CFG_SECURITY_SWITCH` shows `introspection: true` or playground / GraphiQL enabled in production, with the schema structure enumerable externally
- `EVID_NODE_CFG_RUNTIME_SETTING` shows depth / complexity limits unconfigured, and the schema has deep nesting / batch query amplification surfaces (DoS candidate)
- `EVID_NODE_CFG_ERR_HANDLER` shows `formatError` / `formattedErrors` not sanitizing stacks and internal paths, with error responses externally triggerable and readable
- `EVID_NODE_CFG_MIDDLEWARE_ORDER` shows resolver-level authentication rules mounted on only some query / mutation, with reachable unauthenticated resolvers / nested fields
- Resolver `args` passing through into query / command construction without sanitization → coordinate with node-nosql (`EVID_NODE_NOSQL_RAW_OBJECT_PASS` / `EVID_NODE_NOSQL_OPERATOR_INJECTION`) or node-cmd to confirm injection (`EVID_NODE_CMD_USER_PARAM_TO_CMD`)

### ⚠️Pending Verification

- Whether missing depth / complexity limits can be actually exploited for DoS depends on the schema structure and resolver costs; server resource confirmation is needed (`EVID_NODE_CFG_RUNTIME_SETTING`)
- Whether an unauthenticated resolver can be called externally depends on the schema stitching / federation boundary and HTTP-layer precondition authentication; the precondition control plane needs confirmation
- Error stack leakage depends on the runtime `NODE_ENV` and framework version default behaviors; the deployment environment cannot be confirmed statically
- Batch query / alias abuse amplification depends on resolver implementations (N+1 queries); tracing to the data access layer is needed for confirmation

### False Positive

- Production configuration with `introspection: false` and playground disabled, with clear development / production configuration isolation
- `validationRules` registering both depth and complexity limits with thresholds matching the schema nesting depth
- Resolver authentication rules covering all query / mutation / nested fields and fail-close (unauthenticated requests directly rejected)
- `formatError` customized with sanitized responses (no stacks / internal paths), `includeStacktraceInErrorResponses` off

## Testing Recommendations (Mandatory)

### Positive Testing

- Send an introspection query in production → should be rejected or return an empty schema
- Construct deeply nested queries / large batch alias queries → should be rejected by depth / complexity limits rather than entering resolver execution
- Query fields of an uncovered resolver without authentication → should be rejected (401 / 403)
- Trigger a resolver exception → the response should be a sanitized error without stacks / internal paths
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Legitimate queries with valid tokens return normally, and all authorized fields in the schema are usable
- Nested queries within the normal depth range work and are not wrongly rejected
- In production mode (`NODE_ENV=production`), error responses do not leak stacks

### Regression Testing

- Newly added query / mutation / fields in the schema must be included in the authentication rule list before retesting
- Re-verify switches and limit surfaces after introspection / depth limit configuration changes
- Retest the stack leakage surface after error formatting changes

## Evidence References

- `EVID_NODE_CFG_SECURITY_SWITCH` (introspection / playground switches and security configuration evidence)
- `EVID_NODE_CFG_RUNTIME_SETTING` (depth / complexity limits and runtime configuration evidence)
- `EVID_NODE_CFG_ERR_HANDLER` (formattedErrors stack leakage evidence)
- `EVID_NODE_CFG_MIDDLEWARE_ORDER` (resolver authentication rule coverage and execution order evidence)
- `EVID_NODE_NOSQL_RAW_OBJECT_PASS` and `EVID_NODE_NOSQL_OPERATOR_INJECTION` (resolver parameters passing through into query structures, coordinating with node-nosql-audit)
- `EVID_NODE_CMD_USER_PARAM_TO_CMD` (resolver parameters entering command construction, coordinating with node-cmd-audit)

## Output

- `node/framework_audit/graphql_{timestamp}.md`
- Must state: entry endpoints and framework selection (Apollo / express-graphql / mercurius / nestjs-graphql), schema and resolver lists, resolver parameter sources and sanitization status, introspection / playground switches, depth / complexity limits, resolver authentication coverage and uncovered fields, error formatting behavior
- Must state environment differences: development / production configuration branches (introspection / playground), `NODE_ENV` branches, schema stitching / federation deployment differences
- Consumption relationships: when affecting strong vulnerability conclusions, it must be explicitly stated how it is consumed by `node/route_tracer`, each `node-vuln-audit` specialty (nosql / cmd / ssrf / expr, etc.), and `node-audit-pipeline`
