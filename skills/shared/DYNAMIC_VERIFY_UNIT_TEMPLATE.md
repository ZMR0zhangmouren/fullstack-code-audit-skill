# DYNAMIC_VERIFY(STATIC_UNIT) Unit-Level Dynamic Verification Template

This file defines the local dynamic verification execution standard for pending_pool entries with "Closure Method = dynamic-unit", for use by dotnet-audit-pipeline / node-audit-pipeline Phase 7 and for manual execution. Purpose: to give the "Confirmed (Dynamic Verification)" label a zero-credential local execution path (the only compliant trigger path is defined in this file; the existing semantics of the two pipelines remain unchanged).

## Scope

- Applies only to pending_pool entries with "Closure Method = dynamic-unit and Status = OPEN"
- Applies only to "unit-test-level reproducible" items (pure logic defects such as validateParams every/some negation, regex over-escaping, etc.)
- Not applicable to integration-level items (service startup / test tenants / credential hosting); the closure method for such entries is `needs-env` — this phase skips them without attempting, and integration-level items are tracked as separate projects
- Test projects are temporary: discarded after the run and not merged into the target repository

## Red-Line Self-Check (Mandatory PASS on Every Item Before Running)

The following four-zero red lines must each be confirmed PASS; if any is not met → the entire phase is NOT_RUN with the reason noted in the report:

1. **Zero credentials** — do not read or construct any account, token, connection string, cookie, or key
2. **Zero network** — do not make any outbound request (loopback included) and do not perform DNS resolution
3. **Zero services** — do not start any listening port or any background process / daemon
4. **Zero writes outside the scratch directory** — the test project and all artifacts are written only to `{output_root}/quality/dynamic_verify_scratch/`; no file in the target repository may be modified

**Pure function precondition**: the function / module under test must be a pure function / pure module (no I/O side effects — no file reads/writes, no network access, no global state other than environment variables). This precondition is substantiated by the entry's "Missing Evidence" field at registration: at registration, confirm that the missing evidence is only "lack of dynamic trigger observation", not "lack of runtime environment". Entries that cannot meet the pure-function precondition must not use this path; re-assign the closure method or track as a separate project.

Self-check table (fill in item by item; all must be ✔ before generation and execution):

| Check Item | Result | Notes |
|--------|------|------|
| Zero credentials | ☐ PASS / ☐ FAIL | {notes} |
| Zero network | ☐ PASS / ☐ FAIL | {notes} |
| Zero services | ☐ PASS / ☐ FAIL | {notes} |
| Zero writes outside scratch directory | ☐ PASS / ☐ FAIL | {notes} |
| Function under test is a pure function / pure module | ☐ PASS / ☐ FAIL | Basis: entry "Missing Evidence": {missing_evidence} |

## dotnet Template

**Copy-don't-reference policy**: **copy** the source file under test from the target repository into the scratch test project directory; do **not reference** the target project (no ProjectReference / no `<Compile Include>` of files outside the target repository path / no restoring the target project's NuGet dependency graph), avoiding the target project's dependency graph and build side effects. After copying, the file under test may in principle only receive minimal adaptations needed to compile (e.g., removing unrelated usings); the tested logic itself must not be modified.

Temporary xunit project skeleton (create under `{output_root}/quality/dynamic_verify_scratch/case_{pool_id}/`):

````xml
<!-- case_{pool_id}/VerifyCase_{pool_id}.csproj key lines -->
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <IsPackable>false</IsPackable>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.9.0" />
    <PackageReference Include="xunit" Version="2.7.0" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.7" />
  </ItemGroup>
  <!-- Copied source file under test (from the target repository; copied, not referenced) -->
  <ItemGroup>
    <Compile Include="src/{relative_path_of_file_under_test}" />
  </ItemGroup>
</Project>
````

Unit test class structure:

````csharp
// case_{pool_id}/UnitTest_{pool_id}.cs
using Xunit;

namespace DynamicVerify;

public class UnitTest_{pool_id}
{
    // Assertions are written item by item per the entry's "Evidence-Supplementing Action":
    // e.g., if the action is "reproduce validateParams every/some negation in a unit test" →
    // construct the triggering input and assert actual behavior matches the action description
    [Fact]
    public void {pool_id}_{scenario_name}()
    {
        // Arrange: construct the minimal triggering input (taken from the call-site parameters in the entry's "Associated Chain/Finding")
        // Act: invoke the pure function under test
        // Assert: assert the expected behavior (written per the "Evidence-Supplementing Action"; tautological assertions are forbidden)
        Assert.Equal({expected}, {actual});
    }
}
````

Assertion writing guidelines:

