---
name: dotnet-ssrf-audit
description: .NET SSRF audit tool. Identifies risk paths where user-controllable URLs enter HttpClient, WebRequest, Webhooks, or internal call clients.
---

# .NET SSRF Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to URL sources, HTTP clients, webhooks, callbacks, proxies, and protocol restrictions
- If the project has secondary encapsulations such as ApiClient, WebhookSender, HttpGateway, or CallbackService, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align request-initiating entries, URL sources, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement proxies, hosts, network boundaries, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- request initiation points of HttpClient, HttpRequestMessage, SocketsHttpHandler, WebRequest, RestSharp, or third-party SDKs
- paths where URLs enter request construction from routes, queries, bodies, configuration, databases, message queues, GraphQL parameters, or Hub messages
- handling of Uri, UriBuilder, Path / Query concatenation, protocol-relative addresses, double encoding, userinfo segments, IPv6, and decimal / octal IP representations
- automatic redirect following, proxy configuration, DNS resolution, Host header rewriting, X-Forwarded-* trust boundaries, and second-hop redirects
- business scenarios such as webhook callbacks, open scraping, file / image downloads, OpenID / OAuth discovery, S3 / Blob synchronization, and GraphQL schema introspection pulls
- whether restrictions on dangerous protocols or addresses such as localhost, 169.254.169.254, cloud metadata, intranet CIDRs, Unix sockets, and gopher / file are effective
- whether result echoing, error messages, download content staging, subsequent parsing, or server-side probing amplify the exploitation impact

## Enumeration Rules (Mandatory Refinement)

