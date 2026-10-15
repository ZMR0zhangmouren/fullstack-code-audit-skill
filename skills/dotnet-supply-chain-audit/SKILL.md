---
name: dotnet-supply-chain-audit
description: .NET supply chain security audit tool. Scans NuGet package versions, known CVE/Advisory matching, dependency transitive chain analysis, insecure protocols, and private feed security.
---

# .NET Supply Chain Security Audit

## Shared Grabber Index References

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as this Skill's base retrieval index
- By default, use shared/DOTNET_SINK_REFERENCE.md as this specialty's sink type definition and trace-gate validation baseline
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must cover supply-chain-related configuration, dependency declaration, and security switch grabbers
- Supply chain security involves: package version management, dependency transitive chains, NuGet feed configuration, development/runtime dependency separation, signature verification
- If the project has private feeds, a unified package management platform, or an internal package repository, they must be added to the in-project grabbers section of the output
- When this Skill's specialty enumeration rules are more detailed than the shared index, this Skill prevails, but the shared index's base coverage must not be reduced

## Input Dependencies

- `source_path`: .NET project, solution, or repository root (required).
- `route_mapping` / `route_tracer`: upstream artifacts (if present), used to evaluate runtime-reachable entries of vulnerable dependencies; confirm dependencies are available and timestamps are consistent.
- `framework_audit`: framework specialty artifacts (if present), used to cross-confirm dependency usage surfaces.
- When upstream artifacts are missing, vulnerability reachability determination is degraded to `⚠️Pending Verification` with a missing-evidence list recorded.

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (e.g. `route_mapping` / `route_tracer` / `framework_audit`), confirm dependencies are available and timestamps are consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: write to the agreed path per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing-evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (Dependency Inventory Confirmation)**: a complete SBOM of NuGet/SDK/toolchain must be confirmed.
- 🔴 **CHECKPOINT B (Source Integrity Confirmation)**: feed trustworthiness, signature/hash verification, and locking policies must be confirmed.
- 🔴 **CHECKPOINT C (Build Pipeline Confirmation)**: credential isolation in CI/CD and artifact traceability must be confirmed.
- 🛑 **STOP**: if the source of a key dependency cannot be verified, the conclusion is degraded to `⚠️High Uncertainty`.

## Resource References & Reachability Validation (Mandatory)

