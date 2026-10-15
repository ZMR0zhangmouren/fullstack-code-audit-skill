---
name: node-ssti-audit
description: Node.js server-side template injection audit tool. Identifies risks such as user input concatenated into ejs/pug/nunjucks/handlebars template strings, controllable template names, and controllable engine options; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js SSTI Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to template engine entries, template string construction, template name resolution, and engine options
- If the project has secondary encapsulations such as TemplateService, ViewRenderer, or MailTemplate, they must be added to the project-internal grabbers section of the output
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

- Template strings of ejs / pug / nunjucks / handlebars / mustache directly concatenating user input (non-expression parameterization)
- `res.render` template names from user-controllable input
- Template engine `.compile(` directly consuming user input strings
- Controllable template engine options (such as ejs `delimiter`, `context`)
- Templates and data not separated, with user input interpreted as template expressions

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites of `ejs`, `pug`, `nunjucks`, `handlebars`, `mustache`, `.compile(`, `.render(`, `res.render(`
- For each template call site record: template source (file / string), template name source, data object source, engine options, and whether a sandbox is enabled
- Distinguish template file rendering (`res.render(view, data)`) from template string rendering (`ejs.render(str, data)` / `nunjucks.renderString(str, context)` / `handlebars.compile(str)(data)`)
- Check whether template strings are concatenated from user input or come entirely from user input
- Check whether the first argument of `res.render` (template name) comes from `req.query` / `req.params` / `req.body`
- Check whether template engine options come from external input (e.g., ejs `delimiter`, `compileDebug`, handlebars `strict`)
- Check whether sandbox / strict mode is disabled, exposing global objects such as `require`, `process`, `child_process`
- Identify the same class of risks in other template engines such as lodash.template, doT, and eta
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real template engine call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Template / data separation | `render(name, data)` parameterized; template name a literal or from a controlled mapping | Check whether the template name / template string is fixed and user input enters only data | template name fixed / whitelisted and data parameterized → ✅ safe; template string from user input → 🔴 high risk |
| Template name allowlist | Template name dictionary mapping / path prefix whitelist | Read the template selection logic, confirming unknown template names are refused execution | fail-close (enumeration-outside refusal / exception) → ✅ safe; fail-open (default path concatenation) → ⚠️ bypassable; no validation → 🔴 high risk |
| User-controllable engine options disabled | ejs `delimiter` fixed; handlebars helpers registered under control; options such as `compileDebug` not exposed | Check whether the engine options object comes from external input | options from fixed constants → ✅ safe; options from `req.query` / `req.body` → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter template strings, template names, or engine options
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

- `EVID_NODE_SSTI_RENDER_POINT` + `EVID_NODE_SSTI_TEMPLATE_CONCAT` + no effective Barrier
- User input is concatenated directly into template strings and compiled / rendered by the template engine
- `res.render` template names come from user-controllable input without an allowlist
- Template engine options (such as ejs `delimiter`) come from user input and can alter template parsing semantics

### ⚠️Pending Verification

- The context shows a suspicious pattern (e.g., an `ejs.render` call), but the external input source is unclear (trace or call chain needs to be supplemented)
- A barrier function (e.g., template name whitelist) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
- Template strings partially come from external input, but whether they enter a template expression context at the current call site cannot be confirmed

### False Positive

- Template names are fixed literals, user input enters only the `data` object, and template auto-escaping is not bypassed
- Template strings are fully static with no user-controllable concatenation
- The template name allowlist is fail-close, rejecting unknown template names
- Template engine options come from fixed constants and are unreachable by user input

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct SSTI payloads: `<%= process.mainModule.require('child_process').execSync('id').toString() %>` (ejs), `#{process.mainModule.require('child_process').execSync('id')}` (pug), `{{ process.mainModule.require('child_process').execSync('id') }}` (nunjucks), etc.; note engine differences: Handlebars / Mustache do not execute arbitrary JS by default and usually require custom helpers or sandbox bypasses to trigger SSTI
- Verify user parameters entering template strings are executed as expressions
- Verify controllable template names leading to reading arbitrary template files or path traversal execution
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct parameterized template string inputs: user data is output only as ordinary variables
- Verify the template name whitelist explicitly rejects unknown template names
- Verify engine options are fixed constants and external input cannot change parsing behavior

### Regression Testing

- Retest after remediation, confirming template strings no longer concatenate user input
- Retest the template name allowlist and fixed engine option strategy
- Verify newly added templates or options remain fail-close

## Evidence References

- `EVID_NODE_SSTI_RENDER_POINT`
- `EVID_NODE_SSTI_TEMPLATE_CONCAT`
- `EVID_NODE_SSTI_TEMPLATE_NAME_CONTROL`

## Output

- `node/vuln_audit/ssti_{timestamp}.md`
- `node/vuln_poc/ssti_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
