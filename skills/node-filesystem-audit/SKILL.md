---
name: node-filesystem-audit
description: Node.js filesystem operation comprehensive audit tool. Identifies risks of user input participating in path.join/resolve across the fs.rename/unlink/chmod/access family, symlink following, and directory permission scope; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js Filesystem Operation Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to path input convergence, link following, TOCTOU, directory permissions, and delete / move / copy operations
- If the project has secondary encapsulations such as StorageManager, PathHelper, CleanupJob, or SyncService, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to associate trigger entries, path sources, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to associate background cleanup tasks, admin entries, and permission boundaries)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, container mounts, and runtime control plane)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **static-evidence-driven**: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Path sources of comprehensive operations such as `fs.rename` / `unlink` / `chmod` / `chown` / `access` / `mkdir` / `rm` / `cp` / `mkdtemp`
- Where user input participates in `path.join` / `path.resolve`: fixed root + controllable sub-segment versus fully controllable path
- Symlink following: the choice between `fs.stat` (follows) and `fs.lstat` (does not follow), and the timing of `fs.realpath` resolution
- TOCTOU caused by check-and-use separation: the time window between `fs.access` → `fs.writeFile`, or validate-then-rename
- Runtime permission scope: `chmod 0o777`, `process.umask(0)`, container-mounted directories, and non-root service accounts
- Delete / overwrite / cleanup logic as preconditions for chained exploitation: deleting lock files, replacing configurations, overwriting scheduled-task inputs
- **Specialty boundary**: single-point read, write, and archive extraction belong to node-file-read-audit / node-file-write-audit / node-archive-extract-audit respectively; this specialty covers the comprehensive operation surface, link behavior, and permission scope

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites of `rename(`, `unlink(`, `chmod(`, `chown(`, `access(`, `mkdir(`, `rm(`, `cp(`, `mkdtemp(`, `realpath(`, `symlink(`, `lstat(`, `stat(`
- Search directory semantics such as temp, cache, upload, export, log, backup, staging, working, and quarantine first
- For each operation point record: trigger entry, path source, `stat`/`lstat` choice, race window, and permission boundary
- Check whether the second argument onward of `path.join` directly concatenates sources from `req.params` / `req.query` / `req.body`
- Check whether `chmod` permission bits are overly broad, whether `process.umask` is set to 0, and whether operation directories are exposed on container-mounted volumes
- Check whether the same path is validated first and then rebuilt in multi-step flows (concatenation-point drift invalidating validation)
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real `fs` call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Path input convergence | Fixed root + file name allowlist | Check the sources of each `path.join` argument and the allowlist implementation | only the file name is controllable and the allowlist is fail-close → ✅ safe; controllable directory segment → ⚠️ to be confirmed; fully controllable path → 🔴 high risk |
| Symlink validation | `fs.lstat` + `isSymbolicLink()` rejection | Check whether `lstat` rather than `stat` validates the target before the operation | `lstat` rejecting links → ✅ safe; `stat` only (follows links) → ⚠️ bypassable; no validation → 🔴 high risk |
| TOCTOU protection | Atomic operations (`rename`) / `fstat` after open | Check whether an injectable time window exists between the validation point and the operation point | validation and operation atomic → ✅ safe; `access`-then-write with a window → ⚠️ to be confirmed |
| Permission scope minimization | Minimal `chmod` permissions, directory isolation, non-root execution | Check permission bits, the runtime account, and container mount boundaries | minimal permissions with directory isolation → ✅ safe; `0o777` or root execution → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to participate in filesystem comprehensive operation paths or permission adjustment
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

- `EVID_NODE_FS_OPERATION_POINT` + `EVID_NODE_FS_PATH_JOIN_CONTROL` + no effective Barrier: user input participates in `path.join` and reaches rename/unlink/chmod directly
- `EVID_NODE_FS_OPERATION_POINT` + `EVID_NODE_FS_SYMLINK_FOLLOW`: only `fs.stat` validation before the operation, and symlinks can redirect to sensitive paths
- `EVID_NODE_FS_PERMISSION_SCOPE` corroborates the impact: `chmod 0o777`, writable container-mounted directories, or root execution amplifying the operation consequences

### ⚠️Pending Verification

- The operation point exists, but the path source (fixed directory segment or request parameter) is unclear (call chain needs to be supplemented)
- `lstat` symlink validation exists, but whether the current branch invokes it and whether failures are refused cannot be confirmed
- Permission boundaries depend on the runtime environment (container mounts, umask, service account) and cannot be confirmed statically

### False Positive

- The path comes from fixed constants / enum mappings, and unknown input is explicitly rejected (fail-close)
- `fs.lstat` + `isSymbolicLink()` rejects links, and the operation is an atomic rename
- User input does not participate in the path, directory permissions are minimized, and the runtime account is restricted

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct requests that trigger `unlink` / `chmod` after a symlink points to `/etc/passwd`, verifying link following
- Construct directory-segment inputs with `..` participating in `path.join` and TOCTOU races (replacing the target after validation)
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct symlink-containing targets and verify explicit rejection by `lstat` validation
- Construct out-of-bounds paths and illegal permission adjustments, verifying rejection with no partial execution
- Verify out-of-allowlist file names are rejected

### Regression Testing

- Retest after remediation, confirming link validation and path convergence remain effective
- Retest junction and symlink resolution differences on both Windows and Linux
- Verify that newly added cleanup / sync tasks still keep atomic operations and minimal permissions

## Evidence References

- `EVID_NODE_FS_OPERATION_POINT`
- `EVID_NODE_FS_PATH_JOIN_CONTROL`
- `EVID_NODE_FS_SYMLINK_FOLLOW`
- `EVID_NODE_FS_PERMISSION_SCOPE`
- `EVID_NODE_CFG_RUNTIME_SETTING` (overlay evidence for runtime configuration such as directory sources / umask / container environment variables)

## Output

- `node/vuln_audit/filesystem_{timestamp}.md`
- `node/vuln_poc/filesystem_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
