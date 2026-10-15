---
name: node-proto-pollution-audit
description: Node.js prototype chain pollution audit tool. Identifies prototype pollution risks caused by controllable __proto__/constructor/prototype key names in recursive merge/clone/assign operations; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js Prototype Chain Pollution Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to prototype chain pollution (recursive merging, deep copying, key-traversal assignment after JSON deserialization, etc.)
- If the project has secondary-encapsulated merge/clone/assign utilities, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, serialization configuration, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **static-evidence-driven**: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Recursive merge/clone convergence points
- Controllable `__proto__` / `constructor` / `prototype` key names
- Post-pollution gadget trigger surfaces (options objects, template engines, child_process options)

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites of `merge(`, `extend(`, `Object.assign`, `lodash.merge`, `_.merge`, `deepmerge`, `clone(`, `defaultsDeep`
- Enumerate key-traversal assignment patterns after JSON parsing: `for (const k in obj)` + `target[k] = ...`
- For each hit record: function origin (native / lodash / deepmerge / project-internal wrapper), target object type, and whether the source comes from `req.body` / `req.query` / `req.params` / JSON.parse results
- Record the key name filtering mechanism: whether `__proto__`, `constructor`, and `prototype` are explicitly checked, or whether a schema whitelist is relied upon
- Record gadgets that may trigger after pollution: Express options objects, template engine configurations, `child_process` options, JWT algorithm configurations, etc.
- If secondary-encapsulated merge/clone/assign utilities exist, their internal implementations must be unwrapped layer by layer

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Key name filtering | joi / zod schema whitelist | Read the schema definitions and validation entry, confirming whether `__proto__` / `constructor` / `prototype` are explicitly rejected | whitelist present and fail-close (illegal keys directly rejected) → ✅ safe; blacklist bypassable via Unicode / case / array paths → ⚠️ to be confirmed; no filtering → 🔴 high risk |
| Object storage isolation | `Object.create(null)` or `Map` replacing plain objects | Search how target objects of merge / assign / clone are created | null-prototype objects or Maps used, and downstream gadgets do not read `Object.prototype` → ✅ safe; plain objects still used → 🔴 high risk |
| Prototype freezing | `Object.freeze(Object.prototype)` | Search whether it exists and is not bypassable (e.g., via `Reflect.defineProperty` or `constructor.prototype` reassignment) | frozen with no bypass path → ✅ defense in depth; not frozen or bypassable → ⚠️ to be confirmed |
| Dependency version | `lodash.merge` / `_.merge` / `defaultsDeep`, etc. | Check the lodash version in `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` | ≥ 4.17.21 with no known CVEs → ✅ safe; below the safe version or unknown version → ⚠️ to be confirmed |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter the source of a merge/clone/assign with a plain object as the target
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

- All three of `EVID_NODE_PROTO_MERGE_SINK` + `EVID_NODE_PROTO_MAGIC_KEY_CONTROL` + `EVID_NODE_PROTO_KEY_FILTER_ABSENT_OR_BYPASS` present, with a reachable entry

### ⚠️Pending Verification

- `EVID_NODE_PROTO_GADGET_TRIGGER` (post-pollution gadget trigger surface evidence) is missing
- Key name filtering exists, but whether it is fail-close or bypassable cannot be confirmed
- The call chain from the source to merge/clone/assign is not fully closed

### False Positive

- An effective key name whitelist exists and is non-bypassable (fail-close)
- `Object.create(null)` / `Map` is used to store untrusted keys, and downstream gadgets do not read `Object.prototype`
- `Object.freeze(Object.prototype)` is enabled with no bypass path
- The source comes entirely from fixed constants / enum mappings, with no externally controllable entry

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct JSON payloads such as `{"__proto__":{"isAdmin":true}}` or `{"constructor":{"prototype":{"isAdmin":true}}}` and verify whether pollution takes effect
- Verify post-pollution gadget triggers (e.g., Express options, template engine configurations, `child_process` parameters tampered)
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct out-of-schema-whitelist key names (`__proto__`, `constructor`, `prototype`) and verify explicit rejection
- Construct Unicode / array-path variants (`__proto__`, `constructor.prototype`) and verify the filtering is robust
- Verify pollution cannot propagate to plain object chains under `Object.create(null)` / Map scenarios

### Regression Testing

- Retest after remediation with the original pollution payload, confirming the target object is no longer polluted
- Retest schema rejection logic, null-prototype object usage, and upgraded lodash versions, confirming barriers remain effective
- Verify no new bypass paths were introduced (e.g., re-pollution via `constructor.prototype`)

## Evidence References

- `EVID_NODE_PROTO_MERGE_SINK`
- `EVID_NODE_PROTO_MAGIC_KEY_CONTROL`
- `EVID_NODE_PROTO_KEY_FILTER_ABSENT_OR_BYPASS`
- `EVID_NODE_PROTO_GADGET_TRIGGER`

## Output

- `node/vuln_audit/proto-pollution_{timestamp}.md`
- `node/vuln_poc/proto-pollution_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
