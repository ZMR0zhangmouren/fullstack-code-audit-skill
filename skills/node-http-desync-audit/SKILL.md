---
name: node-http-desync-audit
description: Node.js HTTP request smuggling audit tool. Identifies parsing differences and request smuggling risks between the Node http_parser (llhttp) and proxy chains such as nginx/Envoy/cloud LBs regarding Content-Length and Transfer-Encoding; outputs severity rating, PoC, and remediation recommendations.
---

# Node.js HTTP Request Smuggling (HTTP Desync) Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to CL/TE parsing, proxy chains, header forwarding, and request body boundaries
- If the project has secondary encapsulations such as http-proxy wrappers, ForwardMiddleware, or HeaderRewrite, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **static-evidence-driven + protocol-level testing recommended**: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Priority and conflict handling of `Content-Length` and `Transfer-Encoding` by the Node `http_parser` (llhttp): duplicate CL, CL+TE mixing, TE-TE confusion
- `Transfer-Encoding` header variants: `Transfer-Encoding: xchunked`, spaces in the value / case / comma separation, duplicate headers, `0\r\n\r\n` prefix pollution
- Reverse-proxy parsing differences: how nginx / Envoy / HAProxy / cloud LBs versus the Node backend handle ambiguous messages (TE priority vs rejecting dual headers)
- Version differences in Node 18+ error behavior on illegal headers: llhttp strict mode disconnecting directly versus older versions' lenient acceptance
- Combinations of Node front proxies and backend parsers: `http-proxy` / `http-proxy-middleware` passthrough, deduplication, and rewriting of `rawHeaders`
- Smuggling surfaces formed by TE headers being rewritten or stripped by proxies and then combined with backend Content-Length reads
- This specialty is a protocol-level vulnerability: **practical testing is required; static analysis can only give candidate surfaces**; strong conclusions based on keyword hits alone are forbidden

## Enumeration Rules (Mandatory Refinement)

- Enumerate all occurrences of `http.createServer`, `https.createServer`, `Content-Length`, `content-length`, `Transfer-Encoding`, `transfer-encoding`, `chunked`, `rawHeaders`, `writeHead`, `setHeader`
- Enumerate proxy and forwarding chains: `http-proxy`, `http-proxy-middleware`, `createProxyServer`, `proxy.web(`, `changeOrigin`, `xfwd`
- Enumerate runtime parser configurations: `--http-parser`, `maxHttpHeaderSize`, `headersTimeout`, `requestTimeout`, `keepAliveTimeout`, `maxRequestsPerSocket`
- For each ambiguity point record: the relationship between the CL value and the actual body length, explicit TE values, whether CL and TE coexist in the same request, and whether the proxy rewrites or deduplicates the headers
- If the repository contains deployment configurations (nginx.conf, Envoy yaml, Dockerfile, k8s Ingress), list the proxy-layer parsers and versions as well; when missing, record it as an environment evidence gap
- Record the Node version (engines / Dockerfile base image): 18+ llhttp strict rejection versus lenient behavior on 16 and below

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Parser consistency | CL/TE trade-offs of nginx / Envoy / cloud LBs versus Node llhttp | Compare how front and back ends parse duplicate CL, CL+TE, and TE variants | both ends consistent (both reject ambiguous messages) → ✅ safe; front accepts while back rejects (or vice versa) → 🔴 high-risk candidate |
| Illegal message rejection | Node 18+ llhttp strict mode | Send duplicate CL / illegal TE messages directly to the backend, confirming whether `HPE_*` errors are thrown and the connection dropped | error and disconnect (fail-close) → ✅ safe; lenient acceptance or taking the first value → 🔴 high risk |
| Header passthrough control | `http-proxy` passthrough and rewriting of `rawHeaders` | Check whether the proxy passes through verbatim, deduplicates, or strips `Transfer-Encoding` | verbatim passthrough with consistent parsing on both ends → ✅ safe; deduplication / rewriting introducing ambiguity → 🔴 high-risk candidate |
| Protocol chain consistency | End-to-end HTTP/1.1 versus h2c / downgrade chains | Confirm whether HTTP/2 → HTTP/1.1 downgrade and h2c plaintext upgrade exist | end-to-end protocol consistency → ✅ safe; downgrade points present → ⚠️ requires practical verification |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: an ambiguous message appears to form a smuggling primitive between front-end and back-end parsing differences
- `Pending`: the context shows a suspicious pattern, but the proxy chain, parser version, or message construction path is unclear
- `False Positive`: the message has no ambiguous boundary, or the parsing chain has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found of front-end / back-end parsing differences with the ambiguous message able to pass through → `Confirmed Vulnerability` (practical test records must be attached)
- Evidence of the parsing chain consistently rejecting / fail-close is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: parsers, proxy header handling, and message validation must be evaluated in their failure mode. Illegal / ambiguous messages must error, disconnect, or be rejected — they must never silently take the first value or pass through; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_DESYNC_FRONTEND_VARIANT` + `EVID_NODE_DESYNC_SMUGGLE_PRIMITIVE` + practical test records (timeout differential method or injected `X` header probing confirming successful smuggling)
- `EVID_NODE_DESYNC_PROXY_CHAIN` + `EVID_NODE_DESYNC_HEADER_CONTROL`: the proxy deduplicates / rewrites TE and the backend llhttp parses leniently, and smuggled requests reach sensitive endpoints with side effects

### ⚠️Pending Verification

- A front proxy exists but its configuration is not visible; only static CL/TE ambiguity hits (proxy evidence or practical testing needed)
- Ambiguous messages can be constructed, but timeout differential / `X` header probing has not been performed, and end-to-end smuggling cannot be confirmed

### False Positive

- Node 18+ directly exposed (no front proxy), and llhttp throws errors such as `HPE_UNEXPECTED_CONTENT_LENGTH` on duplicate CL / illegal TE and disconnects (fail-close)
- Proxy and backend parsing behavior is consistent (both reject ambiguous messages), or no constructible ambiguous boundary exists
- End-to-end pure HTTP/2 with no downgrade chain or h2c surface

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct CL+TE dual-header smuggling messages (front end chunks by TE, back end truncates by CL), confirming backend hanging or misaligned parsing via the timeout differential method
- Inject `X` header probing: carry `X-Foo: x` in the smuggled suffix and observe whether the next real request hits the appended header, verifying successful smuggling
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Send duplicate CL / illegal TE directly to a Node 18+ backend, verifying error and disconnect
- Verify nginx default configuration rejects CL+TE dual headers (4xx response)
- Verify consistent front-end / back-end behavior under `http-proxy` passthrough

### Regression Testing

- Retest llhttp strictness and proxy trade-offs after upgrading Node / proxy versions
- Retest whether parsing differences reappear after adding new proxy chains (Envoy / cloud LBs)
- Verify header rewriting logic changes still keep both ends consistent

## Evidence References

- `EVID_NODE_DESYNC_FRONTEND_VARIANT`
- `EVID_NODE_DESYNC_SMUGGLE_PRIMITIVE`
- `EVID_NODE_DESYNC_PROXY_CHAIN`
- `EVID_NODE_DESYNC_HEADER_CONTROL`
- Optional overlays: `EVID_NODE_CFG_RUNTIME_SETTING` (Node version and `--http-parser` runtime configuration evidence), `EVID_NODE_CFG_MIDDLEWARE_ORDER` (front proxy and middleware chain order evidence)

## Output

- `node/vuln_audit/http-desync_{timestamp}.md`
- `node/vuln_poc/http-desync_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
