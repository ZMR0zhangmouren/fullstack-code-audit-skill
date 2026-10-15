---
name: dotnet-spreadsheet-export-audit
description: .NET spreadsheet export (CSV / Excel) formula injection audit tool. Identifies formula / DDE / hyperlink injection risks caused by user-controllable fields without formula neutralization in export paths such as CsvHelper, EPPlus, ClosedXML, NPOI, and handwritten CSV concatenation; outputs severity rating, PoC, and remediation recommendations.
---

# .NET Spreadsheet Export (CSV / Excel) Formula Injection Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use the "EXPORT / Spreadsheet Export" chapter of shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the generator definitions in the EXPORT chapter: `CsvWriter` (CsvHelper), `ExcelPackage` / `EPPlus`, `ClosedXML`, `NPOI`, `StringWriter` / handwritten CSV concatenation, and formula injection patterns (values starting with `=` `+` `-` `@`, DDE payloads such as `=cmd|' /C calc'!A1`, and HYPERLINK phishing chains)
- If the project has unified secondary encapsulations such as ExportService, report generators, or CSV / Excel Helpers, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- **This specialty is of the trace-gate type**: source parameters of exported fields (request parameters, database user data, downstream stored values) require evidence closure from `route_tracer/{route_id}/trace_{timestamp}.md`; `route_tracer/{route_id}/trace_{timestamp}.md` is a hard precondition; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align export endpoint entries, parameter bindings, and `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to confirm anonymous reachability of export endpoints, P0 / P1 bucketing, and the sensitivity of exported data)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement Content-Type / Content-Disposition response header conventions, static file middleware, and runtime control plane)
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`
- When traces are missing or `trace_status=PARTIAL/UNRESOLVED`, all conclusions are downgraded to `⚠️Pending Verification` (see "Two-Phase Determination")

## Key Checks

- CSV / Excel export endpoints: actions returning file results via `[HttpGet]` / `[HttpPost]`, report exports, and bulk data download entries
- mapping of exported fields to request parameters / database user data: which columns in exported rows come from user-controllable input (query parameters, form fields, request bodies, database columns writable by users)
- formula prefix neutralization: whether values starting with `=` `+` `-` `@` are prefixed with `'` or rejected before being written into cells / CSV fields
- cell format forced to text: whether the Excel generation path explicitly sets user data columns to text format (NumberFormat `@` / `Style.Numberformat.Format`), blocking formula interpretation
- CSV delimiter and quote escaping: `CsvWriter` configuration versus handwritten `string.Join(",", values)` direct output (the latter often lacks both quote escaping and formula neutralization)
- response presentation consistency: whether `Content-Type` (`text/csv`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) matches the actual file extension and content format, avoiding browsers / spreadsheets opening the file with the wrong interpreter
- paths where export content is pure constants / enum dictionaries (no user data involved) are marked as irrelevant rather than vulnerabilities

## Enumeration Rules (Mandatory Refinement)