- Enumerate HttpClient, HttpRequestMessage, WebRequest, RestSharp, Refit, GraphQL clients, webhook clients, and custom downloaders
- Search key fields such as URL, Uri, BaseAddress, RequestUri, Location, callback, webhook, avatar, download, and proxy first
- Enumerate all URL concatenation, normalization, redirect following, DNS resolution, and proxy configuration logic before external request initiation
- For each request point record: source parameter, protocol restrictions, host allowlist, intranet / metadata protection, and the destination of the final returned content

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Post-resolution host / ip validation** | Read the host allowlist / denylist implementation source, confirming validation is based on the resolved host / ip / port (not string blacklists) | fail-close (unknown hosts rejected after resolution) → ✅ safe; string blacklist (such as `Contains("localhost")`) → ⚠️ bypassable; no validation → 🔴 high risk |
| **Protocol restrictions** | Confirm whether request protocols are restricted to `http` / `https`, with `file://`, `gopher://`, `dict://`, and `ftp://` forbidden | strictly restricted and non-bypassable → ✅ safe; frontend-only restrictions or bypassable via encoding → ⚠️ bypassable; no restrictions → 🔴 high risk |
| **Redirect following policy** | Confirm `AllowAutoRedirect` or custom redirect handling, and whether host / ip validation is re-executed after following | re-validated after following → ✅ safe; followed without re-validation → 🔴 high risk; redirects not followed → 🟠 business impact to be assessed |
| **Intranet / CIDR / metadata blocking** | Confirm whether IMDS (`169.254.169.254`), intranet CIDRs (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`) are blocked | fully blocked and non-bypassable → ✅ safe; only some segments blocked or bypasses known → ⚠️ bypassable; no blocking → 🔴 high risk |
| **DNS rebinding protection** | Confirm whether DNS rebinding protection exists (such as post-resolution re-validation, TTL checks, or IP cache pinning) | secondary validation / IP pinning present → ✅ safe; relying on DNS resolution results without secondary validation → ⚠️ to be confirmed |
| **Proxy and forwarding trust boundaries** | Confirm whether `X-Forwarded-Host`, `X-Forwarded-Proto`, and similar headers are blindly trusted, and whether Host header injection can bypass the allowlist | strict validation or distrust of external forwarding headers → ✅ safe; trusting externally supplied forwarding headers → ⚠️ bypassable |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion as "Confirmed Safe" or "False Positive" is forbidden.**

## Two-Phase Determination (Mandatory)

Follow the two-phase determination process of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

1. **Phase 1 (interim conclusion)**: mark each hit as `Confirmed Vulnerability Candidate` / `Pending` / `False Positive` first
2. **Phase 2 (mandatory evidence chasing)**:
   - if Phase 1 is `Confirmed Vulnerability Candidate` → all relevant items of the Barrier verification matrix must be completed before `Confirmed` may be marked
   - if Phase 1 is `Pending` → chase at least one more hop of the call chain or downstream parser downward, until a determination can be made
   - if Phase 2 still cannot close → remain `Pending`, and explicitly record which hop of evidence is missing

## Determination Rules (Mandatory Refinement)

### Confirmed Vulnerability

At least one of the following conditions holds:

1. user-controllable URLs enter request construction of `HttpClient`, `WebRequest`, `RestSharp`, etc. directly, with no host / ip / port validation
2. the host allowlist is `fail-open` or `silent-fallback`, or based on string blacklists rather than post-resolution validation
3. redirects are followed automatically and host / ip validation is not re-executed after following
4. a feasible DNS rebinding path exists (the pre-resolution host is in the allowlist, while the resolved address points to intranet / metadata)
5. in nested / recursive structures (such as multi-layer ApiClient wrappers), the top level has validation but sub-levels do not perform equivalent validation

### Pending

1. the context shows a suspicious pattern (such as an `HttpClient.SendAsync` call), but the external input source is unclear (trace or call chain needs to be supplemented)
2. a barrier function (such as the host allowlist) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
3. parameter passing in asynchronous / queue / event chains (such as message queue consumers processing webhook callbacks) is not closed
4. a redirect policy exists but its implementation is not visible (such as the behavior of a custom `RedirectHandler` being uncertain)

### False Positive

1. the final request target comes from fixed constants / enum mappings, and unknown hosts are refused execution (fail-close allowlist)
2. all recursive levels reuse the same post-resolution host allowlist validator, and the allowlist is fail-close
3. the request target is a fixed base URL, and users control only path / query with strict validation of path / query
4. redirects are not followed, and host validation executes after resolution and pins the IP (anti-DNS-rebinding)

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct requests pointing to `169.254.169.254` (IMDS), `localhost`, `127.0.0.1`, and intranet IPs (such as `10.0.0.1`), verifying SSRF really exists
- **Negative testing**: construct hosts intercepted by the allowlist (such as `evil.com`) and illegal protocols (such as `file:///etc/passwd`), verifying the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced (such as redirect bypasses or DNS rebinding)

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Evidence References

- EVID_SSRF_URL_NORMALIZATION
- EVID_SSRF_FINAL_URL_HOST_PORT
- EVID_SSRF_DNSIP_AND_INNER_BLOCK

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (request surface identification)**: all outbound HTTP / Socket / DNS entries and controllable parameters must be confirmed.
- 🔴 **CHECKPOINT B (destination constraints)**: allowlists / denylists, protocol and port restrictions, and redirect policies must be confirmed.
- 🔴 **CHECKPOINT C (cloud metadata protection)**: IMDS / intranet segment blocking and bypass strategies must be confirmed.
- 🛑 **STOP**: if key destination restrictions are missing or bypassable, outputting a "low risk" conclusion is forbidden.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| URL source to request initiation chain incomplete | back-trace to the RequestUri / BaseAddress construction points | downgrade to `⚠️Pending Verification` |
| post-resolution host / ip / port constraints unclear | complete normalization and post-resolution validation evidence | no low-risk conclusion |
| redirect and intranet blocking strategy evidence insufficient | verify second-hop re-validation and IMDS / CIDR protection | assess conservatively and retain pending items |

🔴 **STOP: when any fallback triggers, outputting "low risk" is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Mandatory shared indexes: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber source) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: persistence paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from directories are forbidden.
- Evidence consistency validation: if graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: confirm at least once before submission that key referenced files are accessible (such as `DOTNET_AUDIT_GRABBER_INDEX.md` and `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Every skill maintains at least 2 typical test cases (one happy path + one complex scenario) and annotates the case IDs in the results.
- Each evaluation round executes `full_test` on at least 1 case; if limited to `dry_run`, `dry_run_reason` and a supplementary test plan must be recorded.
- Pass criteria must simultaneously satisfy: `intent achieved`, `key evidence hit`, and `output format compliant`; if any is not met, "pass" must not be given.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `input constraints` → `execution steps` → `output and acceptance`; missing layers or cross-layer mixing are forbidden.
- A single paragraph is recommended not to exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into the single-source-of-truth section.
- AI-style filler and empty connectives are forbidden (such as "first / second / finally / in summary / to put it simply / in other words"); rewrite them into executable statements upon discovery.

## Quality Gate & Assessment Consistency (Mandatory)

- Execute the minimal gate self-check before output: `input completeness`, `key evidence hit`, and `output path valid` must all be PASS.
- If any of `key evidence missing`, `chain not closed`, or `consistency_check_status=BLOCKED` exists, the conclusion must be downgraded to `BLOCKED`; outputting "Confirmed Exploitable / Deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

- Anti-pattern: interception via string blacklists only. Correct practice: validate based on the resolved host / ip / port.
- Anti-pattern: ignoring second-hop redirects. Correct practice: restrict and re-verify every redirect target.
- Anti-pattern: blocking only 127.0.0.1 without blocking cloud metadata ranges. Correct practice: cover IMDS and intranet CIDRs.
- Anti-pattern: outputting low risk with missing validation. Correct practice: downgrade conservatively and supplement evidence requirements.

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion levels: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose one of three; blank is forbidden).
- Minimum evidence set: at least the five items `Entry Point`, `Controllable Parameter`, `Key Call`, `Security Boundary`, and `Missing Evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softened wording is forbidden: such as "may be at risk / suggested attention / depends on the situation / most likely"; when evidence is insufficient, `⚠️Pending Verification` and the next evidence-supplementing action must be explicitly written.

Minimal output fragment (directly reusable):

```md
- Hit ID: M{hash} (file path fragment + line number + sequence, used for cross-phase tracking and regression alignment)
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameter=...; key call=...; security boundary=...; missing evidence=none
- test_id: T{hash} (associated test case)
- Next action: if gaps exist, supplement the parameter-propagation evidence of trace_id=...
```

## Output

- vuln_audit/ssrf_{timestamp}.md
- Optional: vuln_poc/ssrf_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
