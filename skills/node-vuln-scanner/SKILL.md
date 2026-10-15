---
name: node-vuln-scanner
description: Node.js npm dependency vulnerability scanner. Enumerates package.json and lockfiles, producing a list of dependency vulnerabilities, typosquatting, lifecycle scripts, protocol risks, and version drift.
---

# Node.js npm Dependency Vulnerability Scan

## Shared Grabber Index Reference

- The enumeration keywords, priority targets, and record criteria of this skill take `skills/shared/NODE_AUDIT_GRABBER_INDEX.md` as the single source of truth, focusing on the "Dependency Manifests" section of its "Security Configuration Grabbers".
- Paths and artifact naming follow the `node/` subtree conventions in `skills/shared/IO_PATH_CONVENTION.md`.
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced.
- Exclusion rules: `node_modules/` is not part of the source-code audit surface; lockfiles such as `package-lock.json`, `yarn.lock`, and `pnpm-lock.yaml` must be included in the supply chain audit surface.

## Input Dependencies

User provides:

- `node_source_path`: Node.js project, repository root, or a directory containing `package.json` (required).
- `package.json`: project dependency declaration file (required).
- lockfile: at least one of `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` (strongly recommended; when missing, version drift and locked-version determination are downgraded to `Pending Verification`).
- `node/stack_detect/stack_detect_{timestamp}.md`: Phase 0 tech-stack detection result (optional, used to confirm the package manager type and workspace structure).
- Optional: `offline_audit_report` (a user-injected offline scan report — `yarn audit --json` output; when provided, parse (package, version, vulnerability ID, severity) and join with the local dependency manifest into the conclusions, listing "hits from the injected report" and "hits from built-in knowledge" as two separate groups in the artifact)

## Enumeration Rules (Mandatory Refinement)

1. **Dependency manifest enumeration**:
   - Fully read `dependencies`, `devDependencies`, and `optionalDependencies` in `package.json` (recording `peerDependencies` is recommended).
   - Each record must include: name, version range, and the locked version in the lockfile.
   - When the lockfile is missing, the locked version is marked `N/A (Pending Verification)`.

2. **Known vulnerability comparison**:
   - When the environment allows, running `npm audit --json` or `osv-scanner` is recommended (as external tool suggestions; the skill itself contains no code).
   - When external vulnerability databases are inaccessible or tools cannot run, compare manually against an offline CVE / GHSA list and label `Pending Verification`.
   - Every hit vulnerability must record: CVE / GHSA ID, affected version range, current / locked version, severity, and the recommended fixed version.

3. **Typosquatting / dependency confusion**:
   - Identify dependencies whose names are highly similar to mainstream npm packages (character substitution, character insertion / deletion, case confusion, scope-prefix forgery).
   - Similarity determination is based on npm registry popularity (download counts / publication time / maintenance activity): unknown dependencies highly similar to high-popularity package names must be labeled `Pending Verification` and manually reviewed; querying the registry or referencing same-source package distributions in the lockfile is allowed to assist the judgment.
   - Identify scoped packages (`@scope/pkg`) without a locked registry (missing `registry=` or `@scope:registry=` configuration in `.npmrc`).
   - Hit items are annotated with `risk level` and `manual review recommendation`.

4. **Lifecycle scripts**:
   - List in full the `preinstall`, `install`, and `postinstall` entries of `scripts` in `package.json`.
   - Manually review each lifecycle script, identifying sensitive behaviors such as downloading remote scripts, compiling native modules, modifying system paths, and executing external commands.
   - Also record lifecycle scripts in `node_modules/<pkg>/package.json` of each dependency (if the lockfile carries this information or installed dependencies are accessible).

5. **Protocol risks**:
   - Enumerate dependencies using non-https protocols in dependency declarations or lockfiles:
     - `git+http://` protocol dependencies (plaintext transmission, high risk, treated the same as `http://`).
     - `git+https://` / `git+ssh://` protocol dependencies (transport encryption; source trustworthiness validation needed; conclusions may be below `Pending Verification` but the provenance declaration location must be recorded).
     - `http://` protocol dependencies.
     - `file:` protocol dependencies (local path references).
   - Record the protocol type, provenance declaration location, and whether it can be replaced with a secure source.

