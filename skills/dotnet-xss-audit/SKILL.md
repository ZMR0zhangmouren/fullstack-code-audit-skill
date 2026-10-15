---
name: dotnet-xss-audit
description: .NET XSS audit tool. Identifies unencoded output, raw output, and DOM injection risks in Razor, Blazor, and MVC / View output contexts.
---

# .NET XSS Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to output contexts, encoding boundaries, template rendering, frontend component echoes, and JSON / HTML / JS returns
- If the project has secondary encapsulations such as HtmlHelper, TemplateRenderer, EmailRenderer, or PreviewService, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align output entries, parameter sources, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement output context control planes such as Razor / Blazor / GraphQL / SignalR)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- output boundaries of Razor's Html.Raw, IHtmlContent, TagHelpers, Partial, ViewComponent, DisplayTemplate, and EditorTemplate
- Blazor's MarkupString, RenderFragment, dynamic component parameters, JSInterop backfill, and prerender hybrid rendering scenarios
- mappings of ViewData, ViewBag, Model, TempData, query parameters, API-returned JSON, and database content into HTML, attribute, JS, CSS, and URL contexts
- patterns of hand-concatenated script, onclick, href, style, data-* attributes, and JSON serialized then embedded into pages
- code paths with custom HtmlEncoder, JavaScriptEncoder, UrlEncoder, disabled encoding, or UnsafeRelaxedJsonEscaping
- rich text, Markdown, template content, WYSIWYG editor output, and server-side sanitizer allowlist / denylist rules
- whether CSP, Trusted Types, Razor default encoding, Blazor component isolation, and frontend framework re-rendering truly reduce the impact

## Enumeration Rules (Mandatory Refinement)

- Enumerate all Razor Views, Partials, Layouts, ViewComponents, TagHelpers, Blazor Components, email templates, and export HTML templates
- Search Html.Raw, MarkupString, IHtmlContent, RenderFragment, UnsafeRelaxedJsonEscaping, and custom encoder configurations first
- Enumerate positions where user input, database fields, rich text content, CMS templates, GraphQL data, and Hub messages echo into HTML / attributes / JS / URL / CSS
- For each output point record: context type, encoding method, whether sanitization was applied, and whether downstream frontend frameworks interpret it again

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **HTML context encoding** | Confirm whether Razor / Blazor default encoders take effect and whether user input entering HTML bodies passes through `HtmlEncoder` | default encoding effective and non-bypassable → ✅ safe; custom encoders fail-open → ⚠️ bypassable; using `Html.Raw` / `MarkupString` without sanitization → 🔴 high risk |
| **Attribute context encoding** | Confirm whether user input in HTML attribute values (such as `href`, `src`, `alt`) undergoes attribute encoding | attribute encoding effective → ✅ safe; unencoded input entering attribute values directly → 🔴 high risk; HTML encoding only without attribute encoding → ⚠️ to be confirmed |
| **JS context encoding** | Confirm whether user input entering `<script>` tags or event handlers (`onclick`, etc.) undergoes `JavaScriptEncoder` | JS encoding effective → ✅ safe; unencoded input entering JS contexts directly → 🔴 high risk |
| **URL context encoding** | Confirm whether user input entering `href`, `src`, and `url()` undergoes `UrlEncoder`, and whether the `javascript:` / `data:` protocols are allowed | URL encoding effective with dangerous protocols forbidden → ✅ safe; `javascript:` protocol allowed → 🔴 high risk |
| **CSS context encoding** | Confirm whether user input entering `style` attributes or `<style>` tags undergoes CSS encoding | CSS encoding effective → ✅ safe; unencoded input entering CSS directly → 🔴 high risk |
| **Rich text sanitization** | Read the rich text sanitizer (such as HtmlSanitizer) implementation source, confirming whether it is fail-close (only whitelisted tags / attributes allowed) | fail-close whitelist → ✅ safe; blacklist mode → ⚠️ bypassable; no sanitization → 🔴 high risk |
| **CSP / Trusted Types** | Confirm whether CSP headers are configured, whether `unsafe-inline` is forbidden, and whether Trusted Types is enabled | strict CSP + Trusted Types → ✅ safe; loose or missing CSP → 🟠 to be confirmed; no CSP → 🔴 high-risk amplification |

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

1. user-controllable input enters HTML / attribute / JS / URL / CSS contexts directly via `Html.Raw`, `MarkupString`, or unencoded output
2. custom encoders are fail-open, with unknown input allowed to pass through by default
3. rich text sanitization is in blacklist mode, bypassable via unknown tags / attributes
4. frontend frameworks (React / Vue / Angular) do not encode server-provided data during secondary rendering
5. in nested / recursive structures (such as multi-layer HtmlHelper wrappers), the top level encodes but sub-levels do not perform equivalent encoding

### Pending

1. the context shows a suspicious pattern (such as an `Html.Raw` call), but the external input source is unclear (trace or call chain needs to be supplemented)
2. a barrier function (such as an encoder) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
3. data passing in asynchronous / queue / event chains (such as SignalR message pushes) is not closed
4. frontend framework secondary rendering boundaries are not visible

### False Positive

1. the final output comes from fixed constants / enum mappings, and unknown input is refused execution (fail-close)
2. all recursive levels reuse the same fail-close encoder / sanitizer
3. user input enters only strictly encoded value slots, and the encoder is fail-close
4. strict CSP configuration + Trusted Types enabled, with no bypassable paths

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct XSS payloads (such as `<script>alert(1)</script>`, `javascript:alert(1)`, `onerror=alert(1)`, and CSS expressions) and verify the vulnerability really exists
- **Negative testing**: construct inputs intercepted by barriers (such as unknown HTML tags sanitized, dangerous protocols blocked, and unencoded input automatically encoded) and verify the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Evidence References

- EVID_XSS_OUTPUT_POINT
- EVID_XSS_USER_INPUT_INTO_OUTPUT
- EVID_XSS_ESCAPE_OR_RAW_CONTROL

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (output context confirmation)**: the encoding strategy of each context (HTML / attribute / JS / URL / CSS) must be confirmed.
- 🔴 **CHECKPOINT B (dangerous output confirmation)**: dangerous points such as Html.Raw / MarkupString / custom encoders must be confirmed.
- 🔴 **CHECKPOINT C (sanitization and isolation confirmation)**: rich text sanitization rules and frontend secondary rendering boundaries must be confirmed.
- 🛑 **STOP**: if contexts and encoding chains are not closed, no "safe" conclusion may be drawn.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| output context cannot be precisely classified | complete evidence per HTML / attribute / JS / URL / CSS separately | downgrade to `⚠️Pending Verification` |
| dangerous output point source unclear (Raw / MarkupString) | back-trace to input sources and sanitization chains | no "safe" conclusion |
| frontend secondary rendering boundary unclear | complete DOM injection and framework interpretation paths | assess conservatively and list pending evidence |

🔴 **STOP: when any fallback triggers, outputting "safe" is forbidden.**

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

- Anti-pattern: treating "encoded" as a uniform conclusion. Correct practice: verify per HTML / attribute / JS / URL / CSS context.
- Anti-pattern: ignoring Html.Raw / MarkupString risk points. Correct practice: verify sources and sanitization strategies point by point.
- Anti-pattern: looking only at the backend without frontend secondary interpretation. Correct practice: evaluate DOM injection and framework re-rendering.
- Anti-pattern: declaring safety with an unclosed evidence chain. Correct practice: downgrade and supplement verification items.

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

- vuln_audit/xss_{timestamp}.md
- Optional: vuln_poc/xss_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
