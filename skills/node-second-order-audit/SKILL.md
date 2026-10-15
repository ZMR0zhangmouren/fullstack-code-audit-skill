---
name: node-second-order-audit
description: Node.js second-order injection audit tool. Identifies injection risks at second-order trigger points — such as admin backend rendering, email templates, CSV export, and SQL re-concatenation — after user input passes through Mongoose/Redis/file storage; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js Second-Order Injection Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to storage entries (DB / cache / file / session writes) and trigger entries (rendering / export / SQL concatenation / command execution)
- If the project has data access and business encapsulations such as Repository, CacheService, MailService, or ExportService, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Required: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align the `route_id`s of storage entries and trigger entries)
- Required: `node/route_tracer/*_{timestamp}.md` (used to trace the complete data flow from storage to trigger)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement authentication state differences between storage entries and trigger entries)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement queue / background task / session configuration)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate (cross-entry)**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; storage-trigger pairings across multiple route_ids must be analyzed together, consuming the trace artifacts of each paired route; if `trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- First-order storage: user-controllable data such as registration names / nicknames / shipping addresses / uploaded file names entering the database (mongoose `save`/`insertOne`, knex/sequelize `insert`, `redis.set`, `fs.writeFile`)
- Second-order trigger — admin backend rendering: stored values output verbatim via `res.render` (ejs `<%- %>` / pug `!{}`)
- Second-order trigger — email templates: stored values entering nodemailer templates or text contexts
- Second-order trigger — CSV/Excel export: stored values entering cells in `json2csv`/`exceljs`, enabling formula injection (`=HYPERLINK` / `=CMD`)
- Second-order trigger — SQL retrieval and re-concatenation: stored values re-concatenated into queries in `knex.raw` / `$queryRawUnsafe` / `sequelize.literal`
- Second-order trigger — background tasks: BullMQ / Agenda consuming stored paths / parameters to execute child_process or file operations
- Encoding inconsistency between storage and use phases: encoding at write time but outputting verbatim at read time (or vice versa, or output-context mismatch)
- Trust boundary differences: the storage entry is writable by ordinary users, while the trigger entry is an admin backend or an anonymously reachable export / rendering

## Enumeration Rules (Mandatory Refinement)

- Enumerate storage entries: `.save(`, `insertOne(`, `insertMany(`, `bulkWrite(`, `.create(`, `redis.set(`, `fs.writeFile(`, `req.session.` assignments
- Enumerate trigger entries: `.find(`, `findOne(`, `redis.get(`, `fs.readFile(`, `res.render(`, `<%-`, `!{`, `json2csv`, `exceljs`, `nodemailer`, `knex.raw(`, `$queryRawUnsafe`, `sequelize.literal(`
- Pair by storage key: align storage and trigger sides by collection name / table name, cache key patterns, file path patterns, and message queue topics / channels
- For each pairing record: storage entry route_id, write source and controllability, trigger entry route_id, trigger conditions and triggerer identity, and two-phase encoding methods
- Record trust boundary differences (authentication state of the storage entry vs the trigger entry) and tenant / user isolation conditions
- If Repository / CacheService / MailService and similar wrappers exist, they must be unwrapped layer by layer to the real storage and trigger call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Pre-write sanitization | sanitize-html / xss package / escape-html at the write entry | Check whether the write entry sanitizes and is fail-close (illegal input rejected rather than passed through) | fail-close sanitization → storage layer may not hold; no sanitization or fail-open → 🔴 high risk |
| Post-read encoding consistency | ejs `<%= %>` auto-escaping vs `<%- %>`, React default escaping vs dangerouslySetInnerHTML | Compare whether the two-phase encoding methods of storage and use match the output context | both phases consistent and correct → ✅ safe; inconsistent (`EVID_NODE_SECOND_ORDER_ENCODE_MISMATCH`) → 🔴 high risk |
| Parameterization | Retrieved values still go through placeholders / parameter binding | Check whether secondary queries re-concatenate strings via `knex.raw` / `$queryRawUnsafe` | parameter binding → ✅ safe; string re-concatenation → 🔴 high risk |
| Trust boundary difference | Storage entry writable by ordinary users vs trigger entry in admin backend / anonymous export | Compare authentication requirements and triggerer identity on both sides | difference exists and the trigger side is low-privilege → 🔴 high-risk amplification; same privilege → risk downgraded |
| Isolation and backend permissions | Tenant / user data isolation, BullMQ worker execution account | Check whether attacker data can be triggered by the target user / high-privilege worker | strict isolation → risk downgraded; no isolation / high-privilege worker → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each storage-trigger pairing, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: controllable input enters storage and an unprotected second-order trigger context appears to exist
- `Pending`: one side (storage or trigger) is hit, but the pairing relationship, data flow, or encoding consistency is unclear
- `False Positive`: retrieval goes through parameter binding / automatic template escaping, or the trigger context has no injection slot

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found that the stored value enters the trigger context without effective barriers → `Confirmed Vulnerability`
- Evidence of parameter binding / two-phase encoding consistency fail-close is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_SECOND_ORDER_STORE_POINT` + `EVID_NODE_SECOND_ORDER_TRIGGER_CONTEXT` + `EVID_NODE_SECOND_ORDER_STORAGE_TYPE` three-point closure: controllable input enters storage and, after retrieval, enters a rendering / export / SQL / command context
- `EVID_NODE_SECOND_ORDER_ENCODE_MISMATCH`: encoding inconsistency between the write and trigger phases (e.g., HTML-encoded at write time but output verbatim into a CSV formula slot; or `<%- %>` / `!{}` rendering stored values verbatim)
- A trust boundary difference exists between the trigger entry and the storage entry, and the trigger side is reachable with low privilege / anonymously

### ⚠️Pending Verification

- One side (storage or trigger) is hit, and the pairing or data-flow mapping is missing one hop
- Queue consumption chain (BullMQ / Agenda) trigger conditions and worker execution permissions cannot be confirmed
- Two-phase encoding evidence is incomplete and the output context cannot be confirmed

### False Positive

- Retrieval goes entirely through parameter binding or automatic template escaping, with consistent two-phase encoding (`EVID_NODE_SECOND_ORDER_ENCODE_MISMATCH` excluded)
- Stored values return only to the writer's own session with no privilege difference and no cross-user reachable surface
- The trigger context is pure numeric / boolean comparison with no syntax injection slot

## Testing Recommendations (Mandatory)

### Positive Testing

- Step 1: write `<svg onload=alert(1)>` into a registration name / shipping address; Step 2: trigger execution on the admin backend list page / export
- Write malicious column names to trigger report queries; write `=HYPERLINK("http://evil.com")` to trigger CSV/Excel export
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Pre-write sanitization rejects malicious input; post-retrieval parameterization / automatic template escaping neutralizes injection
- Under trigger-entry authentication / tenant isolation, attacker data cannot be triggered by the target user
- Verify the export layer escapes cells starting with `=`, `+`, `-`, `@`

### Regression Testing

- Retest after remediation at both storage and trigger points, confirming encoding consistency is maintained
- Retest that the queue consumption chain introduces no new high-privilege execution paths
- Newly added export / rendering / background task points are included in the two-phase encoding check

## Evidence References

- `EVID_NODE_SECOND_ORDER_STORE_POINT`
- `EVID_NODE_SECOND_ORDER_TRIGGER_CONTEXT`
- `EVID_NODE_SECOND_ORDER_STORAGE_TYPE`
- `EVID_NODE_SECOND_ORDER_ENCODE_MISMATCH`
- Optional overlay: `EVID_NODE_CFG_MIDDLEWARE_ORDER` (sanitization / authentication middleware mount order)

## Output

- `node/vuln_audit/second_order_{timestamp}.md`
- `node/vuln_poc/second_order_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
