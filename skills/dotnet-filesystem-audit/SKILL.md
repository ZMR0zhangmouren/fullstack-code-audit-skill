---
name: dotnet-filesystem-audit
description: .NET filesystem operation audit tool. Focuses on directory creation, permissions, links, deletion, renaming, TOCTOU, and host filesystem differences, providing exploitability amplification evidence for FILE, UPLOAD, WRITE, and other chains.
---

# .NET Filesystem Operation Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to directory traversal, link following, TOCTOU, permission inheritance, and delete / move / copy operations
- If the project has secondary encapsulations such as StorageManager, PathHelper, ArchiveManager, or SyncService, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to associate trigger entries, path sources, and `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to associate background operations, admin entries, and permission boundaries)
- Optional: `route_tracer/{route_id}/trace_{timestamp}.md` and `route_tracer/{route_id}/trace_summary_{timestamp}.md` (may serve as cross-reference evidence between filesystem side effects and entries; not hard preconditions)

Key checks:

- dangerous usage patterns of Directory.CreateDirectory, CreateSymbolicLink, File.Move, File.Copy, File.Delete, File.Replace, and Directory.Delete
- behavioral differences of symlinks, junctions, hardlinks, network shares, container-mounted volumes, host bind mounts, and read-only filesystems
- TOCTOU caused by check-and-use separation, such as checking Exists / ACL before opening, validating before renaming, and resolving before writing
- whether the landing point after GetFullPath / realpath normalization is re-concatenated, redirected, or replaced in subsequent steps
- permission inheritance and cross-directory moves among temp directories, cache directories, log directories, export directories, and upload directories
- Windows ACLs, Linux chmod / chown, IIS / Kestrel / container service account permissions, and impersonation behavior
- whether delete, overwrite, replace, and cleanup logic can serve as preconditions for chained exploitation, such as deleting lock files, replacing configurations, or overwriting scheduled task inputs

## Key Checks

- path sources and permission control of File.Move / File.Copy / File.Delete / Directory.Delete
- creation and resolution logic of symlinks, hardlinks, and junctions
- TOCTOU races: the time window between checking file existence and operating
- creation locations, permission inheritance, and cleanup logic of temp files / directories
- trust boundaries of container volume mounts and network share paths
- ACL change operations: SetAccessControl and permission inheritance modifications
- the value of filesystem operations as intermediate links in exploit chains (trigger after write, replace after delete)

## Evidence References

- EVID_FS_TOCTOU_OR_LINK_BEHAVIOR

## Enumeration Rules (Mandatory Refinement)

- Enumerate all APIs related to Directory.CreateDirectory, File.Move, File.Copy, File.Delete, File.Replace, Directory.Delete, and symlink creation and resolution
- Search directory semantics such as temp, cache, upload, export, log, backup, staging, working, and quarantine first
- Enumerate ACL changes, permission inheritance, container volume mounts, network shares, and the creation and usage positions of junctions, symlinks, and hardlinks
- For each filesystem operation record: trigger entry, path source, race window, and subsequent chained exploitation value

Key evidence: EVID_FS_TOCTOU_OR_LINK_BEHAVIOR.

## Barrier Verification Matrix (Mandatory)

Evaluate per the fail-close three-level standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Level | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Level 1 | filesystem operation point exists with controllable path source | operation points such as File.Move / Copy / Delete / CreateDirectory / symlink creation exist and their path source includes user input | BLOCKED → no user input mapping; the specialty ends |
| Level 2 | TOCTOU / links exploitable | a time window exists between check and operation (TOCTOU), or symlinks / junctions / hardlinks can be used for path redirection | BLOCKED → conclusion downgraded to `⚠️Environment-Dependent` |
| Level 3 | permissions / host environment allow exploitation | the runtime account / ACL / container mounts / host semantics allow the operation to actually take effect with security impact | PARTIAL → only output environment-dependent risks and review recommendations |

## Two-Phase Determination Process (Mandatory)

- **Phase 1 (initial screening hit)**: hit a filesystem operation point + path source from user input, and output `hit ID: M{hash}`.
- **Phase 2 (refined confirmation)**:
  1. back-trace the input → path normalization → filesystem operation chain;
  2. verify the exploitability of TOCTOU time windows (Exists → Open, validate → rename, etc.) or link following (symlink / junction / hardlink);
  3. assess whether the runtime account / ACL / container mounts / host semantics allow the operation to take effect;
  4. if all three-level Barriers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priorities (Mandatory)

1. **Confirmed Vulnerability**: operation point exists + path controllable + TOCTOU / links exploitable + permissions / host environment allow. Output `Confirmed Vulnerability`.
2. **Pending**: the operation point and path mapping exist, but TOCTOU / link or permission evidence is insufficient. Output `Pending`.
3. **False Positive / No Risk**: the path source is uncontrollable, or the TOCTOU time window is too short to exploit, or permissions are strictly limited. Output `False Positive` with the determination basis.

## Testing Recommendations and Minimal Trigger Conditions (Mandatory)

- **Minimal trigger conditions**:
  - a filesystem operation entry exists (Move / Copy / Delete / CreateDirectory / symlink creation)
  - the operation path contains user-controllable input
  - a TOCTOU time window or link following is exploitable
- **Test case suggestions**:
  - Happy Path: normal file operations succeed; out-of-bounds / illegal paths are intercepted
  - Boundary / ambiguity: symlinks pointing to sensitive paths, junction cross-volume jumps, TOCTOU races (replacing files after validation), ACL inheritance bypasses
- Each hit output appends `hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (operation point confirmation)**: create / move / delete / replace filesystem operation points must be confirmed.
- 🔴 **CHECKPOINT B (race and link confirmation)**: whether TOCTOU or link following evidence holds must be explicit.
- 🔴 **CHECKPOINT C (permission and host confirmation)**: the actual boundaries of ACLs / service accounts / container mounts must be recorded.
- 🛑 **STOP**: if host semantics and permission evidence are incomplete, the conclusion is downgraded to `⚠️Environment-Dependent`; strong conclusions are forbidden.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| TOCTOU or link following evidence incomplete | complete the time window evidence between check points and actual operations | downgrade to `⚠️Environment-Dependent` |
| ACL / runtime account boundary unclear | supplement permission inheritance and service account information | only output environment-dependent risks and review recommendations |
| host semantic differences cause conflicting conclusions | record behavioral differences per platform | adopt the most conservative criteria; strong conclusions are forbidden |

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

- Anti-pattern: treating Exists / PathCheck as the final security guarantee. Correct practice: evaluate TOCTOU time windows and subsequent operations.
- Anti-pattern: ignoring semantic differences of symlinks / junctions / hardlinks. Correct practice: verify link behavior per platform.
- Anti-pattern: not auditing ACL inheritance and runtime account permissions. Correct practice: complete permission boundary evidence.
- Anti-pattern: strong conclusions without host evidence. Correct practice: downgrade to `⚠️Environment-Dependent`.

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

- vuln_audit/fs_{timestamp}.md
- Optional: vuln_poc/fs_{timestamp}.md (if link, race, overwrite, or cross-directory write verification steps can be constructed)
