---
name: node-file-read-audit
description: Node.js file read and path traversal audit tool. Identifies path concatenation, double-encoding, and directory escape risks in fs.readFile/readFileSync/createReadStream, res.sendFile/res.download, and express.static mount scope; outputs exploitability rating, PoC, and remediation recommendations.
---

# Node.js File Read Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to read path construction, normalization, base-directory locking, download endpoints, and static directory mounting
- If the project has secondary encapsulations such as FileService, AttachmentReader, DownloadController, or StaticResolver, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align read / download entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and static middleware mount positions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, static directory mounts, and runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **trace-gate**: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Path sources of `fs.readFile` / `readFileSync` / `createReadStream` / `fs.promises.readFile` read points
- Controllability of the `path` parameter of `res.sendFile` / `res.download` download and attachment endpoints, and whether the `root` option of `sendFile` is enabled
- `express.static` / `serve-static` / `koa-static` mount root directories, and `dotfiles` and `fallthrough` configurations
- `path.join(req.params.xxx)` / `path.join(req.query.xxx)` directory traversal, and missing prefix validation after `path.resolve`, or validate-then-concatenate ordering
- `decodeURIComponent` decode ordering and double-encoding (`%252e%252e%252f`) bypasses
- Whether read targets cover sensitive assets such as `.env`, keys, configurations, source code, logs, and uploaded files
- Whether read content further enters execution boundaries such as template rendering, configuration parsing, or dynamic `require`

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites of `readFile(`, `readFileSync(`, `createReadStream(`, `fs.promises.readFile`, `sendFile(`, `download(`, `express.static(`, `serve-static`, `koa-static`
- Search parameter names such as path, file, filename, template, view, config, download, export, doc, and attachment first
- For each read point record: target root directory, `path.join`/`path.resolve` concatenation logic, prefix validation position, encoding handling, output method, and authentication conditions
- Distinguish three modes: fully controllable path, controllable directory segment, and controllable file name only
- Check whether static middleware mount roots cover sensitive directories such as `.env`, source code, and logs, and whether the `dotfiles` configuration allows `/.env`-style requests
- Check whether `res.sendFile` passes the `root` option: when `root` is not passed, absolute paths from requests can hit directly
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real `fs` / `send` library call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Path normalization and base-directory locking | `path.resolve` + `startsWith(root + path.sep)` prefix validation | Check whether validation executes after normalization and whether the prefix comparison includes the path separator | locked after normalization and fail-close → ✅ safe; validate-then-concatenate or missing separator (`/app-evil` impersonating `/app`) → ⚠️ bypassable; no base-directory locking → 🔴 high risk |
| Path traversal filtering | Filtering `../`, `..\`, null bytes after `decodeURIComponent` | Check whether filtering executes after decoding and covers encoded and re-encoded variants | filtering after decoding covering all variants → ✅ safe; only string replacement of raw `../` → ⚠️ bypassable; no filtering → 🔴 high risk |
| Extension / file type whitelist | Extension allowlist + MIME validation | Read the whitelist implementation source, confirming whether unknown types are rejected | fail-close (out-of-whitelist rejection) → ✅ safe; blacklist mode → ⚠️ bypassable; no restriction → 🔴 high risk |
| Static directory boundary | `express.static` mount root selection, `dotfiles: 'deny'`, `fallthrough: false` | Check the relationship between the mount root and sensitive directories, and the dotfiles/fallthrough configuration | mount root isolated from sensitive directories and dotfiles denied → ✅ safe; mount root containing `.env` / source directories → 🔴 high risk |
| Authentication and resource ownership | Middleware authentication + resource ownership validation (anti-IDOR) | Check whether identity validation and resource ownership validation exist before reads | identity + ownership dual validation → ✅ safe; identity only without ownership → ⚠️ to be confirmed; no authentication → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter read path construction or a static directory exposure surface
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

- `EVID_NODE_FILE_READ_POINT` + `EVID_NODE_FILE_READ_PATH_CONSTRUCTION` + no effective `EVID_NODE_FILE_READ_TRAVERSAL_GUARD`
- User-controllable parameters are concatenated via `path.join` straight into `fs.readFile` / `res.sendFile`, with no post-resolve prefix validation
- `express.static` / `serve-static` mount root covers `.env`, source code, or log directories (`EVID_NODE_FILE_READ_STATIC_ROOT`)
- Prefix validation executes before decoding and can be bypassed by double encoding (`%252e%252e%252f`) or absolute paths without `root`

### ⚠️Pending Verification

- The context shows a suspicious pattern (e.g., `fs.readFile(path.join(base, req.query.file))`), but the external input source is unclear (trace or call chain needs to be supplemented)
- A prefix-validation function exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
- The static directory mount root depends on runtime configuration (e.g., `process.env.STATIC_ROOT`), and the boundary cannot be confirmed statically

### False Positive

- The final path comes from fixed constants / enum mappings, and unknown paths are refused reads (fail-close)
- Post-`path.resolve` prefix validation is fail-close, with an extension whitelist and resource ownership validation
- User input affects only the file name (no directory segments), and the file name passes strict allowlist validation

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct path traversal inputs: `../../../etc/passwd`, `..%2f..%2fetc/passwd`, double-encoded `%252e%252e%252f`, backslashes `..\..\windows\win.ini`
- Construct absolute-path passthrough (`path=/etc/passwd`) and dotfile requests (`/.env`) to verify static directory boundaries
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct inputs intercepted by barriers: out-of-base-directory paths, out-of-whitelist extensions, overlong paths
- Verify the interception effect of post-resolve prefix validation against encoded variants and symlinks
- Verify `/.env`-style requests are explicitly rejected under the `dotfiles: 'deny'` configuration

### Regression Testing

- Retest after remediation, confirming base-directory locking and prefix validation remain effective
- Retest double-encoding, symlink, case, and other variants, confirming no new bypass paths were introduced
- Verify that newly added mount directories or download endpoints still keep base-directory locking fail-close

## Evidence References

- `EVID_NODE_FILE_READ_POINT`
- `EVID_NODE_FILE_READ_PATH_CONSTRUCTION`
- `EVID_NODE_FILE_READ_TRAVERSAL_GUARD`
- `EVID_NODE_FILE_READ_STATIC_ROOT`
- `EVID_NODE_CFG_SECURITY_SWITCH` (overlay evidence for `dotfiles` / `fallthrough` / mount root security switches)

## Output

- `node/vuln_audit/file-read_{timestamp}.md`
- `node/vuln_poc/file-read_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
