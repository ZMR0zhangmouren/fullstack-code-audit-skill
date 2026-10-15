---
name: dotnet-config-audit
description: .NET configuration security audit tool. Identifies misexposure, CORS, security headers, debug and dangerous switch risks in appsettings, web.config, launchSettings, and middleware configuration.
---

# .NET Configuration Security Audit

## Shared Grabber Index References

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as this Skill's base retrieval index
- By default, use shared/DOTNET_SINK_REFERENCE.md as this specialty's sink type definition and trace-gate validation baseline
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover shared grabbers related to appsettings, web.config, environment variables, Options binding, runtime overrides, and security switches
- If the project has secondary encapsulations such as ConfigHelper, FeatureFlagService, TenantSettingsProvider, SecretResolver, they must be added to the in-project grabbers section of the output
- When this Skill's specialty enumeration rules are more detailed than the shared index, this Skill prevails, but the shared index's base coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to correlate affected entries, functional surfaces, and `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to correlate anonymous entries, P0/P1 bucketing, and authorization boundaries)
- Optional: `route_tracer/{route_id}/trace_{timestamp}.md` and `route_tracer/{route_id}/trace_summary_{timestamp}.md` (can serve as cross evidence of configuration impact on specific entries; not a hard prerequisite)

Key checks:

- Exposure of DeveloperExceptionPage, DetailedErrors, Swagger/OpenAPI, GraphQL Playground, Hangfire Dashboard, health checks, metrics, and diagnostic pages
- CORS allow-any, AllowCredentials, security headers, HSTS, HTTPS redirection, CookiePolicy, StaticFile configuration, and cache headers
- appsettings.*, appsettings.{Environment}.json, web.config, launchSettings, User Secrets, environment variables, KeyVault/Secrets Manager merge and override order
- Reverse proxies, ForwardedHeaders, KnownProxies/KnownNetworks, PathBase, Host header trust, TLS termination, and real client IP determination boundaries
- DataProtection key storage, connection strings, log levels, feature flags, experiment switches, tenant configuration, and default account configuration
- Debug/trace/sandbox/test endpoints, file browsers, directory listings, static file mappings, Razor Runtime Compilation, and other dangerous switches
- Whether configuration only takes effect in development, or is exposed in production due to wrong environment checks, container variable mismatches, or pipeline release mistakes

## Key Checks

- CORS configuration: AllowAnyOrigin + AllowCredentials combination, permissive SetIsOriginAllowed policies, wildcard subdomains
- Error exposure: UseDeveloperExceptionPage in non-development environments, detailed exceptions returned to clients, stack trace leakage
- Missing security headers: X-Content-Type-Options, X-Frame-Options, CSP, HSTS, Referrer-Policy
- Dangerous switches: debug mode, Swagger/HealthCheck exposure, Hangfire Dashboard without authorization, static file directory listings
- Proxy trust: improper ForwardedHeaders configuration, missing HostFiltering, PathBase override
- Configuration overrides: environment variables overriding security settings, appsettings.Development.json leaked to production
- Kestrel limits: secure defaults for request size, connection timeouts, and concurrency limits

## Evidence References

- EVID_CFG_CONFIG_LOCATION
- EVID_CFG_RUNTIME_SETTING_CODE
- EVID_CFG_IMPACT_ASSOCIATION
- EVID_CFG_SECURITY_SWITCH_EVIDENCE

## Enumeration Rules (Mandatory Refinement)

- Enumerate appsettings*.json, web.config, launchSettings, User Secrets, environment variables, KeyVault/Secret Manager, Helm/container configuration maps
- Search with priority: UseDeveloperExceptionPage, UseSwagger, AllowAnyOrigin, ForwardedHeaders, Kestrel, DataProtection, StaticFiles, FeatureFlag, and other key configuration items
- Enumerate runtime configuration overrides, environment branches, and default values in Program.cs / Startup.cs / extension methods
- For each configuration point record: configuration location, runtime code, impact surface, environment-scoped conditions, and whether it is a security switch

## Barrier Verification Matrix (Mandatory)

Assess against the fail-close three-tier standard in `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Tier | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Tier 1 | Configuration items exist and affect runtime modifiable behavior | Security-behavior-affecting configuration items exist in appsettings/web.config/environment variables/KeyVault | BLOCKED → no security-related configuration items; the specialty ends |
| Tier 2 | Dangerous configuration items enabled | DeveloperExceptionPage/Swagger/AllowAnyOrigin+AllowCredentials/Hangfire Dashboard/debug switches enabled in production | BLOCKED → dangerous configuration items are all off or environment-scoped; conclusion degraded |
| Tier 3 | Configuration impact reaches sensitive endpoints | Overly permissive CORS/missing security headers/improper proxy trust causes sensitive endpoint exposure or cross-origin exploitation | PARTIAL → only potential risks and verification steps are output |

