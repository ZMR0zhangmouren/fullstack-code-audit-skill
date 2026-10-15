---
name: node-nosql-audit
description: Node.js NoSQL injection audit tool. Identifies risks of req.body/req.query raw objects passed straight into mongoose/mongodb queries and $where/$regex/$gt operator injection; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js NoSQL Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to MongoDB / mongoose query construction, ODM sanitization, and operator injection
- If the project has secondary encapsulations such as Repository, QueryBuilder, or MongoHelper, they must be added to the project-internal grabbers section of the output
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

- Raw `req.body` / `req.query` objects passed straight into `find` / `findOne` / `updateOne`
- `$where` / `$regex` / `$gt` operator injection
- Mongoose query concatenation

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites of `mongoose`, `mongodb`, `.find(`, `.findOne(`, `.updateOne(`, `.aggregate(`, `$where`, `$regex`, `$gt`, `$ne`
- For each query point record: driver / ODM package name, query object construction method, and parameter sources (`req.body` / `req.query` / `req.params` / parsed fields)
- Distinguish raw object passthrough (`Model.find(req.body)`) from field-level concatenation (`Model.find({ field: req.query.x })`)
- Record operator usage scenarios: `$where` strings, `$regex` user input, comparison operators such as `$gt` / `$ne` / `$in`
- Record ODM sanitize configuration: `express-mongo-sanitize`, `mongoose.set('sanitizeFilter', true)`, `schema.pre('find')` cleaning
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real mongodb / mongoose query call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Type coercion | Explicit type conversion such as `String(req.body.x)` | Check whether inputs are coerced to primitive types before query construction | all query fields coerced to scalars such as string / number → ✅ safe; objects still passed directly → 🔴 high risk |
| Schema object rejection | joi / zod schema rejecting object types | Read the schema definitions, confirming whether objects / unknown keys are forbidden | fail-close and objects forbidden → ✅ safe; only some fields validated → ⚠️ to be confirmed; no schema → 🔴 high risk |
| ODM sanitize | `express-mongo-sanitize` / `mongoose.set('sanitizeFilter', true)` | Check whether sanitize is enabled and confirm `$` / `.` filtering behavior | enabled and non-bypassable → ✅ safe; loose configuration (e.g., allowDots) → ⚠️ to be confirmed; none → 🔴 high risk |
| $where disabled | Not constructing / not passing `$where` | Search the source for `$where` usage, including `Model.where().$where()` | not used → ✅ safe; used with controllable input → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter query object structures or operator fields directly
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

- `EVID_NODE_NOSQL_QUERY_POINT` + `EVID_NODE_NOSQL_RAW_OBJECT_PASS` + `EVID_NODE_NOSQL_OPERATOR_INJECTION` + no effective Barrier
- Raw `req.body` / `req.query` objects passed directly into `Model.find` / `findOne` / `updateOne` / `aggregate`
- Operator fields such as `$where` / `$regex` / `$gt` come from externally controllable input with no schema / sanitize interception
- User input enters query structures in mongoose query concatenation

### ⚠️Pending Verification

- The context shows a suspicious query call, but the external input source is unclear (trace or call chain needs to be supplemented)
- Barrier functions (e.g., `express-mongo-sanitize`, joi/zod schema) exist, but whether the current branch invokes them and whether the return value is used cannot be confirmed
- The key evidence `EVID_NODE_NOSQL_TYPE_COERCE_GUARD` is missing

### False Positive

- Input types are coerced to strings (`String(req.body.x)`), so objects cannot enter query structures
- joi / zod schemas explicitly reject object types and are fail-close
- `express-mongo-sanitize` or `mongoose.set('sanitizeFilter', true)` is enabled and non-bypassable
- `$where` is not used, and all query fields come from fixed constants / enum mappings

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct raw object passthrough payloads: `{"username":"admin","password":{"$ne":null}}`
- Construct `$where` injection: `{"$where":"this.password.length > 0"}`
- Construct `$regex` injection: `{"username":{"$regex":"^admi[n]?"}}`
- Verify unauthorized data reads or authentication bypass
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct inputs intercepted by barriers: object types rejected by schema, `$` / `.` filtered by sanitize
- Verify objects become `[object Object]` after type coercion, losing operator semantics
- Verify `$where` is explicitly disabled or the key is forbidden by schema

### Regression Testing

- Retest after remediation, confirming schema / sanitize / type coercion remain effective
- Retest raw object passthrough and operator injection payloads, confirming they cannot bypass
- Verify newly added query fields still go through unified validation

## Evidence References

- `EVID_NODE_NOSQL_QUERY_POINT`
- `EVID_NODE_NOSQL_RAW_OBJECT_PASS`
- `EVID_NODE_NOSQL_OPERATOR_INJECTION`
- `EVID_NODE_NOSQL_TYPE_COERCE_GUARD`

## Output

- `node/vuln_audit/nosql_{timestamp}.md`
- `node/vuln_poc/nosql_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
