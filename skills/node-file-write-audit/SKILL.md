---
name: node-file-write-audit
description: Node.js arbitrary file write audit tool. Identifies sensitive file overwrite risks caused by controllable paths and content in fs.writeFile/writeFileSync/appendFile/createWriteStream and multer landing callbacks; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js File Write Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to path concatenation, file name generation, overwrite modes, write content sources, and post-write consumption chains
- If the project has secondary encapsulations such as FileStore, ConfigWriter, ExportService, or ReportGenerator, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align write entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, accessible directories, and runtime control plane)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Write points of `fs.writeFile` / `writeFileSync` / `appendFile` / `createWriteStream` / `fs.promises.writeFile`
- The `diskStorage({ destination, filename })` callback path and file name generation of `multer` (upload filtering and limits belong to node-file-upload-audit; this specialty focuses on landing paths and coverage)
- How user input enters target paths, file names, directory segments, or extensions
- Write content sources: `req.body`, template strings, remotely fetched content, deserialized data
- `flag` configurations: `'w'` direct overwrite, `'ax'`/`'wx'` conflict refusal, append-mode pollution of existing files
- Whether controllable write extensions / landing points can overwrite sensitive files such as `.env`, `package.json`, crontab, templates, and `authorized_keys`
- Post-write consumption chains: static resources, download endpoints, dynamic `require`, template rendering, pm2 / scheduled tasks

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites of `writeFile(`, `writeFileSync(`, `appendFile(`, `createWriteStream(`, `fs.promises.writeFile`, `outputFile(`, `move(`, `copy(`
- Search target path fields such as dest, path, target, filename, output, export, report, template, and config first
- For each write point record: path source, content source, `flag` configuration, overwrite conflict policy, and post-write accessible surface
- Distinguish two independent evidence chains — path controllability and content controllability; strong conclusions require both chains closed
- Check whether `fs-extra` wrappers such as `outputFile` / `move` / `copy` pass user input through to the real `fs` calls
- Check whether file name concatenation and `destination` directory selection in multer landing callbacks use original file names or request parameters
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real `fs` call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Path normalization and base-directory locking | `path.resolve` + prefix validation (including `path.sep`) | Check the ordering of concatenation, normalization, and validation, and separator handling | validation after resolve and fail-close → ✅ safe; re-concatenating raw input after validation → ⚠️ bypassable; no base-directory locking → 🔴 high risk |
| File name regeneration / whitelist | Random name (UUID/hash) + fixed extension | Check whether the file name discards raw input and whether the extension comes from a whitelist | random name + whitelist → ✅ safe; original name or extension landing directly → 🔴 high risk |
| Overwrite protection | `flag: 'ax'` / `'wx'`, conflict refusal policy | Check the write flag and existing-file conflict handling logic | `'ax'`/`'wx'` failing on conflict → ✅ safe; `'w'` direct write to controllable path → 🔴 high risk; `access`-then-write (TOCTOU) → ⚠️ to be confirmed |
| Content and extension control | Extension allowlist, content schema validation | Check whether write content is validated and whether the extension is fixed | content validation + fixed extension → ✅ safe; content and extension both decided by the request → 🔴 high risk |
| Post-write reachability isolation | Landing in non-web directories; static directories not parsing scripts | Check the relationship between the landing point and the web root, template directories, and plugin directories | non-web directory with no consumption chain → ✅ safe; landing in an executable / renderable directory → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter write path construction or write content mapping
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

- `EVID_NODE_FILE_WRITE_POINT` + `EVID_NODE_FILE_WRITE_PATH_CONSTRUCTION` + no effective `EVID_NODE_FILE_WRITE_OVERWRITE_PROTECTION`
- User-controllable paths can overwrite sensitive files such as `.env`, `package.json`, templates, or crontab, with `flag: 'w'` direct write
- Write content and extension are both decided by the request (`EVID_NODE_FILE_WRITE_CONTENT_CONTROL`), and the landing point can be consumed by static resources, template rendering, or dynamic `require`
- Prefix validation exists but re-concatenates raw input after validation, bypassable via encoded variants or symlinks

### ⚠️Pending Verification

- The write point exists, but either the path source or the content source chain is unclear (trace or call chain needs to be supplemented)
- Overwrite protection (e.g., `'ax'` flag, conflict checks) exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
- Post-write reachability depends on runtime configuration (e.g., `process.env.OUTPUT_DIR` pointing to a web directory)

### False Positive

- Both path and content come from fixed constants / whitelists, and unknown input is explicitly rejected (fail-close)
- The target file name is server-generated randomly, and `'ax'`/`'wx'` fails on conflict
- The written file is in a non-web directory with no consumption chain such as template rendering / dynamic `require` / scheduled tasks

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct write requests with `../` overwriting `.env` and `package.json`, verifying the target files are actually replaced
- Construct writes of `.js` files into static executable directories and trigger them via requests, or write template files and then trigger rendering
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct out-of-base-directory paths and out-of-whitelist extensions, verifying explicit rejection
- Verify `flag: 'ax'` fails the write when the target exists, with no partial-write residue
- Verify that original file names no longer participate in landing paths after random renaming

### Regression Testing

- Retest after remediation, confirming base-directory locking and overwrite protection remain effective
- Retest the temp-file + `fs.rename` atomic replacement chain, confirming no new bypass paths were introduced
- Verify that newly added export / report features keep dual path-and-content validation

## Evidence References

- `EVID_NODE_FILE_WRITE_POINT`
- `EVID_NODE_FILE_WRITE_PATH_CONSTRUCTION`
- `EVID_NODE_FILE_WRITE_OVERWRITE_PROTECTION`
- `EVID_NODE_FILE_WRITE_CONTENT_CONTROL`
- `EVID_NODE_CFG_RUNTIME_SETTING` (overlay evidence for landing directories / output paths coming from `process.env`)

## Output

- `node/vuln_audit/file-write_{timestamp}.md`
- `node/vuln_poc/file-write_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
