---
name: dotnet-ssti-audit
description: .NET Server-Side Template Injection (SSTI) audit tool. Identifies template engine misconfiguration, controllable template sources, user input injection, and sandbox escape risks; an independent specialty split from dotnet-tpl-audit.
---

# Server-Side Template Injection (SSTI) Audit

## Shared Grabber Index References

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as this Skill's base retrieval index
- By default, use shared/DOTNET_SINK_REFERENCE.md as this specialty's sink type definition and trace-gate validation baseline
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover shared grabbers related to template injection: user input handling, template rendering entries, and expression evaluation chains
- If the project has template engine secondary encapsulation, a view engine base, or a rendering pipeline wrapper layer, they must be added to the in-project grabbers section of the output
- When this Skill's specialty enumeration rules are more detailed than the shared index, this Skill prevails, but the shared index's base coverage must not be reduced
- This Skill is split from `dotnet-tpl-audit`, focusing on SSTI vulnerability detection and not covering other TPL check surfaces

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, authorization boundaries, or business preconditions)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement view engine configuration, template engine settings, or runtime boundaries)
- If this is a trace-gate specialty: prefer consuming `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it can serve as a summary index
- If this is a static-evidence-driven specialty: `route_tracer/*` serves only as cross evidence, not a hard prerequisite

## Key Checks

### Template Engine Identification

- **Scriban**: `Scriban.Scripting.ScriptRuntime` / `Template.Parse()` / `template.Render()`
- **Fluid**: `Fluid.FluidParser` / `Fluid.Template.Parse()` / `template.Render()`
- **Nunjucks.NET**: `Nunjucks.Precompile` / `Environment.RenderString()`
- **Razor**: interpolation inside `@* ... *@` comments, `Render Razor` / `IRazorEngine`
- Other templates: `DotLiquid.Template` / `Handlebars.NET` / `Mustache`

### Controllable Template Sources

- Template file paths: `Template.Parse(File.ReadAllText(userInput))`
- Template string sources: `Template.Parse(request.Form["template"])`
- Dynamically concatenated template names: `template.Parse(GetTemplateName(userInput))`
- Templates loaded from databases/caches then rendered
- Templates embedded in Proto definitions

### User Input to Template Injection

- Direct rendering of user input: `template.Render(userInput)`
- Parameter injection into template context: `template.Render(new { name = userInput })`
- Nested template inclusion: template A includes template B, with user input controlling B
- Injection after template precompilation: `CompiledTemplate.Create(userTemplate)`

### Sandbox Escape

- Scriban unsafe functions: `@"@{ System.Diagnostics.Process..." }`
- Fluid unrestricted object access: `model.GetType()` / `model.GetType().GetMethod()`
- Disabled-function bypass: `member access`, `function call` configuration
- Object construction: `new Object()` in templates
- Reflection call chains: `GetType().GetMethod().Invoke()`

### Template Engine Configuration

- Safe mode configuration: `FluidParserOptions` / `ScriptRuntime.Allow(memberAccess: false)`
- Default safety settings: whether dangerous operations are disabled by default
- Compilation cache: `Template.Compile()` caching strategy
- Template sandbox: `IHost` / `IMemberVisitor` configuration

## Enumeration Rules (Mandatory Refinement)

### Template Engine Detection

Search the following keywords and record the engine type:

```
// Scriban
Scriban.Template
Scriban.Scripting
Template.Parse
template.Render

// Fluid
Fluid.Template
Fluid.FluidParser
template.Render
FluidParserOptions

// Nunjucks
Nunjucks.Precompile
Environment.RenderString
NunjucksTemplateOptions

// Razor
@* *@
RazorLight
IRazorEngine
```

### Template Source Detection

Search the following patterns and record template sources:

```
File.ReadAllText(
File.ReadAllBytes(
request.Form[
request.QueryString[
request.Cookies[
route.Values[
HttpContext.Session
Cache.Get
Redis.Get
```

### User Input to Render Chain Detection

Search the following patterns:

```
template.Parse(userInput
template.Render(
Template.Parse(
ParseAsync(
RenderAsync(
new
```

### Sandbox Configuration Detection

Search the following patterns and record configurations:

```
AllowMemberAccess
AllowFunctionCall
AllowObjectConstruction
MemberAccess
FunctionInterceptor
SafeMemberAccess
```

### Dangerous Function Call Detection

Search the following patterns:

```
System.Diagnostics.Process
GetType()
GetMethod(
Invoke(
Runtime.GetType
typeof(
Activator.CreateInstance
Assembly.Load
```

## Barrier Verification Matrix (Mandatory)

Assess against the fail-close three-tier standard in `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Tier | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Tier 1 | Template engine exists and rendering entry is reachable | A template engine such as Scriban/Fluid/Razor exists and the user can trigger the rendering entry | BLOCKED → no template engine or rendering entry unreachable; the specialty ends |
| Tier 2 | Template source is controllable | Template string/file name/path sources include user input (request.Form/QueryString/Cookie/database) | BLOCKED → template source is hardcoded and uncontrollable; conclusion degraded |
| Tier 3 | Sandbox is escapable or dangerous functions executable | Sandbox configuration is permissive (AllowMemberAccess/AllowObjectConstruction), or dangerous functions such as System.Diagnostics.Process/GetType/Invoke are callable in templates | PARTIAL → only potential risks and verification steps are output |

## Two-Phase Determination Flow (Mandatory)

- **Phase 1 (Initial Screening Hit)**: template engine + template source + sandbox/dangerous function configuration hit; output `Hit ID: M{hash}`.
- **Phase 2 (Refined Confirmation)**:
  1. Trace in reverse: user input → template source (string/file/database) → rendering entry chain;
  2. Verify template engine sandbox configuration (AllowMemberAccess/AllowFunctionCall/AllowObjectConstruction);
  3. Assess whether dangerous functions (Process/GetType/Invoke/Activator.CreateInstance/Assembly.Load) are callable in templates;
  4. If all three barrier tiers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priority (Mandatory)

1. **Confirmed Vulnerability**: template engine reachable + template source controllable + sandbox escape/dangerous function executable. Output `Confirmed Vulnerability`.
2. **Pending Confirmation**: template engine and source evidence partially exists, but sandbox configuration or execution chain cannot be proven. Output `Pending Confirmation`.
3. **False Positive / No Risk**: template source hardcoded, sandbox strictly disables dangerous operations, no user input enters templates. Output `False Positive` with determination basis.

## Testing Suggestions and Minimum Trigger Conditions (Mandatory)

- **Minimum Trigger Conditions**:
  - A template engine exists (Scriban/Fluid/Nunjucks/Razor)
  - Template sources include user-controllable input
  - Or sandbox configuration is permissive, allowing dangerous operations
- **Test Case Suggestions**:
  - Happy Path: normal template rendering with hardcoded template sources and a strict sandbox
  - Edge/Ambiguity: template string injection `{{ 7*7 }}`, File.ReadAllText path traversal, AllowMemberAccess reflection calls, nested template inclusion injection
- Each hit output appends `Hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Evidence References
```

## Evidence References

- EVID_SSTI_TEMPLATE_SOURCE: controllability evidence of the template source
- EVID_SSTI_SANDBOX_ESCAPE: sandbox escape evidence
- EVID_SSTI_USER_INPUT_TO_TEMPLATE: evidence of user input to template injection point
- EVID_SSTI_RENDER_EXEC_CHAIN: template rendering execution chain evidence
- EVID_TPL_ENGINE_RENDER_OR_PARSE_ENTRY: template engine entry evidence (cross-specialty)
- EVID_TPL_TEMPLATE_OR_EXPR_CONTROL: template name or expression controllability evidence (cross-specialty)

## Failure and Degradation Branches (Mandatory)

| Trigger Condition | First-Line Handling | Fallback if Still Failing |
|---|---|---|
| Template engine identified but template source unconfirmable | First output the rendering entry and context parameters | Mark `⚠️Template Source Pending Verification`, degrade to PARTIAL |
| Template source controllable but sandbox configuration invisible | Record visible configuration and default behavior assumptions | Classify as Environment-Dependent; no confirmed RCE conclusion |
| Only dangerous function hits without a closed execution chain | Supplement the "input → template → execution" chain trace | List as potential risk only when unclosed |
| Evidence conflicts with TPL/EXPR specialties | Keep conflicting evidence with sources annotated | Final severity after cross-review |

🔴 **STOP: when evidence of template source controllability or execution chain closure is missing, outputting "confirmed SSTI exploitable" is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Required shared index references: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber sources) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: on-disk paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from the directory structure are not allowed.
- Evidence consistency validation: if severity-graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: before submission, confirm at least once that key referenced files are accessible (e.g. `DOTNET_AUDIT_GRABBER_INDEX.md`, `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Each skill must maintain at least 2 typical test cases (happy path + one complex scenario), and annotate the case ID in the results.
- Each evaluation round must execute `full_test` for at least 1 case; if only `dry_run` is possible, `dry_run_reason` and a make-up test plan must be recorded.
- Pass criteria must simultaneously satisfy: `intent achieved`, `key evidence hit`, `output format compliant`; if any one is not met, "pass" must not be given.

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
| 1 | Judging SSTI upon seeing a template engine | Engine existence ≠ controllable input | Must prove source controllability and injection path |
| 2 | Treating XSS output points as SSTI execution points | Different risk types | Distinguish template execution from frontend rendering |
| 3 | Giving an RCE conclusion without verifying sandbox configuration | Conclusion strength is distorted | Grade as Pending Confirmation / Environment-Dependent first |

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (e.g. `route_mapping` / `route_tracer` / `framework_audit`), confirm dependencies are available and timestamps are consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: write to the agreed path per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing-evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (Template Entry Confirmation)**: template rendering entries and engine types must be confirmed.
- 🔴 **CHECKPOINT B (Expression Controllability Confirmation)**: whether user input can enter expression evaluation must be confirmed.
- 🔴 **CHECKPOINT C (Sandbox Isolation Confirmation)**: function whitelists and execution isolation boundaries must be confirmed.
- 🛑 **STOP**: if template execution capability and input controllability are not both established, a "not exploitable" conclusion is not allowed.

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion level: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose exactly one; leaving blank is forbidden).
- Minimum evidence set: must include at least the five items `entry point`, `controllable parameters`, `key calls`, `security boundary`, `missing evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softening wording is forbidden: e.g. "possibly at risk / worth noting / depends on the situation / very likely"; when evidence is insufficient, must explicitly write `⚠️Pending Verification` and the next follow-up confirmation action.

Minimal output snippet (directly reusable):

```md
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameters=...; key calls=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement parameter propagation evidence for trace_id=...
```

## Output

- vuln_audit/ssti_{timestamp}.md
- Must state the vulnerability type (Scriban/Fluid/Nunjucks/Razor), injection point, controllability level, and exploit chain complexity
- If a template source is found fully controllable with a sandbox escape, additionally output `vuln_poc/ssti_{timestamp}.md` (including PoC template fragments)
- If only potential risks are found without a complete data flow trace, output to the `Pending Evidence Risk Pool` and mark `⚠️Pending Verification`

## Linkage with Other Specialties

- `dotnet-tpl-audit` covers other TPL check surfaces (template filename injection, expression injection); this Skill does not duplicate them
- Render chains found by this Skill can be passed to `dotnet-route-tracer` for a complete trace
- When reflection or dynamic code generation is involved, `dotnet-deser-audit` can be linked
- When expression evaluation is involved, `dotnet-expr-audit` can be linked
