---
name: node-dom-xss-audit
description: Node.js DOM-XSS audit tool. Identifies client-side code source pollution flows such as innerHTML/document.write/eval with location.hash/search and postMessage, and dangerouslySetInnerHTML/v-html risks; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js DOM-XSS Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to client-side DOM sinks, browser sources, framework dangerous APIs, sanitizers, and CSP security headers
- If the project has secondary encapsulations such as DomRenderer, HtmlBridge, MarkdownRenderer, or RichTextEditor, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path` (must cover client-side code directories: `*.js`/`*.jsx`/`*.ts`/`*.tsx`/`*.vue`)
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align page entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the SSR mode, hydration data, security headers, and other framework control planes)
- Optional: `node/vuln_audit/xss_{timestamp}.md` (server-side XSS and DOM-XSS overlap; some findings may be reused)
- This specialty is **static-evidence-driven** (primarily static analysis of client-side code): `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), discovered client-side entries should be linked back to `route_id`s in `node/cross_analysis/high_risk_routes_{timestamp}.md` where possible

## Key Checks

- DOM sinks in client-side code (`*.js`/`*.jsx`/`*.ts`/`*.tsx`/`*.vue`): `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write`/`eval`/`new Function`/`location.href` assignment/`setAttribute`
- Browser sources: `location.hash`/`location.search`/`document.referrer`/`window.name`/`postMessage` (`event.data`)/`localStorage`/`sessionStorage`
- Protocol control at `location.href`/`location.replace` assignments (`javascript:`/`data:`)
- Whether `window.addEventListener('message')` callbacks validate `event.origin`
- Next.js `dangerouslySetInnerHTML` (including props/URL-derived values) and Vue `v-html`, `__html` direct passing
- Framework safe APIs: `textContent`/`createElement` + `appendChild`/`DOMPurify.sanitize`
- Chains from SSR hydration data (`__NEXT_DATA__`/`__NUXT__`) into DOM sinks
- Boundary with server-side XSS: server-side rendering output injection belongs to node-xss-audit; this specialty covers only browser-side execution paths

## Enumeration Rules (Mandatory Refinement)

- Enumerate sinks in `*.js`/`*.jsx`/`*.ts`/`*.tsx`/`*.vue`: `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval(`, `new Function(`, `location.href =`, `location.replace(`, `setAttribute(`, `setTimeout('`
- Enumerate sources: `location.hash`, `location.search`, `URLSearchParams`, `document.referrer`, `window.name`, `addEventListener('message'`, `localStorage`, `sessionStorage`
- Search framework dangerous APIs first: `dangerouslySetInnerHTML`, `v-html`, `__html`
- Enumerate sanitizers and safe APIs: `DOMPurify.sanitize`, `sanitize-html`, `textContent`, `innerText`
- For each sink record: source type, whether source→sink is a direct same-chain connection (URL parameter entering the sink directly), sanitizer and its configuration, framework, and postMessage origin validation

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Framework safe API | `textContent`/`createElement`, React/Vue default escaping | Confirm whether the sink position can be replaced with a safe API and is actually used | `textContent`/default escaping → ✅ safe; `dangerouslySetInnerHTML`/`v-html` with source-derived content → 🔴 high risk |
| Sanitizer | `DOMPurify.sanitize`/`sanitize-html` | Check whether the configuration allows event attributes, `javascript:` URIs, and custom tags | strict default configuration → ✅ safe; loosened `ADD_TAGS`/`ALLOW_UNKNOWN_PROTOCOLS` → ⚠️ to be confirmed; no sanitization → 🔴 high risk |
| postMessage origin validation | `event.origin === 'https://trusted.com'` whitelist | Check whether `addEventListener('message')` strictly compares `event.origin` | strict whitelist → ✅ safe; missing or `'*'` → 🔴 high risk |
| URL protocol restriction | Protocol validation before `location.href` assignment | Check whether `javascript:`/`data:` is explicitly rejected | explicitly rejected → ✅ safe; unrestricted → 🔴 high risk |
| CSP / Trusted Types | CSP `script-src`, `require-trusted-types-for`, helmet configuration | Check response headers / meta and framework security header configuration | strict CSP + Trusted Types → ✅ mitigated; no CSP or loose → 🟠 to be confirmed |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: a browser-controllable source appears to enter a DOM sink or a dangerous framework API
- `Pending`: the context shows a suspicious pattern, but the source origin, sanitization behavior, or propagation chain is unclear
- `False Positive`: the input comes from fixed constants / compile-time-determined values, or the sanitizer / safe API has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found that a controllable source enters the sink position → `Confirmed Vulnerability`
- Fixed constant mapping / fail-close sanitization evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_DOM_SINK_POINT` + `EVID_NODE_DOM_SOURCE_TRACE`: sources such as `location.hash`/`location.search` reach the sink on the same chain (e.g., `elem.innerHTML = location.hash.slice(1)`)
- `EVID_NODE_DOM_URL_PARAM_SINK`: URL parameters enter the sink directly without sanitization, or a `postMessage` callback has no `event.origin` validation
- `dangerouslySetInnerHTML`/`v-html` content comes from URL/props-controllable data without a sanitizer (`EVID_NODE_DOM_FRAMEWORK_SAFE_API` evidence shows safe APIs are not used)

### ⚠️Pending Verification

- The sink is hit but the source passes through multiple layers of props/context, and whether intermediate sanitization occurs is not visible
- `DOMPurify.sanitize` exists but its configuration items (`ADD_TAGS`/`ALLOW_UNKNOWN_PROTOCOLS`) cannot be confirmed
- The chain from SSR hydration data (`__NEXT_DATA__`/`__NUXT__`) to a DOM sink is not closed

### False Positive

- The sink input is a hardcoded constant or compile-time-determined value
- The whole chain uses `textContent`/`DOMPurify` default configuration (`EVID_NODE_DOM_FRAMEWORK_SAFE_API` + `EVID_NODE_DOM_SOURCE_TRACE` dual evidence closed)
- postMessage uses a strict origin whitelist and the data does not enter a DOM sink

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct `#<img src=x onerror=alert(1)>` entering hash-type sinks, `javascript:alert(1)` entering location assignment points
- Construct cross-origin `postMessage` payloads to verify callback execution without origin validation
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- postMessages from illegal origins are rejected, and the `javascript:` protocol is blocked
- `DOMPurify.sanitize` default configuration removes `<script>` and event attributes
- Verify `textContent` assignment does not parse HTML

### Regression Testing

- Retest after remediation, confirming the sanitizer and origin validation remain effective
- Retest that framework upgrades do not add new unsanitized usages of `v-html`/`dangerouslySetInnerHTML` to the inventory
- Verify inline scripts remain blocked after CSP/Trusted Types configuration changes

## Evidence References

- `EVID_NODE_DOM_SINK_POINT`
- `EVID_NODE_DOM_SOURCE_TRACE`
- `EVID_NODE_DOM_FRAMEWORK_SAFE_API`
- `EVID_NODE_DOM_URL_PARAM_SINK`
- Optional overlay: `EVID_NODE_CFG_SECURITY_SWITCH` (CSP/helmet security header configuration)

## Output

- `node/vuln_audit/dom_xss_{timestamp}.md`
- `node/vuln_poc/dom_xss_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
