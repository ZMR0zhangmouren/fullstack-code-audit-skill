---
name: node-supply-chain-audit
description: Node.js supply chain security audit tool. Based on npm audit --json / osv-scanner output and lockfile drift analysis, identifies known CVE hits, postinstall scripts, typosquatting, and dependency confusion risks; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js Supply Chain Security Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- **Use `shared/NODE_SUPPLY_CHAIN_CRITERIA.md` as the source of truth for this specialty's determination criteria (the three-tier criteria of Confirmed / Pending Confirmation / False Positive)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to dependency declarations, lockfiles, package source configuration, and install scripts
- If the project has a private registry, monorepo workspaces, or an internal package repository, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align affected entries and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack dependency surface and build-artifact linkage analysis)
- This specialty is **static-evidence-driven**: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions; however, the runtime reachability determination must combine route-trace and build-artifact analysis (criteria see `shared/NODE_SUPPLY_CHAIN_CRITERIA.md`)
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- Tool initial screening: `npm audit --json` / `osv-scanner` output (`EVID_NODE_SUPPLY_TOOL_OUTPUT`)
- Lockfile (package-lock.json / yarn.lock / pnpm-lock.yaml) versus package.json drift, and missing lockfiles
- Install scripts: `preinstall` / `postinstall` / `prepare` executing arbitrary commands
- Typosquatting characteristics: package names highly similar to popular packages, registries with no publication history
- Dependency confusion: internal package names without scoped private-source mapping, susceptible to public-registry squatting
- Direct / transitive dependency reachability: whether the vulnerable package is loaded by runtime `require` / `import`, or is devDependencies only

## Enumeration Rules (Mandatory Refinement)

- Enumerate dependency declarations: `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `.npmrc`
- rg searches: `dependencies`, `devDependencies`, `scripts`, `preinstall`, `postinstall`, `prepare`, `registry`, `require(`, `import `
- Tool commands: `npm audit --json`, `osv-scanner --format json`; when tools are unavailable, record the reason and compare OSV/GHSA package by package against the lockfile, labeled `Pending Verification`
- For each hit package record: package name, locked version, CVE/GHSA, affected range, fixed version, direct / transitive, and runtime reachability
- Typosquatting / dependency confusion uses registry popularity and provenance declarations as the baseline; hits are labeled `Pending Verification` and require manual review
- If dependencies go through monorepo workspaces or alias resolution, they must be unwrapped layer by layer to the real installation source

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Tool initial screening | `npm audit --json` / `osv-scanner` | Run the tools and retain the raw JSON output | parseable output produced → ✅ screening evidence; tools unavailable → record the reason and fall back to manual comparison ⚠️ |
| Version pinning | package-lock.json / yarn.lock / pnpm-lock.yaml | Compare lockfile against package.json range drift | lockfile committed with no drift → ✅ safe; missing or drift → 🔴 high risk |
| Runtime reachability | `require` / `import` load paths and build artifacts | Trace whether the vulnerable package enters a runtime load path | runtime-reachable with no mitigation → conclusion stands; devDependencies only and not in build output → downgraded |
| Trusted source | `.npmrc` registry / scope mapping | Verify private scopes and intranet source mappings, and package name spellings | scope explicitly mapped → ✅ safe; no declaration with similar name → ⚠️ typosquatting / confusion suspicion |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: a vulnerable dependency appears to exist in the lockfile and may be reachable on a runtime load path
- `Pending`: the context shows a suspicious pattern, but the external input source, barrier behavior, or call chain is unclear
- `False Positive`: the input comes from fixed constants / enum mappings, or the barrier has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found that the vulnerable dependency is reachable on a runtime load path with no effective mitigation → `Confirmed Vulnerability`
- Fixed whitelist mapping / fail-close evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_SUPPLY_TOOL_OUTPUT` + lockfile version hits a known CVE/GHSA + the dependency is reachable on a runtime load path + no effective mitigation (fixed version / alternative package)
- `EVID_NODE_SUPPLY_TOOL_OUTPUT` + an install-time script such as `postinstall` hits arbitrary command execution or downloader characteristics

### ⚠️Pending Verification

- The intersection between the CVE-affected version range and the locked version is unclear; manual comparison against the fixed version is needed
- Runtime reachability evidence is insufficient (missing `require`/`import` call chain or build-artifact analysis)
- Typosquatting / dependency confusion suspicion hit; registry popularity and provenance declarations not yet reviewed

### False Positive

- The locked version is above the fixed version and no longer affected by the CVE
- The vulnerable package is devDependencies only and does not enter build artifacts or the runtime
- The package name is spelled correctly with the scope mapped to an intranet source, excluding typosquatting and dependency confusion suspicion

## Testing Recommendations (Mandatory)

### Positive Testing

- Reproduce the `npm audit --json` hit for a locked version with a known CVE and associate it with the runtime call chain
- Construct a `postinstall` downloader script to verify the install-time execution surface
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Fixed versions and devDependencies-only scenarios should output `False Positive` with determination basis attached
- When the scope private-source mapping is correct, same-named public-registry packages cannot install successfully

### Regression Testing

- Retest after remediation: the lockfile has no version drift and no new install scripts
- After tool version upgrades, verify that hit range criteria have not changed

## Evidence References

- `EVID_NODE_SUPPLY_TOOL_OUTPUT`

## Output

- `node/vuln_audit/supply-chain_{timestamp}.md`
- `node/vuln_poc/supply-chain_{timestamp}.md` (supply chain PoCs are mostly version / provenance evidence and reproduction steps: CVE/GHSA IDs, affected ranges, locked versions, install script reproduction commands; not runtime request templates)
