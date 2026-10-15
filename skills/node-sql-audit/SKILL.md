---
name: node-sql-audit
description: Node.js SQL injection audit tool. Identifies risks in mysql/mysql2 query concatenation, knex.raw, sequelize.literal, prisma.$queryRawUnsafe, and ORDER BY structure positions; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js SQL Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to SQL construction, driver / ORM calls, parameter binding, raw escape hatches, and structure positions
- If the project has secondary encapsulations such as DbHelper, QueryService, Repository, or SqlBuilder, they must be added to the project-internal grabbers section of the output
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

- The mixing boundary between mysql / mysql2 `query(sql)` (whole-string concatenation) and `execute(sql, params)` (placeholders)
- Template strings such as `` `SELECT ... WHERE id=${id}` `` and `+` concatenation entering `query()` / `pool.query()` directly
- knex: the boundary between `knex.raw(concatenated string)` and object-style queries like `.where({ col: value })`
- sequelize: the boundary between `sequelize.query(concatenated string)`, `sequelize.literal`, and `replacements` parameter substitution
- prisma: distinguishing `$queryRaw` (tagged template with automatic parameterization) from `$queryRawUnsafe` / `$executeRawUnsafe` (fully controllable strings)
- Drivers such as pg / oracledb / mssql: missing parameter arrays in `client.query(text, values)`
- Whether non-parameterizable structure positions such as ORDER BY column names, sort directions, table names, and IN lists have fail-close whitelists
- LIKE value wildcard injection of `%` `_` and self-wrapped escape implementations

## Enumeration Rules (Mandatory Refinement)

- Enumerate call sites with rg: `\.query\(`, `\.execute\(`, `\$queryRaw`, `\$queryRawUnsafe`, `\$executeRawUnsafe`, `knex\.raw`, `sequelize\.query`, `sequelize\.literal`
- Enumerate template strings and concatenated SQL: rg `SELECT `, `INSERT INTO`, `UPDATE `, `DELETE FROM`, `ORDER BY`, `LIMIT `, and trace back whether the hit strings contain `${` interpolation or `+` concatenation
- For each call site record: driver / ORM, construction method (concatenation vs placeholders), parameter sources, whether it is a raw escape hatch, and connection pool and account privileges
- Separately enumerate "non-parameterizable fragments": sort keys, column names, table names, pagination directions, IN lists, and dynamic where fragments, and verify the whitelist mapping implementations
- Distinguish `$queryRaw` (tagged template with parameterized value slots) from `$queryRawUnsafe` (whole string passed directly); do not conflate them
- If secondary encapsulation exists (QueryService / SqlBuilder / Repository), it must be unwrapped layer by layer to the real driver call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Placeholder parameterization | mysql2 `execute(sql, [params])` / pg `query(text, values)` | Check whether the call site passes values via `?` / `$1` placeholder arrays, with interpolation only in value slots | all value slots via placeholders → ✅ safe; concatenated strings entering `query()` → 🔴 high risk |
| ORM raw escape hatch | `prisma.$queryRawUnsafe` / `knex.raw` / `sequelize.literal` | Read the call source, confirming the sources of interpolated variables and whether external input can influence them | `$queryRaw` tagged template or fixed raw → ✅ safe; the Unsafe family concatenating user input → 🔴 high risk |
| Sort key / identifier whitelist | sortKey → column name mapping table / enum | Read the mapping implementation, confirming only fixed column names are returned, the default branch fails closed, and sort direction is fixed | fail-close whitelist → ✅ safe; column names / sort directions passed through directly → 🔴 high risk |
| LIKE value escaping | Self-wrapped `escapeLike()` | Read the implementation source, confirming `%` `_` `\` escaping and the ESCAPE clause | complete escaping → ✅ safe; partial escaping → ⚠️ bypassable; no escaping → 🟠 wildcard injection |
| Input validation | joi / zod / regex | Check whether the validator covers the concatenated variables and whether types are coerced | fail-close validation → ✅ safe; bypassable via truncation / encoding → ⚠️ to be confirmed; no validation → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter SQL text concatenation or structure positions
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

- `EVID_NODE_SQL_QUERY_POINT` + `EVID_NODE_SQL_STRING_CONCAT` + no effective `EVID_NODE_SQL_PARAM_BINDING_GUARD`
- Externally controllable parameters enter `query()` / `pool.query()` as whole strings via template strings / `+` concatenation
- `EVID_NODE_SQL_STRUCTURE_POSITION`: ORDER BY column names, sort directions, table names, and other structure positions are front-end controllable with no fail-close whitelist
- Raw escape hatches (`$queryRawUnsafe` / `$executeRawUnsafe` / `knex.raw` / `sequelize.literal`) concatenate user input and the barrier is fail-open

### ⚠️Pending Verification

- The context shows suspicious concatenation (e.g., template-string SQL), but the external input source is unclear (trace or call chain needs to be supplemented)
- Sort key / identifier mapping logic exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
- Parameter passing in asynchronous / queue / event chains (e.g., background report tasks) is not closed

### False Positive

- All value slots go through `execute(?, ...)` / pg `query(text, values)` / `$queryRaw` tagged templates / ORM object-style queries, and structure positions have whitelists
- Sort keys / column names come from fixed enum mappings, and unknown input is rejected (fail-close)
- Input enters only strictly escaped LIKE value slots, and the SQL structure is fully fixed

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct confirmed-exploitable injection inputs: `' OR 1=1--`, `1; DROP TABLE`, `UNION SELECT`, `' AND (SELECT ...)`
- Verify structure-position injection: pass illegal ORDER BY fields and boolean blind-injection payloads
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct inputs intercepted by barriers: out-of-whitelist sort fields, non-numeric ids, strings containing quotes
- Verify `' OR 1=1--` is treated as an ordinary value under placeholders
- Verify joi / zod / regex whitelists explicitly reject illegal input

### Regression Testing

- Retest after remediation, confirming placeholders and whitelists remain effective
- Retest the raw escape hatch refactoring, confirming no new concatenation paths were introduced
- Verify that adding sort key columns remains fail-close

## Evidence References

- `EVID_NODE_SQL_QUERY_POINT`
- `EVID_NODE_SQL_STRING_CONCAT`
- `EVID_NODE_SQL_PARAM_BINDING_GUARD`
- `EVID_NODE_SQL_STRUCTURE_POSITION`

## Output

- `node/vuln_audit/sql_{timestamp}.md`
- `node/vuln_poc/sql_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
