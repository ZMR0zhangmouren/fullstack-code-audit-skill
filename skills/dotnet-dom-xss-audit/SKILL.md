---
name: dotnet-dom-xss-audit
description: .NET DOM-XSS audit tool. Identifies client-side XSS risks in Blazor JavaScript interop, IJSRuntime calls, and frontend frameworks; split from the XSS specialty.
---

# .NET DOM-XSS Audit

## Shared Grabber Index References

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as this Skill's base retrieval index
- By default, use shared/DOTNET_SINK_REFERENCE.md as this specialty's sink type definition and trace-gate validation baseline
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover shared grabbers related to frontend output, JavaScript execution contexts, URL parsing, DOM operations, and Blazor JSInterop
- If the project has secondary encapsulations such as JSBridge, BlazorInterop, DynamicComponentRenderer, ClientTemplateRenderer, they must be added to the in-project grabbers section of the output
- When this Skill's specialty enumeration rules are more detailed than the shared index, this Skill prevails, but the shared index's base coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align page entries, parameter sources, and `route_id`)
- Optional: `framework_audit/blazor_{timestamp}.md` (used to supplement Blazor JSInterop configuration and security control surfaces)
- Optional: `vuln_audit/xss_{timestamp}.md` (DOM-XSS and server-side XSS overlap; some findings can be reused)
- In trace-gate scenarios, prefer consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it can serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

### Blazor JavaScript Interop
- IJSRuntime.InvokeAsync calls: JS method names, parameter sources, whether user input is passed
- Reflection calls of DotNet.invokeMethodAsync, DotNet.invokeMethod
- JSRuntime.SetTonicInitialValueAsync and component state synchronization
- JS calls and state injection during Blazor Server prerendering
- JS bridging in CustomElement and WebComponent encapsulation

### JavaScript Sink Points
- eval(), setTimeout/setInterval (string form)
- innerHTML, outerHTML, insertAdjacentHTML
- document.write, document.writeln
- location.* (href, pathname, search, hash)
- eval, Function constructor
- setAttribute/on* event handlers
- postMessage callbacks

### URL Location Management
- window.location, document.URL, document.documentURI
- location.hash, location.search, location.pathname
- URLSearchParams, new URL() parsing
- History API (pushState, replaceState)
- referrer, cookie values entering scripts

### Frontend Framework Security
- React: dangerouslySetInnerHTML, eval
- Vue: v-html, $refs access
- Angular: bypassSecurityTrustHtml/Url/Script
- jQuery: .html(), .append(), .after()
- Component libraries: rich text editors, Markdown renderers

### Data Flow Tracing
- Data transfer from C# server to client (JsonSerializer, WebAssembly serialization)
- Dynamic construction with Blazor's RenderTreeBuilder
- Data usage in PersistentComponentState and OnAfterRender
- Data backfill at JavaScript endpoints

## Enumeration Rules (Mandatory Refinement)

- Enumerate all C# files using IJSRuntime and IJSInProcessRuntime
- Search with priority: InvokeAsync, InvokeVoidAsync, InvokeMethodAsync, DotNet.invokeMethod, SetTonicInitialValueAsync, and other key calls
- Enumerate sink points in JavaScript files: eval, innerHTML, document.write, location, postMessage
- Enumerate where URL parameters, route parameters, cookies, localStorage, and sessionStorage enter scripts
- Enumerate data usage in the Blazor prerender phase, OnParametersSet, and OnAfterRender
- Enumerate dangerous API usage specific to frontend frameworks
- For each sink point record: data source, sink type, whether encoding is applied, and frontend framework re-rendering

## Barrier Verification Matrix (Mandatory)

This specialty must perform verification on the following barrier types, assessed against the fail-close standard in `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **DOM sink controllability** | Confirm whether data sources of sinks such as `innerHTML`/`document.write`/`eval`/`location` come from user-controllable input (URL/hash/postMessage/storage) | User-controllable data directly entering a sink → 🔴 High-risk; data source fixed and uncontrollable → ✅ Safe |
| **Blazor JSInterop boundary** | Confirm whether parameters of `IJSRuntime.InvokeAsync` come from user input, and whether the JS side validates parameters | User input passed directly to JS without validation → 🔴 High-risk; a validation layer exists and is fail-close → ✅ Safe |
| **URL parsing and navigation** | Confirm whether targets of `location.href`/`location.replace` come from user-controllable input, and whether protocols are restricted | `javascript:`/`data:` protocols allowed → 🔴 High-risk; restricted to http/https → ✅ Safe |
| **postMessage origin validation** | Confirm whether `window.addEventListener('message')` callbacks validate `event.origin` | No origin validation → 🔴 High-risk; strict origin whitelist → ✅ Safe |
| **Frontend framework security boundary** | Confirm whether React/Vue/Angular use dangerous APIs (`dangerouslySetInnerHTML`/`v-html`/`bypassSecurityTrustHtml`) | Dangerous API used with controllable content → 🔴 High-risk; safe APIs used → ✅ Safe |
| **CSP / Trusted Types** | Confirm whether CSP is configured, whether inline scripts are restricted, and whether Trusted Types is enabled | Strict CSP + Trusted Types → ✅ Safe; no CSP or permissive CSP → 🟠 Needs Confirmation |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion "Confirmed Safe" or "False Positive" is forbidden.**

## Two-Phase Determination (Mandatory)

Follow the two-phase determination flow in `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

