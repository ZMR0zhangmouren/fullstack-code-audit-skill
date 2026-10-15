---
name: dotnet-xpath-audit
description: .NET XPath injection audit tool. Identifies injection risks from user input into XPath query construction in XPathNavigator, XPathDocument, and XPathExpression; split from the XXE specialty.
---

# .NET XPath Injection Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to XML parsers, XPath expressions, data flows, user input, and query construction
- If the project has secondary encapsulations such as XmlQueryHelper, XPathHelper, ConfigQuerier, or DocumentNavigator, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align XML query entries, parameter sources, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement XML parsing configuration, XPath engines, and runtime control plane)
- Optional: `vuln_audit/xxe_{timestamp}.md` (XPath injection and XXE overlap; some findings may be reused)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- query expression construction of XPathNavigator, XPathDocument, and XPathExpression
- XmlNamespaceManager and XPath namespace resolution
- concatenation paths from user input into XPath query strings
- XPath injection payloads: `' or '1'='1`, `//user[password/text()='xxx']`, `substring(//password,1,1)='a'`
- XML data sources: configuration XML, XML configuration files, AppSettings, Web.config, appsettings.json
- echoing, writing, and logging of XPath query results
- XmlResolver configuration in XPath queries (potentially enabling XXE combination exploitation)

## Enumeration Rules (Mandatory Refinement)

- Enumerate all code files using XPathNavigator, XPathDocument, and XPathExpression
- Search key calls such as Select, XPathCompile, XPathEvaluate, SelectNodes, SelectSingleNode, Matches, and XmlNamespaceManager first
- Enumerate positions where string concatenation, interpolated strings, String.Format, and StringBuilder construct XPath expressions
- Enumerate XML data sources: configuration file loading, HTTP request XML bodies, SOAP messages, uploaded files, database XML columns, and message queue XML messages
- For each XPath query point record: expression construction method, parameter source, whether parameterization is used, XPath engine version, and XmlResolver configuration

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **XPath string concatenation** | Read the XPath expression construction source, confirming whether it comes from string concatenation / interpolation (such as `$"//user[password='{input}']"`) | user input participating in XPath concatenation → 🔴 high risk; fixed XPath template + parameterized value slots → 🟠 value-slot boundary to be confirmed |
| **XPath parameterization / precompilation** | Confirm whether `XPathExpression.Compile` + variable binding is used instead of string concatenation | parameterization / variable binding used correctly → ✅ safe; parameterization mixed with concatenation → ⚠️ to be confirmed; no parameterization → 🔴 high risk |
| **Input escaping / whitelist** | Confirm whether escaping or whitelist validation exists before user input enters XPath (such as allowing only alphanumeric characters) | fail-close whitelist → ✅ safe; partial escaping (such as escaping quotes only) → ⚠️ bypassable; no escaping → 🔴 high risk |
| **XmlResolver configuration** | Confirm whether `XmlResolver` is disabled or restricted, preventing XPath + XXE combination exploitation | disabled / restricted XmlResolver → ✅ safe; external entity resolution allowed → ⚠️ to be confirmed (XXE specialty re-verification needed) |
| **Namespace management** | Confirm whether `XmlNamespaceManager` strictly manages namespaces and whether users can inject namespace prefixes | namespaces strictly managed → ✅ safe; user-controllable namespace prefixes → ⚠️ to be confirmed |
| **Query result sensitive semantics** | Confirm whether XPath query results enter authorization, business decisions, echoing, or write operations | entering authorization / sensitive business judgments → 🔴 high-risk amplification; internal logging only → 🟠 to be confirmed |

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

1. user-controllable input enters XPath string concatenation positions directly, without parameterization / escaping
2. string interpolation is used in the XPath expression to construct query conditions (such as `$"//user[@name='{input}']"`)
3. input escaping is fail-open or silent-fallback, bypassable via encoding / double escaping
4. XmlResolver allows external entity resolution, and XPath queries can be exploited for XXE combination attacks
5. in nested / recursive structures (such as multi-layer XmlQueryHelper wrappers), the top level has validation but sub-levels do not perform equivalent validation
6. XPath query results enter authorization / sensitive business judgments

### Pending

1. the context shows a suspicious pattern (such as a `SelectNodes` call), but the external input source is unclear (trace or call chain needs to be supplemented)
2. a barrier function (such as a parameterization wrapper) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
3. parameter passing in asynchronous / queue / event chains is not closed
4. XmlResolver configuration is scattered across multiple places, and the complete configuration behavior cannot be confirmed

### False Positive

