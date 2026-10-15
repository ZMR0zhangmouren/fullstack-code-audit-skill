---
name: node-spreadsheet-export-audit
description: Node.js spreadsheet export (CSV / Excel) formula injection audit tool. Identifies formula / DDE / hyperlink injection risks caused by user-controllable fields without formula neutralization in export chains such as exceljs, csv-stringify, fast-csv, json2csv, and handwritten CSV concatenation; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js Spreadsheet Export (CSV / Excel) Formula Injection Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use the "EXPORT" chapter of `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline (EXPORT type code)
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the exporter definitions in the EXPORT chapter: `exceljs` (`worksheet.addRow` / `addRows`), `csv-stringify` (`stringify` / `stringifier.write`), `fast-csv`, `json2csv` (`new Parser().parse`), handwritten `` `${v1},${v2}` `` CSV concatenation, and formula injection patterns (values starting with `=` `+` `-` `@`, DDE payloads such as `=cmd|' /C calc'!A1`, and HYPERLINK phishing chains)
- If the project has unified secondary encapsulations such as exportService, report generators, or csv / excel helpers, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- **This specialty is of the trace-gate type**: source parameters of exported fields (req.body / req.query / database user-writable columns / downstream stored values) require evidence closure from `node/route_tracer/{route_id}/trace_{timestamp}.md`; `node/route_tracer/{route_id}/trace_{timestamp}.md` is a hard precondition; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align export endpoint entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and export endpoint short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to confirm anonymous reachability of export endpoints, P0/P1 bucketing, and the sensitivity of exported data)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement Content-Type / Content-Disposition response header conventions, static file middleware, and runtime control plane)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`
- When traces are missing or `trace_status=PARTIAL/UNRESOLVED`, all conclusions must be downgraded to `⚠️Pending Verification` (see "Two-Phase Determination")

## Key Checks

- CSV / Excel export endpoints: Express / Koa / Fastify route handlers returning file downloads, report exports, and bulk data download entries
- Mapping of exported fields to request parameters / database user data: which columns in exported rows come from user-controllable input (req.body fields, req.query parameters, database columns writable by users)
- Formula prefix neutralization: whether values starting with `=` `+` `-` `@` are prefixed with `'` or rejected before being written into cells / CSV fields
- Cell format forced to text: whether the `exceljs` generation path explicitly sets user data columns to text format (`cell.numFmt = '@'`), blocking formula interpretation
- CSV delimiter and quote escaping: configurations of `csv-stringify` / `fast-csv` versus handwritten `v1 + ',' + v2` direct output (the latter often lacks both quote escaping and formula neutralization)
- Response presentation consistency: whether `Content-Type` (`text/csv`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) and `Content-Disposition` (`attachment; filename=...`) are consistent with the actual file extension and content format, avoiding browsers / spreadsheets opening the file with the wrong interpreter
- Paths where export content is pure constants / enum dictionaries (no user data involved) are marked as irrelevant rather than vulnerabilities

## Enumeration Rules (Mandatory Refinement)

- Enumeration is limited to business source code; `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`, and coverage directories are not part of the audit surface; lockfiles (`package-lock.json` / `yarn.lock` / `pnpm-lock.yaml`) are dependency manifests rather than export chains and are used only to confirm exporter package versions; they are not audited separately, but business source code checks must not be skipped just because the lockfile hits
- Enumerate all export route handlers returning file downloads, and report generation / file landing paths triggered in Services / scheduled tasks / queue consumers
- Search first: `exceljs` (`new ExcelJS.Workbook()`, `worksheet.addRow(`, `worksheet.addRows(`, `ws.addRow(`), `csv-stringify` (`stringify(`, `new Stringifier`, `stringifier.write(`), `fast-csv` (`csv.write(`, `format({`), `json2csv` (`new Parser(`, `.parse(`), handwritten CSV concatenation (template strings or `+` concatenated fields followed by `res.send(csv)` / `res.end(csv)`), `Content-Disposition` (`attachment;filename=` response headers), `res.download(` / `res.attachment(` combined with CSV / Excel content
- Enumerate formula neutralization helper functions (such as `sanitizeFormula`, `escapeCell`, `prefixApostrophe`): their definitions and all call sites, confirming whether each export chain actually invokes them
- Separately enumerate exported field sources: whether each column field comes from req.body / req.query, database user-writable columns, downstream stored values, or fixed constants, annotating controllability one by one
- Enumerate Excel cell format settings: whether user data columns are explicitly set to `cell.numFmt = '@'`; the default General format in most spreadsheets interprets formulas
- For each hit record: **file, line number, package name (exceljs / csv-stringify / fast-csv / json2csv / handwritten concatenation), field source (req.body / req.query / database user data / constant), and whether formula neutralization exists (yes / no / not visible)**
- Enumerate the encapsulation chains of unified exportService, report generators, and csv / excel helpers, tracing to the final cell / field write points

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| **Formula prefix neutralization** | Detecting before write whether the value starts with `=` `+` `-` `@` (and Tab / CR prefix variants), and prefixing with `'` or rejecting the write (e.g., `value.replace(/^[=+\-@]/, "'$&")`) | Read the neutralization function implementation, confirming whether it is fail-close (all unknown prefixes handled) and whether each export chain actually invokes it | all user-controllable fields uniformly neutralized before write and fail-close → ✅ safe; only some columns neutralized, the neutralization function bypassable, or implementation not visible → ⚠️ to be confirmed; no neutralization with controllable fields → 🔴 high risk |
| **Cell format forced to text** | User data columns in the `exceljs` path explicitly set to `cell.numFmt = '@'` or text format specified in column definitions | Check whether controllable columns in the Excel generation path are explicitly set to text format rather than the default General | all controllable columns forced to text format → ✅ safe; only some columns set or format setting not visible → ⚠️ to be confirmed; not set → 🔴 high risk |
| **Exported field allowlist** | The exported column set comes from a fixed column list (constant array / enum mapping) rather than arbitrary writable columns dynamically selected via req.query | Read the column selection logic, confirming whether column names / column sets can be changed by request parameters | fail-close column list → ✅ safe; column names / column sets from request parameters without validation → 🔴 high risk |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion as "Confirmed Safe" or "False Positive" is forbidden.**

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter export generation / cell write points
- `Pending`: the context shows a suspicious pattern, but the external input source, barrier behavior, or call chain is unclear
- `False Positive`: the input comes from fixed constants / enum mappings, or the barrier has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or field source until any of the following holds:

