---
name: dotnet-logging-audit
description: .NET security logging and monitoring audit tool. Identifies missing audit events, sensitive data in logs, structured log injection, and alerting chain flaws.
---

# .NET Logging and Monitoring Audit

## Shared Grabber Index References

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as this Skill's base retrieval index
- By default, use shared/DOTNET_SINK_REFERENCE.md as this specialty's sink type definition and trace-gate validation baseline
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover shared grabbers related to log fields, exception records, audit trails, monitoring events, sensitive data masking, and alert callbacks
- If the project has secondary encapsulations such as AuditLogger, TelemetryService, EventPublisher, SecurityMonitor, they must be added to the in-project grabbers section of the output
- When this Skill's specialty enumeration rules are more detailed than the shared index, this Skill prevails, but the shared index's base coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to correlate key business entries, audit surfaces, and `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to correlate high-value events such as authentication failures, permission denials, and administrative operations)
- Optional: `route_tracer/{route_id}/trace_{timestamp}.md` and `route_tracer/{route_id}/trace_summary_{timestamp}.md` (can serve as cross evidence of log events mapping to specific side-effect entries; not a hard prerequisite)

Key checks:

- Sensitive field recording in logging and tracing pipelines such as Serilog, NLog, ILogger, ETW, Application Insights, and OpenTelemetry
- Whether authentication success/failure, permission denials, administrative operations, key configuration changes, financial operations, import/export, and tenant switches have audit events
- Risks of structured log template injection, message template parameter pollution, exception stacks, and raw request bodies being written to logs
- Whether TraceId, CorrelationId, UserId, TenantId, ClientIp, and ForwardedHeaders are accurate and usable for post-incident review
- Whether masking, truncation, sampling, retention policies, log rotation, centralized collection, and alert rules cause security events to be missed
- Debug-level logging, development-environment log takeover, third-party library verbose output, and PII leakage issues

## Key Checks

- Log injection: user input directly entering log messages (newline forging of log entries)
- Sensitive information in logs: passwords, tokens, keys, credit card numbers, PII data
- Audit event coverage: whether authentication failure/success, authorization denials, administrative operations, and data exports have logs
- Sensitive information in exception stacks: connection strings, internal paths, configuration values
- Destructure policies in structured logging: whether complex objects expand sensitive fields
- Log retention and access control: log file permissions, access policies of centralized logging systems
- Alert linkage: whether high-risk events trigger real-time alerts

## Evidence References

- EVID_LOG_EVENT_COVERAGE_AND_SENSITIVE_DATA

## Enumeration Rules (Mandatory Refinement)

- Enumerate all logging write points of ILogger, Serilog, NLog, Audit.NET, Application Insights, OpenTelemetry, ETW, and custom audit services
- Search with priority: LogInformation, LogWarning, LogError, Audit, TrackEvent, TrackException, BeginScope, Enrich, Destructure, and other key calls
- Enumerate whether high-value events such as authentication failures, permission denials, configuration changes, administrative operations, import/export, payments, tenant switches, and exception fallbacks have logs
- For each log chain record: event type, sensitive fields, masking policy, retention period, alert linkage, and whether it can be polluted by log injection
- **Dimension bar (mandatory, 2026-09-20): tampering + flooding** — tampering surface: audit log deletion paths, level tampering (downgrading security events to Debug/Info), impact of clock rollback on audit ordering/expiration determination; flooding surface: conclusions are required for both the noise-injection chain (forging low-value events to dilute the audit stream) and the flooding-write chain (high-frequency/high-volume writes exhausting storage) (identity field trustworthiness and write quota evidence see the "Mechanism Extension: Audit Integrity Tampering and Audit Availability Flooding" section of this file). Not-applicable determination condition: the target has no audit log write mechanism at all, and an rg negative-evidence citation (scope + pattern, e.g. `rg "ILogger|Serilog|NLog|Audit\." {scope}` with zero hits) is attached before marking `Not Applicable`; otherwise a bare "not covered" is forbidden

## Barrier Verification Matrix (Mandatory)

Assess against the fail-close three-tier standard in `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Tier | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Tier 1 | Log write points exist and high-value events have log coverage | ILogger/Serilog/NLog etc. log write points exist, and high-value events such as authentication/authorization/administration/payment have log records | BLOCKED → no logging mechanism or high-value events not covered; the specialty ends |
| Tier 2 | Sensitive data/injection can enter logs | User input directly enters log messages (newline forging), passwords/tokens/PII not masked, exception stacks contain sensitive information | BLOCKED → logs contain no sensitive data and injection is infeasible; conclusion degraded |
| Tier 3 | Log flaws can cause security events to be missed or information leakage | High-risk events do not trigger alerts, log retention too short for review, log file permissions too permissive causing leakage | PARTIAL → only potential risks and verification steps are output |

## Two-Phase Determination Flow (Mandatory)

