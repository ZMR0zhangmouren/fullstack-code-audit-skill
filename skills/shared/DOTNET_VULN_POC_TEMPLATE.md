# .NET Vulnerability PoC Output Template

This file standardizes the PoC artifact format for each vulnerability specialty under the vuln_poc directory, so that it can be consumed stably by dotnet-audit-pipeline, manual review, and exploit-chain aggregation.

## Scope

- Applies to vulnerability specialties that have completed vuln_audit and have reproducible conditions
- Applies to scenarios where a request or trigger chain can be constructed: SQL, CMD, SSRF, XSS, file upload, open redirect, XXE, deserialization, expression execution, etc.
- Not applicable to scenarios where trigger conditions cannot be constructed at all and only framework-level risk hints can be output; in such cases the PoC file must be explicitly labeled "Pending Verification" or "Environment-Dependent" rather than omitted

## Usage Rules

- The default output file is vuln_poc/{type}_{timestamp}.md
- Each vuln_poc file must establish a reference relationship with the corresponding vuln_audit/{type}_{timestamp}.md
- Each PoC entry must state the associated route_id, vulnerability ID, trigger preconditions, request template, and expected result
- When direct reproduction conditions are not met, a "Pending Verification PoC" or "Environment-Dependent PoC" must still be output; failing to generate the vuln_poc directory because full reproduction is impossible is not allowed
- Real routes, parameters, headers, cookies, bodies, and file names in request templates should come from route-mapper / route-tracer artifacts as much as possible and must not be fabricated out of thin air

## Template

````md
# {project_name} - {type} PoC
Generated at: {timestamp}
Linked vulnerability report: vuln_audit/{type}_{timestamp}.md

## PoC List

### POC-001 - {finding_id}
- route_id: {route_id}
- Vulnerability ID: {finding_id}
- Severity: {severity}
- Exploitability: Confirmed (Dynamic Verification) / Confirmed (Static Evidence) / Pending Verification / Environment-Dependent
- Preconditions:
  - {condition_1}
  - {condition_2}
- Related evidence:
  - {route_tracer_evidence}
  - {framework_audit_evidence}
  - {vuln_audit_evidence}

### Request Template

```http
POST /example HTTP/1.1
Host: {host}
Authorization: Bearer {token}
Content-Type: application/json

{"key":"value"}
```

### Expected Result

- {expected_behavior}

### Dynamic Verification Record (required when labeled "Confirmed (Dynamic Verification)")

- Verification method: {Direct request / Minimal reproduction project}
- Environment: {Runtime environment or test project description}
- Observed behavior: {observed_behavior}
- Output evidence summary: {response_excerpt_or_console_output}

### Verification Notes

- {notes}
````

## Exploitability Status Semantics

- `Confirmed (Dynamic Verification)`: the PoC has **actually been triggered** in a runtime environment / test project, and the expected effect was observed (supported by a dynamic verification record)
- `Confirmed (Static Evidence)`: the evidence chain is closed (entry → propagation → sink all evidenced), but **not actually triggered**
- `Pending Verification`: an unclosed evidence gap exists, and no definite conclusion can be given
- `Environment-Dependent`: reproduction depends on specific deployment, configuration, or external conditions that the current environment cannot satisfy

**Wording constraint**: a PoC that has not completed dynamic verification must **not** be labeled `Confirmed (Dynamic Verification)`; it may only be labeled `Confirmed (Static Evidence)` or a weaker status; downstream reports referencing "Confirmed" must distinguish the two Confirmed variants and must not mix them.

## Dynamic Verification (Mandatory for C/H Severity)

After the static evidence chain is closed, C/H-severity conclusions must complete dynamic verification (via one of the two paths below) and persist the "Dynamic Verification Record" fields:

1. **Start the application and send the PoC request directly**: start the target application in a local / test environment, send the real request per the request template, and observe the response, logs, or side effects (e.g., database changes, file writes).
2. **Minimal reproduction project**: write a minimal xUnit / console project that directly invokes the target code path (controller → service → sink) and asserts that the vulnerable behavior occurs. Suitable for scenarios where the application cannot be started as a whole or the entry point is hard to construct.

When dynamic verification fails or is blocked by the environment: `dynamic_verify_blocked_reason` must be persisted (environment unavailable / time constraints / missing tools, etc.), and the PoC conclusion is capped at `Confirmed (Static Evidence)`; labeling `Confirmed (Dynamic Verification)` is forbidden; L/M-severity conclusions remain "optional but preferred" and are not subject to this mandatory constraint.

Dynamic verification must record the following fields (see the "Dynamic Verification Record" section of the template):

- Verification method (direct request / minimal reproduction project)
- Environment (runtime environment / test project description, including dependency and configuration differences)
- Observed behavior (whether actual behavior matches expectations)
- Output evidence summary (key response excerpts / console output / log excerpts, for reviewer traceability)

## Minimum Acceptance Requirements

- Each PoC entry maps to a specific vulnerability ID or finding ID in vuln_audit
- Each PoC entry maps to a route_id or an explicit non-HTTP entry identifier
- Each PoC entry states Confirmed (Dynamic Verification) / Confirmed (Static Evidence) / Pending Verification / Environment-Dependent
- Entries labeled `Confirmed (Dynamic Verification)` must be accompanied by a complete dynamic verification record
- Request templates are consistent with route-mapper / route-tracer artifacts on entry points, methods, and parameter names
- Writing only "a request can be constructed manually" without giving a minimal request template is not allowed

## Added: Exclusion Chain (Why Other Parameters Do Not Hold)

For each sink, in addition to explaining why the dangerous parameter is dangerous, you must also explain why the other parameters are not dangerous.

### Rules

If a sink has multiple dynamic parameters but only some are dangerous, you must **explicitly exclude the other parameters**.

You must not just say "SQL injection exists"; you must say "`column_key` is injectable; other parameters excluded".

### Exclusion Chain Template

Add the following content to each PoC entry:

```markdown
### Exclusion Chain

| Parameter | Entry Position | Why It Does Not Hold | Evidence |
|------|---------|-----------|------|
| keyword | LIKE value | Escaped | `escape_like_literal()` implementation confirmed to handle `%`, `_`, `[`, `]` |
| category_id | WHERE equality | Integer convergence | `strict_int()` implementation confirmed to reject non-numeric input |
| sort_key | ORDER BY | Whitelist mapping | `allowlisted_sort_key()` only returns whitelisted fields, no bypass |
| limit | LIMIT | Integer convergence | Handled by `strict_int()` |
| offset | OFFSET | Integer convergence | Handled by `strict_int()` |
```

### Exclusion Chain Acceptance Criteria

- [ ] If a sink has N dynamic parameters, the exclusion chain must cover all N parameters (or be explicitly labeled "not analyzed")
- [ ] Each exclusion item must have concrete evidence (not just "handled")
- [ ] Exclusion evidence must point to the actual implementation (function source / call site / whitelist contents)
- [ ] If a parameter is not analyzed, it must be labeled `⚠️Unverified` rather than pretending to be excluded
