---
name: dotnet-query-injection-audit
description: .NET non-SQL query language injection audit tool. Identifies injection risks caused by SOQL (Salesforce), OData, and FetchXML (Dynamics 365) query string concatenation, structured API condition value misuse, and [EnableQuery] raw query passthrough; outputs severity rating, PoC, and remediation recommendations.
---

# .NET Non-SQL Query Language Injection Audit (SOQL / OData / FetchXML)

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use the "QUERY / Non-SQL Query Languages" chapter of shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the entry definitions in the QUERY chapter: SOQL `ForceClient.QueryAsync` / `SforceService.query`, OData `$filter` / `$orderby` concatenation and `[EnableQuery]`, and FetchXML `RetrieveMultiple(QueryBase)` / `ConditionExpression`
- If the project has secondary encapsulations such as SOQL Builder, OData Helper, or FetchXML wrappers, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- **This specialty is of the trace-gate type**: `route_tracer/{route_id}/trace_{timestamp}.md` is a hard precondition; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to confirm anonymous entries, P0 / P1 bucketing, and the data sensitivity of query results)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement OData routing conventions, Salesforce / Dynamics 365 client configuration, and runtime control plane)
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`
- When traces are missing or `trace_status=PARTIAL/UNRESOLVED`, all conclusions are downgraded to `⚠️Pending Verification` (see "Two-Phase Determination")

## Key Checks

- SOQL construction points: query string sources and concatenation methods of `ForceClient.QueryAsync<T>(soql)`, `SforceService.query(soql)`, and REST `/query?q=`
- OData construction points: `$filter=` / `$orderby=` / `$select=` / `$expand=` query option string concatenation; `ODataClient` / `Container` LINQ providers escaping into raw query strings
- FetchXML construction points: direct concatenation of `<filter>` and `<condition` fragments in FetchXML strings; the `RetrieveMultiple(QueryBase)` execution entry
- controllability of condition values in structured APIs (QueryExpression / strongly-typed query objects): whether `userInput` in `new ConditionExpression(attr, op, userInput)` undergoes type / range validation
- `[EnableQuery]` raw query passthrough: entries where client `$filter` and other query options are pushed down to the data source without server-side constraints in Web API OData
- paths generating query fragments via string concatenation, interpolated strings, StringBuilder, AppendFormat, and Join
- whether "non-parameterizable" dynamic fragments such as dynamic attribute names, sort fields, filter operators, and `<condition operator=` operator slots have allowlists
- whether multi-tenant / row-level security filters are bypassed by injected query fragments (such as OData `$filter` appending `or 1 eq 1`, or FetchXML injecting `or` condition blocks)
- whether exception handling, logs, and debug output expose complete query strings, query parameters, and data source endpoints

## Enumeration Rules (Mandatory Refinement)

- Enumerate all non-SQL query call points in classes inheriting Controller / ControllerBase, Services, Background Jobs, GraphQL Resolvers, and Hubs
- Search first: `QueryAsync`, `query(`, `RetrieveMultiple`, `ConditionExpression`, FetchXML strings (`<filter>`, `<condition`), OData `$filter` / `$orderby` concatenation, and `[EnableQuery]`
- Enumerate usage positions of string concatenation, interpolated strings, StringBuilder, AppendLine, Join, Format, and SOQL Builder / FetchXML Helper
- Separately enumerate "non-parameterizable fragments": dynamic attribute names, sort fields, filter operators, `<condition operator=` operator slots, and `$select` / `$expand` field lists
- Enumerate the encapsulation chains of SOQL Builder, OData Helper, FetchXML wrappers, and custom query builders, tracing to the final execution points
- For each hit record: file, line number, query language type (SOQL / OData / FetchXML), construction method (string concatenation / structured API), and parameter source

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Structured API / parameterization** | Confirm whether QueryExpression, `ConditionExpression` strongly-typed condition values, and OData parameterized queries correctly use SDK parameter binding instead of concatenating user input directly into query strings | all condition value slots come from strongly-typed parameter binding with no interpolation mixed in → ✅ safe; structured APIs are called but condition values still come from string concatenation → ⚠️ to be confirmed |
| **Input allowlist / type validation** | Confirm whether dynamic attribute names, sort fields, and filter operators come from allowlist mappings or enum validation, and the validation is fail-close | fail-close allowlist → ✅ safe; blacklist or no validation → 🔴 high risk; validation implementation not visible → ⚠️ to be confirmed |
| **Escaping** | Confirm whether query string concatenation positions (SOQL quotes, OData quotes / special characters, FetchXML XML entities) have canonical escaping | all fragments canonically escaped with no boundary crossing → ✅ safe; escaping missing or escape function implementation not visible → ⚠️ to be confirmed |
| **Query result scope validation** | Confirm whether injected query fragments can change the result set scope (expanding returned rows, cross-entity queries, bypassing tenant filters), and whether the server re-validates the result scope | injection can expand the result set or cross tenants → 🔴 high risk; result scope fixed by the server and injection only affects single condition values → 🟠 medium-risk candidate |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion as "Confirmed Safe" or "False Positive" is forbidden.**

## Two-Phase Determination (Mandatory)

Follow the two-phase determination process of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

1. **Phase 1 (interim conclusion)**: mark each hit as `Confirmed Vulnerability Candidate` / `Pending` / `False Positive` first
2. **Phase 2 (mandatory evidence chasing)**:
   - if Phase 1 is `Confirmed Vulnerability Candidate` → all relevant items of the Barrier verification matrix must be completed, and the three segments of evidence — Source → query execution Sink → query semantics / impact (three EVIDs) — must all be cited before `Confirmed` may be marked
   - if Phase 1 is `Pending` → chase at least one more hop of the call chain or downstream parser downward, until a determination can be made
   - if Phase 2 still cannot close → remain `Pending`, and explicitly record which hop of evidence is missing
3. **trace-gate check**: if `route_tracer/{route_id}/trace_{timestamp}.md` does not exist or `trace_status=PARTIAL/UNRESOLVED`, all conclusions must be downgraded to `⚠️Pending Verification`; outputting `✅Confirmed Exploitable` is forbidden

🔴 **STOP — when only query concatenation syntax is found without proving that user input enters an executable query structure, outputting "Confirmed Vulnerability" is forbidden; conclusions must be `⚠️Pending Verification`, with the missing evidence and evidence-supplementing actions stated.**

## Determination Rules (Mandatory Refinement)

### Confirmed Vulnerability

All three of the following must be satisfied simultaneously, with all three EVIDs cited, all indispensable:

1. **Source closure**: the user-controllable input source is clear (`EVID_QUERY_USER_PARAM_TO_FRAGMENT` — evidence of the mapping from user input to query fragments, conditions, or structures)
2. **Query execution Sink closure**: the input reaches the SOQL / OData / FetchXML execution point (`EVID_QUERY_EXEC_POINT` — non-SQL query execution point evidence)
3. **Query construction and semantic impact closure**: the input participates in query string / structure construction (`EVID_QUERY_STRING_CONSTRUCTION`), and the injected fragment changes query semantics (result set expansion, cross-entity / cross-tenant access, filter bypass)

🔴 **Confirmation threshold (hard rule): without simultaneously citing EVID_QUERY_EXEC_POINT + EVID_QUERY_STRING_CONSTRUCTION + EVID_QUERY_USER_PARAM_TO_FRAGMENT, outputting "Confirmed" or 🔴/🟠 level conclusions is forbidden.**

### Pending

1. Only query concatenation syntax is found (such as `$"SELECT Id FROM Account WHERE Name = '{userInput}'"`), but it is not proven that user input enters an executable query structure → `⚠️Pending Verification`; confirmation is forbidden
2. the context shows a suspicious pattern (such as a `RetrieveMultiple` call), but the external input source is unclear (trace or call chain needs to be supplemented)
3. a barrier function (such as a query parameterization wrapper) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
4. query parameter passing in asynchronous / queue / event chains is not closed
5. structured APIs and string concatenation are mixed, and the specific usage path at the current call site cannot be confirmed

### False Positive

1. QueryExpression strongly-typed condition values pass type / enum validation, and unknown input is refused execution (fail-close)
2. the final query comes from fixed constants / template mappings, and unknown input is refused execution (fail-close)
3. user input enters only SDK parameterized value slots, and the query string template is fully fixed with no interpolation
4. dynamic attribute names / sort fields are locked to a fail-close allowlist before query construction and cannot be overridden
5. `[EnableQuery]` server-side constraints (`AllowedQueryOptions`, `MaxTop`, row-level filters) take effect forcibly before query pushdown, and client query options cannot be bypassed

### Anti-Pattern Blacklist

| # | Anti-pattern | Why it is wrong | Correct practice |
|---|---|---|---|
| 1 | Outputting ✅Confirmed without a trace | static grabbers alone cannot prove parameter controllability and execution paths | downgrade to `⚠️Pending Verification`, stating the missing evidence |
| 2 | Confirming high risk upon finding `$"WHERE Name = '{input}'"` concatenation | concatenation syntax ≠ user input entering an executable structure; constant concatenation or unreachable paths do not constitute a vulnerability | close the Source and execution Sink evidence before confirming |
| 3 | Judging `RetrieveMultiple(QueryExpression)` uniformly safe | when the condition value of `new ConditionExpression(attr, op, userInput)` is controllable, query semantics can still be injected | check condition value sources and type validation, not just the API name |
| 4 | Treating `[EnableQuery]` as natively safe for OData | raw query option passthrough lets clients filter / sort / expand arbitrarily, expanding the data exposure surface | verify `AllowedQueryOptions`, row-level filters, and result scope validation |
| 5 | Ignoring FetchXML XML injection | quote escaping in `<condition value='{input}'>` can inject extra `<condition>` or `or` condition blocks | enumerate FetchXML string concatenation and verify XML escaping |

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct injected query fragments that change the result set (SOQL: `x' OR Name != NULL` (SOQL does not support `--` comments; closing the quote truncates the original condition); OData: `$filter=Name eq 'x' or 1 eq 1`; FetchXML: quote-escape concatenation injecting extra condition blocks), verifying injection really exists and the result set is expanded
- **Negative testing**: construct inputs intercepted by barriers (out-of-allowlist attribute names / sort fields, illegal typed condition values, non-parameterized value slots), verifying parameterized / structured API construction is unaffected
- **Regression testing**: retest QueryExpression condition value validation and parameterization paths after remediation, confirming barriers remain effective and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Evidence References

- EVID_QUERY_EXEC_POINT
- EVID_QUERY_STRING_CONSTRUCTION
- EVID_QUERY_USER_PARAM_TO_FRAGMENT

## Output

- vuln_audit/query_{timestamp}.md (vulnerability ID format: `{severity prefix}-QUERY-{sequence}`, e.g., `H-QUERY-001`, aligned with the QUERY type code of shared/SEVERITY_RATING.md)
- vuln_poc/query_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC, referencing shared/DOTNET_VULN_POC_TEMPLATE.md)
- Each hit in the output must record: query language type (SOQL / OData / FetchXML), construction method (string concatenation / structured API), trace_id, and the citation status of the three EVIDs
