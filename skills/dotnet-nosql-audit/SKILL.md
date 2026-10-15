---
name: dotnet-nosql-audit
description: .NET NoSQL injection audit tool. Identifies structure injection, operator injection, and dynamic filter risks in query construction for MongoDB, Cosmos DB, and similar stores.
---

# .NET NoSQL Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to NoSQL query objects, filter construction, aggregation pipelines, and document updates
- If the project has secondary encapsulations such as Repository, DocumentStore, CustomFilterBuilder, or SearchGateway, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement the host, serialization configuration, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- dynamic construction paths of BsonDocument, Builders.Filter, Builders.Update, and aggregation pipelines in the MongoDB Driver
- scenarios where JSON, Dictionary<string, object>, ExpandoObject, anonymous objects, or frontend-passthrough structures are mapped directly as query conditions
- whether operators such as $where, $regex, $ne, $gt, $lt, $or, and $expr can be directly controlled by user input
- string query concatenation and placeholder boundaries in Cosmos DB, Elastic, LiteDB, or custom document query syntaxes
- whether sort fields, projection fields, pagination conditions, aggregation stages, and lookup / join clauses use whitelists or enum constraints
- whether deserialized objects, GraphQL parameters, or Hub message bodies are sent verbatim into query builders
- whether query results are used for authentication, authorization, tenant boundaries, or high-value business judgments, amplifying the impact

## Enumeration Rules (Mandatory Refinement)

- Enumerate query entries in the MongoDB Driver, Cosmos DB, Elastic, LiteDB, and custom document query wrappers
- Search BsonDocument, FilterDefinition, Builders.Filter, Builders.Update, Aggregate, PipelineDefinition, and QueryDefinition first
- Enumerate code that maps data from JSON, Dictionary, ExpandoObject, GraphQL Input, Hub messages, and dynamic forms directly into query structures
- For each query point record: filter source, operator controllability, sort and projection field controllability, and pagination fragment controllability
- Separately enumerate high-risk capabilities such as $where, $expr, regex, script queries, text searches, and aggregation lookup / facet / union

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Direct query structure mapping** | Confirm whether JSON / Dictionary / ExpandoObject / GraphQL Input is mapped directly as a query structure (such as `BsonDocument.Parse(userInput)`) | user input parsed directly into a query structure → 🔴 high risk; an intermediate mapping layer exists and is fail-close → 🟠 to be confirmed |
| **Operator whitelist** | Confirm whether operators such as `$where`, `$expr`, `$regex`, `$ne`, `$gt`, `$lt`, and `$or` can be controlled by user input | user-controllable high-risk operators → 🔴 high risk; only safe operators (such as `$eq`) allowed and fail-close → ✅ safe; whitelist not visible → ⚠️ to be confirmed |
| **Sort / projection field whitelist** | Confirm whether sort fields, projection fields, and pagination conditions come from a whitelist mapping | fail-close whitelist → ✅ safe; blacklist or no whitelist → 🔴 high risk |
| **Aggregation pipeline injection** | Confirm whether user-controllable input is mixed into the aggregation pipeline (such as `$lookup` target collections and `$match` conditions) | aggregation stages contain user-controllable input → 🔴 high risk; aggregation pipeline fully fixed → ✅ safe |
| **Deserialization into query structures** | Confirm whether deserialized objects (such as from HTTP bodies or Hub messages) are sent verbatim into query builders | sent verbatim without validation → 🔴 high risk; validation layer present and fail-close → ✅ safe |
| **Query result impact surface** | Confirm whether query results enter authentication, authorization, tenant boundaries, or high-value business judgments | query results affect authentication / authorization → 🔴 high-risk amplification; data returned only with no subsequent sensitive operations → 🟠 to be confirmed |

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

1. user-controllable input is mapped directly as a query structure (such as `BsonDocument.Parse(userInput)`), with no barrier validation
2. high-risk operators (`$where`, `$expr`, `$regex`) can be controlled by user input
3. sort / projection / pagination fields have no whitelist or the whitelist is fail-open
4. user-controllable input is mixed into the aggregation pipeline
5. in nested / recursive structures (such as multi-layer Repository wrappers), the top level has validation but sub-levels do not perform equivalent validation
6. deserialized objects are sent verbatim into query builders, and the deserialization layer has no validation

### Pending

1. the context shows a suspicious pattern (such as a `Builders.Filter` call), but the external input source is unclear (trace or call chain needs to be supplemented)
2. a barrier function (such as the operator whitelist) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
3. parameter passing in asynchronous / queue / event chains (such as message queue consumers processing query requests) is not closed
4. a mapping layer from JSON / Dictionary to query structures exists but its implementation is not visible

### False Positive

1. the final query structure comes from fixed constants / enum mappings, and unknown input is refused execution (fail-close)
2. all recursive levels reuse the same fail-close operator whitelist validator
3. user input enters only safe parameterized value slots (such as `$eq` values), and the query structure is fully fixed
4. the deserialization layer has strict type validation, and the validator is fail-close

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct NoSQL injection payloads (such as `{"$where": "this.password == 'admin'"}`, `{"$regex": ".*"}`, and illegal sort fields) and verify injection really exists
- **Negative testing**: construct inputs intercepted by barriers (such as out-of-whitelist operators, illegal field names, and unexpected types) and verify the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Evidence References

- EVID_NOSQL_QUERY_CONSTRUCTION
- EVID_NOSQL_USER_INPUT_INTO_QUERY_STRUCTURE
- EVID_NOSQL_OPERATOR_INJECTION_FIELDS

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (query structure confirmation)**: the query construction points and operator usage positions must be confirmed.
- 🔴 **CHECKPOINT B (structure controllability confirmation)**: the mapping evidence from inputs to query structures / operators must be given.
- 🔴 **CHECKPOINT C (impact surface confirmation)**: whether query results affect authentication, authorization, or high-value business judgments must be stated.
- 🛑 **STOP**: if there are only dynamic query traces without controllability mapping, the conclusion is downgraded to `⚠️Pending Verification`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| dynamic queries exist but input mapping incomplete | complete the mapping from inputs to query structures / operators | downgrade to `⚠️Pending Verification` |
| operator controllability evidence insufficient | analyze the sources of high-risk fragments such as `$where` / `$expr` / regex | no high-risk confirmation; give verification steps only |
| impact surface unclosed (authentication / authorization / high-value business) | trace the usage of query results in business judgments | assess the risk conservatively and retain pending evidence |

🔴 **STOP: when any fallback triggers, outputting "Confirmed Injection" is forbidden.**

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

- Anti-pattern: equating dynamic queries with a valid injection. Correct practice: prove that user input enters operators / structures.
- Anti-pattern: ignoring sort / projection field controllability. Correct practice: check filter, sort, and aggregation fragments simultaneously.
- Anti-pattern: not distinguishing direct dependencies from transitive wrappers. Correct practice: trace to the actual driver call sites.
- Anti-pattern: high-risk conclusions with insufficient evidence. Correct practice: downgrade to `⚠️Pending Verification`.

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

- vuln_audit/nosql_{timestamp}.md
- Optional: vuln_poc/nosql_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