- Evidence is found that externally controllable input enters the Sink position → `Confirmed Vulnerability`
- Fixed whitelist mapping / fail-close evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**trace-gate check**: if `node/route_tracer/{route_id}/trace_{timestamp}.md` does not exist or `trace_status=PARTIAL/UNRESOLVED`, all conclusions must be downgraded to `⚠️Pending Verification`; outputting `✅Confirmed Exploitable` is forbidden.

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

🔴 **STOP — when only export generation syntax is found without proving that user-controllable fields enter export content, outputting "Confirmed Vulnerability" is forbidden; conclusions must be `⚠️Pending Verification` with the missing evidence and evidence-supplementing actions stated.**

## Determination Rules (Mandatory Refinement)

### Confirmed

All three of the following must be satisfied simultaneously, with all three EVIDs cited, all indispensable:

1. **Source closure**: exported fields come from user-controlled data (`EVID_NODE_EXPORT_FIELD_USER_CONTROLLED` — evidence that req.body / req.query parameters, database user-writable columns, or downstream stored values enter exported data columns)
2. **Export generation Sink closure**: user-controllable fields reach the export generation / cell write point (`EVID_NODE_EXPORT_FORMULA_SINK` — evidence of `exceljs` `addRow` / `addRows` cell assignment, `csv-stringify` / `fast-csv` / `json2csv` field writes, handwritten CSV concatenation writes, or `res.send(csv)` direct output)
3. **Interpretation path and impact closure**: the exported content will be interpreted by spreadsheets as formulas / commands / links (`EVID_NODE_EXPORT_INTERPRETATION_PATH` — evidence that the `.csv` / `.xlsx` download is opened in Excel / WPS or similar spreadsheets, cell values starting with `= + - @` are interpreted as formulas, and DDE payloads or HYPERLINK chains can be triggered)

🔴 **Confirmation threshold (hard rule): without simultaneously citing EVID_NODE_EXPORT_FIELD_USER_CONTROLLED + EVID_NODE_EXPORT_FORMULA_SINK + EVID_NODE_EXPORT_INTERPRETATION_PATH, outputting "Confirmed" or 🔴/🟠 level conclusions is forbidden.**

🔴 **Plain text exports (no formula interpretation possible, such as fixed-template notification text, export content without any characters at the start that could be interpreted as formulas, and with the interpretation path proven absent) or when the interpretation path is not proven must not be confirmed.**

### ⚠️Pending Verification

- Only `addRow` / `stringify` / cell write syntax is found, but it is not proven that the written fields come from user-controllable data (trace or call chain needs to be supplemented)
- The export endpoint exists, but the field sources of exported columns are unclear (trace needed to confirm whether they are user-writable data)
- A formula neutralization function exists, but whether the current export chain invokes it and whether it covers all controllable columns cannot be confirmed
- Export data sources in asynchronous / queue / scheduled report chains are not closed
- The interpretation path of export content is unclear (e.g., `Content-Type` inconsistent with the extension, and the opening interpreter cannot be confirmed)
- When traces are missing or `trace_status=PARTIAL/UNRESOLVED`, all conclusions are downgraded to this tier

### False Positive