- Required shared index references: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber sources) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: on-disk paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from the directory structure are not allowed.
- Evidence consistency validation: if severity-graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: before submission, confirm at least once that key referenced files are accessible (e.g. `DOTNET_AUDIT_GRABBER_INDEX.md`, `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Each skill must maintain at least 2 typical test cases (happy path + one complex scenario), and annotate the case ID in the results.
- Each evaluation round must execute `full_test` for at least 1 case; if only `dry_run` is possible, `dry_run_reason` and a make-up test plan must be recorded.
- Pass criteria must simultaneously satisfy: `intent achieved`, `key evidence hit`, `output format compliant`; if any one is not met, "pass" must not be given.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `Input Constraints` → `Execution Steps` → `Output and Acceptance`; no layer may be missing or mixed across layers.
- A single paragraph should not exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into a single source-of-truth section.
- AI-isms and empty filler transitions are forbidden (e.g. "first/second/finally/in summary/put simply/in other words"); any found must be rewritten as executable statements.

## Quality Gate & Assessment Consistency (Mandatory)

- A minimal gate self-check must be executed before producing output: `input completeness`, `key evidence hit`, `output path valid` — all three must be PASS.
- If any of `key evidence missing`, `chain not closed`, `consistency_check_status=BLOCKED` holds, the conclusion must be degraded to `BLOCKED`; outputting "confirmed exploitable/deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with the `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

- Anti-pattern: only looking at direct dependencies, ignoring the transitive chain. Correct approach: trace the complete dependency path to exploitability.
- Anti-pattern: equating a CVE hit directly with exploitability. Correct approach: evaluate together with the call surface and deployment context.
- Anti-pattern: ignoring private feeds and signature policies. Correct approach: verify feed trustworthiness, signatures, and hash checks.
- Anti-pattern: drawing strong conclusions with unverified key sources. Correct approach: degrade to `⚠️High Uncertainty`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback if Still Failing |
|---|---|---|
| Dependency inventory incomplete (missing lock/transitive dependencies) | Fill in SBOM and dependency graph sources | Conclusion degraded to `⚠️High Uncertainty` |
| Vulnerability hit lacks call-surface evidence | Correlate to affected components and runtime paths | Do not output an exploitable strong conclusion; give priority suggestions only |
| Feed trustworthiness and signature policy unknown | Verify source, signatures, hashes, and CI policies | Keep high uncertainty and give a follow-up evidence list |

🔴 **STOP: when any fallback is triggered, outputting "confirmed exploitable supply chain risk" is forbidden.**

- **NuGet package version scanning**:
  - Parse *.csproj, Directory.Packages.props, Directory.Build.props, packages.config, NuGet.lock.json, NuGet.Config
  - Identify direct and transitive dependency versions, pinned versions vs floating versions vs version ranges
  - Flag whether the highest allowed version in a version range still has known vulnerabilities

- **External database integration tools (preferred when the environment allows; the skill itself contains no code)**:
  - `dotnet list package --vulnerable`: built into .NET 8+, outputs direct/transitive dependencies with known vulnerabilities based on the NuGet Audit source (output includes CVE IDs and affected version ranges).
  - `osv-scanner --format json --lockfile NuGet.lock.json` (or scan packages.lock.json / *.csproj): offline/online comparison against the OSV database; JSON output can be used directly as EVID_SUPPLY_TOOL_OUTPUT evidence.
  - Offline path: download the OSV database export (all.zip / NuGet ecosystem subset) and consume it via osv-scanner's `--offline-vulnerabilities` parameter; or manually compare package by package against NuGet.lock.json using the NuGet Advisory sources (`https://api.nuget.org/v3-flatcontainer/` and advisory sources), annotated `Pending Verification`.
  - Tool output must record: tool name, command, output summary (EVID_SUPPLY_TOOL_OUTPUT); replacing reachability determination with tool conclusions alone is forbidden.

- **Known CVE/Advisory matching**:
  - Integrate NVD/NuGet Advisory API/GitHub Advisory Database/OWASP Top 10 for .NET
  - Identify affected version ranges, fixed versions, and vulnerability types (remote code execution, denial of service, information disclosure, privilege escalation)
  - Distinguish CVSS 3.1 levels: Critical (9.0-10.0), High (7.0-8.9), Medium (4.0-6.9), Low (0.1-3.9), aligned with the level mapping table in skills/shared/SEVERITY_RATING.md

- **Dependency transitive chain analysis**:
  - Trace exploitable paths of transitive dependencies: direct dependency → transitive dependency → final exploitable interface
  - Identify "phantom dependencies": packages actually referenced but not explicitly declared in csproj
  - Identify "test dependencies": whether dependencies only in Test projects leak into runtime
  - Identify "development dependencies": DotNetCliToolReference, BuildDependsOn, MSBuild task dependencies

- **Insecure protocol risks**:
  - Identify http:// feeds vs https:// feeds (man-in-the-middle risk)
  - Identify unofficial or third-party NuGet feeds (package tampering risk)
  - Identify feeds without integrity verification (hash/Signature)

- **Private NuGet feed security**:
  - Identify V3/V2 protocol private feeds and authentication methods (API Key / Azure Artifacts / nuget.config)
  - Check for hardcoded credentials or environment variable references in nuget.config or Directory.Build.props
  - Identify whether internal packages contain sensitive PDBs, XML documentation, or debug symbols

- **Signature and integrity verification**:
  - Identify NuGet package signature verification configuration (trustedSigners, allowUntrustedRoot)
  - Check whether Signed Package Verification is enabled
  - Identify signature differences between community packages and Microsoft official packages

- **Outdated component risks**:
  - Identify packages that are no longer maintained (EOL, no longer maintained)
  - Identify exposure windows of version-frozen (frozen lockfile) packages when new vulnerabilities appear
  - Identify .NET version and package compatibility: incompatible package versions may cause runtime exceptions or security fallbacks

- **Development toolchain risks**:
  - Identify MSBuild Task injection risks: where custom MSBuild Tasks execute
  - Identify Source Link, Debug Type, and source path leakage in PDB files
  - Identify Build-InlineTask and UsingTask dynamic loading risks

## Enumeration Rules (Mandatory Refinement)

- **Dependency declaration file enumeration**:
  - Search keywords: *.csproj, PackageReference, PackageVersion, <ProjectReference>, Directory.Packages.props, packages.config, NuGet.lock.json, NuGet.Config, nuget.config
  - Record: direct dependency names/versions, transitive dependency names/versions, pinned version policies, version ranges, floating version policies
  - Identify ImplicitlyExpandDesignTimebuildTargets, TreatAsLocalPackage, IsShippingPackage

- **Vulnerability matching enumeration**:
  - Search keywords: nuget.org advisory, CVE-*, GHSA-*, security advisory, NuGet.Security.Advisories
  - Record: CVE ID, CVSS score, vulnerability type, affected version range, fixed version, patch link
  - Identify whether the package name + version tuple is in a known vulnerability database

- **Transitive dependency path enumeration**:
  - Search keywords: <Dependency>, TransitiveProjectReference, ProjectAssetsFile, NuGet.DepencyGraph
  - Record: dependency levels, exploitable transitive paths, direct/transitive distinction, scope (compile/runtime/test/build/custom)
  - Identify IsImplicitlyDefined, PrivateAssets, IncludeAssets, ExcludeAssets

- **Feed configuration enumeration**:
  - Search keywords: <packageSources>, <add key=, <clear />, http://, https://, <credential>, <dotnet nuget>
  - Record: feed URL, protocol type, authentication method, whether official, whether private, whether local
  - Identify packageSourceMap, restoreSources, fallbackFolders

- **Signature verification enumeration**:
  - Search keywords: trustedSigners, allowUntrustedRoot, SignedPackageVerification, nuget verify, --signature
  - Record: signature verification configuration, trusted signers, certificate chain verification, whether origin is verified
  - Identify AllowAuthorUnsingedPackages, AllowUntrustedRoot risks

- **Development toolchain enumeration**:
  - Search keywords: MSBuildTask, UsingTask, BuildDependsOn, SourceLink, DebugType, Embed, PDB
  - Record: Task sources, Task execution locations, whether dynamically loaded, PDB file paths, source link exposure
  - Identify InlineTask, DynamicLoad risks

- **Outdated component enumeration**:
  - Search keywords: EOL, no longer maintained, deprecated, legacy, <legacyPackageAllowDuringBuild>, frozen lockfile
  - Record: package name, last publish date, maintenance status, .NET version compatibility, known security issues
  - Identify exposure windows of frozen versions when new vulnerabilities appear

- For each vulnerable dependency record: package name, version, CVSS score, vulnerability type, affected entry/route, transitive dependency path, fixed version recommendation

## Barrier Verification Matrix (Mandatory)

Assess against the fail-close three-tier standard in `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Tier | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Tier 1 | NuGet/dependency declarations exist | Dependency declarations exist in *.csproj/packages.config/NuGet.lock.json | BLOCKED → no dependency declaration files; the specialty ends |
| Tier 2 | Known CVEs/unsafe feeds/missing signatures exist | Dependency versions match known CVEs, http:// feeds/unofficial feeds in use, allowUntrustedRoot enabled | BLOCKED → all dependency versions safe, feeds trusted, signature verification complete; conclusion degraded |
| Tier 3 | Vulnerable dependencies are runtime-reachable and exploitable | Vulnerable transitive dependencies are loaded at runtime and their vulnerable interfaces are reachable via project code paths | PARTIAL → only potential risks and verification steps are output |

## Two-Phase Determination Flow (Mandatory)

- **Phase 1 (Initial Screening Hit)**: dependency declaration + CVE/unsafe feed/signature issue + runtime reachability hit; output `Hit ID: M{hash}`.
- **Phase 2 (Refined Confirmation)**:
  1. Trace in reverse: dependency declaration → version → CVE database match chain;
  2. Verify NuGet feed protocols (http vs https) and signature verification configuration (trustedSigners/allowUntrustedRoot);
  3. Assess the transitive path and runtime reachability of vulnerable dependencies (whether vulnerable interfaces are reachable via project code paths);
  4. If all three barrier tiers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priority (Mandatory)

1. **Confirmed Vulnerability**: dependency declaration exists + known CVE/unsafe feed/missing signature + runtime reachable and exploitable. Output `Confirmed Vulnerability`.
2. **Pending Confirmation**: dependency declaration exists but CVE affected-version or runtime reachability evidence is insufficient. Output `Pending Confirmation`.
3. **False Positive / No Risk**: all dependency versions have no known CVEs, official https feeds used, signature verification enabled, no untrusted root, vulnerable dependencies unreachable. Output `False Positive` with determination basis.

## Testing Suggestions and Minimum Trigger Conditions (Mandatory)

- **Minimum Trigger Conditions**:
  - Dependency declarations such as *.csproj/packages.config/NuGet.lock.json exist
  - Dependency versions match known CVEs or http:// feeds/unofficial feeds are used
  - Or signature verification disabled (allowUntrustedRoot)
- **Test Case Suggestions**:
  - Happy Path: normal dependency versions have no CVEs, official https feeds used, signature verification passes
  - Edge/Ambiguity: transitive dependency CVE exploitation paths, version-range floating introducing vulnerable versions, private feed credential hardcoding, MSBuild Task injection
- Each hit output appends `Hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Evidence References

- EVID_SUPPLY_CVE_MATCH: evidence of dependency versions matching known CVE/GHSA databases (CVE ID, affected version range, current/locked version, fixed version)
- EVID_SUPPLY_UNSAFE_SOURCE: evidence of feed protocol or source risk (feed URL, protocol type, authentication method)
- EVID_SUPPLY_SIGNATURE_GAP: evidence of missing signature verification or configuration flaws (allowUntrustedRoot, trustedSigners not configured)
- EVID_SUPPLY_TRANSITIVE_PATH: evidence of exploitable transitive dependency paths (direct dependency → transitive dependency → exploitable interface)
- EVID_SUPPLY_SPOOF_DEP: evidence of dependency confusion/typosquatting/phantom dependency suspicion (package name similarity, declaration location)
- EVID_SUPPLY_TOOL_OUTPUT: raw tool scan output evidence (dotnet list package --vulnerable / osv-scanner / npm audit)
- EVID_SUPPLY_LOCK_GAP: evidence of missing lockfiles or version drift (declaration location, range, locked version)

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion level: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose exactly one; leaving blank is forbidden).
- Minimum evidence set: must include at least the five items `entry point`, `controllable parameters`, `key calls`, `security boundary`, `missing evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softening wording is forbidden: e.g. "possibly at risk / worth noting / depends on the situation / very likely"; when evidence is insufficient, must explicitly write `⚠️Pending Verification` and the next follow-up confirmation action.

Minimal output snippet (directly reusable):

```md
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameters=...; key calls=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement parameter propagation evidence for trace_id=...
```

## Output

- Output file: vuln_audit/supply_chain_{timestamp}.md
- Results must be organized into seven sections: Dependency Inventory and Version Distribution, Known Vulnerability Matches, Transitive Dependency Risks, Feed Configuration and Protocol Security, Signature Verification, Development Toolchain Risks, Outdated Components
- Each vulnerable package must state: package name, version, CVSS score, vulnerability type, affected entry/route (if any), transitive dependency path, fixed version recommendation, priority (P0/P1/P2)
- Four categories must be listed separately: high-risk supply chain risks (P0), medium-risk supply chain risks (P1), low-risk supply chain risks (P2), and components pending evaluation
- Unresolvable dependency conflicts (mutually exclusive versions) and mitigations must be listed
- If executed via `dotnet-audit-pipeline`, `vuln_report/{project_name}_nuget_vuln_report_{timestamp}.md` should be generated in sync
- If private feed configuration issues are found, the nuget.config location and credential configuration method must be recorded in the in-project grabbers section
- SBOM output (optional enhancement, executed when tooling is available): `dotnet list package --format json` or the CycloneDX .NET tool generates `vuln_report/{project_name}_sbom.cdx.json` (CycloneDX); for SPDX requirements output `*.spdx.json`. The SBOM must cover direct + transitive dependencies, locked versions, and license information (where obtainable). When the generation tool is unavailable, record `sbom_status=NOT_RUN + reason`.
