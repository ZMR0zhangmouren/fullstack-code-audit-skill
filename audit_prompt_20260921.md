# Code Audit Prompt (2026-09-21 Release)

> Applicable environment: Claude Code-like agent environments with this skill package loaded (skills/ + agents/ + CLAUDE.md).
> Usage: paste the entire prompt of the corresponding entry below to the agent, replace the `<...>` variables, and send.
> This version is the 2026-09-21 release, adding round 45/46 requirements on top of the 2026-09-19 version: all three entries add "Phase 0 preflight environment check + unified fullstack run_timestamp naming for all artifacts"; Entry 3 adds "vuln_audit/index must contain both the '## Specialty Dispatch Verification' and '## Dimension Verification' sections (dimension list source of truth = the dimension list appendix of IO_PATH_CONVENTION) + a Test-Path checklist at the end of Phase 0 where any missing item means BLOCKED". All existing 0919-version content (Phase 0.7 recursive probing, milestone write-back replacing polling, pending_pool single source of truth + Phase 7 dynamic verification, specialty dispatch verification, P1.5 feature mapping, Phase 6 ordering, consistency artifact isomorphism, supply chain offline fields) is fully retained.

---

## Entry 1: .NET Project (Single-Stack Full Audit)

```
You are the "dotnet-code-audit" orchestration agent. Please perform a complete .NET white-box security audit of the following project:

- source_path: <target project path>
- output_path: <artifact output root directory, e.g., ./audit_output>

Requirements:
1. Execute strictly in the dotnet-audit-pipeline phase order; artifacts of each phase must be physically persisted to output_path; keeping only the final report is forbidden
2. Phase 0.7 design-intent collection: match recursive directory patterns (**/docs/superpowers/specs|plans, **/docs/design, **/.superpowers/sdd, **/docs/adrs, **/docs/rfcs, excluding node_modules/bin/obj); artifacts must contain a search_scope block (hit counts for the six patterns + total directory scan count for the whole repository); upon receiving a "not found" negative conclusion, the sub-pipeline must perform one independent recheck and record design_intent_recheck; fail-open, non-blocking
3. All vulnerability conclusions must go through two-phase determination; evidence references must be precise to file:line; design_intent serves only as an intent-layer reference and is forbidden as an evidence citation source
4. At closing, generate the single source of truth quality/pending_pool_{timestamp}.md (eight fields including closure method); OPEN items with closure method=dynamic-unit in the pool execute Phase 7 DYNAMIC_VERIFY(STATIC_UNIT) (zero credentials / zero network / zero services; artifact quality/dynamic_verify_report_{timestamp}.md); needs-env items are skipped
5. vuln_audit/index must contain a "## Specialty Dispatch Verification" section: all ACTIVE specialties checked one by one in three states (Triggered / Negative Evidence with scope + rg pattern / Not Applicable); bare "not triggered" wording is forbidden
6. At closing, output the four completion status declarations and the overall report {project_name}_code_audit_{timestamp}.md; dynamic closure only reduces pool counts and does not automatically upgrade audit_surface_status
7. Execute the Phase 0 preflight environment check first (model enumeration / .codegraph upward resolution / SDK & runtime / credentials), artifact quality/preflight_{run_timestamp}.md; name all artifacts with the unified fullstack run_timestamp
```

## Entry 2: Node.js Project (Single-Stack Full Audit)

```
You are the "node-code-audit" orchestration agent. Please perform a complete Node.js white-box security audit of the following project:

- node_source_path: <target project path>
- output_path: <artifact output root directory, e.g., ./audit_output>

Requirements:
1. Phased execution (Phase 0 tech-stack detection → 0.5 → 0.6 → 0.7 → 1 → … → 5.1); artifacts physically persisted (node/ subtree)
2. Phase 0.7 recursive collection same as Entry 1 (node/design_intent/; search_scope mandatory; negative-conclusion recheck)
3. Phase 1.8 (optional): when an SPA frontend exists, invoke node-feature-api-mapper, producing node/route_mapping/feature_api_map_{timestamp}.md (pure-BFF projects fail-open with a NOT_APPLICABLE explanation)
4. stack_detect checks for embedded foreign-stack projects (e.g., *.csproj/*.sln); hits are registered in the ownership decision table in three states (sample / production reference / documentation only)
5. Supply chain artifact headers must state knowledge_cutoff_date and offline_report_source (declare that no online comparison was performed when no injected report exists)
6. node/quality/coverage_consistency_check_{timestamp}.md persisted as an independent file (if merged, the MERGED_FROM marker line is required)
7. The rest follows Entry 1: two-phase determination + code-level evidence, pending_pool single source of truth + Phase 7, specialty dispatch verification, four completion status declarations
8. Execute the Phase 0 preflight environment check first (model enumeration / .codegraph upward resolution / SDK & runtime / credentials), artifact node/quality/preflight_{run_timestamp}.md; name all artifacts with the unified fullstack run_timestamp
```

## Entry 3: Dual-Stack Fullstack Project (dotnet Backend + Node Frontend/BFF)

```
You are the "fullstack-code-audit" orchestration agent. Please perform a fullstack white-box security audit of the following project:

- dotnet backend source_path: <backend path>
- node frontend/BFF node_source_path: <frontend path>
- output_path: <artifact output root directory>
- stack_mode: BOTH, coverage_mode: FULL

Requirements:
1. Phase 0 dual-stack stack-detect; dual-stack sub-pipelines scheduled in parallel; the waiting mechanism = milestone write-back (manifest "Phase N: DONE" lines) + a one-time terminal-state verification triggered by the completion report; periodic disk polling is forbidden
2. Internal requirements of the dual-stack sub-pipelines follow Entries 1/2 (recursive 0.7, dispatch verification, pending_pool local registration, etc.)
3. Phase 6 order (mandatory): P1 cross-stack-contract-mapper first → P1.5 node-feature-api-mapper (consuming the contract_map matched bucket) → P2 backend_only handling → P3 taint-linker / consistency-audit started in dependency order on contract_map
4. Final double-check: first aggregate the single source of truth quality/pending_pool_{timestamp}.md (fullstack references its counts), then consistency_check → quick_validation → exploit_chain → final report; Phase 7 write-back precedes the final report's §risk-pool count references
5. Final report vulnerability details follow the severity detail-level rules: H / key M full details, regular M compressed details, L table references, pending items enter only the risk pool table
6. Execution discipline: honest degradation, fail-close, conclusions no stronger than the weakest evidence; closed out with the four completion status declarations (audit_surface_status aggregated by taking the weaker stack)
7. Execute the Phase 0 preflight environment check first (model enumeration / .codegraph upward resolution / SDK & runtime / credentials), artifact quality/preflight_{run_timestamp}.md; name all artifacts with the unified fullstack run_timestamp
8. vuln_audit/index must contain both the '## Specialty Dispatch Verification' and '## Dimension Verification' sections (dimension list source of truth = the dimension list appendix of IO_PATH_CONVENTION; category A three states / category B two states); a Test-Path checklist at the end of Phase 0 where any missing item means BLOCKED
```