6. **Version drift**:
   - Compare the version ranges in `package.json` against the locked versions in the lockfile item by item.
   - List all items where the `package.json range` and the `lockfile locked` version disagree, including:
     - the lockfile version exceeding the declared range (a sign of lockfile corruption / manual tampering).
     - wildcard ranges (`*`, `x`, empty) making the locked version uncontrollable.
   - Additionally record `the lockfile not updated for a long time, leaving the locked version significantly behind the latest resolvable version within the range` as a **maintainability risk** (not a range / locked mismatch).

## Determination Rules (Mandatory Refinement)

| Conclusion | Determination Condition | Record Requirements |
| ---- | ---- | ---- |
| **Confirmed** | A known CVE / GHSA hits the current locked version, corroborated by a lockfile or tool output | Record CVE / GHSA, affected versions, current version, fixed version, source_file:line |
| **Pending Verification** | External scanning tools cannot run, the lockfile is missing, the version range cannot be parsed, or a typosquatting hit needs manual review | Explicitly label `Pending Verification`, recording missing evidence and evidence-supplementing actions |
| **False Positive / Not Applicable** | The dependency is pure type declarations with no runtime impact, the vulnerability affects only unused platforms / APIs, or the confirmed version is outside the affected range | Record the exclusion basis; writing only "no risk" is forbidden |

- When any protocol risk (`git+http://`, `http://`, `file:`) is hit and provenance trustworthiness cannot be proven, the conclusion must not be lower than `Pending Verification`.
- When a lifecycle script downloads / executes external code and has not undergone explicit manual review, the conclusion must not be lower than `Pending Verification`.
- When typosquatting / dependency confusion is suspected, `Pending Verification` must be maintained until the package provenance is manually confirmed.

## Output

Persist per the Node.js artifact paths in `skills/shared/IO_PATH_CONVENTION.md`:

| Artifact | Physical Path |
| ---- | ---- |
| Dependency vulnerability scan report | `node/vuln_scanner/npm_audit_{timestamp}.md` |
| Phase index | `node/vuln_scanner/index_{timestamp}.md` |
| Empty-result explanation (if applicable) | `node/vuln_scanner/empty_result_{timestamp}.md` |

- SBOM output (optional enhancement): generate `vuln_report/{project_name}_sbom.cdx.json` (CycloneDX) with `@cyclonedx/cyclonedx-npm`; use `spdx-sbom-generator` for SPDX. When tools are unavailable, record `sbom_status=NOT_RUN + reason`.
- The artifact header must contain `knowledge_cutoff_date: {YYYY-MM-DD|unknown}` (built-in knowledge declaration cutoff date; when unknown, accompanied by a "conclusions may lag" statement) and `offline_report_source: {path|none}`; when there is no injected report and no online comparison, "no online comparison performed" must be declared.

### Minimum Fields of npm_audit_{timestamp}.md

- `pkg_id`: dependency unique sequence number.
- `name`: package name (including scope).
- `version_range`: the version range declared in `package.json`.
- `locked_version`: the lockfile-resolved version; write `N/A (Pending Verification)` when no lockfile exists.
- `registry`: the registry source of installation (if determinable).
- `known_vulns`: the list of hit CVEs / GHSAs; write `none confirmed` when empty.
- `typosquatting_flag`: `YES / NO / Pending Verification`.
- `lifecycle_scripts`: the full list of `preinstall` / `install` / `postinstall`.
- `protocol_risk`: `git+` / `http://` / `file:` / none.
- `version_drift`: `YES / NO`; when inconsistent, record the specific difference between the range and the locked version.
- `conclusion`: `Confirmed` / `Pending Verification` / `Not Applicable`.
- `next_action`: fix, upgrade, manual review, offline evidence supplementation.

### Pre-Output Self-Check

- [ ] `dependencies` / `devDependencies` / `optionalDependencies` have been fully enumerated.
- [ ] The lockfile has been parsed; when missing, related fields are marked `Pending Verification`.
- [ ] Lifecycle scripts `preinstall` / `install` / `postinstall` have been fully listed.
- [ ] Protocol risks `git+` / `http://` / `file:` have been recorded item by item.
- [ ] Version drift comparison items have been listed item by item.
- [ ] All `Confirmed` conclusions are supported by CVE / GHSA or tool output.
