---
name: node-ssrf-audit
description: Node.js SSRF audit tool. Identifies controllable server-side axios/fetch/got/request/undici URLs and redirect-following bypass risks; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js SSRF Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to server-side HTTP client calls, URL concatenation, and redirect configuration
- If the project has secondary encapsulations such as HttpClient, WebHookClient, or RequestHelper, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, serialization configuration, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Controllable server-side `axios` / `fetch` / `got` / `request` / `undici` URLs
- Allowlist bypass via redirect following
- Missing validation of protocols (`file:` / `gopher:`) and intranet segments

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites of `axios.`, `fetch(`, `got(`, `request(`, `undici`, `http.get`, `https.get`, `followRedirects`, `maxRedirects`
- For each call site record: HTTP client package name, URL construction method (concatenation / template string / `baseURL` + `url`), and parameter sources
- Record redirect-related configuration: `followRedirects`, `maxRedirects`, `beforeRedirect` callbacks, and protocol restrictions
- Record URL validation logic: protocol whitelists, host whitelists, post-DNS-resolution IP validation, and intranet segment blocking
- Identify special protocol risks: whether `file://`, `gopher://`, `dict://`, `ftp://` are explicitly forbidden
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real HTTP client call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| URL allowlist | Protocol + host + port whitelist | Read the allowlist implementation, checking protocol restrictions (http / https only), host matching method, and port ranges | fail-close and dangerous protocols such as `file` / `gopher` forbidden → ✅ safe; wildcards allowed or origin reflected → ⚠️ to be confirmed; no allowlist → 🔴 high risk |
| Post-DNS IP validation | Resolving the URL host and checking whether the IP belongs to intranet / reserved ranges | Check whether the code does `dns.lookup` before validation, preventing DNS rebinding | validated after resolution covering IPv4 / IPv6 / short forms / CIDR → ✅ safe; hostname regex matching only → ⚠️ to be confirmed; no validation → 🔴 high risk |
| Redirect control | `followRedirects` / `maxRedirects` | Check the HTTP client configuration: whether redirect following is disabled or re-validated hop by hop | following disabled or allowlist / DNS validation re-executed per hop → ✅ safe; automatic following allowed without per-hop validation → 🔴 high risk |
| Response restrictions | Response size / timeout limits | Check whether `timeout` / `maxBodyLength` / `responseType` / maximum read bytes are configured | limits present and fail-close (exceptions / truncation on exceed) → ✅ safe; no limits → ⚠️ to be confirmed |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter HTTP client URL parameters or redirect targets
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

- `EVID_NODE_SSRF_HTTP_CALL_POINT` + `EVID_NODE_SSRF_URL_CONSTRUCTION` + no effective Barrier
- Externally controllable parameters enter URL strings or `baseURL` / `url` concatenation positions directly, with no allowlist / DNS validation
- An allowlist exists but is bypassable via redirect following (e.g., no per-hop validation, allowing 302 to intranet)
- Dangerous protocols such as `file:` / `gopher:` are not disabled, and users can control the protocol portion

### ⚠️Pending Verification

- The context shows a suspicious HTTP call, but the external input source is unclear (trace or call chain needs to be supplemented)
- Allowlist / DNS validation exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
- Key evidence such as `EVID_NODE_SSRF_REDIRECT_FOLLOW` or `EVID_NODE_SSRF_ALLOWLIST` is missing

### False Positive

- URLs are fully static or the allowlist is non-bypassable (fail-close)
- Post-DNS IP validation covers intranet / reserved ranges, and redirects are disabled or validated per hop
- Dangerous protocols are explicitly disabled, and unknown protocols are directly rejected

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct intranet target URLs: `http://127.0.0.1:22/`, `http://169.254.169.254/latest/meta-data/`, `http://[::1]/`
- Construct dangerous protocol payloads: `file:///etc/passwd`, `gopher://127.0.0.1:6379/_INFO`
- Construct redirect bypasses: 302 from an out-of-allowlist domain to the intranet, verifying per-hop interception
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct inputs intercepted by barriers: protocols other than http / https, hosts not in the allowlist, DNS-resolved intranet addresses
- Verify allowlist handling of case / encoding / port variants
- Verify redirects are not automatically followed when `followRedirects:false` or `maxRedirects:0`

### Regression Testing

- Retest after remediation, confirming allowlist / DNS validation / redirect control remain effective
- Retest protocol whitelists and intranet segment blocking, confirming no new bypass paths were introduced
- Verify newly allowlisted hosts remain fail-close

## Evidence References

- `EVID_NODE_SSRF_HTTP_CALL_POINT`
- `EVID_NODE_SSRF_URL_CONSTRUCTION`
- `EVID_NODE_SSRF_ALLOWLIST`
- `EVID_NODE_SSRF_REDIRECT_FOLLOW`

## Output

- `node/vuln_audit/ssrf_{timestamp}.md`
- `node/vuln_poc/ssrf_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
