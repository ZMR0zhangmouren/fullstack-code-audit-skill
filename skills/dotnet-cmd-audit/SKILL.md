---
name: dotnet-cmd-audit
description: .NET command execution audit tool. Identifies Process.Start, shell argument concatenation, and script execution risks; outputs exploitability rating, PoC, and remediation recommendations.
---

# .NET Command Execution Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to command construction, shell selection, parameter passing, working directories, and environment variables
- If the project has secondary encapsulations such as ShellHelper, JobRunner, ScriptExecutor, or DeployManager, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement the host platform, external command runtime environment, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- call sites of Process.Start, ProcessStartInfo.FileName, Arguments, ArgumentList, UseShellExecute, and Verb
- indirect execution chains such as cmd.exe, powershell.exe, pwsh, bash, sh, wscript, cscript, msbuild, and dotnet tools
- paths where user input enters command names, arguments, working directories, environment variables, script file paths, or standard input
- whether ProcessStartInfo.ArgumentList is used to safely separate parameters, or the code falls back to whole command line string concatenation
- common external tool invocations such as file upload, export, compression, image processing, backup, git / svn / hg operations, ffmpeg, and wkhtmltopdf
- Windows vs Linux host differences, quoting rules, escaping rules, and handling differences of spaces and shell metacharacters
- whether mitigations such as low-privilege service accounts, containers, sandboxes, AppLocker, and ConstrainedLanguageMode truly exist

## Enumeration Rules (Mandatory Refinement)

- Enumerate all Process.Start, ProcessStartInfo, cmd / powershell / bash wrappers, and custom script execution services
- Search FileName, Arguments, ArgumentList, UseShellExecute, RedirectStandardInput, WorkingDirectory, and EnvironmentVariables first
- Enumerate common external command invocation businesses such as file conversion, backup and restore, git / svn, compression and extraction, image processing, PDF generation, diagnostic scripts, and CI / CD helpers
- For each execution point record: command construction method, parameter source, whether a whitelist was applied, host platform, service account permissions, and whether output is echoed

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Whole-string concatenation (Arguments)** | Read the `ProcessStartInfo.Arguments` construction source, confirming whether it comes from string concatenation / interpolation | externally controllable input participating in concatenation without constant prefix constraints → 🔴 high risk; fixed command + only user parameters controllable → 🟠 parameter slots to be verified further |
| **ArgumentList separation** | Confirm whether `ArgumentList.Add()` is used instead of whole-string concatenation, and check for whole-string mixing (such as `ArgumentList.Add($"-flag {input}")`) | used correctly with no whole-string mixing → ✅ safe; mixed usage or interpolation within a single argument slot → ⚠️ to be confirmed |
| **UseShellExecute** | Confirm the shell interpretation path of `FileName` and `Arguments` when `UseShellExecute = true` | user input entering `FileName` or shell metacharacters unescaped → 🔴 high risk; fixed command + fixed arguments → ✅ safe |
| **Command whitelist** | Read the whitelist implementation source, confirming whether it is fail-close (unknown commands refused execution) | fail-close (enumeration-outside refusal / exception) → ✅ safe; fail-open (allow by default / fallback) → ⚠️ bypassable; no whitelist → 🔴 high risk |
| **Path / working directory traversal** | Confirm whether `WorkingDirectory` or script paths come from user input and are confined to the base directory | user input can traverse to sensitive directories such as `/etc`, `C:\Windows`, and `.ssh` → 🔴 high risk; fixed paths or sandbox locking → ✅ safe |
| **Environment variable injection** | Confirm whether `EnvironmentVariables` is polluted by user input, especially `PATH`, `LD_PRELOAD`, and `COMSPEC` | user-controllable → 🔴 high risk; system-set only → ✅ safe |

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

1. externally controllable parameters enter concatenation / interpolation positions of `Arguments`, `FileName`, `WorkingDirectory`, or `EnvironmentVariables` directly, with no barrier validation
2. when `UseShellExecute = true`, user input enters `FileName` or parameter slots containing shell metacharacters
3. `ArgumentList` is misused (string interpolation exists within a single argument slot)
4. the command whitelist is `fail-open` or `silent-fallback`, and externally controllable input can bypass the whitelist into the Sink
5. in nested / recursive structures (such as multi-layer helper wrappers), the top level has validation but sub-levels do not perform equivalent validation

### Pending

1. the context shows a suspicious pattern (such as a `Process.Start` call), but the external input source is unclear (trace or call chain needs to be supplemented)
2. barrier functions (such as whitelists and path validation) exist, but whether the current branch invokes them and whether the return value is used cannot be confirmed
3. parameter passing in asynchronous / queue / event chains (such as Hangfire, Quartz, and message queues) is not closed
4. `ArgumentList` and whole-string concatenation are mixed, and the specific usage path at the current call site cannot be confirmed

### False Positive

1. the final command or identifier comes from fixed constants / enum mappings, and unknown input is refused execution (fail-close)
2. all recursive levels reuse the same command whitelist validator, and the whitelist is fail-close
3. parameters are safely separated via `ArgumentList`, and every parameter slot comes from fixed constants or verified whitelist outputs
4. a real sandbox / container isolation exists in the runtime environment, and user input cannot escape into the host command execution context

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct confirmed-exploitable command injection inputs (such as `; cat /etc/passwd`, `& whoami`, `$(id)`) and verify the vulnerability really exists
- **Negative testing**: construct inputs intercepted by barriers (such as out-of-whitelist commands, illegal path traversal, and overlong parameters) and verify the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Evidence References

- EVID_CMD_EXEC_POINT
- EVID_CMD_COMMAND_STRING_CONSTRUCTION
- EVID_CMD_USER_PARAM_TO_CMD_FRAGMENT

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (execution point confirmation)**: real command execution points (`Process.Start` / script entries) must be confirmed before risk judgments.
- 🔴 **CHECKPOINT B (parameter mapping confirmation)**: mapping evidence of `user input -> command fragment / parameter slot` must be given.
- 🔴 **CHECKPOINT C (host difference confirmation)**: Windows / Linux shell differences and quoting / escaping boundaries must be stated.
- 🛑 **STOP**: if the input-to-execution chain cannot be closed, the conclusion is downgraded to `⚠️Pending Verification`; outputting Confirmed Command Injection is forbidden.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| cannot prove user input enters command fragments / parameter slots | back-trace parameter binding to the `ProcessStartInfo` construction chain | mark `⚠️Pending Verification`, retaining the suspicious call site |
| ArgumentList and whole-string concatenation mixed, causing unclear judgment | evaluate parameter separation and shell interpretation paths separately | downgrade conservatively per the high-risk path; give no confirmed injection |
| host and account boundary evidence insufficient | supplement runtime account, container, and platform difference evidence | only output environment-dependent exploitation assumptions and verification steps |

🔴 **STOP: when any fallback triggers, outputting "Confirmed Command Injection" is forbidden.**

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

- Anti-pattern: equating command keyword hits with a valid injection. Correct practice: the `input -> parameter slot -> execution point` evidence chain must be closed.
- Anti-pattern: ignoring the difference between ArgumentList and whole-string concatenation. Correct practice: evaluate parameter separation and shell interpretation risks separately.
- Anti-pattern: ignoring the impact of runtime accounts and container isolation. Correct practice: supplement permission boundary and consequence scope analysis.
- Anti-pattern: strong conclusions without PoC conditions. Correct practice: annotate `⚠️Pending Verification / Environment-Dependent`.

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

- vuln_audit/cmd_{timestamp}.md
- Optional: vuln_poc/cmd_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