- **Phase 1 (Initial Screening Hit)**: log write points + sensitive data/injection + alerting/retention/permission configuration hit; output `Hit ID: M{hash}`.
- **Phase 2 (Refined Confirmation)**:
  1. Trace in reverse: high-value events → log write points → sensitive fields/user input chain;
  2. Verify whether user input can inject logs (newline forging), whether passwords/tokens/PII are masked, and whether exception stacks contain sensitive information;
  3. Assess whether alert rules, retention periods, and log file permissions cause security events to be missed or information leakage;
  4. If all three barrier tiers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priority (Mandatory)

1. **Confirmed Vulnerability**: logging mechanism exists + sensitive data/injection enters logs + alerting/retention/permission flaws exploitable. Output `Confirmed Vulnerability`.
2. **Pending Confirmation**: logging mechanism exists but sensitive data/injection or alerting evidence is partially missing. Output `Pending Confirmation`.
3. **False Positive / No Risk**: high-value events fully covered, logs contain no sensitive data, user input is escaped, alert rules complete, retention periods reasonable, permissions strict. Output `False Positive` with determination basis.

## Testing Suggestions and Minimum Trigger Conditions (Mandatory)

- **Minimum Trigger Conditions**:
  - A logging mechanism exists (ILogger/Serilog/NLog)
  - User input directly enters log messages or passwords/tokens/PII are not masked
  - Or high-risk events (authentication failure/permission denial/administrative operations) do not trigger alerts
- **Test Case Suggestions**:
  - Happy Path: normal high-value events are completely recorded, sensitive data masked, alerts triggered correctly
  - Edge/Ambiguity: newline injection forging log entries, exception stack leaking connection strings, Destructure expanding sensitive fields, debug logs retained long-term in production
- Each hit output appends `Hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Key Evidence

Key evidence: EVID_LOG_EVENT_COVERAGE_AND_SENSITIVE_DATA.

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (e.g. `route_mapping` / `route_tracer` / `framework_audit`), confirm dependencies are available and timestamps are consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: write to the agreed path per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing-evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (Event Surface Confirmation)**: must confirm authentication failures, permission denials, and high-value operations are covered by records.
- 🔴 **CHECKPOINT B (Sensitive Field Confirmation)**: must check whether keys/tokens/PII enter logs.
- 🔴 **CHECKPOINT C (Alert Chain Confirmation)**: must state whether high-risk events trigger observable alerts.
- 🛑 **STOP**: if there are only log calls without audit coverage evidence, the conclusion is degraded to `⚠️Pending Verification`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback if Still Failing |
|---|---|---|
| Only log call sites found, missing event coverage evidence | Fill in the high-value event list and corresponding log points | Degrade to `⚠️Pending Verification` |
| Sensitive field masking policy unclear | Verify templates and object expansion policies | Assess leakage risk conservatively and give remediation suggestions |
| Alert linkage chain incomplete | Fill in rules, thresholds, and notification channel evidence | Output only an observability-gap conclusion |

🔴 **STOP: when any fallback is triggered, outputting "audit is comprehensive" is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Required shared index references: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber sources) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: on-disk paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from the directory structure are not allowed.
- Evidence consistency validation: if severity-graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: before submission, confirm at least once that key referenced files are accessible (e.g. `DOTNET_AUDIT_GRABBER_INDEX.md`, `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Each skill must maintain at least 2 typical test cases (happy path + one complex scenario), and annotate the case ID in the results.
- Each evaluation round must execute `full_test` for at least 1 case; if only `dry_run` is possible, `dry_run_reason` and a make-up test plan must be recorded.
- Pass criteria must simultaneously satisfy: `intent achieved`, `key evidence hit`, `output format compliant`; if any one is not met, "pass" must not be given.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `Input Constraints` → `Execution Steps` → `Output and Acceptance`; no layer may be missing or mixed across layers.
- A single paragraph should not exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into a single source-of-truth section.
- AI-isms and empty filler transitions are forbidden (e.g. "first/second/finally/in summary/put simply/in other words"); any found must be rewritten as executable statements.

## Quality Gate & Assessment Consistency (Mandatory)

- A minimal gate self-check must be executed before producing output: `input completeness`, `key evidence hit`, `output path valid` — all three must be PASS.
- If any of `key evidence missing`, `chain not closed`, `consistency_check_status=BLOCKED` holds, the conclusion must be degraded to `BLOCKED`; outputting "confirmed exploitable/deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with the `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

- Anti-pattern: treating the presence of logs as auditability. Correct approach: verify key security event coverage and field completeness.
- Anti-pattern: ignoring sensitive field masking. Correct approach: check whether tokens/keys/PII enter logs.
- Anti-pattern: retaining debug logs in production long-term. Correct approach: enforce grading, retention, and access control policies.
- Anti-pattern: not checking alert linkage. Correct approach: verify whether high-risk events can be detected in real time.

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

- vuln_audit/log_{timestamp}.md
- Optional: vuln_poc/log_{timestamp}.md (if a reproduction path, audit-gap verification steps, or an environment-dependent verification chain can be constructed)

## Mechanism Extension: Audit Integrity Tampering and Audit Availability Flooding (2026-09-14 Ledger Round)

