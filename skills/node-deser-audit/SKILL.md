---
name: node-deser-audit
description: Node.js deserialization audit tool. Identifies function execution risks in node-serialize.unserialize, js-yaml.load (unsafe schema), serialize-javascript, funcster, and express-session custom deserializers; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js Deserialization Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to deserialization call sites, serialization library and schema selection, input sources, and function execution trigger surfaces
- If the project has secondary encapsulations such as SerializeHelper, SessionCodec, CacheSerializer, or MessageDecoder, they must be added to the project-internal grabbers section of the output
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

- `node-serialize`'s `unserialize()`: functions marked with `_$$ND_FUNC$$_` execute immediately as IIFE, an RCE-equivalent primitive
- `js-yaml` <4 `yaml.load()`: the default `DEFAULT_FULL_SCHEMA` supports the `!!js/function` function type; ≥4 `load` defaults to the safe schema and throws `YAMLException` on function types
- The deserialization direction of `serialize-javascript`: the output contains function bodies; if the restore side rebuilds them via `eval`/`new Function`, an execution chain forms
- `funcster`: VM sandbox function restoration, but deep-copy and prototype-chain restoration have escape surfaces
- `express-session`'s default `JSON.stringify`/`JSON.parse` storage is safe; explicitly configured `serializer`/`deserializer` options require focused review
- Redis/Memcached session caches (connect-redis, etc.) and the second-order deserialization pollution surface after cross-service reads
- `JSON.parse` itself only parses JSON text and does not execute code (false-positive boundary; see determination rules)

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites of `unserialize(`, `node-serialize`, `serialize-javascript`, `funcster`, `deserialize(`, `yaml.load(`, `safeLoad(`, `DEFAULT_FULL_SCHEMA`, `DEFAULT_SAFE_SCHEMA`, `!!js/function`
- Enumerate session and cache chains: `express-session`, `deserializer`, `serializer`, `connect-redis`, `connect-memcached`, `JSON.parse(`, `eval(`, `new Function`
- For each deserialization point record: library and version (package.json + lockfile), explicit schema value, input source (req.body / req.headers / cookie / Redis / MQ), and whether function types are involved
- Distinguish safe directions from dangerous directions: `JSON.stringify`→`JSON.parse` pure data round-trip is safe; `serialize-javascript`→`eval` restore, `yaml.load` full schema, and `unserialize` function markers are dangerous directions
- Identify IIFE trigger surfaces: a `_$$ND_FUNC$$_` function body immediately followed by `()` invocation, and `!!js/function` auto-compilation execution
- Record the `store` backend of `express-session` and custom `serializer`/`deserializer` options, unwrapping to the real restore call sites
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real `unserialize`/`yaml.load`/`JSON.parse` call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Safe schema / version | `js-yaml` ≥4 `load` default safe schema; `{ schema: DEFAULT_SAFE_SCHEMA }` | Confirm the js-yaml version and the schema parameter of `yaml.load` | ≥4 default or explicit safe schema → ✅ safe; <4 default `DEFAULT_FULL_SCHEMA` with controllable input → 🔴 high risk |
| Data format whitelist | `JSON.parse` + ajv/zod/joi fixed schema | Check whether restore is preceded by forced JSON-text and fixed-schema validation | JSON.parse + fail-close schema validation → ✅ safe; direct restore of arbitrary text → 🔴 high risk |
| Input source control | cookie-signature signing / HMAC / internal trusted source | Check whether deserialized data has signature validation and the key is not weak | signature validation fail-close (verification failure → refuse) → ✅ safe; no signature or key leakage → 🔴 high risk |
| Session store configuration | `express-session` default JSON serialization | Check whether custom `serializer`/`deserializer` is configured and whether the store backend performs second deserialization | default JSON.stringify/parse → ✅ safe; custom deserializer with externally influenceable session data → 🔴 high risk |
| Dangerous library prohibition | `node-serialize` / `funcster` / `serialize-javascript` restore side | Confirm whether the dependency exists and the deserialization entry is reachable | not installed or entry unreachable → 🟠 to be confirmed; installed with controllable input → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter an unsafe deserialization call or a function execution trigger position
- `Pending`: the context shows a suspicious pattern, but the external input source, barrier behavior, or call chain is unclear
- `False Positive`: the input comes from fixed constants / enum mappings, or the barrier has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found that externally controllable input enters the deserialization Sink position → `Confirmed Vulnerability`
- Fixed schema mapping / fail-close evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, schema validators, signature verification, and restorers must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse restoration, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_DESER_UNSAFE_CALL` + `EVID_NODE_DESER_INPUT_CONTROL` + no `EVID_NODE_DESER_SAFE_ALTERNATIVE`: externally controllable data enters `node-serialize.unserialize` / js-yaml <4 `yaml.load` / the `serialize-javascript` restore side
- `EVID_NODE_DESER_UNSAFE_CALL` + `EVID_NODE_DESER_GADGET_REACH`: `!!js/function` or `_$$ND_FUNC$$_` IIFE function bodies reachable and auto-compiled for execution
- `express-session` with a custom `deserializer` and externally influenceable session data (cookie direct storage / cross-service cache writes)
- Redis/Memcached cache values polluted by the writer, then restored in a non-JSON way by the reader, triggering function execution

### ⚠️Pending Verification

- The context shows a suspicious pattern (e.g., an `unserialize(` call), but the external input source is unclear (trace or call chain needs to be supplemented)
- `funcster` / `serialize-javascript` is installed, but the deserialization restore entry is unreachable in the current code
- The Redis/Memcached session chain is not closed: whether stored values contain serialized objects and the writer's controllability cannot be confirmed

### False Positive

- Deserialization data comes only from fixed constants / internal trusted sources, and signature validation is fail-close (verification failure → refuse restore)
- `JSON.parse` + ajv/zod/joi fixed-schema validation is used: `JSON.parse` does not execute code, and there is no function-type trigger surface
- `js-yaml` ≥4 default `load` (safe schema) parses pure-data YAML, and function types throw `YAMLException`

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct a confirmed-exploitable YAML payload: `!!js/function "return require('child_process').execSync('id')"`, verifying command execution under js-yaml <4 `yaml.load`
- Construct a node-serialize IIFE payload: `_$$ND_FUNC$$_function(){require('child_process').exec('id')}()`, verifying immediate execution by `unserialize`
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Verify js-yaml ≥4 throws `YAMLException` on `!!js/function` (fail-close)
- Verify `JSON.parse` throws a syntax error on function-body text, and ajv/zod rejects out-of-schema fields
- Verify signature validation refuses to restore a tampered session cookie

### Regression Testing

- Retest after remediation, confirming the schema / signature barriers remain effective
- Retest after dependency upgrades (js-yaml ≥4, removing node-serialize), confirming no new restore paths were introduced
- Verify that newly added cache backends still keep JSON pure-data round trips

## Evidence References

- `EVID_NODE_DESER_UNSAFE_CALL`
- `EVID_NODE_DESER_INPUT_CONTROL`
- `EVID_NODE_DESER_GADGET_REACH`
- `EVID_NODE_DESER_SAFE_ALTERNATIVE`
- Optional overlays: `EVID_NODE_CFG_SECURITY_SWITCH` (schema / serializer default configuration evidence), `EVID_NODE_CFG_MIDDLEWARE_ORDER` (session middleware and restore call order evidence)

## Output

- `node/vuln_audit/deser_{timestamp}.md`
- `node/vuln_poc/deser_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