1. the final XPath expression comes from fixed constants, and unknown input is refused execution (fail-close)
2. all recursive levels reuse the same fail-close input whitelist validator
3. user input enters only strictly parameterized value slots, and the XPath structure is fully fixed
4. XmlResolver has external entity resolution disabled, and the XPath query has no concatenation / interpolation

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct XPath injection payloads (such as `' or '1'='1`, `' or ''='`, and `//user[password/text()='x' or '1'='1']`) and verify injection really exists
- **Negative testing**: construct inputs intercepted by barriers (such as concatenation attempts outside parameterized value slots and illegal characters escaped) and verify the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

### Mandatory Record Fields

| Field | Description |
|------|------|
| file_path | source file path |
| line_number | line number |
| xpath_api | the XPath API type used |
| query_construction | query construction method (concatenation / parameterization) |
| user_input_source | user input source |
| input_sanitization | input filtering / escaping measures |
| xml_datasource | XML data source type |
| namespace_usage | whether XmlNamespaceManager is used |
| resolver_config | XmlResolver configuration |
| result_usage | query result usage |
| risk_level | risk level (P0-P4) |

## Evidence References

- EVID_XPATH_QUERY_CONSTRUCTION (new): XPath query construction point
- EVID_XPATH_USER_INPUT_INTO_QUERY (new): user input flowing into the XPath query
- EVID_XXE_PARSER_CALL: reuse the XML parser call evidence of the XXE specialty
- EVID_XXE_INPUT_SOURCE: reuse the XML input source evidence of the XXE specialty

## Failure and Degradation Branches (Mandatory)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| XPath query point found but input source untraceable | output query construction evidence and visible variables first | mark `⚠️Source Pending Verification`; confirmed injection conclusions are forbidden |
| user input controllable but missing execution context (namespace / parser) | record the current `XmlNamespaceManager` / `XmlResolver` configuration | downgrade to PARTIAL and list the missing configuration evidence |
| conflict with XXE evidence (inconsistent parser configuration) | retain evidence from both sides and mark the conflict source | downgrade the conclusion; await cross-review with framework / xxe |

🔴 **STOP: when the three segments of evidence — "input → XPath expression → execution result" — are missing, outputting a confirmed vulnerability is forbidden.**

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

| # | Anti-pattern | Why not | Correct practice |
|---|---|---|---|
| 1 | Treating XXE evidence directly as XPath injection evidence | the two have different boundaries | give parser-layer and query-layer evidence separately |
| 2 | Giving only payloads without code mapping | not reviewable or fixable | the API / line number / variable mapping must be stated |
| 3 | Ignoring the namespace context | query reachability may be misjudged | record the relationship between NamespaceManager and the expression |

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (query construction confirmation)**: the XPath expression construction points and input sources must be confirmed.
- 🔴 **CHECKPOINT B (parameterization / escaping confirmation)**: variable binding or safe escaping strategies must be confirmed.
- 🔴 **CHECKPOINT C (data impact confirmation)**: whether query results affect authorization, business decisions, or echoing must be confirmed.
- 🛑 **STOP**: if expression construction and protection evidence are not closed, declaring XPath injection invalid is forbidden.

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

- vuln_audit/xpath_{timestamp}.md
- Optional: vuln_poc/xpath_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC)

### Structure of vuln_audit/xpath_{timestamp}.md

```markdown
# XPath Injection Audit Report

## Overview
- Audit scope: `source_path`
- Audit time: {timestamp}
- Number of XPath injection risk points found: N

## High-Risk Findings (EVID_XPATH_* evidence references)
...list item by item, including file path, line number, vulnerability description, and risk level...

## Medium-Risk Findings
...list item by item...

## Low-Risk Findings
...list item by item...

## Project-Internal XPath-Related Grabbers
...project-specific secondary encapsulations...

## XPath Injection Payload Reference
### Authentication Bypass
' or '1'='1
' or ''='

### Data Extraction
//element[@attribute='value']
//*/text()
substring(//password,1,1)='a'

### Conditional Inference
[position()=N]
[count(//element)=N]

## Remediation Suggestions
1. Use parameterized XPath queries (XPathExpression.SetContext)
2. Input whitelist validation
3. XPath result desensitization
4. Disable XmlResolver or use a restricted XmlUrlResolver
```

## Boundary with the XXE Specialty

- **This skill's responsibility**: XPath query logic, expression construction, data flow from user input to XPath
- **dotnet-xxe-audit responsibility**: XML parser configuration, external entities, DTD handling, XInclude
- **Cross scenario**: XmlResolver configuration affects both XXE and XPath injection; the XXE specialty covers parser configuration first, and this skill focuses on the XPath query layer
