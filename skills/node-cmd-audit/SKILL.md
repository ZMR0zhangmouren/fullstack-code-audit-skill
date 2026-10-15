---
name: node-cmd-audit
description: Node.js command execution audit tool. Identifies concatenation and shell interpretation risks in child_process.exec/execSync/spawn(shell:true)/execFile; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js Command Execution Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to command construction, shell selection, parameter passing, and parameter array-ification
- If the project has secondary encapsulations such as ShellHelper, CommandRunner, or ScriptExecutor, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, serialization configuration, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- `child_process.exec` / `execSync` concatenation
- `shell:true` in `spawn` / `execFile`
- Missing parameter array-ification

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites of `child_process`, `exec(`, `execSync(`, `spawn(`, `execFile(`, `fork(`, `shell: true`, `shell:true`
- For each execution point record: command construction method, parameter source, whether a whitelist was applied, whether shell interpretation is used, host platform, and service account privileges
- Distinguish whole-string concatenation (`exec(command)`) from parameter array-ification (`execFile(file, args)` / `spawn(command, args, {shell:false})`)
- Record the explicit value of `options.shell`, its default behavior, and whether user input enters the `command` string or `args` array elements
- Identify scenarios where parameter array-ification is misused: string interpolation within a single argument slot, or `shell:true` re-enabling shell interpretation
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real `child_process` call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Parameter array-ification | `child_process.execFile` / `spawn` default `shell:false` | Check whether the call site uses array arguments with shell interpretation disabled | array-ified and `shell:false`, no single-argument interpolation → ✅ safe; still using `exec` / `execSync` or explicit `shell:true` → 🔴 high risk |
| Command whitelist | Command / argument allowlist | Read the whitelist implementation source, confirming whether it is fail-close (unknown commands refused) | fail-close (enumeration-outside refusal / exception) → ✅ safe; fail-open (allow by default / fallback) → ⚠️ bypassable; no whitelist → 🔴 high risk |
| Shell disabled by default | `options.shell` of `spawn` / `execFile` | Check the explicit value and default behavior of `options.shell` | `shell:false` or no shell option → ✅ safe; `shell:true` with controllable parameters → 🔴 high risk |
| Input validation | joi / zod / regex whitelist | Check whether the validator covers the command string / parameter sources and rejects illegal input | fail-close validation → ✅ safe; validation bypassable via truncation / encoding / metacharacters → ⚠️ to be confirmed; no validation → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter command string concatenation or a shell-interpreted parameter slot
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

- `EVID_NODE_CMD_EXEC_POINT` + `EVID_NODE_CMD_USER_PARAM_TO_CMD` + no effective Barrier
- Externally controllable parameters enter command string concatenation positions directly, with no barrier validation
- `spawn` / `execFile` explicitly set `shell:true` and user input enters the command or a parameter slot containing shell metacharacters
- The command whitelist is fail-open or silent-fallback, and externally controllable input can bypass the whitelist into the Sink

### ⚠️Pending Verification

- The context shows a suspicious pattern (e.g., a `child_process.exec` call), but the external input source is unclear (trace or call chain needs to be supplemented)
- A barrier function (e.g., whitelist, input validation) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
- Parameter array-ification and whole-string concatenation are mixed, but the specific usage path at the current call site cannot be confirmed

### False Positive

- Parameters are fully static or the allowlist is non-bypassable (fail-close)
- `execFile` / `spawn` parameter array-ification is used with `shell:false`, and every parameter slot comes from fixed constants or verified whitelist outputs
- The command string comes from fixed constants / enum mappings, and unknown input is refused execution (fail-close)

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct confirmed-exploitable command injection inputs: `; cat /etc/passwd`, `&& whoami`, `$(id)`, `| dir`, `` `whoami` ``
- Verify command execution when user parameters enter `exec` / `execSync` whole strings or `shell:true` scenarios
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct inputs intercepted by barriers: out-of-whitelist commands, illegal shell metacharacters, overlong parameters
- Verify shell metacharacters are treated as ordinary parameters under parameter array-ification / `shell:false`
- Verify joi / zod / regex whitelists explicitly reject illegal input

### Regression Testing

- Retest after remediation, confirming barriers remain effective
- Retest `execFile` / `spawn` parameter array-ification and `shell:false` configuration, confirming no new bypass paths were introduced
- Verify the command whitelist remains fail-close when new commands are added

## Evidence References

- `EVID_NODE_CMD_EXEC_POINT`
- `EVID_NODE_CMD_STRING_CONSTRUCTION`
- `EVID_NODE_CMD_USER_PARAM_TO_CMD`
- `EVID_NODE_CMD_ARG_ARRAY_OR_ALLOWLIST`

## Output

- `node/vuln_audit/cmd_{timestamp}.md`
- `node/vuln_poc/cmd_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
