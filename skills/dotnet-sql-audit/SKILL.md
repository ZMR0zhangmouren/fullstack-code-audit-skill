---
name: dotnet-sql-audit
description: .NET SQL injection audit tool. Identifies injection risks in ADO.NET, Dapper, EF Core RawSQL, and dynamic query construction; outputs severity rating, PoC, and remediation recommendations.
---

# .NET SQL Injection Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the SQL-related grabbers of entry definitions, binding / conversion, precondition controls, sensitive operations, and security configuration
- If the project has secondary encapsulations such as Repository, QueryBuilder, SQL Helper, or DbExecutor, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement ORM, serialization configuration, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`
- Optional (if automated pre-screening exists): `scan_audit/sql_injection_matches_{timestamp}.jsonl` (pre-screening hits, used for prioritization and quick location)

## Key Checks

- call sites and command text sources of SqlCommand, DbCommand, SqlDataAdapter, and ExecuteReader / ExecuteScalar / ExecuteNonQuery
- paths generating SQL via string concatenation, interpolated strings, StringBuilder, FormattableString, AppendFormat, and Join
- parameterization boundaries of Dapper Query / Execute, multi-result sets, anonymous object parameters, and DynamicParameters
- RawSQL execution points of EF Core FromSqlRaw, ExecuteSqlRaw, Database.SqlQueryRaw, migration scripts, and repository layer wrappers
- whether "non-parameterizable" dynamic fragments such as sort fields, column names, table names, pagination fragments, condition fragments, and IN lists have whitelists
- whether LINQ ultimately degrades to raw SQL and whether unvalidated strings are mixed in during expression-tree-to-SQL translation
- whether multi-tenancy, soft delete, and row-level permission filters are bypassed by RawSQL, IgnoreQueryFilters, or custom repositories
- whether exception handling, logs, and debug output expose complete SQL, parameter values, and connection information

## Enumeration Rules (Mandatory Refinement)

- Enumerate all database call points in classes inheriting Controller / ControllerBase, Repositories, Services, Background Jobs, GraphQL Resolvers, and Hubs
- Search SqlCommand, DbCommand, FromSqlRaw, ExecuteSqlRaw, Query, Execute, SqlQueryRaw, CreateCommand, and CommandText first
- Enumerate usage positions of string concatenation, interpolated strings, StringBuilder, FormattableString, AppendLine, Join, Format, and raw SQL helpers
- Separately enumerate "non-parameterizable fragments": sort fields, column names, table names, where fragments, group by, having, offset / fetch, TOP, and IN lists
- Enumerate the degradation chains of repository wrappers, QueryBuilders, custom Specifications, and Dynamic LINQ to RawSQL
- For each call point record: SQL source, parameter object source, upstream entry of the call stack, and whether it executes under transactions / multi-tenant filters / soft-delete filters

## Evidence References (Mandatory)

- EVID_SQL_EXEC_POINT
- EVID_SQL_STRING_CONSTRUCTION
- EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT

## Barrier Verification (Mandatory, New)

For every dynamic parameter in every sink, its actual barrier behavior must be verified — **look at the actual implementation, not the function name**.

### Barrier Verification Matrix

| Parameter Type | Typical Barrier | Verification Requirements |
|---------|-------------|---------|
| LIKE values | `escape_like_literal()` / `SqlLikeString` | read the actual source: whether `%`, `_`, `[`, `]` escaping is handled; whether Unicode / UTF-8 bypasses exist; whether the ESCAPE clause is handled |
| integers | `strict_int()` / `int.TryParse()` | read the actual source: whether non-numeric input is rejected; whether length limits exist; whether the return value is validated |
| ORDER BY fields | `allowlisted_sort_key()` / `Enum.Parse<T>()` | read the actual source: whether only whitelisted fields are returned; whether case / encoding issues exist; whether there is a default branch that fails closed; **whether sub-levels reuse the same validator in nested / recursive calls; whether sub-levels performing independent resolution are validated separately** |
| column / table names | whitelist / mapping table / `ValidateColumnName()` | read the actual source: whether it is bypassable; whether it is case-sensitive; whether wildcards are allowed |
| nested filter fields | unified validator across recursive levels | **verify level by level**: top-level validation + unvalidated sub-levels → ⚠️ high risk; all levels reuse the same fail-close validator → may be downgraded; sub-levels performing independent resolution without reuse → must be audited separately |
| dynamic fragment | none | ⚠️ entering structure positions directly → mark as high risk; no barrier verification needed |
| dynamic fragment | none | ⚠️ entering structure positions directly → mark as high risk; no barrier verification needed |

### Verification Actions (Mandatory, Choose One of Three)

For each barrier, at least one of the following actions must be performed:

1. **Inspect the implementation**: use the Read tool to read the barrier function's actual source code and confirm its behavior
2. **Inspect the call site**: confirm the barrier is used correctly at the call site (no missing parameters, not skipped by conditional branches, return value used)
3. **Test boundaries**: attempt to construct bypass inputs to verify whether the barrier is effective

### fail-close Determination Standard (Mandatory)

Barrier robustness must be evaluated in the "failure mode", not the happy path:

- ✅ **fail-close (safe)**: unknown / illegal input → throws an exception / returns empty / refuses execution / logs an alert, **never passes through the raw value**
- ❌ **fail-open (bypassable)**: unknown / illegal input → allowed by default / silently falls back to the raw value / only returns false but the caller does not check → mark as `⚠️ Bypassable`
- ❌ **silent-fallback (high risk)**: unknown fields → passed through to SQL concatenation positions without interception → mark as high risk directly; no further barrier verification needed

### Barrier Verification Output Format

In the audit report, every barrier must be recorded:

```markdown
| Parameter | Barrier Function | Actual Behavior | Verification Result |
|------|-------------|---------|---------|
| keyword | escape_like_literal() | handles % _ [ ] escaping, Unicode test passed | ✅ PASSED |
| category_id | strict_int() | rejects non-numeric input, length limit of 10 digits | ✅ PASSED |
| sort_key | allowlisted_sort_key() | returns only whitelisted fields, no bypass | ✅ PASSED |
| column_key | none | enters the column identifier position directly, no whitelist | ⚠️ FAILED |
```

### Anti-Patterns (Forbidden)

- ❌ judging safe upon seeing `escape_like_literal()` → **the implementation source must be read**
- ❌ judging safe upon seeing `int.TryParse()` → **you must confirm the return value is used correctly**
- ❌ judging whitelist upon seeing `switch` → **you must confirm there is a `default` branch and no fallthrough**
- ❌ judging safe upon seeing parameterized queries → **you must check whether external input is mixed in via string interpolation** (such as `FromSqlRaw($"... {input}")`)
- ❌ judging identifier positions safe upon seeing parameterized queries → **parameterization does not protect identifier slots**; `ORDER BY {param}` still requires whitelist validation

## Two-Phase Determination (Mandatory)

Phase 1 (interim conclusion): give one of three interim conclusions for each hit first
- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter SQL construction
- `Pending`: the context shows suspicious concatenation, but the external input source or barrier behavior is unclear
- `False Positive`: fields come from fixed constants / enum mappings, or the barrier has been verified as fail-close

Phase 2 (mandatory evidence chasing): if Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser downward until any of the following holds:
- ✅ evidence is found that externally controllable input enters an SQL slot → `Confirmed Vulnerability`
- ✅ fixed whitelist mapping / fail-close evidence is found → `False Positive`
- ❌ a key call chain is still missing → remain `Pending`, but you must state which hop is missing

🔴 **STOP: Phase 2 must not stop at surface phenomena; you must chase evidence until a determination can be made.**

## Determination Rules (Structured)

### Confirmed Vulnerability (any one satisfied)

1. externally controllable parameters enter SQL string construction directly (concatenation / interpolation / `StringBuilder` / `Format`)
2. identifier slots (sort fields, column names, table names, group fields) only undergo character replacement, wrapping in `[]` / `"` / `` ` ``, or blacklist filtering, **without whitelist mapping**
3. nested filters: field validation exists at the top level, but recursive sub-level nodes do not perform equivalent validation
4. dynamic fragments (where condition fragments, IN lists, offset / fetch, TOP) have no whitelist or fail barrier verification

