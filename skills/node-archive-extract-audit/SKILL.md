---
name: node-archive-extract-audit
description: Node.js archive extraction path traversal (Zip Slip) audit tool. Identifies landing-escape risks caused by entryName containing ../, absolute paths, or drive letters in unzipper/adm-zip/yauzl/extract-zip/tar-stream extraction chains; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js Archive Extraction Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to archive entry names, extraction target directories, path sanitization, symlink entries, and downstream consumption chains
- If the project has secondary encapsulations such as ArchiveService, PackageImporter, PluginInstaller, or BackupRestore, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, static directories, plugin/template directories, and runtime control plane)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Call sites and target-directory sources of `unzipper.Extract` / `adm-zip`'s `extractAllTo` / `extractEntryTo` / `yauzl` entry streams / `extract-zip` / `tar-stream` entries
- Whether `entryName` / `entry.fileName` / tar header `name` contains `../`, leading-`/` absolute paths, drive letters (`C:\`), or UNC (`\\host\share`) fragments
- Whether `path.join(root, entryName)` is followed by `path.resolve` + prefix validation, and whether the validation executes before normalization
- Symlink / hardlink entries (tar symlink/hardlink) and the overwrite behavior of directory-type entries
- Whether extraction targets are in reachable surfaces such as `public/`, plugin directories, template directories, or downloadable directories
- Whether extraction results are consumed by downstream chains such as dynamic `require`, template rendering, or configuration reads
- The complete chain of upload archive → staging → extraction → landing → consumption (upload filtering and limits belong to node-file-upload-audit)

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites of `unzipper`, `Extract({ path`, `adm-zip`, `extractAllTo(`, `extractEntryTo(`, `yauzl`, `extract-zip`, `tar-stream`, `decompress(`, `entry(`
- Search business semantics such as extract, unzip, untar, archive, restore, import, theme, plugin, and backup first
- For each extraction point record: archive source, target directory, `entryName` handling, final resolved path, and post-extraction reachable surface
- Distinguish library built-in protections from project-built sanitization, and confirm the actually effective version (check `package-lock.json` / `node_modules` against known Zip Slip fix records)
- Check whether entry-name sanitization is only string replacement of `../` (bypassable via `....//` and encoded variants) rather than post-resolve validation
- Check whether zip / tar symlink entries are rejected, or whether a final path validation is performed after creation
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real extraction library call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Entry path sanitization | Filtering `../`, leading `/`, drive letters, null bytes | Check whether sanitization executes per entry before `path.join` and covers `....//` and encoded variants | per-entry validation after normalization → ✅ safe; only string replacement of raw `../` → ⚠️ bypassable; no sanitization → 🔴 high risk |
| Target root prefix validation | `path.resolve(root, entryName)` + `startsWith(root + path.sep)` | Check whether validation executes after resolve and includes the path separator | locked after resolve and fail-close → ✅ safe; missing separator (`/app-evil` impersonating `/app`) → ⚠️ bypassable; direct `path.join` landing → 🔴 high risk |
| Entry type restriction | Rejecting symlink/hardlink/device entries | Check the extraction library's handling of entry types and project-side filtering | non-regular-file entries rejected → ✅ safe; symlink entries created directly → 🔴 high risk; behavior depends on library version → ⚠️ to be confirmed |
| Target directory isolation | Extracting into non-web-reachable directories | Check the relationship between the extraction root and `public/`, plugin, template, and configuration directories | non-web directory with no consumption chain → ✅ safe; landing in a reachable surface → 🔴 high risk |
| Overwrite policy | Conflict rejection / renaming / in-whitelist overwrite | Check whether same-name entry overwrite logic can replace existing configurations or scripts | conflict rejection or renaming → ✅ safe; silently overwriting any existing file → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable archive entries appear to enter the extraction landing path without sanitization
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

- `EVID_NODE_ARCHIVE_EXTRACT_POINT` + `EVID_NODE_ARCHIVE_ENTRY_PATH_SANITIZE` missing: `entryName` passes straight into `path.join` for landing
- `EVID_NODE_ARCHIVE_EXTRACT_POINT` + `EVID_NODE_ARCHIVE_ZIP_SLIP_GUARD` validation bypassable: absolute paths, drive letters, or `....//` variants escape the base directory
- The extraction landing point is in `public/`, a plugin or template directory, and entries can overwrite existing configurations / scripts

### ⚠️Pending Verification

- The extraction point exists, but the archive source (user upload / remote pull) is unclear (trace or call chain needs to be supplemented)
- A sanitization or prefix-validation function exists, but whether the current entry branch invokes it cannot be confirmed
- Symlink entry behavior depends on the extraction library version, and the locked file version differs from the actually installed version

### False Positive

- Every entry passes prefix validation after `path.resolve` and fails closed; out-of-bounds entries are explicitly rejected
- The extraction library's built-in protection is confirmed effective (pinned version has no known Zip Slip) + project-side secondary validation
- The archive content is fixed-generated by the server and entry names contain no external input

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct zip/tar packages containing entries such as `../../../.ssh/authorized_keys`, absolute path `/etc/cron.d/pwn`, and drive letter `C:\Temp\evil`
- Construct `....//....//` and double-encoded variant entries, and tar symlink entries, to verify escape and link following
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct archives with normal entries; verify extraction succeeds and files land within the target root
- Construct out-of-bounds entries; verify the prefix validation explicitly rejects them and aborts the extraction flow
- Verify symlink entries are rejected under type restrictions

### Regression Testing

- Retest after remediation, confirming prefix validation remains effective against all escape variants
- Retest after upgrading the extraction library version, confirming built-in protections and project validation stack effectively
- Verify drive letters, backslashes, and path separator differences on both Windows and Linux

## Evidence References

- `EVID_NODE_ARCHIVE_EXTRACT_POINT`
- `EVID_NODE_ARCHIVE_ENTRY_PATH_SANITIZE`
- `EVID_NODE_ARCHIVE_ZIP_SLIP_GUARD`

## Output

- `node/vuln_audit/archive-extract_{timestamp}.md`
- `node/vuln_poc/archive-extract_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