## Two-Phase Determination Flow (Mandatory)

- **Phase 1 (Initial Screening Hit)**: security-related configuration items + dangerous configuration switches + configuration impact surface hit; output `Hit ID: M{hash}`.
- **Phase 2 (Refined Confirmation)**:
  1. Trace in reverse: configuration item → runtime code → affected endpoint/component chain;
  2. Verify whether dangerous configurations such as DeveloperExceptionPage/Swagger/CORS/debug switches are enabled in non-development environments;
  3. Assess the impact of CORS policies, security headers, and proxy trust configuration on sensitive endpoint exposure;
  4. If all three barrier tiers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priority (Mandatory)

1. **Confirmed Vulnerability**: security configuration items exist + dangerous configuration enabled in non-development + configuration causes sensitive endpoint exposure. Output `Confirmed Vulnerability`.
2. **Pending Confirmation**: configuration items exist but environment-scoped conditions or runtime override evidence is insufficient. Output `Pending Confirmation`.
3. **False Positive / No Risk**: all dangerous configurations only enabled in development with strict production restrictions, security headers complete, CORS strict, proxy trust boundaries correct. Output `False Positive` with determination basis.

## Testing Suggestions and Minimum Trigger Conditions (Mandatory)

- **Minimum Trigger Conditions**:
  - Configuration sources such as appsettings/web.config/environment variables/KeyVault exist
  - Dangerous configuration items (DeveloperExceptionPage/AllowAnyOrigin/Swagger/debug switches) enabled in non-development environments
  - Or CORS/security headers/proxy trust configuration causes sensitive endpoint exposure
- **Test Case Suggestions**:
  - Happy Path: under normal configuration, security controls are in effect and dangerous configurations are only enabled in development
  - Edge/Ambiguity: environment variables overriding security settings, appsettings.Development.json leaked to production, container variable mismatch, Kestrel request size limit bypass
