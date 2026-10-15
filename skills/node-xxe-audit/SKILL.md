---
name: node-xxe-audit
description: Node.js XXE audit tool. Identifies risks in libxmljs parseXml(noent:true), DOCTYPE handling switches in xmldom/sax, and entity configuration in xml2js/fast-xml-parser; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js XXE Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to XML parser selection, DTD / entity switches, input surfaces, and result echoing
- If the project has secondary encapsulations such as XmlParser, SoapAdapter, SsoMetadataLoader, or ConfigImporter, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align XML / SOAP entries, parameter sources, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, serialization configuration, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- libxmljs: `libxml.parseXml(xml, { noent: true })` and `replaceEntities: true` — once enabled, entities are substituted, and external entities can reach file reads and SSRF
- @xmldom/xmldom: how `DOMParser` handles DOCTYPE / ENTITY declarations and its `onError` configuration
- sax: whether the `ondoctype` event and entity declarations are allowed into the parsing flow
- xml2js: defaults to sax-based parsing and does not resolve external entities (relatively safe); verify the version and that entity-related custom configurations have not been extended
- fast-xml-parser: ignores external entities by default (relatively safe); watch for known CVEs in older versions and custom `processEntities` behavior
- Second-order parsing entries such as SAML / SSO metadata, SOAP messages, configuration imports, and docx / xlsx embedded XML uploads
- Whether entity expansion results are echoed to responses, error messages, or trigger outbound requests (blind XXE surface)

## Enumeration Rules (Mandatory Refinement)

- Enumerate with rg: `require\(['"]libxmljs`, `parseXml\(`, `noent`, `replaceEntities`, `DOMParser`, `@xmldom/xmldom`, `require\(['"]sax`, `ondoctype`, `xml2js`, `fast-xml-parser`, `XMLParser\(`
- Record by "library + dangerous switch" pairs: parser library name, version (package.json / package-lock.json), entity / DOCTYPE-related options, and default behavior
- For each parsing point record: XML input source (HTTP body / uploaded file / message queue / configuration import / SSO metadata), whether DOCTYPE is allowed, and the result echo or subsequent usage path
- Do not judge high risk solely on "uses xml2js / fast-xml-parser": they do not resolve external entities by default; after verifying the version and custom configuration, treat them as a low-risk surface
- If a secondary-encapsulated parser exists, it must be unwrapped layer by layer to the real parsing call site and final options

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Dangerous entity switch | libxmljs `noent: true` / `replaceEntities: true` | Read the parseXml call options, confirming the actual value of noent and input controllability | `noent:false` or not enabled → ✅ safe; `noent:true` with controllable input → 🔴 high risk |
| DOCTYPE / ENTITY declaration handling | sax `ondoctype`, xmldom DOMParser configuration | Check whether DOCTYPE / ENTITY declarations are rejected or stripped | stripped before declarations or fail-close rejection → ✅ safe; DTD declarations allowed into parsing → 🔴 high risk |
| Parser default behavior | xml2js / fast-xml-parser do not resolve external entities by default | Verify library versions and custom configurations, confirming the entity resolution path is not enabled | default behavior not extended by customization → 🟠 low-risk surface; custom switches enabling entity handling → 🔴 high risk |
| Input surface validation | Schema validation / DOCTYPE stripping / whitelists | Confirm whether XML input entries are validated or preprocessed | fail-close validation → ✅ safe; parsing directly without validation → 🔴 high risk |
| Echo and outbound | Response echo / error messages / outbound probes | Trace whether entity expansion results are echoed or trigger external requests | echo / controllable outbound → 🔴 high-risk amplification; no echo → 🟠 blind XXE to be confirmed |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable XML input appears to enter a parser with entity processing enabled
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

- `EVID_NODE_XXE_PARSE_POINT` + `EVID_NODE_XXE_EXTERNAL_ENTITY_FLAG`: externally controllable XML enters a `noent:true` parser or one allowing DOCTYPE, with no `EVID_NODE_XXE_SAFE_PARSER_ALTERNATIVE` protection
- libxmljs `noent:true` and the XML input comes from an HTTP body / uploaded file, with entity expansion results echoed to the response
- DOCTYPE / ENTITY declarations allowed and parser exception information echoed, forming a blind XXE channel

### ⚠️Pending Verification

- The context shows suspicious parsing (e.g., a libxmljs call), but the actual option values or external input source are unclear (trace or call chain needs to be supplemented)
- Secondary-encapsulated parser options are scattered, and the final noent / DOCTYPE behavior cannot be confirmed
- XML sources in asynchronous / message queue / SSO metadata pull chains are not closed

### False Positive

- The parser uses xml2js / fast-xml-parser default configuration, the version has no known entity-handling bypasses, and the input surface has fail-close validation
- All levels strip DOCTYPE / reject DTD declarations (fail-close), and the parser has entity substitution disabled
- XML input comes only from trusted internal constants, with no externally controllable source

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct an XXE payload: `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>`
- Construct Billion Laughs entity expansion and `http://` outbound probing (blind XXE), verifying parsing behavior
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct inputs intercepted by barriers: DOCTYPE stripped, external entity resolution failing, declarations rejected
- Verify entity references remain verbatim under `noent:false` without triggering external resource access
- Verify schema / whitelist validation explicitly rejects illegal XML

### Regression Testing

- Retest after remediation, confirming DOCTYPE stripping and parser configuration remain effective
- Retest after upgrading xml2js / fast-xml-parser versions, confirming default behavior unchanged
- Verify newly added parsing entries still go through the unified safe wrapper

## Evidence References

- `EVID_NODE_XXE_PARSE_POINT`
- `EVID_NODE_XXE_EXTERNAL_ENTITY_FLAG`
- `EVID_NODE_XXE_SAFE_PARSER_ALTERNATIVE`

## Output

- `node/vuln_audit/xxe_{timestamp}.md`
- `node/vuln_poc/xxe_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