- Enumerate all export actions returning file results in classes inheriting Controller / ControllerBase, and report generation / file landing paths triggered in Services / Background Jobs
- Search first: `CsvWriter`, `ExcelPackage`, `EPPlus`, `ClosedXML` (`IXLWorksheet.Cell(` / `InsertTable`), `NPOI` (`ISheet.CreateRow` / `CreateCell` / `SetCellValue`), handwritten CSV concatenation with `StringWriter` (`string.Join`, `WriteLine` field concatenation), `Content-Disposition` (attachment;filename= response headers), `FileContentResult` / `File(...)` returning CSV / Excel, and `ContentResult` directly outputting text / csv
- Enumerate formula neutralization helper functions (such as `SanitizeFormula`, `EscapeCell`): their definitions and all call sites, confirming whether each export chain actually invokes them
- Separately enumerate exported field sources: whether each column field comes from request parameters, database user-writable columns, downstream stored values, or fixed constants, annotating controllability one by one
- Enumerate Excel cell format settings: whether user data columns are explicitly set to `NumberFormat = "@"`; the default General format in most spreadsheets interprets formulas
- For each hit record: **file, line number, generator type (CsvHelper / EPPlus / ClosedXML / NPOI / handwritten CSV), field source (request parameter / database user data / constant), and whether formula neutralization exists (yes / no / not visible)**
- Enumerate the encapsulation chains of unified ExportService, report generators, and CSV / Excel Helpers, tracing to the final cell / field write points

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Formula prefix neutralization** | Confirm whether values starting with `=` `+` `-` `@` (and Tab / CR prefix variants) are detected before writing and prefixed with `'` or the write is rejected; whether the neutralization function is fail-close (all unknown prefixes handled) | all user-controllable fields uniformly neutralized before write and fail-close → ✅ safe; only some columns neutralized, the neutralization function bypassable, or implementation not visible → ⚠️ to be confirmed; no neutralization with controllable fields → 🔴 high risk |
| **Cell format forced to text** | Confirm whether user data columns in the Excel generation path are explicitly set to text format (`NumberFormat = "@"` / `Style.Numberformat.Format = "@"`) rather than the default General | all controllable columns forced to text format → ✅ safe; only some columns set or format setting not visible → ⚠️ to be confirmed; not set → 🔴 high risk |
| **Exported field allowlist** | Confirm whether the exported column set comes from a fixed column list rather than arbitrary writable columns dynamically selected by request parameters | fail-close column list → ✅ safe; column names / column sets from request parameters without validation → 🔴 high risk |
| **Download presentation consistency** | Confirm whether `Content-Type`, the Content-Disposition extension, and the actual file format are consistent, avoiding spreadsheets opening with the wrong interpreter or browsers sniffing the content as executable | all three consistent → ✅ safe; inconsistent or the export can be forced to be interpreted by a spreadsheet → 🟠 medium-risk candidate |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion as "Confirmed Safe" or "False Positive" is forbidden.**

## Two-Phase Determination (Mandatory)

Follow the two-phase determination process of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

1. **Phase 1 (interim conclusion)**: mark each hit as `Confirmed Vulnerability Candidate` / `Pending` / `False Positive` first
2. **Phase 2 (mandatory evidence chasing)**:
   - if Phase 1 is `Confirmed Vulnerability Candidate` → all relevant items of the Barrier verification matrix must be completed, and the three segments of evidence — Source → export generation Sink → interpretation path / impact (three EVIDs) — must all be cited before `Confirmed` may be marked
   - if Phase 1 is `Pending` → chase at least one more hop of the call chain or field source downward, until a determination can be made
   - if Phase 2 still cannot close → remain `Pending`, and explicitly record which hop of evidence is missing
3. **trace-gate check**: if `route_tracer/{route_id}/trace_{timestamp}.md` does not exist or `trace_status=PARTIAL/UNRESOLVED`, all conclusions must be downgraded to `⚠️Pending Verification`; outputting `✅Confirmed Exploitable` is forbidden

🔴 **STOP — when only export generation syntax is found without proving that user-controllable fields enter export content, outputting "Confirmed Vulnerability" is forbidden; conclusions must be `⚠️Pending Verification`, with the missing evidence and evidence-supplementing actions stated.**

## Determination Rules (Mandatory Refinement)

### Confirmed Vulnerability

All three of the following must be satisfied simultaneously, with all three EVIDs cited, all indispensable:

1. **Source closure**: exported fields come from user-controlled data (`EVID_EXPORT_FIELD_USER_CONTROLLED` — evidence that request parameters, database user-writable columns, or downstream stored values enter exported data columns)
2. **Export generation Sink closure**: user-controllable fields reach the export generation / cell write point (`EVID_EXPORT_FORMULA_SINK` — evidence of `CsvWriter` field writes, `ExcelPackage` / EPPlus / ClosedXML / NPOI cell assignments, or handwritten CSV concatenation writes)
3. **Interpretation path and impact closure**: the exported content will be interpreted by spreadsheets as formulas / commands / links (`EVID_EXPORT_INTERPRETATION_PATH` — evidence that the `.csv` / `.xlsx` download is opened in Excel / WPS or similar spreadsheets, cell values starting with `= + - @` are interpreted as formulas, and DDE payloads or HYPERLINK chains can be triggered)

