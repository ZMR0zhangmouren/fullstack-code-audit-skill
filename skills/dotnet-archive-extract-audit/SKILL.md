---
name: dotnet-archive-extract-audit
description: .NET archive extraction path traversal audit tool. Identifies entry name escape and final target path out-of-bounds risks in extraction logic such as ZipArchive, Tar, and SharpCompress.
---

# .NET Archive Extraction Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to archive formats, entry names, extraction directories, overwrite policies, symlinks, and downstream consumption
- If the project has secondary encapsulations such as ArchiveService, PackageImporter, PluginInstaller, or BackupRestore, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement the host, static file directories, upload / plugin directories, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

Key checks:

- extract call sites and target directory sources of ZipArchive, Tar, SharpCompress, and third-party extraction components
- whether ZipArchiveEntry.FullName, entry.Key, tar path, and other archive entry names contain escape fragments such as ../, absolute paths, drive letters, UNC, and reserved device names
- whether the final resolved target still escapes the base directory after entry names are normalized, separators replaced, leading slashes removed, and case-normalized
- whether the extraction directory is located in the web root, plugin directories, template directories, task input directories, downloadable directories, or background scan directories
- whether symlinks, hardlinks, duplicate file names, directory overwrites, file replacements, and archive bomb protections in archives are handled
- whether extraction results are consumed by subsequent template rendering, assembly loading, script execution, configuration reads, or static resource publishing chains

## Key Checks

- Call sites and entry name sources of extraction APIs such as ZipFile.ExtractToDirectory, ZipArchive per-entry extraction, SharpZipLib, SharpCompress, and TarFile
- whether archive entry names (entry.FullName) contain `../` or absolute paths, and whether normalization and directory constraint validation are performed before extraction
- whether the extraction target directory is a web-accessible directory, an executable directory, or a configuration directory
- handling logic for symlink entries, overlong path entries, and duplicate file overwrites
- the extraction chain after user-uploaded archives: upload → staging → extraction → landing → downstream consumption
- whether archive extraction in plugin / theme / template import functions has a whitelist or sandbox isolation

## Evidence References

- EVID_ARCHIVE_EXTRACT_CALLSITE
- EVID_ARCHIVE_ENTRY_NAME_SOURCE
- EVID_ARCHIVE_FINAL_TARGET

## Enumeration Rules (Mandatory Refinement)

- Enumerate extract call sites in ZipArchive, Tar, SharpCompress, SevenZip wrappers, custom extraction services, and import functions
- Search business semantics such as extract, unzip, untar, archive, entry, restore, import package, and theme / plugin import first
- Enumerate entry name normalization, target directory concatenation, duplicate file overwrite, and symlink / hardlink entry handling logic
- For each extraction point record: archive source, target directory, final resolved path, and whether extracted files enter accessible or executable areas

## Barrier Verification Matrix (Mandatory)

Execute per the fail-close three-level standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| # | Check Item | Pass Criteria | Handling on Failure |
|---|--------|----------|------------|
| B1 | Source controllability | entry parameters (uploaded file name / archive content) can be attacker-controlled | source uncontrollable → mark `NO_FINDING` and end |
| B2 | Sink reachability | extraction APIs (ZipFile.ExtractToDirectory / SharpCompress / TarFile) are on a route-reachable path | unreachable → mark `NO_FINDING` and end |
| B3 | Boundary validation missing | entry names lack normalization, directory constraints, or prefix validation | sufficient validation present → mark `NO_FINDING` and end |

**fail-close rule: failure of any Barrier terminates the determination; continuing to output a vulnerability conclusion is forbidden.**

## Two-Phase Determination Process

1. **Phase 1: structural hit**
   - hit an archive extraction call point (ZipArchive / SharpCompress / TarFile)
   - confirm the entry name comes from user-controllable input
   - determination: if the source is uncontrollable → `NO_FINDING`; continue to Phase 2 otherwise

2. **Phase 2: semantic confirmation**
   - confirm the entry name contains path escape fragments (`../`, absolute path, UNC, drive letter)
   - confirm the normalization / directory constraint validation is missing or bypassable
   - confirm the final resolved path escapes the base directory
   - determination: if any condition does not hold → downgrade to `NO_FINDING` or `PENDING_VERIFICATION`

3. **Conclusion output**
   - Phase 1 + Phase 2 satisfied → `FOUND`
   - Phase 1 passed but Phase 2 not fully confirmed → `PENDING_VERIFICATION`
   - Phase 1 not passed → `NO_FINDING`

## Determination Rules

| Condition Combination | Conclusion | Suggested Level |
|----------|------|----------|
| B1=PASS ∧ B2=PASS ∧ B3=PASS ∧ Phase 2 confirms path escape | `FOUND` | 🔴 High |
| B1=PASS ∧ B2=PASS ∧ B3=UNCERTAIN | `PENDING_VERIFICATION` | 🟡 Medium |
| B1=FAIL ∨ B2=FAIL | `NO_FINDING` | 🟢 None |
| validation present but bypassable | `FOUND` (note the bypass path) | 🟠 Medium-High |