- Each hit output appends `Hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Evidence References

Evidence references:

- EVID_CFG_CONFIG_LOCATION
- EVID_CFG_RUNTIME_SETTING_CODE
- EVID_CFG_IMPACT_ASSOCIATION
- EVID_CFG_SECURITY_SWITCH_EVIDENCE

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (e.g. `route_mapping` / `route_tracer` / `framework_audit`), confirm dependencies are available and timestamps are consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: write to the agreed path per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing-evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (Configuration Source Confirmation)**: the override order of configuration files, environment variables, and runtime code must be confirmed together.
- 🔴 **CHECKPOINT B (Environment Boundary Confirmation)**: Development/Production effect conditions must be distinguished before drawing conclusions.
- 🔴 **CHECKPOINT C (Affected Entry Confirmation)**: the mapping of configuration items to affected entries/components must be given.
- 🛑 **STOP**: if the final runtime-effective value cannot be confirmed, the conclusion is degraded to `⚠️Environment-Dependent`; strong conclusions are forbidden.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback if Still Failing |
|---|---|---|
| Final effective configuration value unconfirmable | Align file, environment variable, and code override priorities | Conclusion degraded to `⚠️Environment-Dependent` with missing sources listed |
| Environment branch (Dev/Prod) evidence conflicts | Give configuration evidence and impact surface per environment separately | Adopt the most conservative standard; no strong conclusion |
| Missing configuration-to-entry component mapping | Supplement affected endpoint/component chains | List as Pending Verification risk; a "no risk" conclusion is forbidden |

🔴 **STOP: when any fallback is triggered, outputting "configuration is secure" is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Required shared index references: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber sources) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: on-disk paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from the directory structure are not allowed.
- Evidence consistency validation: if severity-graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: before submission, confirm at least once that key referenced files are accessible (e.g. `DOTNET_AUDIT_GRABBER_INDEX.md`, `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Execute at least 2 typical test cases before each output (happy path + 1 edge/ambiguity scenario), and record expected vs actual differences.
- `full_test >= 1` is required by default; if only `dry_run` is possible, `confidence=LOW` must be marked in the conclusion, with a make-up test plan and owner.
- Pass criteria: key fields complete, evidence chain traceable, conclusion level consistent with gate status; if any fails, marking "passed/deliverable" is forbidden.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `Input Constraints` → `Execution Steps` → `Output and Acceptance`; no layer may be missing or mixed across layers.
- A single paragraph should not exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into a single source-of-truth section.
- AI-isms and empty filler transitions are forbidden (e.g. "first/second/finally/in summary/put simply/in other words"); any found must be rewritten as executable statements.

## Quality Gate & Assessment Consistency (Mandatory)

- A minimal gate self-check must be executed before producing output: `input completeness`, `key evidence hit`, `output path valid` — all three must be PASS.
- If any of `key evidence missing`, `chain not closed`, `consistency_check_status=BLOCKED` holds, the conclusion must be degraded to `BLOCKED`; outputting "confirmed exploitable/deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with the `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