🔴 **Confirmation threshold (hard rule): without simultaneously citing EVID_EXPORT_FIELD_USER_CONTROLLED + EVID_EXPORT_FORMULA_SINK + EVID_EXPORT_INTERPRETATION_PATH, outputting "Confirmed" or 🔴/🟠 level conclusions is forbidden.**

🔴 **Plain text exports (no formula interpretation possible, such as fixed-template notification text, export content without any characters at the start that could be interpreted as formulas, and with the interpretation path proven absent) or when the interpretation path is not proven must not be confirmed.**

### Pending

1. Only `CsvWriter` / cell write syntax is found, but it is not proven that the written fields come from user-controllable data → `⚠️Pending Verification`; confirmation is forbidden
2. the export endpoint exists, but the field sources of exported columns are unclear (trace or call chain needed to confirm whether they are user-writable data)
3. a formula neutralization function exists, but whether the current export chain invokes it and whether it covers all controllable columns cannot be confirmed
4. export data sources in asynchronous / queue / scheduled report chains are not closed
5. the interpretation path of export content is unclear (e.g., the returned format is inconsistent with the extension, and the opening interpreter cannot be confirmed)

### False Positive

1. exports with formula neutralization: all user-controllable fields pass fail-close neutralization before write (`'` prefix or detection of values starting with `= + - @` plus prefixing), and cell formats are forced to text → False Positive
2. all exported fields come from fixed constants / enum dictionaries, with no user-controllable data participation
3. exported columns are locked to a fail-close column list, and request parameters cannot change the exported column set
4. export content is plain text and the client has no spreadsheet interpretation path (e.g., log exports only, headless CSV pipelines consumed by machines only, with the absence of manual spreadsheet opening proven)

### Anti-Pattern Blacklist

| # | Anti-pattern | Why it is wrong | Correct practice |
|---|---|---|---|
| 1 | Outputting ✅Confirmed without a trace | static grabbers alone cannot prove the user controllability of exported fields | downgrade to `⚠️Pending Verification`, stating the missing evidence |
| 2 | Confirming high risk upon finding `CsvWriter.WriteField` | write syntax ≠ field controllability; constant-column exports do not constitute a vulnerability | close the field source (EVID_EXPORT_FIELD_USER_CONTROLLED) before confirming |
| 3 | Judging all `.xlsx` exports safe | the default General format of EPPlus / ClosedXML / NPOI also interprets formulas starting with `=` | verify cell formats forced to text and formula neutralization |
| 4 | CSV has no formula risk | when Excel opens a CSV, `=cmd|' /C calc'!A1` is likewise interpreted as DDE / formula | verify whether formula neutralization is applied before CSV field writes |
| 5 | Judging safe because a neutralization function exists | a neutralization function that is not invoked by the current export chain, covers only some columns, or is bypassable is ineffective | verify actual invocation and coverage of each export chain |

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: write `=cmd|' /C calc'!A1` (or `=HYPERLINK("https://evil.example","click")`) into a user-controllable field, export it, and open it in a spreadsheet, verifying that the formula is interpreted and the DDE / hyperlink chain can be triggered
- **Negative testing**: after field values pass formula neutralization (`'` prefix), export them and verify they display as literal text without executing in spreadsheets; and verify that out-of-allowlist column names and values containing Tab / CR prefix variants are fail-close intercepted
- **Regression testing**: retest all export chains after remediation (including neutralization logic not being bypassed when new export columns are added), confirming neutralization and text format barriers remain effective, and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Evidence References

- EVID_EXPORT_FIELD_USER_CONTROLLED
- EVID_EXPORT_FORMULA_SINK
- EVID_EXPORT_INTERPRETATION_PATH

## Output

- vuln_audit/export_{timestamp}.md (vulnerability ID format: `{severity prefix}-EXPORT-{sequence}`, e.g., `H-EXPORT-001`, aligned with the EXPORT type code of shared/SEVERITY_RATING.md)
- vuln_poc/export_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC, referencing shared/DOTNET_VULN_POC_TEMPLATE.md)
- Each hit in the output must record: generator type (CsvHelper / EPPlus / ClosedXML / NPOI / handwritten CSV), field source (request parameter / database user data / constant), whether formula neutralization exists, trace_id, and the citation status of the three EVIDs
