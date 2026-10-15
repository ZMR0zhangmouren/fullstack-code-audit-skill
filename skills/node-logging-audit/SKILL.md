---
name: node-logging-audit
description: Node.js security logging audit tool. Identifies risks such as pino/winston/console template string injection, sensitive data (authorization headers, passwords) entering logs, log tampering surfaces, and missing audit trails for key operations; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js Security Logging Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to log write points, sensitive fields, audit event coverage, and log retention
- If the project has secondary encapsulations such as logger factories, auditLogger, or requestLogMiddleware, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align key business entries, audit surfaces, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to associate high-value events such as authentication failures, authorization denials, and admin operations)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **static-evidence-driven**: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`
- Responsibility boundary: error responses leaking stacks / internal paths belong to `node-config-audit` (`EVID_NODE_CFG_ERR_HANDLER`); this specialty covers the logging pipeline and audit retention

## Key Checks

- pino / winston / console template strings concatenating user input + `\n` forging log entries
- Sensitive data entering logs: `authorization` headers, tokens, passwords, PII such as phone numbers / ID numbers
- Missing or incomplete redact / desensitization configuration
- Log file permissions, tampering surfaces with controllable write paths, rotation, and centralized collection
- Missing audit trails for key operations (login, payment, permission changes, export)
- Exception stacks and entire raw request bodies written to logs

## Enumeration Rules (Mandatory Refinement)

- rg searches for write points: `console.log(`, `console.error(`, `logger.info(`, `logger.error(`, `winston.createLogger(`, `pino(`, `log.error(`
- rg searches for sensitive sources: `req.headers`, `authorization`, `req.body`, `password`, `token`, `phone`, `idCard`
- rg searches for protection grabbers: `redact`, `censor`, `mask`, `rotate`, `audit`
- For each write point record: format string and parameter sources, sensitive fields, desensitization strategy, whether output is structured single-line, and audit event coverage
- Verify that high-value events (authentication failure, authorization denial, payment, configuration change) have corresponding log points and alerting linkage
- If logging goes through secondary encapsulation, it must be unwrapped layer by layer to the real pino / winston / console write points

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Input desensitization | pino `redact` / desensitization middleware | Verify the redact field list covers authorization, password, token, and PII | fail-close desensitization → ✅ safe; no desensitization → 🔴 high risk |
| Log injection protection | structured JSON (pino) / newline sanitization | Write user input containing `\n` to logs and verify whether entries can be forged | structured single-line or sanitized → ✅ safe; template strings concatenating raw input → 🔴 high risk |
| Audit event coverage | authentication / authorization / payment / permission change log points | Verify high-value events have logs and alerting linkage | key operations fully covered → ✅ safe; missing → 🔴 high risk |
| Retention and tampering surface | rotate / file permissions / centralized collection | Check log file permissions, retention periods, and write entries | permissions tightened with centralized collection → ✅ safe; locally writable without protection → ⚠️ to be confirmed |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: user input or sensitive data appears to enter log write points, or key operations appear to lack audit trails
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

- `EVID_NODE_LOG_INJECTION_POINT` + `EVID_NODE_LOG_TAMPER_SURFACE`: user input enters logs via template strings and newlines can forge entries
- `EVID_NODE_LOG_SENSITIVE_DATA`: `authorization` headers, passwords, or PII entering logs in plaintext without redact
- `EVID_NODE_LOG_AUDIT_TRAIL`: key operations such as payments and permission changes have no audit trail retention
- `EVID_NODE_LOG_INJECTION_POINT`: structured fields (userId, level, etc.) can be polluted by user input

### ⚠️Pending Verification

- The write point is hit but the desensitization logic is in secondary encapsulation not yet unwrapped to the redact configuration
- redact exists but field list coverage is unknown
- Audit events are partially covered, but alerting and retention chain evidence is insufficient

### False Positive

- pino redact fully covers sensitive fields and logs are structured JSON single lines
- User input enters logs after encoding / sanitization, with newlines stripped
- Key operations all have audit logs connected to alerting and centralized collection

## Testing Recommendations (Mandatory)

### Positive Testing

- Write a user name containing `\nINFO ...` to logs to verify forged entries; send a request with `authorization` to verify tokens land in logs in plaintext
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Under redact, tokens display as `[Redacted]`; structured JSON single-line output does not break lines
- Audit logs and alerts are both visible after triggering key operations

### Regression Testing

- Retest after remediation, confirming newly added write points default to desensitization and structured output
- Retest that the audit event coverage list is not lost during refactoring

## Evidence References

- `EVID_NODE_LOG_INJECTION_POINT`
- `EVID_NODE_LOG_SENSITIVE_DATA`
- `EVID_NODE_LOG_TAMPER_SURFACE`
- `EVID_NODE_LOG_AUDIT_TRAIL`

## Output

- `node/vuln_audit/logging_{timestamp}.md`
- `node/vuln_poc/logging_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)

## Mechanism Extension: Audit Integrity Tampering and Audit Availability Flooding (2026-09-14 Ledger Round)

### Mechanism Description and Boundary

This extension covers two mechanism chains:

- **Integrity tampering chain**: controllable header / cookie / audit fields entering audit records → identity impersonation / misattribution. Attackers forge identity-related fields written into audit content, causing the responsible party to be wrongly attributed in after-the-fact tracing.
- **Availability flooding chain**: high-frequency / high-volume writes → audit storage exhaustion. Attackers trigger a large number of audit write paths, exhausting audit storage before business resources and causing audit evidence loss.

Ledger boundary (verbatim): do not escalate general business DoS to audit availability issues; do not classify ordinary log absence as integrity tampering.

### Key Checks and Enumeration Grabbers

Record for each hit: file, line number, write point / consumption path, and field source.

**Integrity tampering surface:**

- **Audit write points**: winston / pino / morgan audit-level writes, custom audit middleware (audit handlers mounted via `app.use`), explicit `logger.audit/info` business audit calls.
- **Identity field source trustworthiness**: whether user identifiers in audit records come from `req.user` / session / authentication subjects mounted by authentication middleware (trusted), or are taken directly from controllable values such as `req.headers['x-user-id']` / request body fields / cookies (untrusted).
- **Audit fields concatenated into records**: whether headers, cookies, query strings, and request body fields are concatenated directly into audit messages without whitelist / escaping, or entire controllable field objects (including `req.body` / `req.headers`) are JSON-serialized and written wholesale into audit records.

**Availability flooding surface:**

- **High-frequency write paths**: audit writes inside loops / batch processing (per-item audit writes in loops), multiple audit records triggered by a single request (one per element in batch endpoints) with no throttling.
- **No throttling / sampling / quota**: whether audit writes have per-request count limits, sampling policies, or write-queue backpressure; whether attacker-controllable batch parameters (such as batch size limits) are amplified by auditing.

### Verification Matrix

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Identity field trusted-source validation** | Trace the assignment source of identity fields in audit records, confirming they come only from authentication subjects (`req.user` / session), with no direct controllable header / cookie paths | all identity fields from authentication subjects → ✅ safe; controllable source path exists → 🔴 high-risk candidate |
| **Audit field sanitization / structuring** | Check whether controllable fields are whitelist-filtered or carried in structured fields (not string concatenation) before entering audit records, and whether escaping is fail-close | whitelist + structured carrying → ✅ safe; raw concatenation or missing sanitization → ⚠️ to be confirmed |
| **Write throttling and quota** | Confirm per-request audit count limits, sampling policies, and queue backpressure exist and are fail-close | hard limit present with controlled rejection / dropping on exceed → ✅ safe; no limit or silent failure on exceed → 🔴 high-risk candidate |
| **Storage capacity and alerting** | Confirm capacity alerts and rotation / archiving strategies exist before audit storage exhaustion, and whether flooding is operationally visible | alerts + rotation present → ✅ safe; exhaustion invisible → ⚠️ to be confirmed |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion as "Confirmed Safe" or "False Positive" is forbidden.**

### Determination Rules

**Integrity tampering confirmation** requires closing both of the following EVIDs, both indispensable:

1. **Controllable field write path closure**: evidence of the write path by which controllable header / cookie / audit fields are actually written into audit records (`EVID_NODE_LOG_TAMPERABLE_FIELD_SOURCE`).
2. **Impersonation / misattribution impact closure**: evidence of identity impersonation / misattribution impact (`EVID_NODE_LOG_IDENTITY_MISATTRIBUTION_IMPACT`).

**Availability flooding confirmation** requires closing the causal chain: evidence of the causal chain between high-frequency / high-volume writes and audit storage exhaustion (`EVID_NODE_LOG_FLOODING_EXHAUSTION_PATH`).

🔴 **Confirmation threshold (ledger verbatim): general business DoS must not be confirmed; ordinary log absence is not part of this extension.** Integrity tampering requires proving that controllable fields are actually written into audit records and cause impersonation / misattribution; availability flooding requires proving the causal chain between high-frequency / high-volume writes and audit storage exhaustion.

### Testing Recommendations

- **Positive**: forge headers such as `X-User-Id` to perform operations, confirming identity fields in audit records are impersonated; trigger audit writes with high-concurrency / high-volume requests, confirming storage exhaustion or alerts.
- **Negative**: with identity fields taken only from authentication subjects + write throttling, forged headers do not change audit attribution, and high-frequency writes are rate-limited.
- **Regression**: when new audit fields or batch endpoints are added, re-verify field source trustworthiness and write quotas.

### Evidence References

- `EVID_NODE_LOG_TAMPERABLE_FIELD_SOURCE`: evidence of the write path by which controllable header / cookie / audit fields are actually written into audit records (first ID of integrity closure)
- `EVID_NODE_LOG_IDENTITY_MISATTRIBUTION_IMPACT`: evidence of identity impersonation / misattribution impact (second ID of integrity closure)
- `EVID_NODE_LOG_FLOODING_EXHAUSTION_PATH`: evidence of the causal chain between high-frequency / high-volume writes and audit storage exhaustion (third ID of availability closure)
