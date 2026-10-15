---
name: node-xss-audit
description: Node.js XSS audit tool. Identifies cross-site scripting output risks such as res.send/res.write concatenating HTML, dangerouslySetInnerHTML, v-html, and SSR hydration; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js XSS Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to HTML output, template rendering, SSR hydration, and DOM rendering surfaces
- If the project has secondary encapsulations such as RenderHelper, HtmlBuilder, or TemplateEngine, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, serialization configuration, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate (server-side output chain)**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- DOM rendering surfaces (`dangerouslySetInnerHTML` / `v-html` / `innerHTML`) are allowed to be static-evidence-driven and must be explicitly annotated as such
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- `res.send` / `res.write` directly concatenating HTML without encoding
- Unescaped output in `res.render` templates (EJS `<%-`, Pug `!=`, Handlebars `{{{ }}}`, Nunjucks with `autoescape` disabled)
- React `dangerouslySetInnerHTML` using external input directly
- Vue `v-html` using external input directly
- Native `innerHTML` directly assigned external input
- SSR hydration contexts (`__NEXT_DATA__` / `__NUXT__`) injecting user-controllable JSON without escaping characters such as `>` / `<` / `&` / `"`
- Missing output encoding or encoding effective only in some branches

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites and configurations of `res.send(`, `res.render(`, `dangerouslySetInnerHTML`, `v-html`, `innerHTML`, `__NEXT_DATA__`, `__NUXT__`, `escape-html`, `DOMPurify`
- For each output point record: output API, Content-Type, whether user input is concatenated, whether encoding / sanitization is applied, and template engine auto-escaping configuration
- Distinguish the server-side output chain (`res.send` / `res.render`) from client-side / isomorphic rendering surfaces (`dangerouslySetInnerHTML` / `v-html` / `innerHTML`)
- Check whether the template engine has auto-escaping disabled (e.g., `nunjucks.configure({ autoescape: false })`)
- Check templates for explicit raw-output syntax (`<%- %>`, `!=`, `{{{ }}}`, `tripleMustache`)
- Check whether the `__html` / expressions of `dangerouslySetInnerHTML` / `v-html` / `innerHTML` come from external input without prior sanitization
- Check whether JSON serialization in SSR hydration scripts misuses escape-disabling options such as `serialize-javascript`'s `unsafe: true`; if `isJSON` is used, confirm the input source is trusted
- Check whether `escape-html` / `DOMPurify` cover all output branches with strict configuration
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real HTML output or template rendering points

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Template auto-escaping | React / Vue default escaping; EJS `<%= %>`; Nunjucks default `autoescape`; Handlebars default encoding | Check whether template engine default escaping is explicitly bypassed | default escaping not bypassed → ✅ safe; `<%-` / `!=` / `{{{ }}}` outputting user data → 🔴 high risk |
| Output sanitization | `DOMPurify.sanitize(dirty)` / `escape-html` / `he.encode` | Check whether sanitization functions cover all output branches with strict configuration | full branch coverage with `on*` / `style` forbidden → ✅ safe; some branches unsanitized → ⚠️ to be confirmed; no sanitization → 🔴 high risk |
| CSP header | `helmet.contentSecurityPolicy` configuration | Check whether the response issues CSP and restricts `script-src` / `unsafe-inline` | CSP restricting script sources without `unsafe-inline` → ✅ defense in depth; no CSP or `unsafe-inline` allowed → ⚠️ defense-in-depth missing |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter HTML output or SSR hydration contexts
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

- `EVID_NODE_XSS_OUTPUT_POINT` + `EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT` + no effective Barrier
- `res.send` / `res.write` directly concatenating user input and returning `text/html`
- Template engines explicitly bypass auto-escaping to output user input
- `dangerouslySetInnerHTML` / `v-html` / `innerHTML` placing unsanitized external input directly
- SSR hydration (`__NEXT_DATA__` / `__NUXT__`) with user-controllable JSON lacking safe escaping

### ⚠️Pending Verification

- The context shows a suspicious pattern (e.g., `res.send(template)`), but the external input source is unclear (trace or call chain needs to be supplemented)
- Barrier functions (e.g., `escape-html`, `DOMPurify`) exist, but whether the current branch invokes them and whether they cover all output paths cannot be confirmed
- DOM rendering surfaces depend on isomorphic data flows, and the server-to-client propagation path cannot be confirmed statically

### False Positive

- Output content is fully static with no user-controllable input
- User input enters output points after fail-close encoding / sanitization, covering all branches
- Template engine default auto-escaping is not bypassed, and user data does not enter raw-output syntax
- SSR hydration uses a safe JSON serialization library with dangerous options disabled

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct payloads such as `<script>alert(1)</script>`, `<img src=x onerror=alert(1)>`, `javascript:alert(1)`
- Verify script execution when user parameters enter `res.send` concatenation, `res.render` template raw output, or `dangerouslySetInnerHTML` / `v-html`
- Verify JSON closing-tag bypass in SSR hydration scenarios (`</script><script>alert(1)</script>`)
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct inputs processed by `escape-html` / `DOMPurify`, verifying dangerous tags are escaped or stripped
- Verify template default-escaping syntax (`<%= %>`, `{{ }}`) correctly encodes HTML metacharacters
- Verify inline scripts are blocked by the browser under the CSP policy

### Regression Testing

- Retest after remediation, confirming encoding / sanitization covers all output branches
- Retest template engine configuration, confirming dangerous escaping bypasses are not re-enabled
- Verify SSR hydration serialization library upgrades keep dangerous options disabled

## Evidence References

- `EVID_NODE_XSS_OUTPUT_POINT`
- `EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT`
- `EVID_NODE_XSS_ENCODE_OR_SANITIZE`
- `EVID_NODE_XSS_SSR_HYDRATION`

## Output

- `node/vuln_audit/xss_{timestamp}.md`
- `node/vuln_poc/xss_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