1. **Phase 1 (Interim Conclusion)**: for each hit, first mark `Confirmed Vulnerability Candidate` / `Pending Confirmation` / `False Positive`
2. **Phase 2 (Mandatory Evidence Chasing)**:
   - If Phase 1 is `Confirmed Vulnerability Candidate` → all relevant items of the Barrier Verification Matrix must be completed and passed before marking `Confirmed`
   - If Phase 1 is `Pending Confirmation` → at least one more hop of the call chain or downstream parser must be traced until a determination is possible
   - If Phase 2 still cannot close the case → keep `Pending Confirmation`, and explicitly record which hop of evidence is missing

## Determination Rules (Mandatory Refinement)

### Confirmed Vulnerability

At least one of the following conditions holds:

1. User-controllable input (URL/hash/postMessage/storage) directly enters a DOM sink such as `innerHTML`/`document.write`/`eval`/`location`
2. Blazor JSInterop passes user-controllable input directly to the JS side, and the JS side has no validation
3. A `postMessage` callback does not validate `event.origin` and can receive messages from malicious origins
4. A frontend framework uses `dangerouslySetInnerHTML`/`v-html`/`bypassSecurityTrustHtml` with controllable content
5. In nested/recursive structures (e.g. multi-layer JSBridge encapsulation), the top layer has validation but sub-layers perform no equivalent validation

### Pending Confirmation

1. The context shows a suspicious pattern (e.g. an `eval` call), but the data source is unclear (a trace is needed)
2. A barrier function (e.g. origin validation) exists, but whether the current branch invokes it cannot be confirmed
3. Data transfer in asynchronous/event chains (e.g. WebSocket message handling) is not closed
4. Frontend framework re-rendering boundaries are invisible

### False Positive

1. The final data source is fixed (e.g. a hardcoded string) and user-controllable by no one
2. All recursion levels reuse the same fail-close origin whitelist/input validator
3. The DOM sink uses a safe API (`textContent`/`innerText`)
4. CSP is strictly configured + Trusted Types enabled, with no bypass path

## Testing Suggestions (Mandatory)

Follow the testing requirements in `DOTNET_AUDIT_EXECUTION_STANDARD.md`; for each confirmed vulnerability or pending-verification item provide:

- **Positive test**: construct a DOM-XSS payload (e.g. `#<img src=x onerror=alert(1)>`, `javascript:alert(1)`, malicious postMessage) to verify the vulnerability actually exists
- **Negative test**: construct input intercepted by a barrier (e.g. illegal origin rejected, dangerous protocol blocked) to verify the protection is effective
- **Regression test**: retest after remediation, confirming the barrier still works and no new bypass path is introduced

Test cases must be annotated with `test_id` and linked to the corresponding hit ID in the audit report.

### Mandatory Record Fields

| Field | Description |
|------|------|
| file_path | Source file path |
| line_number | Line number |
| sink_type | DOM sink type (eval/innerHTML/location, etc.) |
| data_source | Data source (URL/param/JS interop/database) |
| encoding_applied | Whether encoding is applied |
| framework | Frontend framework in use |
| risk_level | Risk level (P0-P4) |

## Evidence References

- EVID_DOM_XSS_SINK (new): DOM XSS sink point
- EVID_DOM_XSS_SOURCE (new): DOM XSS source (URL/user input)
- EVID_XSS_OUTPUT_POINT: reuse the output-point evidence of the XSS specialty
- EVID_XSS_USER_INPUT_INTO_OUTPUT: reuse the user-input-to-output evidence of the XSS specialty

## Failure and Degradation Branches (Mandatory)

| Trigger Condition | First-Line Handling | Fallback if Still Failing |
|---|---|---|
| DOM sink hit but source not traceable | Output sink and context evidence | Mark `⚠️Source Pending Verification`, degrade to PARTIAL |
| Source controllable but execution context (encoding/CSP) missing | Record encoding and CSP configuration evidence | Do not output confirmed exploitable; defer to Environment-Dependent |
| Only framework dangerous APIs found, lacking a business-reachable path | Output API hits and page entries | Classify as potential risk, pending route-tracer confirmation |
| Evidence boundary conflicts with server-side XSS | Keep conflicting evidence and archive in layers | Degrade and wait for xss/dom-xss cross-review |

