---
name: dotnet-file-read-audit
description: .NET file read and path traversal audit tool. Identifies path control and directory escape risks at read points such as File, FileStream, and PhysicalFileResult.
---

# .NET File Read Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to path sources, normalization, virtual path mapping, download endpoints, and file stream reads
- If the project has secondary encapsulations such as FileProvider, AttachmentService, ExportReader, or StorageGateway, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align download / read entries, parameter sources, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement the host, static file / template directories, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- path normalization boundaries of Path.Combine, Path.Join, GetFullPath, GetRelativePath, PhysicalFileProvider, and IFileProvider
- read points of File.ReadAllText, OpenRead, FileStream, MemoryMappedFile, PhysicalFileResult, VirtualFileResult, and StaticFileMiddleware
- path escape possibilities when user input controls file names, relative paths, extensions, directory segments, tenant directories, or blob keys
- handling of UNC paths, network shares, symlinks, junctions, container mounts, case differences, and Windows reserved device names
- whether read targets include configuration files, certificates, source code, view files, logs, upload directories, NuGet package caches, or secrets files
- read and execution boundaries, such as whether reading Razor / views / assemblies / configurations further affects template execution, assembly loading, or configuration injection
- whether the content-type, content-disposition, cache headers, and authentication conditions of download endpoints cause additional information leakage

## Enumeration Rules (Mandatory Refinement)

- Enumerate File.ReadAllText, ReadAllBytes, OpenRead, FileStream, PhysicalFileResult, VirtualFileResult, StaticFile mappings, and custom downloaders
- Search parameter names such as path, file, filename, template, view, config, download, export, doc, and attachment first
- Enumerate all path concatenation logic related to Path.Combine, GetFullPath, IFileProvider, PhysicalFileProvider, and ContentRoot / WebRoot
- For each read point record: target root directory, normalization logic, authentication conditions, output method, and whether configuration / source code / certificates / logs / uploaded files could be read

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Path normalization and base-directory locking** | Read the path concatenation / normalization source, confirming whether `Path.GetFullPath` + base directory prefix validation is used and the validation occurs after normalization | locked within the base directory after normalization and fail-close → ✅ safe; validation before normalization (e.g., validating only the input string) → ⚠️ bypassable; no base-directory locking → 🔴 high risk |
| **Extension / file type whitelist** | Confirm whether extension or MIME type restrictions exist on read targets and the whitelist is fail-close | fail-close (unknown types rejected) → ✅ safe; blacklist (only known dangerous extensions intercepted) → ⚠️ bypassable; no restrictions → 🔴 high risk |
| **Path traversal filtering** | Confirm whether `..`, null bytes, UNC prefixes, and symlinks are filtered, and whether filtering occurs before or after normalization | filtered after normalization covering all escape methods → ✅ safe; string replacement of `..` only → ⚠️ bypassable; no filtering → 🔴 high risk |
| **Symlink / junction resolution** | Confirm whether the host environment resolves symlinks / junctions and whether user input could point to a symlink to achieve directory traversal | symlink resolution disabled or final path resolution before reads → ✅ safe; symlinks allowed with no final path validation → ⚠️ to be confirmed |
| **Authentication conditions** | Confirm whether identity / permission validation exists before read operations and the validation matches resource ownership (anti-IDOR) | strict identity + resource ownership validation → ✅ safe; identity validation only without resource ownership → ⚠️ to be confirmed; no authentication → 🔴 high risk |
| **Post-read usage boundary** | Confirm whether read content enters template engines, configuration parsers, command execution, deserialization, or other sensitive boundaries | only static content returned after reads → 🟠 content-type to be confirmed; entering templates / configuration / execution after reads → 🔴 high risk |

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

1. user-controllable paths enter read points such as `File.ReadAllText`, `FileStream`, or `PhysicalFileResult` directly, with no base-directory locking or path normalization validation
2. path normalization validation executes before normalization (e.g., validating only the raw input string), bypassable via encoding / double path separators
3. extension / file type restrictions are in blacklist mode (e.g., only intercepting `.exe` and `.aspx`), bypassable via unknown extensions or null bytes
4. read operations have no authentication or only identity validation without resource ownership validation, creating an IDOR risk of reading others' files
5. in nested / recursive structures (such as multi-layer FileProvider wrappers), the top level has validation but sub-levels do not perform equivalent validation

### Pending

1. the context shows a suspicious pattern (such as a `PhysicalFileResult` call), but the external input source is unclear (trace or call chain needs to be supplemented)
2. a barrier function (such as base-directory validation) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
3. parameter passing in asynchronous / queue / event chains (such as message queue processing file download requests) is not closed
4. host environment differences (Windows / Linux path resolution, symlink behavior) are unverified

### False Positive

1. the final path comes from fixed constants / enum mappings, and unknown paths are refused execution (fail-close)
2. all recursive levels reuse the same base-directory locking validator, and the validator is fail-close
3. the path is strictly locked within the base directory after normalization, with an extension whitelist (fail-close) and identity + resource ownership validation
4. user input affects only the file name (no directory segments), and the file name passes strict allowlist validation

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct path traversal inputs (such as `../../../etc/passwd`, `..\windows\win.ini`, `....//....//etc/hosts`, and null byte truncation `%00`) and verify file reads really exist
- **Negative testing**: construct inputs intercepted by barriers (such as out-of-base-directory paths, blacklist extensions, overlong paths, and illegal encodings) and verify the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced (such as double encoding, symlinks, or case bypasses)

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Evidence References

- EVID_FILE_RESOLVED_TARGET
- EVID_FILE_PATH_NORMALIZATION
- EVID_FILE_EXECUTION_BOUNDARY

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (read point confirmation)**: the real read APIs and triggering entries must be confirmed.
- 🔴 **CHECKPOINT B (path closure confirmation)**: a three-segment evidence of `input path -> normalization -> final target` must be given.
- 🔴 **CHECKPOINT C (boundary confirmation)**: whether reads enter template / configuration / execution boundaries must be stated.
- 🛑 **STOP**: if the final target path cannot be confirmed, the conclusion is downgraded to `⚠️Pending Verification / Environment-Dependent`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| path normalization chain incomplete | complete the `input -> normalize -> final path` evidence | downgrade to `⚠️Pending Verification / Environment-Dependent` |
| host resolution differences (symlink / junction / UNC) unverified | verify path resolution semantics per platform | adopt the most conservative conclusion and retain verification steps |
| post-read usage unknown | trace to template / configuration / execution boundaries | if still unclosed, only output the suspicious impact |

🔴 **STOP: when any fallback triggers, outputting a strong "no risk" conclusion is forbidden.**

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

- Anti-pattern: drawing a path traversal conclusion upon a `..` hit alone. Correct practice: prove that the final landing point after normalization escapes the boundary.
- Anti-pattern: ignoring symlink / junction / UNC differences. Correct practice: verify resolution semantics per host environment.
- Anti-pattern: not checking post-read usage. Correct practice: confirm whether reads enter template / configuration / execution boundaries.
- Anti-pattern: writing "no risk" with insufficient evidence. Correct practice: downgrade to `⚠️Pending Verification / Environment-Dependent`.

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

- vuln_audit/file_{timestamp}.md
- Optional: vuln_poc/file_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