- Each "Evidence-Supplementing Action" corresponds to at least one `[Fact]` test method; the test method name carries the pool_id for traceability
- Assertions must be able to fail: tautological assertions such as `Assert.True(true)` are forbidden; failure itself is a valid result (record FAILED, keep OPEN)
- Triggering inputs are excerpted from the call sites in the entry's "Associated Chain/Finding" and must not be fabricated

Run and output saving:

```bash
cd "{output_root}/quality/dynamic_verify_scratch/case_{pool_id}"
dotnet test --logger "console;verbosity=detailed" > run_{pool_id}.log 2>&1
```

## node Template

**Copy-don't-reference policy**: same as the dotnet side — use `cp` to copy the source file under test into the scratch test project directory and import the copied copy via a relative path; `require` / `import` of absolute paths in the target repository is forbidden, and executing the target repository's postinstall / build scripts is forbidden, to avoid triggering its dependency graph.

Temporary vitest project skeleton (if vitest is unavailable, use the native `node --test` runner; choose one of the two):

````text
case_{pool_id}/
├── package.json        # only the vitest devDependency (or a minimal empty package for node --test)
├── src/
│   └── {copy_of_file_under_test.js}   # copied from the target repository
└── test_{pool_id}.test.js
````

````json
// package.json
{
  "name": "dynamic-verify-case-{pool_id}",
  "private": true,
  "type": "module",
  "scripts": { "test": "vitest run" },
  "devDependencies": { "vitest": "^1.6.0" }
}
````

````js
// test_{pool_id}.test.js — vitest version; for node:test, use the equivalent structure with node:test / node:assert
import { describe, it, expect } from 'vitest';
import { {export_under_test} } from './src/{copy_of_file_under_test.js}';

// Assertions are written item by item per the entry's "Evidence-Supplementing Action"
describe('{pool_id}', () => {
  it('{scenario_name}', () => {
    // Arrange: construct the minimal triggering input (taken from the entry's "Associated Chain/Finding")
    // Act + Assert: assert actual behavior matches the action description; tautological assertions are forbidden
    expect({actual}).toBe({expected});
  });
});
````

Run and output saving:

```bash
cd "{output_root}/quality/dynamic_verify_scratch/case_{pool_id}"
npx vitest run > run_{pool_id}.log 2>&1
# or (without vitest): node --test > run_{pool_id}.log 2>&1
```

## Run and Write-Back Protocol

- **Test project path convention**: `{output_root}/quality/dynamic_verify_scratch/case_{pool_id}/` (fullstack: `{output_root}/quality/`; same for single-stack; this is the only directory in the whole repository where writes are allowed)
- **Run output saving**: the complete run output of each case is stored at `case_{pool_id}/run_{pool_id}.log`, serving as the output evidence of dynamic verification
- **Artifact report**: `quality/dynamic_verify_report_{timestamp}.md`, recording item by item `pool_id | closure method | result (VERIFIED/FAILED/SKIPPED) | test project path | run output summary`
- **Write-back semantics**:
  - Pass → the report records `VERIFIED`, the pending_pool entry status flips to `DYNAMIC_VERIFIED`, and only then may the associated finding's report / PoC be labeled "Confirmed (Dynamic Verification)" (citing the report path)
  - Failure → the report records `FAILED + output summary`; **the pool entry stays OPEN** with the failure reason recorded; labeling `DYNAMIC_VERIFIED` is forbidden
  - `needs-env` entries → skipped without attempting in this phase (SKIPPED); integration-level items are tracked as separate projects
- **Conservative semantics (anti-inflation)**: no result of this phase changes the `audit_surface_status` determination logic; the report only affects the `open_count` / `dynamic_verified_count` bucket counts of pending_pool; the `pool_total` scope remains unchanged
- **Cleanup**: after the report is persisted and pool entries are written back, the scratch directory is retained until the end of the current audit confirms everything is correct, then cleaned up; the cleanup action itself must not touch any path outside the scratch directory

## Minimum Acceptance Requirements

- [ ] The four-zero red-line self-check table passes item by item, recorded at the head of `run_{pool_id}.log` or in an accompanying note
- [ ] The test project is entirely within `dynamic_verify_scratch/case_{pool_id}/`, with zero writes outside the directory
- [ ] The source file under test is a copied copy, does not reference the target project, and the tested logic is unmodified
- [ ] Each "Evidence-Supplementing Action" has at least one failable assertion; no tautological assertions
- [ ] The report gives VERIFIED / FAILED / SKIPPED item by item with run output summaries
- [ ] FAILED entries keep pool status OPEN with the failure reason recorded
- [ ] The `audit_surface_status` determination logic is untouched throughout

Consumers (the dotnet pipeline Phase 7 report section) must cite the four-zero clauses of this section verbatim in the red-line verification table header; the same applies when this template is used directly by humans.