- Anti-pattern: drawing conclusions from static appsettings values alone. Correct approach: also verify environment variables and runtime overrides.
- Anti-pattern: confusing development and production configuration. Correct approach: annotate effect conditions and differences per environment.
- Anti-pattern: ignoring proxy and host differences. Correct approach: make the Kestrel/IIS/reverse-proxy boundary explicit.
- Anti-pattern: giving strong conclusions with unclosed evidence. Correct approach: degrade to `⚠️Environment-Dependent` and list missing items.

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion level: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose exactly one; leaving blank is forbidden).
- Minimum evidence set: must include at least the five items `entry point`, `controllable parameters`, `key calls`, `security boundary`, `missing evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softening wording is forbidden: e.g. "possibly at risk / worth noting / depends on the situation / very likely"; when evidence is insufficient, must explicitly write `⚠️Pending Verification` and the next follow-up confirmation action.

Minimal output snippet (directly reusable):

```md
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameters=...; key calls=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement parameter propagation evidence for trace_id=...
```

## Output

- vuln_audit/cfg_{timestamp}.md
- Optional: vuln_poc/cfg_{timestamp}.md (if a reproduction request can be constructed or explicit verification steps exist)

## Mechanism Extension: Security Configuration Exposure and Response Information Disclosure (2026-09-14 Ledger Round)

### Mechanism Description and Boundary

This extension covers two exposure chains:

- **Internal information disclosure chain**: route/config request → documentation/config/metadata response → internal information exposure. Unauthorized requesters obtain internal implementation details, deployment configuration, and middleware information from responses.
- **Secret leakage chain**: response field → secret material → credential leakage. Responses directly carry credential material such as connection strings, private keys, and access keys.

Ledger boundary (verbatim): secret material findings are prioritized into the secret exposure path; public and expected API documentation is not judged as a vulnerability.

### Key Checks and Enumeration Grabbers

Record for each hit: file, line number, endpoint/response point, and exposed content type.

- **Configuration/metadata endpoints**: `IConfiguration` full export / debug endpoints, `/swagger` (including all Swashbuckle documentation and schema exposure), `/hangfire` Dashboard, `/healthchecks` (detail-level health check exposure of dependency information), `Web.config` / `appsettings*.json` downloadable, IIS directory browsing.
- **Error response disclosure**: `DeveloperExceptionPage` enabled in production, `UseDeveloperExceptionPage` not conditioned on environment, error responses carrying stack/configuration details, `IncludeScopes` leaking log scopes (including internal state), `DetailedErrors` enabled.
- **Secret patterns in responses**: connection strings (`Server=`/`Data Source=` with passwords), `-----BEGIN PRIVATE KEY-----` / `-----BEGIN RSA PRIVATE KEY-----`, AKIA-style access keys, JWTs hardcoded in responses or frontend configuration, storage account keys.

### Verification Matrix

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Endpoint access control** | Issue an unauthorized request to a configuration/metadata endpoint and confirm whether authentication + authorization is required | Unauthorized rejected or only expected public docs → ✅ Safe; unauthorized access to internal information → 🔴 High-risk Pending Confirmation |
| **Production error page convergence** | Trigger an exception under production configuration and confirm the response is a unified error page without stack/configuration/scope details | Unified convergence → ✅ Safe; leaks stack/configuration/internal paths → 🔴 High-risk Pending Confirmation |
| **Secret pattern scanning and response interception** | Scan response bodies for secret patterns such as connection strings, private key headers, AKIA, JWTs, and trace their paths into responses | No secrets in responses → ✅ Safe; detected with locatable source → 🔴 High-risk Pending Confirmation |
| **Public documentation whitelist** | Confirm whether an exposed documentation endpoint is expected to be public (e.g. public API documentation) and exclude by expectation | Expected public → not a vulnerability; unexpected public → ⚠️ Pending Confirmation |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion "Confirmed Safe" or "False Positive" is forbidden.**

### Determination Rules

Confirmation requires closing EVIDs per path:

**Internal information path** requires simultaneously closing the following two EVIDs; none may be missing:

1. **Endpoint exposure surface closure**: evidence that route/config/metadata endpoints are unauthorized-accessible (`EVID_CFG_SENSITIVE_ENDPOINT_EXPOSURE`).
2. **Actual internal information disclosure closure**: evidence that responses actually expose internal implementation/deployment configuration, not merely that the endpoint exists (`EVID_CFG_INTERNAL_INFO_DISCLOSURE`).

**Secret path** replaces the second ID with a third: credential leakage evidence of secret material detected in responses (`EVID_CFG_SECRET_MATERIAL_IN_RESPONSE`).

🔴 **Confirmation threshold (ledger verbatim): must prove the response content actually exposes internal information or secret material; confirmation based solely on endpoint existence or suspicious field names is not allowed; public and expected API documentation is not judged as a vulnerability.**

### Testing Suggestions

- **Positive**: unauthorized access to configuration/metadata endpoints confirms internal information is obtained; scanning responses confirms secret patterns are detectable.
- **Negative**: after authentication + authorization convergence, unified production error pages, and secret-in-response interception, the issue is no longer exploitable.
- **Regression**: when adding metadata/diagnostic endpoints (including health checks, scheduling dashboards, configuration exports), re-verify access control and the expected-public whitelist.

### Evidence References

- `EVID_CFG_SENSITIVE_ENDPOINT_EXPOSURE`: evidence that route/config/metadata endpoints are unauthorized-accessible (first ID shared by both paths)
- `EVID_CFG_INTERNAL_INFO_DISCLOSURE`: evidence that responses actually expose internal implementation/deployment configuration (second ID for the internal information path)
- `EVID_CFG_SECRET_MATERIAL_IN_RESPONSE`: credential leakage evidence of secret material detected in responses (replaces the second ID for the secret path)