- Exports with formula neutralization: all user-controllable fields pass fail-close neutralization before write (`'` prefix or detection of values starting with `= + - @` plus prefixing), and cell formats are forced to text → False Positive
- All exported fields come from fixed constants / enum dictionaries, with no user-controllable data participation
- Exported columns are locked to a fail-close column list, and request parameters cannot change the exported column set
- Export content is plain text and the client has no spreadsheet interpretation path (e.g., log exports only, headless CSV pipelines consumed by machines only, with the absence of manual spreadsheet opening proven)

### Anti-Pattern Blacklist

| # | Anti-pattern | Why it is wrong | Correct practice |
|---|---|---|---|
| 1 | Outputting ✅Confirmed without a trace | Static grabbers alone cannot prove the user controllability of exported fields | Downgrade to `⚠️Pending Verification`, stating the missing evidence |
| 2 | Confirming high risk upon finding `addRow` | Write syntax ≠ field controllability; constant-column exports do not constitute a vulnerability | Close the field source (EVID_NODE_EXPORT_FIELD_USER_CONTROLLED) before confirming |
| 3 | Judging all `.xlsx` exports safe | The exceljs default General format also interprets formulas starting with `=` | Verify cell format forced to text and formula neutralization |
| 4 | CSV has no formula risk | When Excel opens a CSV, `=cmd|' /C calc'!A1` is likewise interpreted as DDE / formula | Verify whether formula neutralization is applied before CSV field writes |
| 5 | Judging safe because a neutralization function exists | A neutralization function that is not invoked by the current export chain, covers only some columns, or is bypassable is ineffective | Verify actual invocation and coverage of each export chain |

## Testing Recommendations (Mandatory)

### Positive Testing

- Write `=cmd|' /C calc'!A1` (or `=HYPERLINK("https://evil.example","click")`) into a user-controllable field, export it, and open it in a spreadsheet, verifying that the formula is interpreted and the DDE / hyperlink chain can be triggered
- Verify that req.body / req.query parameters enter `exceljs` `addRow` / `csv-stringify` writes via the trace chain, and that the payload remains intact in the exported file
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- After field values pass formula neutralization (`'` prefix), verify they display as literal text in spreadsheets without executing
- Out-of-allowlist column names and values containing Tab / CR prefix variants are fail-close intercepted
- Verify that formulas are not interpreted after `exceljs` controllable columns are forced to text format (`numFmt = '@'`)

### Regression Testing

- Retest after remediation across all export chains (including neutralization logic not being bypassed when new export columns are added), confirming neutralization and text format barriers remain effective
- Retest secondary-encapsulated exportService and direct call points, confirming no new bypass paths were introduced
- Verify that adding columns to the exported field allowlist remains fail-close

## Evidence References

- `EVID_NODE_EXPORT_FIELD_USER_CONTROLLED`
- `EVID_NODE_EXPORT_FORMULA_SINK`
- `EVID_NODE_EXPORT_INTERPRETATION_PATH`

## Output

- `node/vuln_audit/export_{timestamp}.md` (vulnerability ID format: `{severity prefix}-EXPORT-{sequence}`, e.g., `H-EXPORT-001`, aligned with the EXPORT type code of `shared/SEVERITY_RATING.md`)
- `node/vuln_poc/export_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC, referencing `shared/DOTNET_VULN_POC_TEMPLATE.md`)
- Each hit in the output must record: package name (exceljs / csv-stringify / fast-csv / json2csv / handwritten concatenation), field source (req.body / req.query / database user data / constant), whether formula neutralization exists, trace_id, and the citation status of the three EVIDs

## Minimum Acceptance Requirements

- Name, description, and responsibility boundaries are clear, without large-scale overlapping responsibilities with existing node specialties such as node-cmd-audit
- `shared/NODE_AUDIT_GRABBER_INDEX.md`, `shared/NODE_SINK_REFERENCE.md`, `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`, `shared/SEVERITY_RATING.md`, and `shared/IO_PATH_CONVENTION.md` are referenced
- The complete twelve-section structure exists: shared grabber index reference + input dependencies + key checks + enumeration rules (mandatory refinement) + Barrier verification matrix (mandatory) + two-phase determination (mandatory) + determination rules (mandatory refinement) + testing recommendations (mandatory) + evidence references + output + minimum acceptance requirements
- The evidence reference criteria are stated (EVID_NODE_EXPORT_FIELD_USER_CONTROLLED / EVID_NODE_EXPORT_FORMULA_SINK / EVID_NODE_EXPORT_INTERPRETATION_PATH)
- The relationships with `node/route_tracer` (hard precondition), `node/framework_audit`, `node/auth_audit`, pipeline, and the cross stack are stated
- It is stated that this specialty is of the trace-gate type and `node/route_tracer/*` is a hard precondition
- The Barrier verification matrix header is exactly `| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |`
- Output paths comply with `shared/IO_PATH_CONVENTION.md` and are explicitly written as `node/vuln_audit/export_{timestamp}.md` and `node/vuln_poc/export_{timestamp}.md`
- The body contains the node exclusion rules: `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`, and coverage directories are not part of the audit surface; lockfiles are an exception
