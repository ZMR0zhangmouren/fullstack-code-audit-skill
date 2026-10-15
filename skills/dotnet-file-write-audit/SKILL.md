---
name: dotnet-file-write-audit
description: .NET arbitrary file write audit tool. Identifies paths where user-controllable data enters write Sinks and evaluates post-write accessibility, includability, and executability.
---

# .NET File Write Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to path concatenation, directory creation, overwrite writes, temp files, permissions, and atomic replacement
- If the project has secondary encapsulations such as FileStore, ConfigWriter, ExportService, or DocumentWriter, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align write entries, parameter sources, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement the host, accessible directories, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- write points such as File.WriteAllText, WriteAllBytes, FileStream, StreamWriter, AppendAllText, and report Save / Export / Generate operations
- how user input or external data enters target paths, file names, directory segments, extensions, or blob / object keys
- whether base directory prefix validation is performed after Path.Combine / GetFullPath, and whether re-concatenation after validation causes bypasses
- whether write content comes from request bodies, template content, log forgery, archive extraction results, deserialized data, or remotely fetched content
- whether written files can be further consumed via static resources, download endpoints, template engines, assembly loading, scheduled tasks, or background jobs
- whether overwrite, append, truncate, atomic replacement, temp-file-then-rename, permission inheritance, and ACL settings amplify the impact
- access surface differences among local disks, network shares, object storage, container volumes, and host-mounted directories

## Enumeration Rules (Mandatory Refinement)

- Enumerate all WriteAllText, WriteAllBytes, AppendAllText, StreamWriter, Save, Export, Generate, template save, and config save operations
- Search target path fields such as path, dest, target, filename, output, export, report, template, and config first
- Enumerate path concatenation, temp file landing, rename / move, object storage key generation, and container volume mount landing selection logic
- For each write point record: path source, content source, overwrite mode, post-write access surface, and whether it could enter template / configuration / static resource / assembly consumption chains

## Barrier Verification Matrix (Mandatory)

Evaluate per the fail-close three-level standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Level | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Level 1 | write point exists with controllable path / content source | write points such as File.WriteAllText / StreamWriter / Save exist and their path or content source includes user input | BLOCKED → no user input mapping; the specialty ends |
| Level 2 | path validation / filtering bypassable | base directory validation after Path.Combine / GetFullPath is bypassable (re-concatenation, decode differences, link following) | BLOCKED → conclusion downgraded to `⚠️Pending Verification / Environment-Dependent` |
| Level 3 | accessible / executable after write | written files can be consumed or executed by static resources / downloads / template inclusion / assembly loading / scheduled tasks | PARTIAL → only output conservative risk conclusions and verification steps |

## Two-Phase Determination Process (Mandatory)

- **Phase 1 (initial screening hit)**: hit a write point + path or content source from user input, and output `hit ID: M{hash}`.
- **Phase 2 (refined confirmation)**:
  1. back-trace the input → path concatenation / normalization → write point chain, tracing the content source simultaneously;
  2. verify bypass conditions such as base directory validation, re-concatenation after Path.Combine, and symlink following;
  3. assess whether written files can be consumed or executed by static resources / downloads / inclusion / assemblies / tasks;
  4. if all three-level Barriers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priorities (Mandatory)

1. **Confirmed Vulnerability**: write point exists + path / content controllable + validation bypassable + accessible / executable after write. Output `Confirmed Vulnerability`.
2. **Pending**: the write point and input mapping exist, but path validation bypass or post-write reachability evidence is insufficient. Output `Pending`.
3. **False Positive / No Risk**: the write point has no user input mapping, or path validation is strict and written files are unreachable. Output `False Positive` with the determination basis.

## Testing Recommendations and Minimal Trigger Conditions (Mandatory)

- **Minimal trigger conditions**:
  - a file write point exists (WriteAllText / StreamWriter / Save / Export)
  - the target path or write content contains user-controllable input
  - path validation is bypassable or missing, and written files are accessible
- **Test case suggestions**:
  - Happy Path: normal path writes succeed; out-of-bounds paths are intercepted
  - Boundary / ambiguity: re-concatenation bypass after Path.Combine, symlink following, temp file rename attacks, encoding difference bypasses
- Each hit output appends `hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Evidence References

- EVID_WRITE_CALLSITE
- EVID_WRITE_DESTPATH_JOIN_AND_NORMALIZATION
- EVID_WRITE_CONTENT_SOURCE_INTO_WRITE
- EVID_WRITE_EXECUTION_ACCESSIBILITY_PROOF

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (write point confirmation)**: the write call sites and triggering entries must be confirmed first.
- 🔴 **CHECKPOINT B (path and content confirmation)**: both the path source and content source mappings must be closed.
- 🔴 **CHECKPOINT C (post-write impact confirmation)**: whether written files are accessible, includable, or executable must be stated.
- 🛑 **STOP**: if post-write reachability evidence is missing, the conclusion is downgraded to `⚠️Pending Verification / Environment-Dependent`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| path source or content source unclosed | complete the path chain and content chain evidence separately | downgrade to `⚠️Pending Verification / Environment-Dependent` |
| post-write reachability unknown | supplement static resource / download / task consumption evidence | no high-risk confirmation; retain pending evidence |
| temp file and atomic replacement chain missing | fully trace the landing and rename / move flow | only output a conservative risk conclusion |

🔴 **STOP: when any fallback triggers, outputting "Confirmed High Risk" is forbidden.**

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

- Anti-pattern: judging high risk directly upon proving "files can be written". Correct practice: supplement post-write accessibility / executability evidence.
- Anti-pattern: ignoring atomic replacement and temp file rename paths. Correct practice: audit the complete landing chain.
- Anti-pattern: not distinguishing content controllability from path controllability. Correct practice: close both chains before drawing conclusions.
- Anti-pattern: strong conclusions with insufficient evidence. Correct practice: downgrade to `⚠️Pending Verification / Environment-Dependent`.

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

- vuln_audit/write_{timestamp}.md
- Optional: vuln_poc/write_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
