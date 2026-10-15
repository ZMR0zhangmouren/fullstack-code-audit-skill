# Node-Side Supply Chain Specialty Determination Criteria

> node-supply-chain-audit has been delivered (ACTIVE, 2026-09-04); this file is the single source of truth for its determination criteria.

## Determination Criteria

1. **Confirmed vulnerability**: the lockfile version hits a known CVE/GHSA + the dependency is reachable on a runtime load path + no effective mitigation (fixed version / alternative package).
2. **Pending confirmation**: the intersection between the CVE-affected version range and the locked version is unclear, or runtime reachability evidence is insufficient → downgrade to `Pending Verification`.
3. **False positive**: the version is fixed, unreachable, or locked only in devDependencies and does not enter the build output → output `False Positive` + determination basis.

## Integration with the Toolchain

- Tool output (`npm audit --json` / `osv-scanner`) serves only as initial screening evidence (EVID_NODE_SUPPLY_TOOL_OUTPUT reserved); the reachability determination must combine route-trace and build-artifact analysis.
- Typosquatting / dependency confusion: use registry popularity and provenance declarations as the baseline; hits are labeled `Pending Verification` and require manual review.