🔴 **STOP: when the three-part evidence "source → sink → execution context" is incomplete, outputting a confirmed DOM-XSS is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Required shared index references: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber sources) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: on-disk paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from the directory structure are not allowed.
- Evidence consistency validation: if severity-graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: before submission, confirm at least once that key referenced files are accessible (e.g. `DOTNET_AUDIT_GRABBER_INDEX.md`, `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Execute at least 2 typical test cases before each output (happy path + 1 edge/ambiguity scenario), and record expected vs actual differences.
- `full_test >= 1` is required by default; if only `dry_run` is possible, `confidence=LOW` must be marked in the conclusion, with a make-up test plan and owner.
- Pass criteria: key fields complete, evidence chain traceable, conclusion level consistent with gate status; if any fails, marking "passed/deliverable" is forbidden.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `Input Constraints` → `Execution Steps` → `Output and Acceptance`; no layer may be missing or mixed across layers.
- A single paragraph should not exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into a single source-of-truth section.
- AI-isms and empty filler transitions are forbidden (e.g. "first/second/finally/in summary/put simply/in other words"); any found must be rewritten as executable statements.

## Quality Gate & Assessment Consistency (Mandatory)

- A minimal gate self-check must be executed before producing output: `input completeness`, `key evidence hit`, `output path valid` — all three must be PASS.
- If any of `key evidence missing`, `chain not closed`, `consistency_check_status=BLOCKED` holds, the conclusion must be degraded to `BLOCKED`; outputting "confirmed exploitable/deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with the `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

| # | Anti-Pattern | Why Not | Correct Approach |
|---|---|---|---|
| 1 | Counting server-side XSS directly as DOM-XSS | Different vulnerability surfaces | Clearly separate browser-side from server-side evidence |
| 2 | Only looking at sinks, not sources | Exploitability cannot be determined | Trace input sources simultaneously |
| 3 | Ignoring encoding and CSP | Conclusion strength is exaggerated | Record the protection context before grading |

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (e.g. `route_mapping` / `route_tracer` / `framework_audit`), confirm dependencies are available and timestamps are consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: write to the agreed path per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing-evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (DOM Sink Confirmation)**: sinks such as innerHTML/document.write/eval must be completely enumerated.
- 🔴 **CHECKPOINT B (Input Controllability Confirmation)**: controllability of input surfaces such as URL/hash/postMessage/storage must be confirmed.
- 🔴 **CHECKPOINT C (Protection Effectiveness Confirmation)**: whether sanitization, CSP, and Trusted Types are actually in effect must be confirmed.
- 🛑 **STOP**: if the sink and input chains are not closed, a "not exploitable" conclusion is not allowed.

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion level: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose exactly one; leaving blank is forbidden).
- Minimum evidence set: must include at least the five items `entry point`, `controllable parameters`, `key calls`, `security boundary`, `missing evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softening wording is forbidden: e.g. "possibly at risk / worth noting / depends on the situation / very likely"; when evidence is insufficient, must explicitly write `⚠️Pending Verification` and the next follow-up confirmation action.

Minimal output snippet (directly reusable):

```md
- Hit ID: M{hash} (file path fragment + line number + sequence number, for cross-phase tracking and regression alignment)
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameters=...; key calls=...; security boundary=...; missing evidence=none
- test_id: T{hash} (associated test case)
- Next action: if gaps exist, supplement parameter propagation evidence for trace_id=...
```
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameters=...; key calls=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement parameter propagation evidence for trace_id=...
```

## Output

- vuln_audit/dom_xss_{timestamp}.md
- Optional: vuln_poc/dom_xss_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC)

### vuln_audit/dom_xss_{timestamp}.md Structure

```markdown
# DOM-XSS Audit Report

## Overview
- Audit scope: `source_path`
- Audit time: {timestamp}
- Number of DOM-XSS risk points found: N

## High-Risk Findings (EVID_DOM_XSS_* evidence references)
...listed item by item, including file path, line number, vulnerability description, risk level...

## Medium-Risk Findings
...listed item by item...

## Low-Risk Findings
...listed item by item...

## Blazor JSInterop Risk Points
...dedicated listing of IJSRuntime-related findings...

## Frontend Framework Sink Points
...enumeration of dangerous API usage in React/Vue/Angular/jQuery frameworks...

## In-Project JS Interop Encapsulation
...project-specific secondary encapsulation...

## DOM-XSS Payload Reference
### URL-based
javascript:alert(1)
data:text/html,<script>alert(1)</script>

### location-based
<a href="javascript:...">...</a>
window.location = userInput

### postMessage-based
window.addEventListener('message', e => eval(e.data))

### eval-based
eval(window.name)
setTimeout(userInput, 100)

### innerHTML-based
element.innerHTML = userInput

## Remediation Suggestions
1. Use safe DOM manipulation APIs (textContent, innerText)
2. Avoid eval/Function/innerHTML for processing user input
3. Use URL encoding for URL-derived data
4. Configure CSP to restrict inline scripts
5. Blazor scenarios: use ElementReference instead of string backfill
```

## Boundary Division with the XSS Specialty

- **This Skill's responsibility**: client-side DOM operations, JavaScript execution contexts, Blazor JSInterop, URL parsing into scripts
- **dotnet-xss-audit responsibility**: server-side rendering, Razor output, ViewData/Model entering HTML, HTTP response injection
- **Core difference**: this Skill focuses on browser-side JavaScript execution; the XSS specialty focuses on server-side HTML/response generation
- **Crossover scenarios**: when the server passes data to the client via IJSRuntime, both specialties must collaborate to cover the complete data flow
