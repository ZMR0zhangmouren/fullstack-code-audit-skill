---
name: dotnet-xxe-audit
description: .NET XXE audit tool. Identifies external entity and DTD risks in parsing scenarios related to XmlDocument, XmlReader, XDocument, XPath, and XSLT.
---

# .NET XXE Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to XML parsers, DTDs, XmlResolver, XSLT, schema imports, and external resource access
- If the project has secondary encapsulations such as XmlHelper, ConfigImporter, FeedParser, or SoapBridge, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align XML / SOAP entries, parameter sources, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement XML parsing configuration, host, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- XmlDocument.LoadXml / Load: whether XmlResolver = null is set
- XmlReader.Create: whether XmlReaderSettings.DtdProcessing is Prohibit
- XDocument / XPathDocument: input sources and parser configuration
- XslCompiledTransform.Load: controllability of XSLT sources and script execution
- DataSet.ReadXml / ReadXmlSchema: DTD handling of XML input
- SOAP / WCF message parsing: XML processing in custom MessageInspectors
- SAML / metadata import: XML parsing of external IdP metadata
- Office / OpenXML file parsing: embedded XML entities in uploaded docx / xlsx files

## Evidence References

- EVID_XXE_PARSER_CALL
- EVID_XXE_INPUT_SOURCE
- EVID_XXE_ENTITY_DOCTYPE_SAFETY_AND_ECHO

## Enumeration Rules (Mandatory Refinement)

- Enumerate entry points of XmlDocument, XmlReader, XDocument, XPathDocument, XslCompiledTransform, DataSet.ReadXml, and SOAP parsing
- Search LoadXml, CreateReader, DtdProcessing, XmlResolver, Transform, ReadXml, schema, and metadata import key calls first
- Enumerate second-order parsing entry points such as HTTP bodies, uploaded files, message buses, configuration imports, WCF / SOAP, SAML / metadata, and Office / OpenXML
- For each parsing point record: safety options, input source, whether DOCTYPE / entities are allowed, and the result echo or subsequent usage path

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **DtdProcessing configuration** | Confirm whether `XmlReaderSettings.DtdProcessing` is `Prohibit`, or `XmlDocument.XmlResolver` is `null` | `Prohibit` / `null` → ✅ safe; `Parse` or allowed by default → 🔴 high risk; configuration not visible → ⚠️ to be confirmed |
| **XmlResolver restrictions** | Confirm whether `XmlSecureResolver` or a custom restricted resolver is used to limit external entity resolution | external resources strictly restricted → ✅ safe; arbitrary external URIs allowed → 🔴 high risk; configuration not visible → ⚠️ to be confirmed |
| **Entity expansion limits** | Confirm whether `MaxCharactersFromEntities` has a reasonable upper bound, preventing Billion Laughs / entity expansion DoS | reasonable upper bound present → ✅ safe; no limits → 🔴 high risk |
| **XSLT external resources** | Confirm whether `XslCompiledTransform` allows the `document()` function to access external resources and whether script execution is enabled | external resources / scripts forbidden → ✅ safe; allowed → 🔴 high risk |
| **Input source validation** | Confirm whether XML inputs (HTTP bodies / uploaded files / SOAP / configuration imports) undergo schema validation or signature verification | schema / signature validation present and fail-close → ✅ safe; no validation → 🔴 high risk |
| **Result echo / outbound** | Confirm whether entity expansion results are echoed to responses, written to files, or trigger outbound requests | controllable echo / outbound → 🔴 high-risk amplification; no echo and no outbound → 🟠 to be confirmed |

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

1. `DtdProcessing` is `Parse` or allowed by default, and `XmlResolver` does not restrict external entities
2. user-controllable XML inputs (HTTP bodies / uploaded files / SOAP) enter parsers without schema / signature validation
3. `XslCompiledTransform` allows the `document()` function to access external resources or has script execution enabled
4. entity expansion is unlimited, creating a Billion Laughs DoS risk
5. in nested / recursive structures (such as multi-layer XmlHelper wrappers), the top level has safe configuration but sub-levels do not apply equivalent configuration

### Pending

1. the context shows a suspicious pattern (such as a `LoadXml` call), but the external input source is unclear (trace or call chain needs to be supplemented)
2. barrier configuration (such as `DtdProcessing`) exists, but whether the current call site uses that configuration cannot be confirmed
3. parameter passing in asynchronous / queue / event chains (such as message queue consumers processing XML) is not closed
4. XSLT external resource restrictions are scattered across multiple places, and the complete behavior cannot be confirmed

### False Positive

1. `DtdProcessing` is explicitly set to `Prohibit`, and `XmlResolver` is `null`
2. all recursive levels reuse the same safe configuration (`Prohibit` + null Resolver)
3. XML input comes only from trusted internal sources and passes strict schema validation + signature verification
4. `XslCompiledTransform` forbids `document()` and script execution

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct XXE payloads (such as `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>` and Billion Laughs) and verify the vulnerability really exists
- **Negative testing**: construct inputs intercepted by barriers (such as DTDs prohibited, external entity resolution failing, and entity expansion limits exceeded) and verify the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (parser configuration confirmation)**: DtdProcessing, XmlResolver, and entity limit configurations must be confirmed.
- 🔴 **CHECKPOINT B (input surface confirmation)**: XML input sources and controllable boundaries (HTTP / upload / messages) must be confirmed.
- 🔴 **CHECKPOINT C (echo and outbound confirmation)**: whether entity expansion results are echoed, written to disk, or trigger outbound requests must be confirmed.
- 🛑 **STOP**: if safe configuration and input controllability are not both verified, declaring XXE invalid is forbidden.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| parser configuration evidence incomplete | complete DtdProcessing / XmlResolver / entity limit configurations | downgrade to `⚠️Pending Verification` |
| input source boundary unclear | enumerate HTTP / upload / message / second-order parsing entries | no "no XXE" conclusion |
| echo and outbound chain unclosed | trace to responses / logs / disk writes / downstream requests | assess conservatively and retain an evidence-supplementation list |

🔴 **STOP: when any fallback triggers, declaring XXE invalid is forbidden.**

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

- Anti-pattern: judging safe based only on default configuration. Correct practice: verify actual parser instances and runtime options.
- Anti-pattern: ignoring second-order parsing paths (upload / messages / OpenXML). Correct practice: cover all XML input surfaces.
- Anti-pattern: not checking XSLT / document() outbound access. Correct practice: audit extension capabilities and resource access policies.
- Anti-pattern: judging "no XXE" directly with insufficient evidence. Correct practice: downgrade and list the pending evidence.

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

- vuln_audit/xxe_{timestamp}.md
- Optional: vuln_poc/xxe_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
