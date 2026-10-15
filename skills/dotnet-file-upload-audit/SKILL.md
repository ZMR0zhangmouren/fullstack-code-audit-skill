---
name: dotnet-file-upload-audit
description: .NET file upload audit tool. Identifies arbitrary upload and executable upload risks in IFormFile, multipart handling, save paths, and file name validation logic.
---

# .NET File Upload Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to IFormFile, multipart, content types, file names, landing paths, and downstream consumption
- If the project has secondary encapsulations such as UploadService, StorageProvider, MediaManager, or TempFileHelper, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align upload entries, file parameters, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement the host, static resource directories, and post-processing chain control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- save points of IFormFile.CopyTo / CopyToAsync, MultipartReader, custom stream writes, third-party upload components, and object storage SDKs
- handling of file names, extensions, double extensions, case bypasses, trailing dots / spaces, Unicode homoglyphs, path separators, and directory traversal fragments
- recognition logic for MIME, Content-Type, file signatures, magic bytes, image re-encoding, archives, and Office / PDF macro and script payloads
- whether the save directory is located in the web root, static file directories, temp directories, container shared directories, CDN sync directories, or directories subject to secondary background processing
- whether uploads can be accessed directly by URL, accessed via download endpoints, or secondarily consumed by image processing / template rendering / antivirus / transcoding components
- whether rename policies, unique file name generation, tenant isolation directories, metadata records, and rollback / deletion logic are reliable
- authentication and validation consistency of form binding, GraphQL Upload, SignalR streaming upload, large file chunked upload, and resumable upload scenarios

## Enumeration Rules (Mandatory Refinement)

- Enumerate all IFormFile, IFormFileCollection, MultipartReader, chunked upload, object storage direct-upload callback, and custom upload service entries
- Search parameter names such as upload, file, attachment, avatar, image, document, import, chunk, resume, and multipart first
- Enumerate file name generation, extension validation, magic byte validation, image re-encoding, archive checks, and Office / PDF security check chains
- For each save point record: save directory, access method, whether it enters the web root, and whether it is re-consumed by background tasks or template / transcoding services

## Barrier Verification Matrix (Mandatory)

Evaluate per the fail-close three-level standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Level | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Level 1 | upload entry exists and reachable | entries such as IFormFile / Multipart / direct upload exist and users can actually trigger uploads | BLOCKED → no upload entry; the specialty ends |
| Level 2 | file name validation / path control bypassable | extension / MIME / magic byte / path validation has bypass possibilities (double extension / Unicode / directory traversal / case) | BLOCKED → conclusion downgraded to `⚠️Pending Verification / Environment-Dependent` |
| Level 3 | accessible / executable after upload | saved files can be accessed or executed via URL / download / inclusion / transcoding / background tasks | PARTIAL → only output bypass hypotheses and verification steps |

## Two-Phase Determination Process (Mandatory)

- **Phase 1 (initial screening hit)**: hit an upload entry + controllable file name / path / content source, and output `hit ID: M{hash}`.
- **Phase 2 (refined confirmation)**:
  1. back-trace the file name parsing → validation chain → save path chain;
  2. verify the bypass conditions of extension / MIME / magic byte / path validation (double extension, Unicode homoglyphs, directory traversal, case);
  3. assess whether saved files can be accessed or executed via URL / download / inclusion / transcoding / background tasks;
  4. if all three-level Barriers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priorities (Mandatory)

1. **Confirmed Vulnerability**: upload entry reachable + validation bypassable + accessible / executable after upload. Output `Confirmed Vulnerability`.
2. **Pending**: the upload entry exists, but validation bypass or post-processing chain evidence is insufficient. Output `Pending`.
3. **False Positive / No Risk**: no upload entry exists, or file names / paths are uncontrollable with strict validation and no access after saving. Output `False Positive` with the determination basis.

## Testing Recommendations and Minimal Trigger Conditions (Mandatory)

- **Minimal trigger conditions**:
  - a file upload entry exists (IFormFile / Multipart / object storage direct-upload callback)
  - file names, extensions, or save paths contain user-controllable input
  - the validation chain is bypassable or missing
- **Test case suggestions**:
  - Happy Path: normal files upload successfully; illegal extensions / MIME are intercepted
  - Boundary / ambiguity: double extensions (`shell.aspx.jpg`), Unicode homoglyphs (`ѕһеll.jsp`), directory traversal (`../../shell`), trailing dot / space bypasses
- Each hit output appends `hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Evidence References

- EVID_UPLOAD_DESTPATH
- EVID_UPLOAD_FILENAME_EXTENSION_PARSING_SANITIZE
- EVID_UPLOAD_ACCESSIBILITY_PROOF

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (upload entry confirmation)**: the upload entry, file parameters, and authentication conditions must be confirmed.
- 🔴 **CHECKPOINT B (landing chain confirmation)**: evidence of `file name / extension -> save path -> final reachability` must be given.
- 🔴 **CHECKPOINT C (post-processing confirmation)**: whether uploads enter transcoding / template / scanning / publishing consumption chains must be stated.
- 🛑 **STOP**: if the reachability of the save directory or the execution boundary cannot be confirmed, the conclusion is downgraded to `⚠️Pending Verification`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| unable to confirm the save directory and access surface | complete the landing directory, access path, and authentication conditions | downgrade to `⚠️Pending Verification` |
| file validation chain incomplete (extension / MIME / magic bytes) | verify validation logic and bypass points stage by stage | only output pending risks; make no "not exploitable" conclusion |
| post-processing chain evidence missing | trace to consumption links such as transcoding / templates / publishing | retain the high-risk hypothesis and give verification steps |

🔴 **STOP: when any fallback triggers, outputting a strong "not exploitable" conclusion is forbidden.**

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

- Anti-pattern: judging safe based only on the extension whitelist. Correct practice: also check magic bytes, rename policies, and accessibility.
- Anti-pattern: ignoring double extension and Unicode homoglyph bypasses. Correct practice: validate against the normalized file name uniformly.
- Anti-pattern: not auditing the post-upload processing chain. Correct practice: trace to secondary consumption such as transcoding / templates / publishing.
- Anti-pattern: judging "not exploitable" with insufficient evidence. Correct practice: downgrade to `⚠️Pending Verification`.

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion levels: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose one of three; blank is forbidden).
- Minimum evidence set: at least the five items `Entry Point`, `Controllable Parameter`, `Key Call`, `Security Boundary`, and `Missing Evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softened wording is forbidden: such as "may be at risk / suggested attention / depends on the situation / most likely"; when evidence is insufficient, `⚠️Pending Verification` and the next evidence-supplementing action must be explicitly written.

Minimal output fragment (directly reusable):

```md
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameter=...; key call=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement the parameter-propagation evidence of trace_id=...
```

## Output

- vuln_audit/upload_{timestamp}.md
- Optional: vuln_poc/upload_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
