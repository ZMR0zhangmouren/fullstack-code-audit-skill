---
name: node-file-upload-audit
description: Node.js file upload audit tool. Identifies risks such as unsanitized file names in multer/busboy/formidable, controllable landing directories, and missing fileFilter/limits; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js File Upload Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to file upload, file name parsing, landing paths, and file filtering limits
- If the project has secondary encapsulations such as UploaderService, FileStorage, or AttachmentHelper, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entries, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, serialization configuration, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **static-evidence-driven**: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Unsanitized `filename` in multer/busboy/formidable (`../` traversal)
- Controllable `dest`/`uploadDir` causing landing directory escape
- Missing or loose `fileFilter`/`limits`
- Executable extensions (`.php`, `.jsp`, `.js`, `.sh`, `.exe`, etc.) landing in statically accessible directories
- Original file names echoed back directly or referenced again by the frontend without renaming

## Enumeration Rules (Mandatory Refinement)

- Enumerate all call sites and configuration objects of `multer(`, `busboy`, `formidable`, `diskStorage`, `filename:`, `dest:`, `uploadDir`, `fileFilter`, `limits`
- For each upload receiving point record: middleware type, landing directory, file name generation strategy, fileFilter whitelist, limits size/count restrictions, and static directory mapping relationships
- Distinguish direct landing (`dest`/`uploadDir`) from custom storage (`diskStorage({ destination, filename })`)
- Check whether the `filename` callback uses `file.originalname` directly or other unsanitized external input
- Check whether `dest`/`destination` concatenates user-controllable paths or relative paths
- Check whether `fileFilter` exists, the extension/MIME validation strategy, and whether it is fail-close (whitelist mode)
- Check whether `limits.fileSize`, `limits.files`, etc. are configured and can effectively intercept over-limit requests
- Check whether the landing directory is under the web root (e.g., `public/`, `static/`, `uploads/`) and can be directly requested for execution
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real multer/busboy/formidable configuration points

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| File name regeneration | Random name + whitelist extension (UUID / hash + `.ext`) | Check whether the `filename` callback discards the original name and uses a safe random name | random name with extension whitelist → ✅ safe; original name landing directly or extension blacklist → 🔴 high risk |
| fileFilter whitelist | Extension whitelist / MIME type validation | Read the fileFilter source, confirming whether it is fail-close (unknown types rejected) | fail-close (whitelist) → ✅ safe; blacklist / MIME-only validation → ⚠️ bypassable; no fileFilter → 🔴 high risk |
| limits size/count restrictions | `limits.fileSize`, `limits.files`, `limits.fields` | Check whether the limits configuration is consistent with backend enforcement | reasonably configured and enforced by the backend → ✅ safe; missing configuration or frontend-only validation → ⚠️ to be confirmed |
| Landing directory isolated from web root | Writing into non-web-accessible directories; static directories do not parse scripts | Check the relationship between `dest`/`uploadDir`/`destination` and the web root | non-web directory or script execution forbidden in static directories → ✅ safe; executable extensions landing in web-accessible directories → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter file names, landing paths, or file filtering configuration
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

- `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG` + `EVID_NODE_UPLOAD_FILENAME_SANITIZE` + no effective Barrier
- Externally controllable parameters enter `filename`/`dest`/`uploadDir` directly without path normalization or random renaming
- Executable-extension files land in web-accessible directories and can be directly requested for execution
- `fileFilter` is a blacklist mode or MIME-only validation, bypassable via double extensions, truncation, null bytes, etc.

### ⚠️Pending Verification

- The context shows a suspicious pattern (e.g., `multer({ dest: req.query.dir })`), but the external input source is unclear (trace or call chain needs to be supplemented)
- Barrier functions (e.g., file name randomization, extension whitelist) exist, but whether the current branch invokes them and whether the return value is used cannot be confirmed
- The relationship between the landing directory and the web root depends on runtime configuration (e.g., `process.env.UPLOAD_DIR`), and isolation cannot be confirmed statically

### False Positive

- File names are fully server-generated random names, and extensions come from a fixed whitelist
- The landing directory is a non-web-accessible directory, and static directories do not parse scripts
- `fileFilter` is a fail-close whitelist, explicitly rejecting unknown extensions
- Uploaded files are only streamed for download and do not enter any execution / rendering context

## Testing Recommendations (Mandatory)

### Positive Testing

- Construct upload requests with file names containing `../` / `..\` / null bytes / double extensions (`.jpg.php`)
- Construct upload requests exceeding `limits.fileSize` / `limits.files`
- Upload files with executable script extensions into web-accessible directories and attempt direct requests
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Construct whitelist-extension files and verify normal landing
- Construct illegal-extension / oversized files and verify explicit rejection by barriers
- Verify that the original file name no longer participates in path resolution or echoing after random renaming

### Regression Testing

- Retest after remediation, confirming the fileFilter whitelist, file name regeneration, and landing directory isolation remain effective
- Retest the over-limit rejection logic of `limits`, confirming no bypass was introduced
- Verify that adding new file types to the whitelist remains fail-close

## Evidence References

- `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG`
- `EVID_NODE_UPLOAD_FILENAME_SANITIZE`
- `EVID_NODE_UPLOAD_FILTER_LIMITS`
- `EVID_NODE_UPLOAD_ACCESSIBILITY`

## Output

- `node/vuln_audit/file-upload_{timestamp}.md`
- `node/vuln_poc/file-upload_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
