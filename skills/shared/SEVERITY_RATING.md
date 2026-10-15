---
name: dotnet-severity-rating
description: Unified severity rating system for .NET code audits.
---

# Unified Vulnerability Severity Rating Standard (.NET)

## Severity Score Formula

```text
Score = R × 0.40 + I × 0.35 + C × 0.25
CVSS mapping = Score / 3.0 × 10.0
```

If C=0 (not exploitable), the Score must be zeroed, and the vulnerability level must not exceed L (Low); deriving M/H from the weighted formula is forbidden.

## Three-Dimension Scoring Criteria

### Reachability (R)

- 3: no authentication required; directly reachable via HTTP/Hub/GraphQL
- 2: regular user authentication required
- 1: admin, intranet, or a specific role required
- 0: unreachable or trace_status=UNRESOLVED

### Impact Scope (I)

- 3: RCE, arbitrary file write, complete data breach, tenant breakout
- 2: sensitive data disclosure, privilege violation, partial arbitrary read/write, high-value business impact
- 1: limited information disclosure, local state anomaly, low-impact configuration exposure
- 0: no actual security impact

### Exploitation Complexity (C)

- 3: low complexity; single request or low-cost trigger
- 2: medium complexity; requires crafted payload, specific role, or multi-step operations
- 1: high complexity; requires race conditions, chained exploitation, or strict environmental conditions
- 0: not exploitable (triggers the Score-zeroing rule)

## Level Mapping

| Prefix | Score Range | CVSS 3.1 |
| ---- | ---- | ---- |
| C | 2.70 - 3.00 | 9.0 - 10.0 |
| H | 2.10 - 2.69 | 7.0 - 8.9 |
| M | 1.20 - 2.09 | 4.0 - 6.9 |
| L | 0.10 - 1.19 | 0.1 - 3.9 |

## Severity Enum Closure (2026-09-20, mandatory)

- The severity enum allows only the four values `C` / `H` / `M` / `L`; no artifact (vulnerability ID prefix, findings statistics table, report severity column, exploit-chain minimum severity) may contain a level outside the enum.
- Boundary cases (between two tiers, evidence insufficient to upgrade but risk is elevated) must use the "upgrade-channel annotation" format: `L (suggest upgrade to M, reason: …)` — the enum value remains `L`, with the suggested tier and specific reason written inside the parentheses.
- Range-value fuzzy labeling is forbidden: `L-M` is a counterexample and non-compliant (any statistics table / report row writing range values like "L-M" or "M~H" must be rewritten in the upgrade-channel annotation format, e.g., `L (suggest upgrade to M, reason: …)`).
- The upgrade-channel annotation does not change the vulnerability ID prefix or the three-dimension scores; it serves only as a manual-review prompt; an actual upgrade must go through review with the reason recorded in the evidence chain.
- Statistics grouping uses the enum value (2026-09-21): all statistics tables / counts / tier summaries group by the enum values `C` / `H` / `M` / `L`; "upgrade-channel annotations" (e.g., `L (suggest upgrade to M, reason: …)`) are not counted in M (nor in any suggested target tier), only in their own enum value (in this example, L).

## Vulnerability ID Convention

Format: {severity prefix}-{type code}-{sequence number}

Suggested type codes (aligned with the vulnerability ID convention section of dotnet-audit-pipeline):

- SQL / NOSQL / KQL / CMD / SSRF / XSS / DOMXSS / FILE / UPLOAD / WRITE / ARCHIVE
- REDIR / CRLF / XXE / DESER / TPL / SSTI / LDAP / EXPR / XPATH / SECOND / DESYNC
- AUTH / CSRF / SESS / CFG / CRYPTO / SUPPLY / LOGIC / FS / LOG
- PROTO: prototype-chain pollution (JS-specific)
- REDOS: regular-expression denial of service (JS-specific)
- QUERY: non-SQL query language injection (SOQL/OData/FetchXML etc.)
- EXPORT: spreadsheet formula injection (CSV/Excel export interpretation boundary)
- PROMPT: AI prompt injection (instruction/data boundary crossing)

The node-side vulnerability ID format is identical to the existing `{severity prefix}-{type code}-{sequence number}`.

## Exploitability Labels

| Label | Meaning |
| ---- | ---- |
| ✅ Confirmed Exploitable | Evidence chain closed; execution point, controllability, and preconditions all hold |
| ⚠️ Pending Verification | Risk exists, but the trace or key evidence is insufficient |
| ❌ Not Exploitable | Effective protection holds or the key execution point is unreachable |
| 🔍 Environment-Dependent | Depends on host environment, deployment configuration, or external component conditions |