### Pending

1. the context shows suspicious concatenation, but the external input source is unclear (trace or call chain needs to be supplemented)
2. a barrier function exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
3. parameter passing in asynchronous / queue / event chains is not closed

### False Positive

1. the final value or identifier comes from fixed constants / enum mappings, and unknown input is rejected (fail-close)
2. all recursive levels reuse the same validator and strictly fail closed
3. parameters are bound via ORM parameterization (not string interpolation), and identifier slots are whitelist-protected

## Execution Checkpoints

- EVID_SQL_EXEC_POINT
- EVID_SQL_STRING_CONSTRUCTION
- EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT

## Execution Checkpoints

🔴 **STOP — the following two items must be verified before outputting conclusions; neither may be missing:**

1. **trace-gate check**: if `route_tracer/{route_id}/trace_{timestamp}.md` **does not exist or trace_status=PARTIAL/UNRESOLVED**, all conclusions must be downgraded to `⚠️Pending Verification`; outputting `✅Confirmed Exploitable` is forbidden.
2. **EVID completeness check**: if EVID_SQL_EXEC_POINT / EVID_SQL_STRING_CONSTRUCTION / EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT are not all satisfied, outputting high-risk (🔴) level conclusions is forbidden.

🔴 **STOP — when any of the following situations is found, it must be annotated separately in the output and must not be silently skipped:**

