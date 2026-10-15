---
name: node-xpath-audit
description: Node.js XPath injection audit tool. Identifies XPath expression concatenation and missing parameterization in xpath.select+xmldom and libxmljs find, plus query results entering authorization decisions; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js XPath Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to XPath expression construction, XML data sources, and query result flows
- If the project has secondary encapsulations such as XmlQueryHelper, XPathHelper, ConfigQuerier, or DocumentNavigator, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align XML query entries, parameter sources, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement XML parsing configuration, XPath engines, and runtime control plane)
- Optional: `node/vuln_audit/xxe_{timestamp}.md` (XPath injection and XXE overlap; some findings may be reused)
- This specialty is **trace-gate**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- xpath package + @xmldom/xmldom: expression concatenation such as `xpath.select("//user[name='" + user + "']", doc)`
- libxmljs: expression concatenation in `doc.find("//user[@name='" + user + "']")` and `doc.get(...)`
- Mainstream Node XPath libraries (xpath / libxmljs) have no native variable binding API: defense relies on whitelists and escaping, and alternative protections must be explicitly confirmed
- XML data sources: configuration XML, request bodies, SSO / SAML responses, message queue messages, database XML columns
- Paths where query results enter authorization, business decisions, response echoes, or logs
- Boundary with node-xxe-audit: parser configuration / entity handling is covered by the XXE specialty; this specialty focuses on the XPath query layer

## Enumeration Rules (Mandatory Refinement)

- Enumerate with rg: `require\(['"]xpath`, `xpath\.select|xpath\.select1`, `\.find\(`, `\.get\(`, `@xmldom/xmldom|DOMParser`, `libxmljs|parseXml`
- Enumerate expression concatenation and interpolation positions: rg `//`, `@`, `text\(\)`, `contains\(`, and trace back the variable sources in hit expressions
- Enumerate XML data sources: configuration file loading, HTTP request bodies, SSO / SAML responses, message queue messages, database XML columns
- For each query point record: expression construction method, parameter sources, whether whitelist / escaping is applied, XML source, and result usage
- If secondary-encapsulated query helpers exist, they must be unwrapped layer by layer to the real `xpath.select` / `doc.find` call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| XPath expression concatenation | `xpath.select('//' + tag + '[...]', doc)` | Read the expression construction source, confirming whether it comes from string concatenation / template interpolation | user input participating in concatenation → 🔴 high risk; fixed expression with no interpolation → ✅ safe |
| Parameterization / variable binding | Mainstream Node xpath libraries (xpath / libxmljs) have no native variable binding API | Confirm whether a parameterized alternative wrapper exists (fail-close concatenator / precompiled cache) | fail-close wrapper present → ✅ safe; no native parameterization and no alternative protection → 🔴 high risk |
| Input whitelist | Regex `[a-zA-Z0-9_-]` / enum mapping | Read the validation implementation, confirming it covers XPath metacharacters such as quotes and brackets and is fail-close | fail-close whitelist → ✅ safe; escaping quotes only → ⚠️ bypassable; no validation → 🔴 high risk |
| Query result sensitive semantics | Results entering authorization / business decisions | Trace the flow of query results | entering authorization decisions → 🔴 high-risk amplification; internal logs only → 🟠 to be confirmed |
| Parser configuration linkage | XML parser-layer entity configuration | Parser-layer risks are covered by node-xxe-audit; hand cross findings to that specialty for review | parser configuration anomalies → handed to the XXE specialty; query-layer issues only → handled by this specialty |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter XPath expression concatenation slots
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

- `EVID_NODE_XPATH_SELECT_POINT` + `EVID_NODE_XPATH_CONCAT` + no effective `EVID_NODE_XPATH_PARAM_BINDING`
- Query results enter authorization / sensitive business decisions, and the expression concatenation slot is externally controllable
- The input whitelist / escape implementation is fail-open or bypassable via encoding / double escaping

### ⚠️Pending Verification

- The context shows a suspicious pattern (e.g., an `xpath.select` call), but the external input source is unclear (trace or call chain needs to be supplemented)
- A parameterized alternative wrapper exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
- XML sources and expression parameter passing in asynchronous / queue / SSO response chains are not closed

### False Positive

- The XPath expression comes from fixed constants, and unknown input is refused execution (fail-close)
- User input enters only value slots validated by a fail-close whitelist, and the expression structure is fully fixed
- Query results are used for internal logs only without echoing, with no authorization / business decision impact

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct XPath injection payloads: `' or '1'='1`, `' or ''='`, `//user[password/text()='x' or '1'='1']`
- Verify authorization query scenario injection achieving authentication bypass and data extraction
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct inputs intercepted by barriers: metacharacters escaped / rejected, out-of-whitelist tag names
- Verify illegal inputs return empty results under a fail-close concatenation wrapper
- Verify the whitelist validator rejects encoded variants

### Regression Testing

- Retest after remediation, confirming whitelists and wrappers remain effective
- Retest after upgrading xpath / libxmljs / xmldom versions, confirming query behavior unchanged
- Verify newly added XPath query entries still go through the unified wrapper

## Evidence References

- `EVID_NODE_XPATH_SELECT_POINT`
- `EVID_NODE_XPATH_CONCAT`
- `EVID_NODE_XPATH_PARAM_BINDING`

## Output

- `node/vuln_audit/xpath_{timestamp}.md`
- `node/vuln_poc/xpath_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