### Mechanism Description and Boundary

This extension covers two mechanism chains:

- **Integrity tampering chain**: controllable header/cookie/audit fields entering audit records → identity impersonation / misattribution. The attacker forges identity-related fields written into audit content, causing the responsible party to be misattributed in post-incident tracing.
- **Availability flooding chain**: high-frequency/high-volume writes → audit storage exhaustion. The attacker triggers a large number of audit write paths, exhausting audit storage before business resources and causing audit evidence loss.

Ledger boundary (verbatim): general business DoS must not be escalated to an audit availability issue; ordinary log absence must not be classified as integrity tampering.

### Key Checks and Enumeration Grabbers

Record for each hit: file, line number, write point/consumption path, and field source.

**Integrity tampering surface:**

- **Audit write points**: `ILogger` audit-level writes, `Audit.NET` `AuditScope` / `AuditAttribute`, custom audit middleware/filters.
- **Identity field source trustworthiness**: whether user identifiers in audit records are taken from authenticated principals such as `HttpContext.User` / ClaimsPrincipal (trusted), or directly from controllable values such as `Request.Headers["X-User-Id"]` / request body fields / cookies (untrusted).
- **Audit field concatenation into records**: whether headers, cookies, query strings, and request body fields are concatenated directly into audit messages or audit entity properties without whitelisting/escaping.

**Availability flooding surface:**

- **High-frequency write paths**: audit writes inside loops (per-record loop audit writes), a single request triggering multiple audit records (one per element in batch endpoints).
- **No throttling/sampling/quota**: whether audit writes have a per-request record limit, sampling policy, or write-queue backpressure; whether attacker-controllable batch parameters (e.g. batch size limits) are amplified into audit writes.

### Verification Matrix

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Identity field trusted-source validation** | Trace the assignment source of identity fields in audit records, confirming they are taken only from authenticated principals (ClaimsPrincipal / User.Identity), with no direct path from controllable headers/cookies | All identity fields from authenticated principals → ✅ Safe; a controllable-source path exists → 🔴 High-risk Pending Confirmation |
| **Audit field sanitization/structuring** | Check whether controllable fields are whitelisted or carried as structured fields (not string concatenation) before entering audit records, and whether escaping is fail-close | Whitelist + structured carrying → ✅ Safe; verbatim concatenation or missing sanitization → ⚠️ Pending Confirmation |
| **Write throttling and quota** | Confirm per-request audit record limits, sampling policies, and queue backpressure exist and are fail-close | Hard limit in place with controlled rejection/dropping on overflow → ✅ Safe; no limit or silent failure on overflow → 🔴 High-risk Pending Confirmation |
| **Storage capacity and alerting** | Confirm capacity alerts and rotation/archiving policies exist before audit storage exhaustion, and flooding is operationally observable | Alerts + rotation in place → ✅ Safe; exhaustion unobserved → ⚠️ Pending Confirmation |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion "Confirmed Safe" or "False Positive" is forbidden.**

### Determination Rules

**Integrity tampering confirmation** requires simultaneously closing the following two EVIDs; none may be missing:

1. **Controllable field write path closure**: evidence of the write path by which controllable headers/cookies/audit fields actually enter audit records (`EVID_LOG_TAMPERABLE_FIELD_SOURCE`).
2. **Impersonation/misattribution impact closure**: impact closure evidence of identity impersonation/misattribution (`EVID_LOG_IDENTITY_MISATTRIBUTION_IMPACT`).

**Availability flooding confirmation** requires closing the causal chain: causal-chain evidence of high-frequency/high-volume writes and audit storage exhaustion (`EVID_LOG_FLOODING_EXHAUSTION_PATH`).

🔴 **Confirmation threshold (ledger verbatim): general business DoS must not be confirmed; ordinary log absence is not within this extension.** Integrity tampering requires proving controllable fields actually enter audit records and cause impersonation/misattribution; availability flooding requires proving the causal chain between high-frequency/high-volume writes and audit storage exhaustion.

### Testing Suggestions

- **Positive**: forge headers such as `X-User-Id` to perform operations, confirming the identity field in audit records is impersonated; trigger audit writes with high-concurrency/high-volume requests, confirming storage exhaustion or alerting.
- **Negative**: when identity fields are taken only from authenticated principals + write throttling is in place, forged headers do not change audit attribution and high-frequency writes are throttled.
- **Regression**: when adding audit fields or batch endpoints, re-verify field source trustworthiness and write quotas.

### Evidence References

- `EVID_LOG_TAMPERABLE_FIELD_SOURCE`: evidence of the write path by which controllable headers/cookies/audit fields actually enter audit records (first ID for integrity closure)
- `EVID_LOG_IDENTITY_MISATTRIBUTION_IMPACT`: impact closure evidence of identity impersonation/misattribution (second ID for integrity closure)
- `EVID_LOG_FLOODING_EXHAUSTION_PATH`: causal-chain evidence of high-frequency/high-volume writes and audit storage exhaustion (third ID for availability closure)