- dynamic fragments (sort fields / column names / table names) without whitelist protection → list a separate `⚠️ Whitelist Missing Risk`
- IgnoreQueryFilters or RawSQL bypassing multi-tenancy / soft-delete filters → list a separate `⚠️ Filter Bypass Risk`
- complete SQL or parameter values leaked in exceptions / logs → list a separate `⚠️ Information Disclosure Risk`

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

| # | Anti-pattern | Why it is wrong | Correct practice |
|---|---|---|---|
| 1 | **Outputting ✅Confirmed without a trace** | static grabbers alone cannot prove parameter controllability and execution paths | downgrade to `⚠️Pending Verification`, stating the missing evidence |
| 2 | **Judging parameterized queries as safe directly** | EF Core `FromSqlRaw($"... {userInput}")` is still an injection risk; parameterization ≠ no risk | check whether parameters are mixed in via interpolation, not just the call pattern |
| 3 | **Searching only one call layer and ignoring the wrapper chain** | the business layer calls QueryBuilder, and QueryBuilder calls RawSQL — the vulnerability sits at the bottom layer | the enumeration rules require tracing to the final execution point |
| 4 | **Treating dynamic ORDER BY / column names as low risk and ignoring them** | column / table name injection enables union-based / error-based attacks | non-parameterizable fragments must be enumerated separately with whitelist recommendations |
| 5 | **Judging all LINQ to SQL as safe** | LINQ may degrade to RawSQL (including `FromSqlRaw`, `Database.ExecuteSql`, etc.) | enumeration must check the final SQL form of LINQ expression trees |
| 6 | **Judging identifier slots safe upon seeing parameterized queries** | in `ORDER BY {param}` and `WHERE {column} = value`, parameterization protects only value slots, not identifier slots; identifier slots still require whitelist validation | distinguish "value parameterization" from "identifier parameterization"; identifier slots must be validated separately |

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (query entry confirmation)**: SQL execution entries and ORM / native call boundaries must be confirmed.
- 🔴 **CHECKPOINT B (parameterization confirmation)**: parameter binding rather than string concatenation must be confirmed.
- 🔴 **CHECKPOINT C (high-risk statement confirmation)**: high-risk fragments such as dynamic sorting, pagination, and batch concatenation must be confirmed.
- 🛑 **STOP**: if parameterization evidence and the execution chain are not closed, outputting a "no injection risk" conclusion is forbidden.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| trace incomplete or missing | supplement route_tracer evidence and align route_id | downgrade to `⚠️Pending Verification`; Confirmed Exploitable is forbidden |
| parameter-to-SQL-fragment mapping unclosed | complete the string construction and execution point chain evidence | no high-risk confirmation; give verification steps only |
| dynamic fragment whitelist evidence insufficient | verify sort / column / table name whitelist logic item by item | conservatively mark high-risk pending items |

🔴 **STOP: when any fallback triggers, outputting "no injection risk" is forbidden.**

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion levels: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose one of three; blank is forbidden).
- Minimum evidence set: at least the five items `Entry Point`, `Controllable Parameter`, `Key Call`, `Security Boundary`, and `Missing Evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softened wording is forbidden: such as "may be at risk / suggested attention / depends on the situation / most likely"; when evidence is insufficient, `⚠️Pending Verification` and the next evidence-supplementing action must be explicitly written.

Minimal output fragment (directly reusable):

```md
- Hit ID: M{hash} (optional, used for cross-phase tracking and regression alignment)
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameter=...; key call=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement the parameter-propagation evidence of trace_id=...
```

## Testing Recommendations (Mandatory)

For each confirmed vulnerability or pending item, at least the following test coverage must be given:

- **Positive testing**: construct confirmed-exploitable inputs and verify the vulnerability really exists (such as `' OR 1=1--`, `1; DROP TABLE`, and illegal ORDER BY fields)
- **Negative testing**: construct inputs intercepted by barriers and verify the protection mechanism is effective (such as out-of-whitelist fields, non-numeric strings, and overlong inputs)
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Output

- vuln_audit/sql_{timestamp}.md
