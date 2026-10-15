---
name: node-crlf-audit
description: Node.js CRLF injection audit tool. Identifies \r\n header injection risks in res.setHeader/res.append/res.writeHead and Set-Cookie value concatenation; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js CRLF Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to header write points, Set-Cookie value concatenation, control character filtering, and proxy passthrough
- If the project has secondary encapsulations such as HeaderBuilder, CookieManager, ResponseHelper, or DownloadService, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align output entries, parameter sources, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, reverse-proxy boundaries, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Positions where `\r\n` enters values of `res.setHeader(name, value)` / `res.append(name, value)` / `res.writeHead(status, headers)`
- Version differences (must be stated explicitly): since Node 8, `setHeader`/`writeHead` throw on header values containing illegal characters (`ERR_INVALID_CHAR`); 14.10+ additionally provides the public validation APIs `http.validateHeaderName`/`http.validateHeaderValue` — direct hits going through such APIs are mostly host fail-close, and conclusion strength must be differentiated by Node version
- Still must cover: self-built `http.createServer` with direct `socket.write` packet assembly, `rawHeaders` passthrough, and old Node versions declared with `engines` < 8
- Still must cover: `res.append` concatenation paths, and scenarios where the value is decoded before being written
- Set-Cookie value concatenation: `cookie.serialize` has fieldContentRegExp validation, but handwritten `name=${user}` template concatenation and Domain/Path attribute concatenation lack this protection
- Content-Disposition download file names coming from request parameters or database fields without `\r\n` filtering
- Reverse-proxy origin-rebuilding of responses, internal HTTP clients (axios/got) forwarding backend headers, and downstream service injection scenarios
- Linked surface: log newline injection (winston/pino template strings) is recorded only as an associated risk and does not independently serve as a CRLF-confirmed basis

## Enumeration Rules (Mandatory Refinement)

- Enumerate all header write points: `res.setHeader(`, `res.append(`, `res.writeHead(`, `res.location(`, `res.set(`, `res.cookie(`, `Set-Cookie`, `Content-Disposition`
- Search first for positions where the value source is user input: interpolation of `req.query.`, `req.params.`, `req.body.`, `req.headers.` into header values
- Enumerate filtering implementations: `replace(/[\r\n]/g`, `replace(/\r?\n/`, `encodeURIComponent`, and self-developed stripNewlines/escape utilities
- Enumerate self-built HTTP servers and version boundaries: `http.createServer`, `socket.write`, `rawHeaders`, and the `engines.node` declaration in `package.json`
- For each output point record: header name, value source, filtering logic and decode count, Node version, and whether it is forwarded via reverse proxy / internal client

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Runtime validation | Node built-in header value validation (`ERR_INVALID_CHAR`), `http.validateHeaderValue` | Confirm the Node version and whether the write API triggers built-in validation | Node ≥8 and going through `setHeader`/`writeHead`/`cookie.serialize` → ✅ host interception (conclusion downgraded to environment-dependent); self-built socket assembly / old versions → 🔴 high risk |
| Input filtering | `replace(/[\r\n]/g, '')`, `encodeURIComponent` utilities | Check whether filtering covers `\r`, `\n`, `%0d`, `%0a`, and residuals after double decoding | fail-close full coverage → ✅ safe; filtering only `\n` without `\r` or literal only → ⚠️ bypassable |
| Cookie serialization | `cookie.serialize` (fieldContentRegExp validation) | Check whether Set-Cookie values go through serialize or handwritten template concatenation | via serialize → ✅ safe; handwritten `name=${value}` concatenation → 🔴 high risk |
| Proxy / forwarding boundary | Handling of illegal response headers by nginx/haproxy and internal HTTP clients | Distinguish layer-by-layer behavior across origin rebuild, forwarding, and direct-connect scenarios | proxy drops / errors → ✅ safe; passes raw value through → ⚠️ to be verified |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter a header value and may carry `\r\n`
- `Pending`: the context shows a suspicious pattern, but the value source, filtering behavior, or runtime interception is unclear
- `False Positive`: the value comes from fixed constants / enum mappings, or runtime validation has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found that externally controllable input carrying control characters enters the header write point → `Confirmed Vulnerability`
- Fixed constant mapping / fail-close filtering or host interception evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_CRLF_HEADER_WRITE_POINT` + `EVID_NODE_CRLF_PAYLOAD_CONTROL` (value contains `\r\n` and is controllable), and the runtime is confirmed not to trigger Node built-in validation (self-built assembly / old version / internal forwarding rebuilding the response)
- Set-Cookie values use handwritten template concatenation and the filtering is fail-open (only filtering `\n` without `\r`, or not covering double decoding)
- `EVID_NODE_CRLF_VALIDATE_STRIP` evidence shows the filter can be bypassed by `%0d%0a` double encoding and the output point is reachable

### ⚠️Pending Verification

- The output point is hit, but evidence of the Node version / `engines` declaration and runtime validation behavior is insufficient
- A filter exists, but the decode count and the coverage of `\r` and `\n` cannot be confirmed
- Layer-by-layer behavior in reverse-proxy origin-rebuild scenarios requires environment verification

### False Positive

- The output point has no user input mapping; the value comes from fixed constants
- Node ≥8 and all header writes go through `setHeader`/`writeHead`/`cookie.serialize`, with host fail-close interception (`EVID_NODE_CRLF_HEADER_WRITE_POINT` + `EVID_NODE_CRLF_VALIDATE_STRIP` dual evidence closed)

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct `?name=a%0d%0aX-Injected: 1` and double-encoded `%250d%250a` to verify actual response header injection
- Verify that Set-Cookie value concatenation can split responses under self-built HTTP servers / old Node versions
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Values containing `\r\n` are rejected with a Node error via `setHeader`/`cookie.serialize` (fail-close)
- The filter intercepts all of `\r`, `\n`, `%0d`, `%0a`, and double-decoded inputs
- Verify the proxy layer drops / errors on illegal response headers

### Regression Testing

- Retest after remediation, confirming the filter and runtime validation remain effective
- Retest that newly added header write points uniformly integrate serialize / filtering utilities
- Verify the `validateHeaderValue` validation path is not removed after a Node version upgrade

## Evidence References

- `EVID_NODE_CRLF_HEADER_WRITE_POINT`
- `EVID_NODE_CRLF_PAYLOAD_CONTROL`
- `EVID_NODE_CRLF_VALIDATE_STRIP`
- Optional overlays: `EVID_NODE_CFG_RUNTIME_SETTING` (Node version / `engines` runtime boundary), `EVID_NODE_CFG_MIDDLEWARE_ORDER` (filter middleware mount order)

## Output

- `node/vuln_audit/crlf_{timestamp}.md`
- `node/vuln_poc/crlf_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