## Testing Recommendations (Mandatory)

- construct ZIP / TAR entries containing `../` paths and verify whether extracted files land outside the target directory
- construct archive entries containing absolute paths, UNC paths, and Windows reserved device names (`CON`, `NUL`, etc.)
- construct symlink entries and verify whether they are handled correctly or followed
- verify path resolution differences on both Windows and Linux
- record `test_id: T{hash}` for each verification, associated with the corresponding `hit ID: M{hash}`

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (entry confirmation)**: before starting, the archive source, extraction target directory, and triggering entry (`route_id` / function point) must be confirmed.
- 🔴 **CHECKPOINT B (path closure)**: before output, a three-segment evidence chain of `entry name -> normalization -> final target path` must be given.
- 🔴 **CHECKPOINT C (impact surface confirmation)**: if extraction results involve the web root / plugins / templates / configuration directories, the impact surface and reachability must be listed separately.
- 🛑 **STOP**: if whether the final target path escapes cannot be confirmed, the conclusion must be downgraded to `⚠️Pending Verification / Environment-Dependent`; outputting "Confirmed Exploitable" is forbidden.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| unable to obtain the three-segment evidence of `entry -> normalize -> final path` | return to the call site to supplement path resolution and normalization process evidence | mark `⚠️Pending Verification / Environment-Dependent` and retain the pending-evidence item |
| host platform differences cause inconsistent path conclusions (Windows / Linux / UNC) | verify per platform separately and record the difference conditions | downgrade the conclusion per the most conservative criteria; outputting Confirmed Exploitable is forbidden |
| unable to confirm extraction landing reachability (webroot / plugins / templates) | supplement directory exposure and downstream consumption chain evidence | retain the risk hypothesis and output verification steps; make no strong conclusion |

🔴 **STOP: when any fallback triggers, outputting "Confirmed Exploitable" is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Mandatory shared indexes: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber source) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: persistence paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from directories are forbidden.
- Evidence consistency validation: if graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: confirm at least once before submission that key referenced files are accessible (such as `DOTNET_AUDIT_GRABBER_INDEX.md` and `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Execute at least 2 typical test cases before each output (one happy path + one boundary / ambiguity scenario), and record expected vs actual differences.
- `full_test >= 1` is required by default; if only `dry_run` is possible, `confidence=LOW` must be marked in the conclusion, with a supplementary test plan and owner given.
- Pass criteria: key fields complete, evidence chains traceable, conclusion levels consistent with gate status; if any fails, marking "passed / deliverable" is forbidden.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `input constraints` → `execution steps` → `output and acceptance`; missing layers or cross-layer mixing are forbidden.
- A single paragraph is recommended not to exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into the single-source-of-truth section.
- AI-style filler and empty connectives are forbidden (such as "first / second / finally / in summary / to put it simply / in other words"); rewrite them into executable statements upon discovery.

## Quality Gate & Assessment Consistency (Mandatory)

- Execute the minimal gate self-check before output: `input completeness`, `key evidence hit`, and `output path valid` must all be PASS.
- If any of `key evidence missing`, `chain not closed`, or `consistency_check_status=BLOCKED` exists, the conclusion must be downgraded to `BLOCKED`; outputting "Confirmed Exploitable / Deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

- Anti-pattern: judging high risk directly upon a `../` keyword hit. Correct practice: a closed chain of `entry -> normalize -> final path` must be given.
- Anti-pattern: ignoring Windows drive letters, UNC, absolute paths, and case normalization differences. Correct practice: verify path constraints per host platform.
- Anti-pattern: giving an exploitation conclusion without confirming the reachability of the extraction landing point. Correct practice: supplement impact surface evidence for webroot / plugin / template / configuration directories.
- Anti-pattern: writing "insufficient evidence" as "no risk". Correct practice: uniformly downgrade to `⚠️Pending Verification / Environment-Dependent` and retain pending-evidence items.

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion levels: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose one of three; blank is forbidden).
- Minimum evidence set: at least the five items `Entry Point`, `Controllable Parameter`, `Key Call`, `Security Boundary`, and `Missing Evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softened wording is forbidden: such as "may be at risk / suggested attention / depends on the situation / most likely"; when evidence is insufficient, `⚠️Pending Verification` and the next evidence-supplementing action must be explicitly written.

Minimal output fragment (directly reusable):

```md
- Audit conclusion level: Confirmed
- Hit ID: M{hash}
- test_id: T{hash}
- Minimum evidence set: entry point=...; controllable parameter=...; key call=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement the parameter-propagation evidence of trace_id=...
```

## Output

- vuln_audit/archive_{timestamp}.md
- Optional: vuln_poc/archive_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
