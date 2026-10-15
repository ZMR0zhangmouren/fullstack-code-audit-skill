---
name: dotnet-http-desync-audit
description: .NET HTTP Desync / Request Smuggling audit. Identifies HTTP request smuggling risks such as Content-Length vs Transfer-Encoding conflicts, proxy inconsistencies, and request prefix truncation; outputs severity rating, evidence, and remediation recommendations.
---

# .NET HTTP Desync / Request Smuggling Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the following HTTP Desync-related shared grabbers:
  - **Entry definition grabbers**: Minimal API (MapGet / MapPost / MapGroup), MVC Controllers, Middleware pipelines
  - **Binding and conversion grabbers**: FromBody, FromForm, Request.Body, Request.ContentLength, Request.ContentType
  - **Precondition control grabbers**: UseRouting, UseCors, ForwardedHeaders, custom request-processing middleware
  - **Security configuration grabbers**: Kestrel configuration, IIS / Nginx reverse proxy configuration, AddKestrel
- If the project has HTTP client wrappers (HttpClientFactory, custom HttpMessageHandler), they must be added to the project-internal grabbers section of the output

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement Kestrel configuration, reverse proxy middleware, and request processing pipelines)
- If this is a trace-gate specialty: prioritize consuming `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If this is a static-evidence-driven specialty: `route_tracer/*` serves only as cross-reference evidence, not as a hard precondition
- This specialty is of the **static-evidence-driven + framework configuration dependency** type; the core analysis is based on HTTP request parsing configuration and proxy layer behavior

## Key Checks

### 1. Content-Length vs Transfer-Encoding conflicts

- boundary behavior when both `Request.ContentLength` and `Request.Headers["Transfer-Encoding"]` exist
- ASP.NET Core Kestrel's handling strategy for CL / TE conflicts (RFC 7230 compliance)
- logic of custom `RequestDelegate` or middleware manually reading `Request.Body`
- `EnableRequestDelegateRewind` and request rewind configuration

### 2. Transfer-Encoding parsing behavior

- parsing entry points of `Transfer-Encoding: chunked`
- handling of incomplete or malformed chunked encoding
- case, spaces, and cascading handling of `Transfer-Encoding` values
- handling of chunked data by custom stream wrappers

### 3. Proxy layer inconsistency

- `ForwardedHeaders.InternalProxies` and `ForwardedHeadersOptions` in the `UseForwardedHeaders` configuration
- trust boundaries of X-Forwarded-For, X-Forwarded-Proto, and X-Forwarded-Host
- protocol inconsistency between proxy and backend (HTTP / 1.1 vs HTTP / 2 or h2c)
- header handling differences when Nginx / Apache / IIS act as reverse proxies
- connection header handling at the load balancer layer

### 4. HTTP / 2 request smuggling

- protocol downgrade points from HTTP / 2 to HTTP / 1.1
- pseudo-header injection risks in HEADERS frames
- request boundary confusion caused by `SO_REUSEADDR` / connection reuse
- boundaries of the HTTP / 2 preface and HTTP / 1.1 upgrade requests

### 5. Request prefix truncation

- early termination handling caused by exceptions in the request pipeline
- residual data after middleware pipeline short-circuits (`next()` not called)
- inconsistent request body reads after response start
- request stream state after error pages or redirects

### 6. Response splitting correlation (Response Tail Injection)

- correlation between response header output points and user input
- dynamic setting of `Response.Headers` and `Response.Cookies`
- request information echoing in error responses
- header injection in custom error handling

### 7. Kestrel-specific configuration

- `KestrelServerOptions.AddServerHeader` configuration
- `ListenOptions.Protocols` settings (HTTP / 1.1, HTTP / 2, h2c)
- `KeepAliveTimeout` and `RequestHeadersTimeout` configuration
- `Http2.MaxConcurrentStreams` settings

## Enumeration Rules (Mandatory Refinement)

### CL / TE conflict enumeration

Search keywords:
- `Request.ContentLength`
- `Request.Headers["Transfer-Encoding"]`
- `Request.EnableBuffering`
- `Request.Body`
- `ReadAsync`, `ReadToEnd`, `CopyToAsync` in `HttpRequest`
- `TransferCoding`, `TransferEncoding`
- `ContentLength`, `Content-Length`

Enumeration record requirements:
- record each combination point of `Request.ContentLength` and `Request.Body` reads
- record deviations between the CL value and the actual body length
- record the `EnableRequestDelegateRewind` configuration (if it exists)
- record any manual ContentLength validation logic

### Proxy configuration enumeration

Search keywords:
- `UseForwardedHeaders`
- `ForwardedHeadersOptions`
- `InternalProxies`
- `KnownProxies`
- `XForwardedForHeaderName`
- `XForwardedProtoHeaderName`
- `XForwardedHostHeaderName`
- `KnownNetworks`
- `KestrelServerOptions`
- `AddKestrel`
- `ConfigureKestrel`
- `IISIntegrationMiddleware`

Enumeration record requirements:
- record the configuration completeness and trust boundaries of `UseForwardedHeaders`
- record the coverage of the KnownProxies / KnownNetworks lists
- record proxy protocol version configuration (HTTP / 1.1, HTTP / 2)
- record any custom header cleanup logic

### HTTP / 2 configuration enumeration

Search keywords:
- `HttpProtocols`
- `Http2`
- `Http1AndHttp2`
- `HttpProtocolVersion`
- `IConnectionLifecycleFeature`
- `IHttpProtocolFeature`
- `Protocol`

Enumeration record requirements:
- record HTTP / 2 enablement status and protocol version configuration
- record any HTTP / 2 to HTTP / 1.1 downgrade configuration
- record h2c (clear text HTTP / 2) configuration
- record connection reuse configuration

### Request processing pipeline enumeration

Search keywords:
- `app.Use`
- `app.Run`
- `app.Map`
- `RequestDelegate`
- `Middleware`
- `next()`
- `await _next(context)`
- `context.Response`
- `context.Request.Body`
- `IApplicationBuilder`

Enumeration record requirements:
- record request body read operations in all custom middleware
- record the middleware pipeline order (especially short-circuit points that do not call `next()`)
- record any logic that continues reading the request after Response Start
- record the impact of exception handling middleware on the request stream

### Response splitting enumeration

Search keywords:
- `Response.Headers`
- `Response.Cookies`
- `Response.AppendHeader`
- `Response.SetCookie`
- `IActionResult`
- `ContentResult`
- `RedirectResult`
- `StatusCodeContext`
- `OnStarting`
- `OnCompleted`

Enumeration record requirements:
- record the correlation between dynamic header setting points and user input
- record user input sources in cookies
- record any request information echoing in error responses
- record custom implementations of status code pages

## Barrier Verification Matrix (Mandatory)

Evaluate per the fail-close three-level standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Level | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Level 1 | proxy-backend parsing chain has differences | the front proxy (Nginx / IIS / ALB) and the ASP.NET Core backend parse CL / TE / chunking inconsistently | BLOCKED → no parsing difference evidence; the specialty ends |
| Level 2 | message ambiguity constructible | ambiguities such as CL / TE conflicts, malformed chunking, and HTTP / 2 downgrade can actually be constructed and pass through the proxy | BLOCKED → conclusion downgraded to `⚠️Environment-Dependent` |
| Level 3 | smuggled request reaches sensitive endpoints | smuggled requests can access sensitive interfaces such as authentication / payment / admin and produce actual side effects | PARTIAL → only output theoretical risks and verification steps |

## Two-Phase Determination Process (Mandatory)

- **Phase 1 (initial screening hit)**: hit a CL / TE conflict point, proxy configuration difference, or HTTP / 2 downgrade configuration, and output `hit ID: M{hash}`.
- **Phase 2 (refined confirmation)**:
  1. confirm the order and behavioral differences of the front proxy-backend parsing chain (CL / TE priority, chunk boundary handling);
  2. verify whether message ambiguity can actually be constructed and pass through the proxy layer;
  3. assess whether smuggled requests can reach sensitive endpoints and produce side effects;
  4. if all three-level Barriers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priorities (Mandatory)

1. **Confirmed Vulnerability**: parsing chain difference exists + message ambiguity constructible + smuggling reaches sensitive endpoints. Output `Confirmed Vulnerability`.
2. **Pending**: parsing differences or configuration evidence partially exists, but proxy behavior or end-to-end exploitability cannot be confirmed. Output `Pending`.
3. **False Positive / No Risk**: proxy and backend parsing behavior is consistent (both RFC 7230 compliant), or no constructible ambiguity boundary exists. Output `False Positive` with the determination basis.

## Testing Recommendations and Minimal Trigger Conditions (Mandatory)

- **Minimal trigger conditions**:
  - a front reverse proxy (Nginx / Apache / IIS / ALB) and an ASP.NET Core backend exist
  - the proxy and backend handle CL / TE priority, chunk boundaries, or HTTP / 2 downgrade inconsistently
  - ambiguous requests can be constructed to pass through the proxy and be parsed by the backend as independent requests
- **Test case suggestions**:
  - Happy Path: normal requests are parsed correctly, and proxy and backend behavior is consistent
  - Boundary / ambiguity: CL + TE dual-header conflicts, malformed chunk lengths, HTTP / 2 pseudo-header injection, connection reuse boundary confusion
- Each hit output appends `hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Evidence References

- EVID_DESYNC_CL_T_CONFLICT: Content-Length vs Transfer-Encoding conflict
- EVID_DESYNC_PROXY_INCONSISTENCY: proxy layer inconsistency
- EVID_DESYNC_REQUEST_PREFIX_TRUNCATION: request prefix truncation
- EVID_DESYNC_HTTP2_SMUGGLING: HTTP / 2 request smuggling
- EVID_DESYNC_RESPONSE_TAIL_INJECTION: response tail injection

## Failure and Degradation Branches (Mandatory)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| cannot confirm the real proxy layer configuration (only application code seen) | output application-side evidence and mark the missing proxy configuration files | downgrade the conclusion to `⚠️Environment-Dependent`; "Confirmed Exploitable" is forbidden |
| CL / TE only has theoretical conflicts, missing reachable request paths | retain the conflict points and supplement entry mapping | classify into the pending-evidence risk pool, with trace_status at least PARTIAL |
| HTTP / 2 downgrade chain unconfirmable | record protocol configuration and downgrade assumptions | output "joint debugging verification required"; give no P0 strong conclusion |
| middleware order undeterminable (multi-environment differences) | output the main path per the known startup configuration | supplement "environment difference branches" and downgrade the conclusion |

🔴 **STOP: when key environment evidence is missing, outputting "Confirmed Exploitable" wording is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Mandatory shared indexes: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber source) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: persistence paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from directories are forbidden.
- Evidence consistency validation: if graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: confirm at least once before submission that key referenced files are accessible (such as `DOTNET_AUDIT_GRABBER_INDEX.md` and `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Execute at least 2 typical test cases before each output (one happy path + one boundary / ambiguity scenario), and record expected vs actual differences.
- `full_test >= 1` is required by default; if only `dry_run` is possible, `confidence=LOW` must be marked in the conclusion, with a supplementary test plan and owner given.
- Pass criteria: key fields complete, evidence chains traceable, conclusion levels consistent with gate status; if any fails, marking "passed / deliverable" is forbidden.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `input constraints` → `execution steps` → `output and acceptance`; missing layers or cross-layer mixing are forbidden.
- A single paragraph is recommended not to exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into the single-source-of-truth section.
- AI-style filler and empty connectives are forbidden (such as "first / second / finally / in summary / to put it simply / in other words"); rewrite them into executable statements upon discovery.

## Quality Gate & Assessment Consistency (Mandatory)

- Execute the minimal gate self-check before output: `input completeness`, `key evidence hit`, and `output path valid` must all be PASS.
- If any of `key evidence missing`, `chain not closed`, or `consistency_check_status=BLOCKED` exists, the conclusion must be downgraded to `BLOCKED`; outputting "Confirmed Exploitable / Deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

| # | Anti-pattern | Why not | Correct practice |
|---|---|---|---|
| 1 | judging smuggling valid based only on keyword hits | desync depends on end-to-end parsing differences | proxy-backend inconsistency evidence must be given |
| 2 | ignoring HTTP / 2 / 1.1 protocol boundaries | protocol downgrade determines exploitability | the protocol chain and downgrade points must be explicitly recorded |
| 3 | writing "Pending" as "high-risk confirmed" | it pollutes the conclusion strength of exploit chains | use the Pending / Environment-Dependent grading |

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (chain topology confirmation)**: the parsing chain order of the front proxy, gateway, and application server must be confirmed.
- 🔴 **CHECKPOINT B (message ambiguity confirmation)**: differences in CL / TE, chunking, and composite header handling must be confirmed.
- 🔴 **CHECKPOINT C (exploitation consequence confirmation)**: whether request smuggling can reach sensitive endpoints must be confirmed.
- 🛑 **STOP**: if the chain topology and parsing differences are not closed, the conclusion is downgraded to `⚠️Pending Verification`.

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion levels: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose one of three; blank is forbidden).
- Minimum evidence set: at least the five items `Entry Point`, `Controllable Parameter`, `Key Call`, `Security Boundary`, and `Missing Evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softened wording is forbidden: such as "may be at risk / suggested attention / depends on the situation / most likely"; when evidence is insufficient, `⚠️Pending Verification` and the next evidence-supplementing action must be explicitly written.

Minimal output fragment (directly reusable):

```md
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameter=...; key call=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement the parameter-propagation evidence of trace_id=...
```

## Output

- vuln_audit/http-desync_{timestamp}.md
- vuln_poc/http-desync_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC)

### Output File Structure

```
vuln_audit/http-desync_{timestamp}.md
├── # HTTP Desync / Request Smuggling Audit Report
├── ## Summary
│   ├── finding count
│   ├── high-risk item list
│   └── suggested priorities
├── ## CL / TE Conflict Analysis
│   ├── conflict point list (route_id + code location + evidence)
│   └── risk rating
├── ## Proxy Configuration Analysis
│   ├── configuration completeness assessment
│   ├── trust boundary assessment
│   └── inconsistency list
├── ## HTTP / 2 Smuggling Analysis
│   ├── protocol downgrade points
│   └── smuggling vector assessment
├── ## Request Processing Pipeline Analysis
│   ├── middleware order diagram
│   └── truncation risk points
├── ## Response Splitting Analysis
│   ├── dynamic header setting points
│   └── injection vector assessment
├── ## Project-Internal Grabber Supplement
│   ├── private wrappers
│   └── special configurations
└── ## Remediation Suggestions
    ├── Kestrel configuration optimization
    ├── proxy configuration hardening
    └── request validation strengthening
```

### vuln_poc Structure

```
vuln_poc/http-desync_{timestamp}.md
├── # HTTP Desync PoC Template
├── ## CL / TE Conflict PoC
│   └── request template
├── ## Proxy Smuggling PoC
│   └── request template
├── ## HTTP / 2 Smuggling PoC
│   └── request template
└── ## Verification Method
    └── test steps
```
