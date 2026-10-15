---
name: node-ldap-audit
description: Node.js LDAP injection audit tool. Identifies filter and DN concatenation in ldapjs search({filter}) / bind, missing RFC 4515 escaping, and anonymous bind fallback risks; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js LDAP Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to LDAP filter construction, DN concatenation, bind methods, search boundaries, and authentication bypass
- If the project has secondary encapsulations such as LdapService, AuthAdapter, DirectoryConnector, or SyncConnector, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align login / directory query entries, parameter sources, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement authentication integration, host configuration, and runtime control plane)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- ldapjs `client.search(base, { filter: ... })`: filter strings concatenating user input without escaping LDAP metacharacters
- `client.bind(dn, password)`: authentication bypass caused by concatenation in the bind DN / credentials
- DN construction: RFC 4514 escaping of RDN component concatenation such as `cn=${user},ou=people,dc=...`
- Implementation of and concatenation ordering for RFC 4515 metacharacter (`*`, `(`, `)`, `\`, NUL) escaping
- Anonymous bind / continue-allow fallback behavior after bind failure
- Overly broad queries caused by user-controllable scope, attributes, and base parameters
- Paths where login validation, user search, group membership queries, directory sync, and SSO assertion content enter filters

## Enumeration Rules (Mandatory Refinement)

- Enumerate with rg: `require\(['"]ldapjs`, `createClient\(`, `\.search\(`, `\.bind\(`, `escapeFilter`, `scope`, `attributes`, `baseDN|baseDn|searchBase`
- Enumerate filter and DN construction positions in login, user search, group membership queries, sync tasks, and SSO integration
- For each call site record: filter / DN construction method, escape implementation, bind method, scope / attributes sources, and the path by which results participate in authentication and authorization
- Distinguish the two risk semantics of authentication bind versus search query; bind scenarios are annotated separately
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real `client.search` / `client.bind` call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Filter string concatenation | `search(base, { filter: 'uid=' + user })` | Read the filter construction source, confirming whether it comes from string concatenation / template interpolation | user input participating in concatenation without RFC 4515 escaping → 🔴 high risk; fixed template + escaped value slot → 🟠 value-slot boundary to be confirmed |
| RFC 4515 escape implementation | Self-wrapped `escapeFilter()` | Read the implementation source, confirming handling of `*` `(` `)` `\` NUL and control characters, and whether escaping completes before concatenation | complete escaping and fail-close → ✅ safe; partial escaping → ⚠️ bypassable; no escaping → 🔴 high risk |
| DN construction (RFC 4514) | `cn=${user},ou=people` concatenation | Confirm the DN component escape implementation and sources | RFC 4514 escaping → ✅ safe; no escaping → 🔴 high risk |
| Authentication bind semantics | `client.bind(dn, password)` | Distinguish bind from search; confirm whether the bind DN / credentials are user-controllable | bind DN concatenation controllable → 🔴 authentication bypass; fixed service account → ✅ safe |
| Anonymous bind fallback | Anonymous fallback or continue-allow in the bind-failure catch | Read the error handling branch and subsequent allow logic | bind failure immediately rejected (fail-close) → ✅ safe; fallback to anonymous / continue allowing → 🔴 high risk |
| Search scope and attributes | scope / attributes / base parameters | Confirm whether scope, attributes, and base come from user input | fixed scope + attribute whitelist → ✅ safe; user-controllable → 🟠 impact to be confirmed |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter filter / DN concatenation or authentication bind credential slots
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

- `EVID_NODE_LDAP_SEARCH_POINT` + `EVID_NODE_LDAP_FILTER_CONCAT` + no effective `EVID_NODE_LDAP_ESCAPE_IMPLEMENTATION`
- `EVID_NODE_LDAP_BIND_ANONYMOUS_FALLBACK`: fallback to anonymous bind after bind failure and subsequent authorization logic allowed
- Authentication bind scenario where DN / filter concatenates the user name, allowing `*)(` injection to close the filter and bypass authentication
- Filter concatenation escape implementation is fail-open or bypassable via double encoding

### ⚠️Pending Verification

- The context shows a suspicious pattern (e.g., a `client.search` call), but the external input source is unclear (trace or call chain needs to be supplemented)
- An escape function exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
- Parameter passing in asynchronous / queue / event chains (e.g., directory sync tasks, SSO assertions) is not closed

### False Positive

- Filter / DN comes from fixed constants / enum mappings, and unknown input is refused execution (fail-close)
- All levels reuse the same RFC 4515/4514 escape function, and escaping completes before concatenation
- Bind uses fixed service account credentials, and user input enters only strictly escaped value slots

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct LDAP injection payloads: `*)(uid=*))(&(uid=*`, `admin*)(objectClass=*`, `cn=admin\00`
- Verify bind-scenario injection achieving authentication bypass and search-scenario injection broadening query scope
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct inputs intercepted by barriers: unescaped metacharacters properly escaped, illegal DN formats rejected
- Verify bind failure is explicitly rejected without anonymous bind fallback
- Verify escape function handling of double-encoded inputs

### Regression Testing

- Retest after remediation, confirming escaping and rejection logic remain effective
- Retest after upgrading the ldapjs version, confirming filter parsing behavior unchanged
- Verify newly added LDAP query entries still go through the unified escape wrapper

## Evidence References

- `EVID_NODE_LDAP_SEARCH_POINT`
- `EVID_NODE_LDAP_FILTER_CONCAT`
- `EVID_NODE_LDAP_ESCAPE_IMPLEMENTATION`
- `EVID_NODE_LDAP_BIND_ANONYMOUS_FALLBACK`

## Output

- `node/vuln_audit/ldap_{timestamp}.md`
- `node/vuln_poc/ldap_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
