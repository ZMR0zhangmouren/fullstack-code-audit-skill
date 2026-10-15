# .NET / Node.js Code Audit Skill

This repository is a collection of white-box code security audit skills for the .NET and Node.js platforms (the node family mirrors the methodology of the dotnet family; the cross-stack layer supports fullstack frontend-backend audits). The overall dotnet-side design follows the methodology of the PHP project:

- Entry and parameter modeling first
- Then data-flow tracing and evidence closure
- Then categorized vulnerability audits
- Finally quality aggregation and exploit-chain consolidation

The project covers ASP.NET Core, ASP.NET MVC, ASP.NET Web API, Blazor, SignalR, GraphQL, WCF, and common class-library scenarios; the Node.js side covers Express, Koa, Fastify, Next.js, Nuxt, NestJS, and GraphQL, and supports fullstack (stack_mode=BOTH) audits. It is suitable for source-code audits, fix verification, and regression analysis under the premise of legitimate authorization.

> 📖 **First-time deployment and usage, please read: [docs/Initialization_and_Usage_Guide.md](docs/Initialization_and_Usage_Guide.md)** (deployment steps, three coverage modes, resume-from-breakpoint, gate acceptance, regression test plan)

## Project Features

- Evidence-contract driven: the EVID_* evidence points output by dotnet-route-tracer serve as the hard gate for most sub-audit skills
- Complete route and parameter modeling: dotnet-route-mapper must output complete entries, parameter structures, and request templates
- Controlled conclusion strength: high-risk conclusions depend on trace_status, Sink Summary, and EVID_* closure
- Balanced recall and precision: false negatives and false positives are suppressed via static fallback, SINK_SUSPECT, and the pending-evidence risk pool
- Compatible with modern and legacy stacks: covers Minimal API, Attribute Routing, MVC Controller, Hub, GraphQL Endpoint, WCF Service

## Capability Overview

### Infrastructure

- **Orchestration & Aggregation**
  - dotnet-audit-pipeline: full-chain orchestration and quality aggregation
- **Preliminary Indexing**
  - dotnet-codegraph-indexer: CodeGraph code knowledge graph index management (mandatory prerequisite; falls back to static analysis on failure)
- **Entry Modeling & Tracing**
  - dotnet-route-mapper: identifies HTTP, Hub, GraphQL, WCF, and other entries and parameters
  - dotnet-route-tracer: traces branches, parameter mappings, and evidence points from entries to Sinks
- **Scanning & Vulnerability Discovery**
  - dotnet-scan-audit: full-codebase scanning and entry baseline establishment (P0 addition)
  - dotnet-vuln-scanner: scans NuGet dependency vulnerabilities and infers affected entries (toolchain: `dotnet list package --vulnerable`, osv-scanner)
- **Coverage & Backfill**
  - dotnet-coverage-audit: incremental change backfill and coverage tracking (P0 addition)
- **Analysis & Quality Check**
  - dotnet-briefing-agent: candidate vulnerability parameter list generation (P0 addition)
  - dotnet-review-agent: audit-output evidence quality check and consistency validation (P0 addition; includes evidence authenticity spot checks with minimal read-only re-verification rights, capable of identifying suspected fabricated evidence)

### Vulnerability Specialties (35)

#### Injection Class (10)
- SQL, NoSQL, KQL, Command, LDAP, Expression, Template, XPath, SSTI, Second-Order Injection

#### Web Security (7)
- XSS, DOM-XSS, SSRF, XXE, Deserialization, HTTP Desync, Open Redirect

#### File Operations (5)
- Read, Upload, Write, Archive Extraction Path Traversal, Filesystem

#### Protocol & Headers (3)
- CRLF, CSRF, Session & Cookie

#### Configuration & Crypto (3)
- Config, Crypto, Supply Chain Security

#### Business Logic (4)
- Logic, Logging, Authentication, IDOR (IDOR has no standalone on-disk skill; it is covered by the resource ownership validation EVID_AUTH_IDOR_OWNERSHIP_CONDITION of dotnet-auth-audit)

#### Export & AI (3)
- Non-SQL query injection (SOQL/OData/FetchXML), spreadsheet formula injection (CSV/Excel export), AI prompt injection (prompt assembly / RAG / tool calls)

#### Framework Specialties (9)

- dotnet-aspnet-core-audit
- dotnet-mvc-audit
- dotnet-webapi-audit
- dotnet-blazor-audit
- dotnet-signalr-audit
- dotnet-graphql-audit
- dotnet-wcf-audit
- dotnet-grpc-audit (gRPC microservice communication specialty)
- dotnet-minimal-api-audit (.NET 6+ Minimal API specialty)

#### Node.js / Fullstack Family (delivered in the 2026-08 P0+P1 rounds)

A parallel extension of the dotnet family (Route B: zero changes to the dotnet family); the node side mirrors its methodology (evidence contract, two-phase determination, fail-close Barrier, trace-gate, coverage gate, manifest resume-from-breakpoint), and the cross-stack layer is an entirely new addition.

##### node Infrastructure & Orchestration Specialties (10, complete after P3 backfill)

- node-route-mapper: Node.js route and parameter mapping (adapter strategy; generic Node + Express first)
- node-route-tracer: Node.js entry-to-Sink data-flow tracing
- node-auth-audit: Node.js authentication and authorization audit (passport / express-jwt / jsonwebtoken / express-session / next-auth)
- node-vuln-scanner: npm dependency vulnerability scan (lockfile CVEs, typosquatting, dependency confusion, postinstall lifecycle script review; external tool suggestions: npm audit --json / osv-scanner)
- node-codegraph-indexer: Node.js CodeGraph index management (mandatory prerequisite; when unavailable, record the reason and fall back to static analysis, accelerating call chains for node-route-mapper / node-route-tracer)
- node-review-agent: node-side audit-output evidence quality check and consistency validation (symmetric with dotnet-review-agent; includes evidence authenticity spot checks with minimal read-only re-verification rights)
- node-scan-audit: Phase 0.5 security scan (risks + safe_regions; discovery only, no determination; mirrors dotnet-scan-audit)
- node-coverage-audit: Phase 0.6 coverage backfill (gap calculation and backfill loop; completion state aligned with dotnet-coverage-audit)
- node-briefing-agent: Phase 3.5 candidate parameter list (sink parameter checklist, including QUERY_OBJECT / MERGE_TARGET structure slots; mirrors dotnet-briefing-agent)
- node-exploit-chain-audit: Phase 5.1 exploit chain aggregation (prototype pollution → RCE / cloud metadata SSRF / cross-stack linkage / consistency linkage; mirrors dotnet-exploit-chain-audit)

##### node Vulnerability Specialties (31; P3 backfill + 2026-09-14 ledger round 2 items)

- node-proto-pollution-audit (prototype chain pollution, JS-specific, highest priority)
- node-cmd-audit / node-ssrf-audit / node-nosql-audit
- node-file-upload-audit / node-xss-audit / node-ssti-audit / node-session-cookie-audit
- P3 backfill 21 items (2026-09-04): node-sql-audit / node-xxe-audit / node-deser-audit / node-ldap-audit / node-expr-audit / node-xpath-audit / node-file-read-audit / node-file-write-audit / node-archive-extract-audit / node-filesystem-audit / node-csrf-audit / node-open-redirect-audit / node-crlf-audit / node-dom-xss-audit / node-second-order-audit / node-http-desync-audit / node-config-audit / node-crypto-audit / node-logic-audit / node-logging-audit / node-supply-chain-audit (all drafted from NODE_VULN_SKILL_TEMPLATE.md, mirroring the dotnet same-named specialties node-ified; evidence points grouped by EVID_NODE_{TYPE}_*)
- 2026-09-14 ledger round 2 items: node-spreadsheet-export-audit / node-ai-prompt-audit (delivered in the 2026-09-14 ledger round, mirroring the dotnet same-named specialties; evidence points grouped by EVID_NODE_{TYPE}_*)

##### node Framework Specialties (7)

- node-express-audit / node-koa-audit / node-fastify-audit: Node.js classic framework specialties (triggered when stack_detect detects the corresponding framework surface)
- node-nextjs-audit / node-nuxt-audit / node-nestjs-audit / node-graphql-audit: fullstack/decorator framework specialties (SSR isomorphic / DI + Guard / GraphQL endpoints)

##### Orchestration & Cross-Stack (3)

- node-audit-pipeline: node-side sub-pipeline orchestration (structure mirrors dotnet-audit-pipeline Phases 0→5.1)
- cross-stack-contract-mapper: frontend-backend contract reconciliation (API contract / parameter mapping / coverage gate three buckets)
- fullstack-audit-pipeline: the sole fullstack main entry (Phase 0 dual-stack detect → dual-stack parallel → Phase 6 cross-stack → merged report)

##### Cross-Stack Supplements (2)

- cross-stack-taint-linker: cross-stack taint chain linking (frontend Source → backend Sink cross-process chains)
- cross-stack-consistency-audit: two-side configuration consistency audit (five groups: JWT / cookie / CORS / CSRF / error handling)

##### Agents (2)

- agents/node-code-audit.agent.md: node single-stack orchestration entry (stack_mode=NODE_ONLY)
- agents/fullstack-code-audit.agent.md: fullstack orchestration entry

##### shared Additions (6)

- NODE_AUDIT_GRABBER_INDEX.md / NODE_SINK_REFERENCE.md / NODE_VULN_SKILL_TEMPLATE.md / NODE_FRAMEWORK_SKILL_TEMPLATE.md / NODE_VULN_POC_TEMPLATE.md
- FULLSTACK_FINAL_REPORT_FIXED_TEMPLATE.md (single source of truth for the fullstack final report fixed template)

##### Node.js / Fullstack Family Skill List

| Category | Skill | Description |
|------|-------|------|
| node infrastructure (10) | node-route-mapper / node-route-tracer / node-auth-audit / node-vuln-scanner / node-codegraph-indexer / node-review-agent / node-scan-audit / node-coverage-audit / node-briefing-agent / node-exploit-chain-audit | Route mapping, data-flow tracing, auth, dependency scanning, index management, evidence QC, scan/coverage/parameter list/exploit chain |
| node vulnerability specialties (31) | node-proto-pollution-audit / node-cmd-audit / node-ssrf-audit / node-nosql-audit / node-file-upload-audit / node-xss-audit / node-ssti-audit / node-session-cookie-audit + P3 backfill 21 items (sql / xxe / deser / ldap / expr / xpath / file-read / file-write / archive-extract / filesystem / csrf / open-redirect / crlf / dom-xss / second-order / http-desync / config / crypto / logic / logging / supply-chain) + 2026-09-14 ledger round 2 items (node-spreadsheet-export-audit / node-ai-prompt-audit) | P1 high-value 8 + P3 backfill 21 + ledger round 2, symmetric with the dotnet family |
| node framework specialties (7) | node-express-audit / node-koa-audit / node-fastify-audit / node-nestjs-audit / node-nextjs-audit / node-nuxt-audit / node-graphql-audit | Triggered by stack_detect detection of the corresponding framework surface |
| node orchestration (1) | node-audit-pipeline | The sole scheduling entry of the node-side sub-pipeline |
| Cross-stack (4) | cross-stack-contract-mapper / cross-stack-taint-linker / cross-stack-consistency-audit / fullstack-audit-pipeline | Contract reconciliation + taint linking + configuration consistency + fullstack main entry |
| Agents (2) | node-code-audit / fullstack-code-audit | Single-stack / fullstack orchestration entries |
| shared (6) | NODE_AUDIT_GRABBER_INDEX.md / NODE_SINK_REFERENCE.md / NODE_VULN_SKILL_TEMPLATE.md / NODE_FRAMEWORK_SKILL_TEMPLATE.md / NODE_VULN_POC_TEMPLATE.md / FULLSTACK_FINAL_REPORT_FIXED_TEMPLATE.md | node specifications and templates + fullstack report template |

##### Delivery Status (2026-09-04 All ACTIVE)

- **node family P3 backfill complete (2026-09-04)**: 4 infrastructure orchestration items delivered (node-scan-audit / node-coverage-audit / node-briefing-agent / node-exploit-chain-audit) + all 21 vulnerability specialties delivered; all entries #6-10 and #27-47 in the node-audit-pipeline comparison table are ACTIVE, and the "degradation instruction for undelivered specialties" is retired; node-side and dotnet-side specialty coverage is symmetric
- The cross-stack 3-piece set is complete: cross-stack-contract-mapper (P1) → cross-stack-taint-linker / cross-stack-consistency-audit (P2), forming a "contract reconciliation → taint linking → consistency audit" closed loop in fullstack Phase 6
- All 7 node framework specialties delivered (express / koa / fastify / nextjs / nuxt / nestjs / graphql), all drafted from NODE_FRAMEWORK_SKILL_TEMPLATE.md (ten sections + three-layer structure), triggered by stack_detect results, output written to `node/framework_audit/{framework}_{timestamp}.md`
- node-review-agent delivered (P1-7, 2026-08-23): node-side audit-output evidence quality check and consistency validation (symmetric with dotnet-review-agent; includes evidence authenticity spot checks with minimal read-only re-verification rights), with completion state aligned to coverage-audit (commits 492f7e8 / deac83a / c57ad1d)
- node-codegraph-indexer delivered (P3-8, 2026-08-23): node-side CodeGraph index management (mandatory prerequisite; when unavailable, record the reason and fall back to static analysis); entry #11 in node-audit-pipeline upgraded from DEFERRED(P3) to ACTIVE (commit 31f12bf)
- EVID_NODE_CFG group landed (5 IDs, appended after the SESS group): SECURITY_SWITCH / RUNTIME_SETTING / MIDDLEWARE_ORDER / SSR_MODE / ERR_HANDLER
- Reference status ACTIVE: entries #12-18 of the node-audit-pipeline sub-skill comparison table, fullstack-audit-pipeline Phase 6, and the agent matrix have all been upgraded to "P2 delivered"
- Final wrap-up (2026-08-23): all P2 deliveries passed the final whole-branch review (rev-final-p2 ✅ / PASS-with-minors, 6/6 checks PASS); the 2 Minors from the T2+T3 review (taint-linker consumer path prefix, specialty name wording) and the 10 Minors from the T4+T5 review (evidence reference bidirectional consistency, etc.) were all fixed and closed (commits 3924e47 / 6ac9416); 4 PARK observation-item FIXes landed + 6 items remain registered (commit b44b878); 15 commits for the whole chain (072132a→3924e47), **zero changes to the dotnet family**
- **Skill registration ledger mechanism + capability gap backfill (2026-09-14)**: added `docs/NewSkillRegistration.md` governance ledger (mechanism merge gate + four dispositions + state machine); delivered 5 new specialties per the ledger (dotnet-query-injection / dotnet-spreadsheet-export / dotnet-ai-prompt / node-spreadsheet-export / node-ai-prompt); 5 existing extensions and 6 negative dispositions registered as pending/observe.
- **Existing skill mechanism extensions landed (2026-09-14 extension round)**: delivered 5 mechanism extensions per the ledger (account enumeration / audit integrity + availability / signed-request replay protection / configuration exposure + response information disclosure / integer overflow), covering 11 existing skills (6 dotnet files + 5 node files) with a "Mechanism Extensions" section appended at the end of each; 30 new evidence points added to the EVID dictionary (new NODE_AUTH group); all statuses capped at "implemented, pending verification".
- **Design-intent collection mechanism (2026-09-16, option A)**: both pipelines add Phase 0.7 (fail-open), distilling a `design_intent` six-section intent summary from the target repository's superpowers artifacts (docs/superpowers, docs/design, .superpowers/sdd); evidence layering rules added to `AUDIT_EXECUTION_COMMON.md` §9 (intent-layer references are forbidden as EVID citations; conflicts resolved in favor of code); logic-audit / auth-audit on both stacks are the first batch integrated (one input-dependency rule + one enumeration rule each); no new skills, no new EVID IDs.

## Evidence Contract

Core shared rules of the repository:

- shared/EVIDENCE_POINT_IDS.md
- shared/IO_PATH_CONVENTION.md
- shared/DOTNET_SINK_REFERENCE.md
- shared/DOTNET_AUDIT_GRABBER_INDEX.md
- shared/DOTNET_AUDIT_EXECUTION_STANDARD.md   # General execution standard (two-phase determination, fail-close, Barrier, testing requirements)
- shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md # Final report fixed template
- shared/DOTNET_FRAMEWORK_SKILL_TEMPLATE.md
- shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md
- shared/DOTNET_VULN_POC_TEMPLATE.md
- shared/DOTNET_VULN_SKILL_TEMPLATE.md
- shared/SEVERITY_RATING.md

Understanding is the same as the PHP version:

1. route-tracer outputs the parameter controllability matrix, Sink locations, Sink Summary, Trace completeness statement, and Sink Evidence Checklist
2. Each sub-audit skill must reference the corresponding EVID_* evidence points item by item
3. When key evidence is missing, only ⚠️Pending Verification or 🔍Environment-Dependent may be output
4. The pipeline must retain unclosed traces / the pending-evidence risk pool and must not silently delete them
5. dotnet-security-audit-skill uses mandatory on-disk persistence by default; structured phase artifacts must not exist only in the final aggregated report

Unified requirements for the shared grabber index:

1. Each vulnerability specialty references shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index by default
2. Framework specialties and route-tracer must also use that index for the five layers of entries, bindings, precondition controls, sensitive operations, and security configuration
3. If the project has secondary encapsulation, "project-internal grabbers" must be added to the specialty output rather than staying only at the framework-native API level

## Main Pipeline

Suggested execution order (consistent with the phase definitions of dotnet-audit-pipeline):

1. dotnet-codegraph-indexer (Phase 0, mandatory prerequisite; when unavailable, record the reason and fall back to static analysis)
2. dotnet-scan-audit (Phase 0.5, security scan)
3. dotnet-coverage-audit (Phase 0.6, coverage backfill)
4. dotnet-route-mapper → dotnet-auth-audit (STATIC_MAPPING) → dotnet-vuln-scanner → framework detection (Phase 1, reconnaissance)
5. Source → Sink modeling (Phase 2) and global sink fallback (Phase 2.5)
6. dotnet-route-tracer (Phase 3, batched tracing)
7. dotnet-briefing-agent (Phase 3.5, candidate parameter list)
8. Each vulnerability specialty skill + vuln_poc (Phase 4, Sink audit execution)
9. dotnet-review-agent (Phase 4.5, evidence quality check)
10. dotnet-audit-pipeline aggregated report (Phase 5)
11. dotnet-exploit-chain-audit (Phase 5.1, exploit chain aggregation)

In addition to `FULL | SAMPLE`, `coverage_mode` supports `INCREMENTAL`: it delimits the changed file set based on git diff (or a user-specified changed-file list) and expands the affected call chains, executing scan/route/trace/specialty audits only on that set; session-level resume-from-breakpoint state is uniformly maintained by `quality/manifest_{run_id}.md`.

**Fullstack mode**: when the audit target is a fullstack frontend-backend project (`stack_mode=BOTH`, inputs `dotnet_source_path` + `node_source_path`), `fullstack-audit-pipeline` is the sole main entry — Phase 0 first performs dual-stack stack-detect, then both stacks execute their sub-pipelines in parallel (artifacts isolated via `output_path` to `{root}/dotnet` and `{root}/node`, with zero changes to the dotnet-audit-pipeline body), Phase 6 performs the cross-stack audit (cross-stack-contract-mapper frontend-backend contract reconciliation), and finally everything is merged into a unified fullstack report; the report completion status uses the per-stack four declarations: `dotnet_api_coverage_status` / `node_api_coverage_status` / `contract_coverage_status` / `audit_surface_status`.

## Pipeline Orchestration Notes

dotnet-audit-pipeline is now not just the "final aggregation" but the unified orchestrator of the entire entry skill. It must explicitly consume the following structured artifacts:

- route_mapping/routes_{timestamp}.md
- route_mapping/params_{timestamp}.md
- auth_audit/auth_mapping_{timestamp}.md
- cross_analysis/high_risk_routes_{timestamp}.md
- route_tracer/{route_id}/trace_{timestamp}.md
- framework_audit/{name}_{timestamp}.md
- vuln_audit/{type}_{timestamp}.md
- vuln_poc/{type}_{timestamp}.md
- vuln_report/{project}_nuget_{timestamp}.md

In other words, the pipeline must not merely check "whether a specialty ran", but must know explicitly:

- which entries have been modeled
- which entries have been traced and what their trace_status is
- which framework specialties have produced framework-boundary conclusions
- which vulnerability specialties are based on trace / framework evidence
- which vulnerability specialties have generated Confirmed / Pending Verification / Environment-Dependent PoCs
- which places remain unclosed due to runtime implementation, environment configuration, proxy layers, or host differences

## How Structured Artifacts Are Consumed

### route-mapper artifacts

Provide a unified entry map:

- Route templates
- HTTP methods / Hub / GraphQL / WCF operation types
- Parameter structures
- Binding sources
- Request templates

This is the unified entry index for all subsequent skills.
Its standard output skeleton is in shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md.

### route-tracer artifacts

Provide a unified evidence chain:

- Parameter controllability matrix
- Sink Summary
- Trace completeness statement
- Sink Evidence Checklist
- Controller / ModelBinder / Filter / Middleware / DI chain tracing results

When vulnerability specialties make high-strength conclusions, they consume these by default with priority.
Its standard output skeleton is in shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md.

### framework_audit artifacts

Provide unified framework-boundary conclusions:

- Middleware order
- Filter / EndpointFilter / HubFilter coverage relationships
- Authorization policy bindings
- Serialization and template boundaries
- Host, proxy, configuration switches, runtime differences

Vulnerability specialties should not re-determine these framework-level facts from scratch; they should consume them as precondition evidence.

### vuln_audit artifacts

Provide categorized vulnerability conclusions:

- Confirmed risks
- Pending-verification risks
- Environment-dependent risks
- Required EVID_* evidence references
- Relationships with framework_audit / route_tracer

### vuln_poc artifacts

Provide PoCs or pending-verification PoCs for specialty vulnerabilities:

- Associated vulnerability ID
- Associated route_id
- Minimal request template
- Trigger preconditions
- Expected results
- Confirmed / Pending Verification / Environment-Dependent status

Its standard output skeleton is in shared/DOTNET_VULN_POC_TEMPLATE.md.

### exploit-chain artifacts

Responsible for connecting single-point risks into composite exploit chains, especially:

- Entry reachability
- Authentication weak points
- Parameter controllability
- Downstream high-value Sinks
- Amplification conditions caused by framework or configuration

## Recommended Directories and Artifact Relationships

- codegraph: CodeGraph index status and quality validation (Phase 0 artifacts)
- route_mapping: entry and parameter modeling
- auth_audit: static authentication mapping and high-risk entry bucketing
- route_tracer/{route_id}: structured tracing per entry
- vuln_poc: vulnerability specialty PoC / pending-verification PoC results
- framework_audit: framework specialty results
- vuln_audit: vulnerability specialty results
- cross_analysis: high-risk entries, trace batch plans, exploit chain aggregation
- vuln_report: dependency vulnerability scan results

## Default On-Disk Directory Structure

By default, this project does not "generate only one final report", but "physically create structured artifacts first, then aggregate".

By default, after executing dotnet-audit-pipeline, at least the following directories should be persisted:

- codegraph/
- scan_audit/
- coverage_audit/
- route_mapping/
- auth_audit/
- route_tracer/
- briefing/
- vuln_audit/
- vuln_poc/
- framework_audit/
- cross_analysis/
- vuln_report/
- exploit_chain/
- global_sink_fallback/
- review/
- quality/

If a phase has no explicit result, the directory should not be missing either; create the directory and use a file to explain the no-result or pending-verification reason.

Index files should also be written for each phase by default, for example:

- scan_audit/index_{timestamp}.md
- coverage_audit/index_{timestamp}.md
- route_mapping/index_{timestamp}.md
- auth_audit/index_{timestamp}.md
- route_tracer/index_{timestamp}.md
- briefing/index_{timestamp}.md
- vuln_audit/index_{timestamp}.md
- vuln_poc/index_{timestamp}.md
- framework_audit/index_{timestamp}.md
- cross_analysis/index_{timestamp}.md
- review/index_{timestamp}.md
- vuln_report/index_{timestamp}.md
- quality/pipeline_execution_{timestamp}.md

If a phase produced no formal finding, at least one of the following must be satisfied:

- state the no-result reason directly in the corresponding index_{timestamp}.md
- additionally write empty_result_{timestamp}.md explaining not executed / initial screening only / insufficient evidence / environment-dependent / not-applicable reasons

## dotnet-audit-pipeline Unified Coordination Rules

- route_tracer is the primary evidence source for most high-strength vulnerability conclusions
- framework_audit is the primary evidence source for framework boundaries, runtime control planes, and deployment differences
- vuln_poc is the default companion artifact of vuln_audit, no longer treated as an optional accessory output
- When the two conflict, the pipeline must retain the conflict and must not silently overwrite
- Without a trace, framework_audit may give framework-level risk hints first, but high-strength vulnerability conclusions remain subject to the trace gate
- Each vulnerability specialty must explicitly state whether it consumed framework_audit and route_tracer artifacts; if not consumed, the reason must be stated

If a specialty has not produced a "Confirmed PoC", a Pending Verification or Environment-Dependent PoC file must still be generated, rather than omitting the vuln_poc directory.

## Vulnerability Specialty Execution Statuses

To make the execution process auditable and accountable, all dotnet-*-audit vulnerability specialties should be recorded in one of the following statuses:

- NOT_RUN: not executed
- INITIAL_SCREENED: only grabber enumeration, keyword scanning, or entry coarse screening was done
- PARTIAL: specialty analysis entered, but evidence closure not yet completed
- COMPLETED: specialty analysis completed with formal output
- NOT_APPLICABLE: not applicable to the current project or current entry

This means "other vulnerability types" must not silently disappear even when they are not the focus of the round; they must at least be marked INITIAL_SCREENED or PARTIAL in the final aggregation rather than being unrecorded.

## Required Skill Sections (Acceptance Criteria)

Every `dotnet-*-audit` SKILL.md must contain:

1. `## Shared Grabber Index Reference` — declares the relationship with the shared index
2. `## Input Dependencies` — clarifies dependencies such as source_path, route_mapping, route_tracer
3. `## Key Checks` — the core check items of the specialty
4. `## Enumeration Rules (Mandatory Refinement)` — specific search keywords and record requirements
5. `## Barrier Verification Matrix (Mandatory)` — specialty-specific barrier types, verification actions, and determination criteria
6. `## Two-Phase Determination (Mandatory)` — references the two-phase determination process of `DOTNET_AUDIT_EXECUTION_STANDARD.md`
7. `## Determination Rules (Mandatory Refinement)` — specialty-specific conditions for Confirmed Vulnerability / Pending / False Positive
8. `## Testing Recommendations (Mandatory)` — positive / negative / regression test coverage requirements
9. `## Evidence References` — the referenced EVID_* evidence points
10. `## Output` — artifact paths and format requirements

> When adding/updating skills, vulnerability specialties are drafted from `DOTNET_VULN_SKILL_TEMPLATE.md`, and framework specialties from `DOTNET_FRAMEWORK_SKILL_TEMPLATE.md`, ensuring the Barrier verification matrix, two-phase determination, hit IDs, and test_id are included in the templates.

## Inputs and Outputs

### Inputs

- source_path: root directory of the .NET project or solution
- output_path: output directory, optional, default {source_path}_audit

### Outputs

In merged mode, the usual output is:

- {output_path}/{project_name}_dotnet_audit_{timestamp}.md

In standalone mode, each skill may persist independent files in the suggested directory structure; the logical names are equivalent to the merged-report sections.

The final merged report should at least contain:

- Execution list
- Skill usage and findings matrix
- Entry coverage matrix
- Trace coverage matrix
- Framework coverage matrix
- Vulnerability coverage matrix
- PoC coverage matrix
- Evidence conflicts and items pending review
- Risk statistics and exploit chains
- Unclosed traces / pending-evidence risk pool

The skill usage and findings matrix is recommended to include at least:

- skill_name
- skill_type
- execution_status
- findings_status
- primary_outputs
- depends_on
- notes

After a complete execution, one can then directly see:

- which dotnet-*-audit skills were actually invoked
- which only had initial screening
- which stalled halfway on trace or environment evidence
- which have confirmed findings
- which found nothing but executed completely

## Applicable Scenarios

- Pre-release audits of ASP.NET Core web projects
- White-box regression of legacy .NET Framework / WCF projects
- Fix verification after dependency upgrades
- Framework configuration and middleware order checks
- Focused review of high-risk points in authentication, serialization, files, and expressions

## Directory Structure

- dotnet-audit-pipeline: overall orchestration
- dotnet-route-mapper / dotnet-route-tracer: entry modeling and tracing
- dotnet-*-audit: categorized audits and framework specialties
- shared: evidence, path, Sink, and rating specifications

The current default physical output directories include:

- route_mapping
- auth_audit
- route_tracer
- vuln_audit
- vuln_poc
- framework_audit
- cross_analysis
- vuln_report
- quality

## How to Extend with New Skills and Artifact Templates

This project supports continued extension with new vulnerability specialties, but the extension must follow the current unified methodology; adding just a name and a few check items is not enough.

### 1. When a New Vulnerability Specialty Skill Is Needed

When any of the following conditions holds, a new standalone skill is recommended rather than squeezing it into an existing specialty:

- The risk type has an independent sensitive-operation model or Sink model
- Risk determination depends on unique framework mechanisms, runtime semantics, or configuration surfaces
- Existing specialties cannot clearly carry its enumeration rules, evidence references, and output requirements
- Audit results need separate statistics, separate rating, and separate entry into exploit chain aggregation

For example: if Message Queue, reverse-proxy trust boundaries, cache poisoning, SSTI variants, reflective-call abuse, object-mapping pollution, and similar types are added later, they should usually be built as new standalone skills.

### 2. Naming Rules for New Skills

- Vulnerability specialties are uniformly named dotnet-{type}-audit
- Framework specialties are uniformly named dotnet-{framework}-audit
- Names must directly reflect the specialty responsibility; avoid overly generic names such as custom, misc, security

Suggested examples:

- dotnet-cache-poisoning-audit
- dotnet-message-queue-audit
- dotnet-reflection-abuse-audit

For framework specialties, refer to shared/DOTNET_FRAMEWORK_SKILL_TEMPLATE.md; for vulnerability specialties, refer to shared/DOTNET_VULN_SKILL_TEMPLATE.md.

### 3. Minimum Structure of a New Vulnerability Specialty Skill

Each new vulnerability specialty should at least contain the following structure:

- YAML frontmatter: name, description
- Shared grabber index reference
- Key checks
- Enumeration rules (mandatory refinement)
- Evidence references
- Output requirements or output files

In other words, new specialties must stay consistent with current mature specialties and must not regress to coarse-grained documents with only "key checks".

If the new skill is a framework specialty, it should likewise keep the three-layer structure, but its output path should land in framework_audit/{framework}_{timestamp}.md, and its consumption relationship with route_tracer, vuln_audit, and pipeline must be stated explicitly.

### 4. Which shared Specifications Must Be Integrated

When adding a skill, the following shared documents must be referenced by default:

- shared/DOTNET_AUDIT_GRABBER_INDEX.md
- shared/EVIDENCE_POINT_IDS.md
- shared/IO_PATH_CONVENTION.md
- shared/SEVERITY_RATING.md
- shared/DOTNET_SINK_REFERENCE.md
- shared/DOTNET_AUDIT_EXECUTION_STANDARD.md
- shared/DOTNET_VULN_POC_TEMPLATE.md

Their responsibilities:

- Grabber index: unified search keywords, priority enumeration targets, and record fields
- Evidence IDs: unified conclusion reference criteria
- IO convention: unified logical section names and physical on-disk paths
- Rating rules: unified risk strength and wording boundaries
- Sink reference: unified sensitive-operation models
- Execution standard: unified two-phase determination, fail-close Barrier, hit ID, and testing requirements

If a new vulnerability type cannot be fully expressed by existing shared rules, shared should be supplemented first, and then the new skill — rather than letting a single skill privately define a new specification set.

### 5. How to Write "Key Checks"

Key checks define the risk surfaces most worth prioritizing for this vulnerability type. When writing, cover:

- Typical .NET native APIs or framework entries
- Common secondary-encapsulation locations
- Contextual conditions affecting whether the risk holds
- Amplification factors related to authentication, authorization, configuration, and host environment

Key checks should not be written as a list of vague concepts; they should directly point out as much as possible:

- which classes
- which methods
- which attributes or configurations
- which common business scenarios

### 6. How to Write "Enumeration Rules (Mandatory Refinement)"

Enumeration rules are the execution-layer core of a skill. Each rule should answer as much as possible:

- which keywords to search first
- which objects to enumerate next
- which fields to record for each hit
- how to supplement project-internal grabbers when secondary encapsulation appears
- which cases require further evidence chasing to route_tracer or framework_audit

Recommended writing style:

- which APIs / attributes / registration points to search first
- which entries, services, and wrapper layers to enumerate
- which input sources, branch conditions, protection logic, and final execution points to record
- for each hit, record code location, call-chain position, controllable parameters, protection measures, and associated entries

### 7. How to Define New Evidence Points

If a new vulnerability type needs new EVID_* evidence points, shared/EVIDENCE_POINT_IDS.md should be updated in sync.

When adding evidence points, follow:

- clear and stable naming that directly reflects the evidence semantics
- describe "factual evidence" as much as possible, not "conclusion labels"
- be stably referenceable by route_tracer, framework_audit, or specialty static analysis results

For example, do not write only EVID_HIGH_RISK; write something more specific:

- EVID_CACHE_KEY_USER_CONTROLLED
- EVID_PROXY_TRUST_HEADER_OVERRIDE
- EVID_REFLECTION_TARGET_USER_CONTROLLED

### 8. How to Integrate with dotnet-audit-pipeline

After adding a vulnerability specialty, pipeline integration must be considered in sync, rather than creating an isolated skill.

At least four things must be clarified:

- which input artifacts this specialty primarily consumes
- whether it depends on the structured trace of route_tracer
- whether it depends on the framework-boundary conclusions of framework_audit
- which vuln_audit/{type}_{timestamp}.md it ultimately outputs to

If a specialty highly depends on framework boundaries — such as caching, proxies, serialization, templates, or authentication context — it must explicitly declare its consumption relationship with framework_audit.

If a specialty highly depends on parameter controllability, call chains, and final execution points, it must explicitly declare its consumption relationship with route_tracer.

If the addition is a route mapping or tracing capability, beyond the skill's own rules, its output skeleton must stay consistent with shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md, to avoid breaking the structured consumption of the pipeline and downstream specialties.

### 9. How to Judge Whether the Extension Is Qualified

A new skill should at least meet the following acceptance criteria:

- name, description, and responsibility boundaries are clear
- the shared grabber index and other necessary shared rules are referenced
- the three-layer structure exists: key checks + enumeration rules + output requirements
- the evidence reference criteria are stated
- the relationships with route_tracer / framework_audit / pipeline are stated
- output paths comply with shared/IO_PATH_CONVENTION.md
- boundaries are distinguishable from existing specialties without large-scale overlapping responsibilities

### 10. Recommended Extension Process

The recommended extension order:

1. Define the responsibility boundary of the new vulnerability type first
2. Confirm whether new shared grabbers, Sinks, or EVID rules are needed
3. Create dotnet-{type}-audit/SKILL.md
4. Complete the three-layer structure and evidence references
5. State which route_tracer / framework_audit artifacts it consumes
6. Add it to the capability overview or extension notes in the README
7. Finally run a whole-directory validation

### 11. Shared Template Files

When adding a vulnerability specialty, prefer using shared/DOTNET_VULN_SKILL_TEMPLATE.md directly as the drafting template, rather than copy-pasting old fragments in the README.

When adding a framework specialty, prefer using shared/DOTNET_FRAMEWORK_SKILL_TEMPLATE.md.

When unifying route-mapper / route-tracer artifact formats, prefer using shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md, rather than repeatedly maintaining a separate set of format samples in each skill.

Usage:

- first copy the template body of shared/DOTNET_VULN_SKILL_TEMPLATE.md
- for a framework specialty, copy the template body of shared/DOTNET_FRAMEWORK_SKILL_TEMPLATE.md
- replace {type} with the specific vulnerability type
- then supplement key checks, enumeration rules (mandatory refinement), evidence references, and output requirements per the specialty
- if shared grabbers, Sinks, or EVID need extension, update the shared documents first, then update the new skill

Usage of the route-mapper / route-tracer artifact templates:

- routes_{timestamp}.md, params_{timestamp}.md, quality/route_mapper_validation_{timestamp}.md follow the route-mapper templates in shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md
- trace_{timestamp}.md, trace_summary_{timestamp}.md follow the route-tracer templates in shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md
- if additional fields are needed, they may only be appended while keeping the core sections and key fields unchanged

If you continue to extend this project, it is recommended to always treat "shared unified criteria + route_tracer evidence chain + framework_audit boundary conclusions + pipeline explicit consumption" as the four fixed constraints for new skills.

## May 2026 Coverage Optimization Update

### New Vulnerability Specialties (6) - Created ✅

| Specialty | Priority | Description |
|----------|--------|------|
| dotnet-xpath-audit | P2 | XPath injection audit, split from XXE |
| dotnet-supply-chain-audit | P0 | Supply chain security audit, OWASP A08 |
| dotnet-ssti-audit | P1 | Server-Side Template Injection audit, split from tpl |
| dotnet-dom-xss-audit | P2 | DOM-XSS audit, split from xss |
| dotnet-http-desync-audit | P2 | HTTP Desync / Request Smuggling audit |
| dotnet-second-order-audit | P2 | Second-order injection audit |

### New Framework Specialties (2) - Created ✅

| Specialty | Priority | Description |
|----------|--------|------|
| dotnet-grpc-audit | P1 | gRPC microservice communication security audit |
| dotnet-minimal-api-audit | P0 | Minimal API security audit, .NET 6+ core |

### Existing Specialty Enhancements (8)

| Specialty | Enhancement | Priority |
|------|----------|--------|
| dotnet-blazor-audit | .NET 8 prerendering security, Blazor United | P2 |
| dotnet-signalr-audit | Streaming messages, Backplane security | P2 |
| dotnet-graphql-audit | Field-level authorization, DataLoader security | P2 |
| dotnet-sql-audit | Second-order injection, WAF bypass detection | P2 |
| dotnet-xss-audit | DOM-XSS entries, CSP bypass | P2 |
| dotnet-cmd-audit | Linux/Windows differences, encoding bypass | P2 |
| dotnet-ssrf-audit | Gopher protocol, DNS rebinding | P2 |
| dotnet-aspnet-core-audit | AOT compilation, Source Generator | P3 |

### Coverage Statistics

- **Vulnerability specialties**: 32
- **Framework specialties**: 9

## This Round of Enhancements

### 2026-06 Coverage Gate Enhancement (Pipeline Criteria Convergence)

To avoid "specialty matrix complete" being misread as "active APIs fully covered", this round adds and strengthens the following constraints:

1. Added `coverage_mode: FULL | SAMPLE` (default FULL)
2. Added `route_mapping/controller_inventory_{timestamp}.md` as the route mapping prerequisite reconciliation artifact
3. Added `quality/api_coverage_gate_{timestamp}.md` as the API coverage gate artifact
4. Clarified the binding of `pipeline_execution` and `api_coverage_status`:
	- when `api_coverage_status != COMPLETE`, `pipeline_execution = COMPLETED` is forbidden
5. Clarified the dual completion statuses:
	- `audit_surface_status` (specialty coverage)
	- `api_coverage_status` (entry coverage)
6. Clarified the dual high-risk-route artifacts:
	- full: `cross_analysis/high_risk_routes_{timestamp}.md`
	- sampled: `cross_analysis/sampled_high_risk_routes_{timestamp}.md`

The sampled artifact must explicitly declare in the file header:

- `coverage_mode`
- `api_coverage_status`
- `controller_coverage_percent`
- `auth_coverage_percent`
- `disclaimer` (represents only candidates among mapped entries, not the full set of active APIs)

The above constraints have been synced to:

- `skills/dotnet-audit-pipeline/SKILL.md`
- `skills/shared/IO_PATH_CONVENTION.md`
- `skills/shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md`

This round made nine categories of structural enhancements to the .NET skill library (see `docs/memory/CHANGELOG_AND_DECISIONS.md` for details):

1. All framework specialties upgraded to the same three-layer structure as vulnerability specialties
2. dotnet-route-tracer upgraded to an execution-level chain tracing specification
3. shared added a unified grabber index, constraining the retrieval and enumeration criteria of each skill
4. All vulnerability specialties now uniformly and explicitly reference the shared grabber index
5. dotnet-audit-pipeline strengthened into a true unified orchestration entry, explicitly consuming route_tracer and framework_audit structured artifacts
6. Added shared vulnerability specialty template file, unifying the drafting of future skill extensions
7. Added shared framework specialty template file, unifying framework skill extensions
8. Added shared route / trace output template file, unifying route mapping and trace artifact formats
9. Added the pipeline mandatory on-disk persistence mode, and formally incorporated vuln_poc into the shared and pipeline output system

### 2026-06 Coverage Gate Phase-2 Strengthening (Template and Example Solidification)

Building on the coverage gate, this round continued to complete the "execution templates" and "minimal examples", reducing criteria drift:

1. Final report fragments solidified in `skills/dotnet-audit-pipeline/SKILL.md`:
	- mandatory dual completion statuses: `audit_surface_status` + `api_coverage_status`
	- mandatory coverage gate summary fields: `api_coverage_percent`, `pipeline_execution`, `gate_decision`
	- mandatory coverage scope statement (must declare "not a full-coverage conclusion" under SAMPLE/PARTIAL)
2. Added a lightweight execution validation checklist (mandatory at closing), recommended to persist:
	- `quality/quick_validation_{timestamp}.md`
3. Added a "minimal sample artifact pack" in `skills/shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md`:
	- `route_mapping/controller_inventory_{timestamp}.md`
	- `quality/api_coverage_gate_{timestamp}.md`
	- `cross_analysis/sampled_high_risk_routes_{timestamp}.md`

4. Standardized `quality/quick_validation_{timestamp}.md`:
	- added the quick validation skeleton and determination rules to the shared templates
	- added path conventions in `IO_PATH_CONVENTION`
	- the pipeline explicitly references the shared template; final validation format drift is forbidden

5. Bound `coverage_mode` to `trace_batch_plan` thresholds:
	- FULL: `trace_batch_max_size` allowed 10–30 (default 10)
	- SAMPLE: `trace_batch_max_size` allowed 5–10 (default 8; exceeding 10 forbidden)
	- plans exceeding thresholds must be judged invalid and re-planned

6. Exploit-chain report passes through the coverage scope (exploit-chain):
	- `exploit_chain/exploit_chains_{timestamp}.md` must carry `coverage_mode`, `api_coverage_status`, `api_coverage_percent`
	- when `coverage_mode=SAMPLE` or `api_coverage_status=PARTIAL`, chain conclusions must explicitly state "covers only the mapped-entry sample scope"
	- the chain overview table adds a `sampled_scope` field to avoid misreading sampled chains as full chains

7. Added `quick_validation_example` minimal example:
	- shared template addition: `quality/quick_validation_example_{timestamp}.md`
	- for training and regression comparison; does not replace the formal `quick_validation_{timestamp}.md`
	- unified example fields: context, checklist, final decision (PASS/BLOCKED)

8. SAMPLE mode adds a batch-count upper bound (batch_count_upper_bound):
	- `trace_batch_plan_{timestamp}.md` adds `batch_count_upper_bound` and `planned_batch_count`
	- when `coverage_mode=SAMPLE`, `planned_batch_count <= 6` is mandatory
	- plans exceeding the limit must be judged invalid and re-planned (prefer merging routes by module to reduce fragmented batches)

9. The final report adds a fixed exploit-chain coverage scope summary block:
	- the fixed final report template adds an `exploit-chain coverage scope summary` block
	- fixed fields: `exploit_chain_coverage_mode`, `exploit_chain_api_coverage_status`, `exploit_chain_api_coverage_percent`, `exploit_chain_sampled_scope`
	- `quick_validation_{timestamp}.md` and `quick_validation_example_{timestamp}.md` add a consistency check item for this block in sync

10. Added `coverage_consistency_check` cross-artifact consistency check:
	- new recommended artifact: `quality/coverage_consistency_check_{timestamp}.md`
	- used to uniformly check key field consistency among `api_coverage_gate`, `trace_batch_plan`, `exploit_chains`, and the final report
	- conflict determination rule: if a key-field conflict affects conclusion semantics, `final_status` must be `BLOCKED`, and a "conflicting field + source file + fix suggestion" triple is output
11. `quick_validation` template enhancement and FULL soft constraint:
	- `quick_validation_{timestamp}.md` adds a "Field Conflict Location" subsection that directly inherits `consistency_check` results
	- if `consistency_check_status=BLOCKED`, `final_decision` is linked to `BLOCKED`
	- the fixed final report template adds `4.5) Consistency Check Summary` with fields: `consistency_check_source`, `consistency_check_status`
	- FULL mode adds a soft batch-count reminder threshold: if `planned_batch_count > 20`, consider merging (forced re-planning not required)

12. `exploit_chain` output adds consistency_check linkage:
	- `dotnet-exploit-chain-audit` may optionally read `quality/coverage_consistency_check_{timestamp}.md`
	- when `final_status=BLOCKED`, chain "feasibility" must not be marked "Confirmed Feasible"; it must be downgraded with a conflict reference attached
	- the chain overview table adds a `consistency_check_status` field, and chain details add a consistency linkage block

13. The final report adds an exploit_chain consistency summary count:
	- the fixed template `4.5) Consistency Check Summary` adds `exploit_chain_consistency_check_counts`
	- when a consistency_check exists, PASS/BLOCKED/N/A counts must be consistent with the exploit_chain overview table
	- `IO_PATH_CONVENTION` adds the exploit_chain artifact mapping and BLOCKED semantics constraints in sync

14. Completed minimal examples and count statistics criteria:
	- `DOTNET_ROUTE_OUTPUT_TEMPLATES.md` adds a "final report fixed fragment minimal example (including consistency summary counts)"
	- `dotnet-exploit-chain-audit` adds a `consistency_check_counts` statistics example row (PASS/BLOCKED/N/A)
	- at execution time, reusing the examples directly is recommended to reduce final report field omissions and manual statistics errors

15. Final double-check flow diagram (execution order visualization):
	- `coverage_gate -> consistency_check -> quick_validation -> exploit_chain/final_report` solidified into a unified flow
	- blocking semantics clarified: when `consistency_check_status=BLOCKED`, "Confirmed Feasible" conclusions must not be entered
	- used for onboarding newcomers and pre-delivery walkthroughs, reducing missed steps

16. Added quick_validation failure counterexample (count reconciliation failure):
	- `Quick Validation Example (Blocked)` added to `DOTNET_ROUTE_OUTPUT_TEMPLATES.md`
	- typical failure: `exploit_chain_consistency_check_counts` inconsistent with the exploit_chain overview table
	- conclusion requirement: when `consistency_check_status=BLOCKED`, `final_decision` must be `BLOCKED`

17. Extracted the final report fixed template + pipeline flow anchors:
	- added `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md` as the single source of truth for the final report quality section
	- `DOTNET_ROUTE_OUTPUT_TEMPLATES.md` and `dotnet-audit-pipeline/SKILL.md` now reference that template to avoid multi-place maintenance drift
	- the pipeline adds a "final double-check flow anchor (execution jump)" executing in the order `api_coverage_gate -> consistency_check -> quick_validation -> exploit_chain -> final_report`

18. exploit-chain adds a BLOCKED count-anomaly automatic degradation wording template:
	- "Step 7: BLOCKED count-anomaly automatic degradation wording template (mandatory)" added to `dotnet-exploit-chain-audit/SKILL.md`
	- trigger condition: `consistency_check_status=BLOCKED` or `exploit_chain_consistency_check_counts` reconciliation failure
	- mandatory action: chain feasibility downgraded to "Inferred Feasible / Theoretically Feasible", with fix actions and source-file references attached

19. Added unmapped-entry standalone artifact + remapping loop template:
	- when `api_coverage_status=PARTIAL`, outputting `quality/unmapped_routes_{timestamp}.md` is mandatory
	- added `quality/route_mapping_backfill_loop_{timestamp}.md` template (recommended), recording remapping rounds and convergence
	- pipeline clarified: the route mapping phase must not end while unmapped active controllers/entries remain non-zero and the user has not explicitly terminated it

20. The final report fixed template adds a BLOCKED minimal example:
	- added "BLOCKED minimal example (count reconciliation failure)" to `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md`
	- used to train executors to recognize the scenario where "final report fields are complete but consistency counts are still not deliverable"
	- clarified: when `consistency_check_status=BLOCKED` or counts are inconsistent, the final report must be fixed first and then `quick_validation` re-run

21. exploit-chain adds a "standard re-run order after count fixes":
	- added the `final_report -> consistency_check -> quick_validation -> exploit_chain` re-run order to `dotnet-exploit-chain-audit/SKILL.md`
	- purpose: avoid fixing one count while missing linked artifacts and wording restoration

22. pipeline adds a "final anchor checklist" template:
	- new recommended artifact: `quality/final_anchor_checklist_{timestamp}.md`
	- used to check off `api_coverage_gate / consistency_check / quick_validation / exploit_chain / final_report` file by file
	- added a PASS/BLOCKED/PENDING summary block for judging closing status at a glance

23. shared adds an exploit-chain BLOCKED failure counterexample:
	- `Exploit Chains Example (Blocked)` added to `DOTNET_ROUTE_OUTPUT_TEMPLATES.md`
	- used to train executors to recognize the scenario where "the exploit chain file itself also needs degraded wording"

24. The final report fixed template adds a "final anchor check result reference":
	- `4.6) Final Anchor Check Result Reference` added to `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md`
	- used to write back the `final_anchor_decision` and PASS/BLOCKED/PENDING counts of `final_anchor_checklist_{timestamp}.md`

25. shared adds a BLOCKED counterexample for `unmapped_routes`:
	- `Unmapped Routes Backlog (Blocked)` added to `DOTNET_ROUTE_OUTPUT_TEMPLATES.md`
	- used to train executors to recognize the scenario where "delivery must be blocked when entry coverage is not fully remapped"

26. `final_anchor_checklist` adds a BLOCKED source file summary:
	- added a `BLOCKED Source File Summary` subsection to the pipeline template
	- used to quickly locate which anchor file is blocking the delivery status

27. `IO_PATH_CONVENTION` completes the final anchor write-back mapping:
	- added the `quality/final_anchor_checklist_{timestamp}.md` path mapping
	- added the "Final Report Fixed Field Write-Back Sources" table, clarifying the single sources of `final_anchor_checklist_source`, `final_anchor_decision`, and `final_anchor_checklist_counts`
	- added constraint: if `final_anchor_decision=BLOCKED`, the final report must not use positive closing wording such as "deliverable / passed"

28. shared adds PASS/BLOCKED minimal examples for `final_anchor_checklist`:
	- positive and negative examples for `quality/final_anchor_checklist_{timestamp}.md` added to `DOTNET_ROUTE_OUTPUT_TEMPLATES.md`
	- clarified `checklist_blocked_count > 0 => final_anchor_decision=BLOCKED`
	- clarified that when `final_anchor_decision=BLOCKED`, the final report must not write "deliverable / passed / closing complete"
29. `DOTNET_FINAL_REPORT_FIXED_TEMPLATE` adds the `unmapped_routes_source` field:
	- added field `unmapped_routes_source` to the fixed skeleton template `2) Coverage Gate Summary`
	- acceptance constraint: when `api_coverage_status=PARTIAL` it must not be N/A and must point to an actual artifact
	- both PASS and BLOCKED examples fill in the actual path in sync

30. `IO_PATH_CONVENTION` adds a `final_anchor ↔ final_report 4.6` minimal reconciliation example:
	- added a three-field mapping table between the checklist summary block and the final report 4.6 fields
	- clarified typical reconciliation failure counterexamples to prevent "one place changed, the other missed"
```mermaid
flowchart TD
	A[quality/api_coverage_gate_{timestamp}.md] --> B[quality/coverage_consistency_check_{timestamp}.md]
	B -->|PASS| C[quality/quick_validation_{timestamp}.md]
	B -->|BLOCKED| D[Fix conflicts and write back related artifacts]
	D --> B
	C --> E[exploit_chain/exploit_chains_{timestamp}.md]
	E --> F[{project_name}_code_audit_{timestamp}.md]
	B --> G[consistency_check_status]
	G --> C
	G --> E
	E --> H[exploit_chain_consistency_check_counts]
	H --> F
```
This example pack is used for regression alignment: executors can directly check whether fields, statuses, and value domains conform to the gate semantics.

### 1. Framework Specialties Completed with the Three-Layer Structure

The following framework skills have been uniformly completed into Key Checks + Enumeration Rules (Mandatory Refinement) + Output Requirements:

- dotnet-aspnet-core-audit
- dotnet-mvc-audit
- dotnet-webapi-audit
- dotnet-blazor-audit
- dotnet-signalr-audit
- dotnet-graphql-audit
- dotnet-wcf-audit

After this completion, framework specialties are no longer just "reminders of what to look at"; they explicitly require:

- which .NET APIs, attributes, registration points, filters, or middleware to search
- which fields at minimum must be recorded per finding
- what sections a framework report should follow, avoiding scattered-point-only conclusions

### 2. dotnet-route-tracer Refined into an Execution-Level Specification

dotnet-route-tracer now requires explicit tracing of the following chains, rather than staying at the abstract "entry to Sink" description:

- Controller / Action metadata
- Binding/conversion layers such as ModelBinder / ValueProvider / JsonConverter / BindAsync
- Precondition control layers such as Filter / EndpointFilter / HubFilter / MessageInspector
- Middleware / branch pipeline / Route Group metadata stacking
- DI resolution chains from interfaces to implementation classes, decorators, factories, proxies, and typed clients

Also supplemented:

- CRITICAL rules
- Core tracing scope
- Five categories of detailed rules for Controller / Binder / Filter / Middleware / DI
- Output template constraints
- More explicit Trace completeness statement requirements

This brings route-tracer closer to the detail level of dotnet-route-mapper, and allows it to more stably provide reusable evidence to downstream vulnerability specialties.

### 3. shared Adds the .NET Audit Grabber Index

New file: shared/DOTNET_AUDIT_GRABBER_INDEX.md

Purpose:

- unify the search keywords of the five layers: entry definition, binding/conversion, precondition controls, sensitive operations, and security configuration
- unify the fields that must be recorded at minimum for each type of enumeration
- unify the supplementation method for project-internal secondary encapsulation

This way, when further refining skills later, there is no need to define search grabbers from scratch in every file; instead, the same baseline index is shared and specialty differences are layered on top.

### 4. All Vulnerability Specialties Uniformly Reference the Shared Grabber Index

All 24 vulnerability specialty skills have now been supplemented with a "Shared Grabber Index Reference" section.

This means:

- every vulnerability specialty explicitly declares shared/DOTNET_AUDIT_GRABBER_INDEX.md as its basic retrieval index
- every vulnerability specialty is required to supplement project-internal private-encapsulation grabbers on top of the shared grabbers
- the enumeration rules of the specialties no longer drift from one another, and future maintenance is easier to keep consistent

### 5. dotnet-audit-pipeline Strengthened as the Unified Orchestration Entry

dotnet-audit-pipeline now clearly specifies:

- which shared rules must be read
- what inputs each phase consumes and what structured results it produces
- how framework_audit and route_tracer are explicitly consumed by downstream vulnerability specialties
- what coverage matrices and conflict-retention sections the final report must have at minimum

After this strengthening, dotnet-audit-pipeline is no longer just an "aggregation description", but the true coordination entry of the entire .NET skill library.

> 📋 Second-round enhancement details have been moved to `docs/memory/CHANGELOG_AND_DECISIONS.md`

## July 2026 CodeGraph Integration Enhancement (After Round 27)

### Goal

Integrate the CodeGraph pre-indexed code knowledge graph tool into the audit pipeline, mandating index building in Phase 0; when indexing succeeds, it accelerates route-mapper and route-tracer; when it fails, it automatically falls back to static analysis.

### New Skill

- `dotnet-codegraph-indexer`: detects the CodeGraph environment, builds/refreshes the index, and produces the index status file

### Modified Skills

| Skill | Changes |
|-------|----------|
| `dotnet-audit-pipeline` | Phase 0 adds CodeGraph index building; output directory adds `codegraph/`; orchestration principles add codegraph-indexer scheduling |
| `dotnet-route-mapper` | Added CodeGraph acceleration branch: prefer obtaining Controller/Action/route mappings via `codegraph_explore` |
| `dotnet-route-tracer` | Added CodeGraph acceleration branch: prefer obtaining cross-file call chains and DI resolution chains via `codegraph_callers` / `codegraph_impact` |

### Modified shared Specifications

- `DOTNET_AUDIT_GRABBER_INDEX.md`: added the "Cross-File Call Chain Tools (Optional Acceleration)" section, listing the purpose and constraints of each CodeGraph command
- `IO_PATH_CONVENTION.md`: added the `codegraph/` directory and the `codegraph_index_status_{timestamp}.md` and `codegraph_index_validation_{timestamp}.md` path mappings

### Execution Order Update

```
dotnet-codegraph-indexer (mandatory prerequisite; when unavailable, record the reason and fall back to static analysis)
  → dotnet-route-mapper → dotnet-auth-audit(STATIC) → dotnet-vuln-scanner
  → dotnet-route-tracer → framework_audit → vuln_audit(each specialty)
  → dotnet-exploit-chain-audit → aggregated report
```

### Key Constraints

- CodeGraph is a **mandatory prerequisite tool**; index failures must record the reason and persist a status file, and subsequent skills automatically fall back to static analysis
- Without an index, route-mapper / route-tracer fall back 100% to the existing static analysis process
- Symbols and call chains returned by CodeGraph still require cross-validation with source code snippets; differences are marked `⚠️manual review required`

## August 2026 P0/P1 Structural Refactoring

### New Pipeline Phases (4)

| Phase | Skill | Type | Description |
|------|-------|------|------|
| Scan phase | `dotnet-scan-audit` | Audit | Full-codebase scanning, producing the route_mapping baseline |
| Coverage backfill | `dotnet-coverage-audit` | Audit | Incremental-change-triggered backfill, maintaining coverage state |
| Candidate parameters | `dotnet-briefing-agent` | Agent | Generates candidate vulnerability parameter lists, supporting PoC construction |
| Evidence QC | `dotnet-review-agent` | Agent | Evidence chain closure validation, Severity consistency check |

### Deep Refactoring of Existing Specialties (2)

| Specialty | Refactoring | Impact |
|------|----------|------|
| `dotnet-sql-audit` | Added Barrier verification section (whitelist / parameterization / context three-layer barriers) | SQL injection audit precision improved, false positives reduced |
| `dotnet-second-order-audit` | Introduced `source_write_entry` / `source_trigger_entry` deep distinction + three-layer verification determination matrix | Second-order injection audit upgraded from "trigger after storage" to a precise responsibility-separation model |

### Shared Template Upgrades (2)

| Template | Upgrade | Impact Scope |
|------|----------|---------|
| `DOTNET_VULN_POC_TEMPLATE.md` | Added exclusion chain (marks non-exploitable when Barrier passes) | All vulnerability PoCs |
| `DOTNET_ROUTE_OUTPUT_TEMPLATES.md` | Added `taint_nodes` structured field definitions (6 taint_type values) | All route / trace / audit outputs |

### Pipeline Integration

`dotnet-audit-pipeline` has updated the sub-skill comparison table and the output directory structure, adding standardized integration points for the 4 new phases.

### Output Directory Extensions

New directories added:
- `coverage/`: coverage backfill results
- `briefing/`: candidate parameter lists
- `quality/`: evidence QC results (existed; now strengthened into a formal phase artifact)

### Changelog

Detailed change records see: `CHANGELOG-P0P1.md`

### Backward Compatibility

- **Breaking change**: `dotnet-second-order-audit` conclusion format upgrade (legacy `Confirmed/Pending Verification` → new version with the three-layer determination matrix)
- **Non-breaking changes**: `taint_nodes` is a new field; the Barrier verification section is a new section; the new pipeline phases are optional triggers

### Consistency Verification

This refactoring passed cross-file consistency checks:
- ✅ All 9 core files exist
- ✅ taint_nodes structure consistent
- ✅ Pipeline sub-skill references aligned
- ✅ Severity ratings consistent
- ✅ YAML name-directory alignment

> Verification time: 2026-08-14

---

## August 2026 General Execution Standard and Barrier Verification Matrix Strengthening

### Goal

Introduce a unified execution standard for all vulnerability specialties, solving the problems of "conclusion drift, missing barrier verification, and insufficient test coverage" during audits. Via shared documents + specialty adaptation, two-phase determination, fail-close evaluation, hit ID tracking, and testing recommendations become mandatory requirements for all vulnerability specialties.

### New Shared Document

| Document | Path | Purpose |
|------|------|------|
| `DOTNET_AUDIT_EXECUTION_STANDARD.md` | `skills/shared/` | Source of truth for the general execution standard: two-phase determination process, fail-close three-level determination, Barrier verification generic actions, testing requirements, hit ID conventions |

### Specialty Synchronization Refactoring (All Vulnerability/Framework Specialties)

The following vulnerability specialties have completed deep refactoring per the general execution standard, adding Barrier verification matrix, two-phase determination, determination rules, and testing recommendations sections; the minimal output fragment appends `Hit ID` and `test_id`:

| Specialty Category | Count | Status |
|----------|------|------|
| Injection class | 10 | ✅ Completed |
| Web security | 7 | ✅ Completed |
| File operations | 5 | ✅ Completed |
| Protocol & headers | 3 | ✅ Completed |
| Configuration & crypto | 3 | ✅ Completed |
| Business logic | 4 | ✅ Completed |
| Framework specialties | 9 | ✅ Completed |
| **Total** | **41** | **✅ All completed** |

> Note: `dotnet-archive-extract-audit` was originally an omission of the C5 batch; its Barrier verification matrix and two-phase determination were completed in this round.

### Template Upgrades

| Template | Upgrade | Impact Scope |
|------|----------|---------|
| `DOTNET_VULN_SKILL_TEMPLATE.md` | Added Barrier verification matrix, two-phase determination, determination rules, and testing recommendations section templates; the minimal output fragment appends `Hit ID: M{hash}` and `test_id: T{hash}` | All future new vulnerability specialties |
| `DOTNET_FRAMEWORK_SKILL_TEMPLATE.md` | Same as above, adapted to the framework specialty context | All future new framework specialties |

### Key Constraints

1. **Barrier Verification Matrix (Mandatory)**: every vulnerability specialty must contain `B1/B2/B3` three-level fail-close Barriers; failure of any one terminates the determination
2. **Two-Phase Determination (Mandatory)**: Phase 1 structural hit → Phase 2 semantic confirmation → conclusion output (FOUND / PENDING_VERIFICATION / NO_FINDING)
3. **Hit ID (Mandatory)**: every vulnerability conclusion must carry a `Hit ID: M{hash}` for cross-artifact traceability
4. **test_id (Mandatory)**: every test verification must record a `test_id: T{hash}` associated with the hit ID
5. **Three conclusion tiers**: `FOUND` / `PENDING_VERIFICATION` / `NO_FINDING`; blank or softened wording is forbidden

### Backward Compatibility

- **Non-breaking changes**: the Barrier verification matrix, two-phase determination, determination rules, and testing recommendations are all new sections
- **Minimal output fragment**: appends the `Hit ID` and `test_id` fields; legacy output remains compatible
- **Shared standard references**: each specialty references the shared document, without changing the original core logic

This refactoring passed cross-file consistency checks:
- ✅ All 41 vulnerability/framework specialty SKILL.md files contain a Barrier verification matrix
- ✅ All 41 specialties have appended `Hit ID` and `test_id` to the minimal output fragment
- ✅ `DOTNET_VULN_SKILL_TEMPLATE.md` and `DOTNET_FRAMEWORK_SKILL_TEMPLATE.md` templates synced
- ✅ `CLAUDE.md` and `README.md` updated with the required skill sections and shared specification descriptions

> Verification time: 2026-08-19

## Round 41 Category-A Quick Fixes (2026-09-18)

Based on `docs/2026-09-18-real-audit-verification-playback-and-fix-plan.md` and a colleague's real-run playback, 6 existing shared-contract defects received quick fixes (small template/script changes, no new mechanisms):

1. **P0-1 route count self-check**: the route output template adds the routes count reconciliation section and the checkpoint count self-check gate; route-mapper must persist it
2. **P0-2 dual-field count criteria unification**: the IO convention and dual-stack route templates enforce the `unique` / `method_path_count` dual-field criteria; the contract-mapper three-bucket denominator locks on `method_path_count`
3. **P0-3 WARN reconciliation scripted**: `scripts/validate_audit.py` adds 4 checks: route count / exploit / final_anchor reconciliation and consistency merge detection
4. **P1-6 orchestration de-polling**: fullstack-audit-pipeline switches to PHASE_STATUS milestone write-back instead of disk polling; `shared/PHASE_STATUS.md` becomes the sole source of truth for the manifest milestone line format, symmetrically referenced by the dotnet / node pipeline manifest sections
5. **P1-8 node consistency artifact symmetry**: node consistency_check upgraded to a mandatory artifact, referencing the dual-stack isomorphic merge marker format
6. **P2-14 final report severity detail-level rules**: `shared/FULLSTACK_FINAL_REPORT_FIXED_TEMPLATE.md` solidifies the mandatory severity detail-level rules

### Key Constraints

- Count iron rule, zero drift: dotnet 53 / node 49 (106 total) / vulnerability specialties 35 / node 31 all unchanged; no skills added or removed this round
- Acceptance baseline unchanged: `scripts/validate_audit.py scripts/_demo_audit/` output stays `PASS=1 FAIL=4 WARN=17`

> Verification time: 2026-09-18

## Round 42 Category-B Mechanism Extensions (2026-09-18)

Based on `docs/superpowers/specs/2026-09-18-b-class-mechanism-extensions-design.md` and the "register first, implement later" convention, all 7 items of the Category-B mechanism extension batch are integrated into existing skills / pipelines without adding directories (16 implementation commits + 3 review supplements + wrap-up; 7 ledger items flipped to "implemented, pending verification"):

1. **P1-4 Phase 0.7 recursive probing + negative-conclusion recheck**: design_intent probing switched to recursive globs (`**/docs/superpowers/`, `**/.superpowers/sdd/`, `**/docs/design/`); sub-pipelines perform a cheap independent recheck of "not found" negative conclusions; artifacts add a `search_scope` self-evidence block (§9 supplementary rules ⑤⑥; positive conclusions do not require a recheck)
2. **P2-12 intent-source whitelist extension**: ADR/RFC-type decision directories added to the configurable intent-source whitelist, with the same six-section summary distillation; red lines unchanged
3. **P1-5 Phase 6 order constraint**: contract-mapper lands its artifact first; consistency-audit / taint-linker start in dependency order, eliminating input races
4. **P1-7 pending-evidence risk pool unified schema**: seven-field schema + `quality/pending_pool_{timestamp}.md` single source of truth, auto-aggregated at closing; validate adds two optional reconciliation checks
5. **P2-13 embedded foreign-stack project detection**: stack-detect adds a "## Embedded Foreign-Stack Projects" section and a three-state ownership decision table (sample / production reference / documentation only), with the GC6 exception explanation; blanks are not allowed
6. **P2-11 supply chain offline enhancement**: scan artifacts add `knowledge_cutoff_date` and `offline_report_source` fields, supporting user-injected offline audit reports
7. **Specialty dispatch verification**: vulnerability specialty index templates and orchestration-layer trigger lists get three-state verification (Triggered / Negative Evidence / Not Applicable), eliminating silently missed dispatches

### Key Constraints

- Count iron rule, zero drift: dotnet 53 / node 49 (106 total) / vulnerability specialties 35 / node 31 all unchanged; no skills added or removed this round
- Acceptance baseline unchanged: `scripts/validate_audit.py scripts/_demo_audit/` output stays `PASS=1 FAIL=4 WARN=17`; P1-4 has passed dogfooding + fault-injection self-checks; the other 6 items await the next real-run playback

> Verification time: 2026-09-18

## Round 43 Category-C Architectural First Item (2026-09-19 node-feature-api-mapper Feature↔API Mapping Layer)

Based on `docs/superpowers/specs/2026-09-19-node-feature-api-mapper-design.md` and the 2026-09-19 brainstorming kickoff (all three decisions took option A), the first of the 3 Category-C architectural items, P2-9 feature↔API mapping layer, completed spec→plan→SDD delivery in four batches (skill body → consumer integration → pipeline integration → wrap-up):

1. **New `node-feature-api-mapper`**: three-layer mapping of feature surface → endpoints → backend route_id (SPA route table extension / component-tree import reverse index ≤6 levels / client method → endpoint reusing the frontend_outbound rg rules); three whitelist penetration modes penetrating one layer; three-class mandatory fallback for broken links (silent dropping forbidden; PARTIAL remapping loop); artifact `feature_api_map_{timestamp}.md` (four mandatory header fields + three-section template); pure-BFF projects without an SPA fail-open with `NOT_APPLICABLE` probe evidence
2. **Consumer integration**: node-logic-audit "feature-surface organization determination", node-auth-audit "feature view priority (export / delete / bulk / tenant / credential endpoints go straight to P0)", dotnet-route-tracer traces_index adds a `feature` column (fullstack reverse-lookup of feature_api_map; single-stack controller-domain heuristic, annotated as non-evidence)
3. **Pipeline integration**: fullstack Phase 6 inserts P1.5 (after contract-mapper, connecting with Round 42 P1-5 order constraint); node pipeline optional Phase 1.8; PHASE_STATUS table adds a delivery-status row
4. **Artifact red line**: all artifacts are view-layer references, forbidden as EVID evidence sources (same red line as design_intent §9); code wins on inconsistency, registering a "feature view - implementation drift" governance finding

### Key Constraints

- Count evolution: node 49→50, total 106→107 (batch 1 created the directory and synced the whole library); the skill directory renamed to `node-feature-api-mapper` completing the node family naming convention, so `ls skills/ | grep -c '^node-'` = 50 holds literally; vulnerability specialty counts dotnet 35 / node 31 unchanged; historical round entries keep their old counts as historical records
- Acceptance baseline unchanged: `scripts/validate_audit.py scripts/_demo_audit/` output stays `PASS=1 FAIL=4 WARN=17`; zero new EVIDs
- Ledger `node-feature-api-mapper` flipped to "implemented, pending verification" (dogfood NOT_APPLICABLE probing + scratch fault-injection dual paths reproduced through independent review; awaiting the next real-run playback); pending-verification count 14 → 15

> Verification time: 2026-09-19

## Round 44 Category-C Architectural Second Item (2026-09-19 DYNAMIC_VERIFY(STATIC_UNIT) Dynamic Verification Phase, P2-10)

Based on `docs/superpowers/specs/2026-09-19-dynamic-verify-unit-design.md`, the second of the 3 Category-C architectural items, P2-10 dynamic verification phase, completed spec→plan→SDD delivery in three batches (schema + shared template → dual pipeline Phase 7 + semantic linkage → wrap-up):

1. **pending_pool schema extension**: "Closure Method" three-value enum (`static-evidence` / `dynamic-unit` / `needs-env`) + entry status enum (`OPEN` / `DYNAMIC_VERIFIED`) + status bucket counts (`open_count` / `dynamic_verified_count`, `pool_total` scope unchanged) + heuristic inference for historical artifacts (`skills/shared/IO_PATH_CONVENTION.md`)
2. **New `skills/shared/DYNAMIC_VERIFY_UNIT_TEMPLATE.md`**: four-zero red-line self-check (zero credentials / zero network / zero services / zero writes outside the scratch directory) + dotnet xunit / node vitest dual test project skeletons (copy-don't-reference) + run and write-back protocol
3. **Dual pipeline optional Phase 7**: dotnet-audit-pipeline / node-audit-pipeline each insert "Phase 7: DYNAMIC_VERIFY(STATIC_UNIT)" (optional, fail-open); the two-level semantics of "Confirmed (Dynamic Verification)" are unchanged verbatim, with only one cross-reference sentence appended (the only compliant trigger path); IO_PATH_CONVENTION registers the dynamic_verify artifact paths

### Key Constraints

- The mechanism-extension three-piece set creates no skill directories: counts 53/50/107 unchanged; zero new EVIDs
- Conservative semantics: FAILED stays OPEN, needs-env is skipped, no result changes the `audit_surface_status` determination; batch-2 review confirmed the conservative-semantics diff has zero deletions
- Integration-level dynamic verification (service startup / test tenants / credential hosting) is explicitly tracked as a separate project; this phase covers only the STATIC_UNIT scope
- Acceptance baseline unchanged: `scripts/validate_audit.py scripts/_demo_audit/` output stays `PASS=1 FAIL=4 WARN=17`
- Ledger P2-10 flipped to "implemented, pending verification" (three fault-injection walkthrough cases reproduced through independent review: A:VERIFIED status flip / B:FAILED stays OPEN / C:needs-env skipped; awaiting real-run playback); pending-verification count 14 → 15 (grep actual count)
- Two leftover batch-2 review supplement sentences, each in an independent commit: Phase 7 vs final report risk-pool count reference order note (dual pipelines); node pipeline risk-pool reference path prefix aligned to the `node/quality/` convention

> Verification time: 2026-09-19

## 2026-09-20 Real-Run Playback (10 Ledger Items Flipped to Verified, Pending Verification 15 → 5) + Option A

Based on the artifacts of run `api-main_2026_09_20_10_38` (`temp/apccr_fullstack_audit_feedback_2026_09_20/api-main_fullstack_audit/`, read-only reference), all 15 ledger items pending verification were fully verified, with the conclusion: 10 passed / 5 failed:

1. **Playback**: 10 items flipped to "verified" with evidence — `dotnet-ai-prompt-audit` (dispatch verification section explicitly Not Applicable with reason) / `node-feature-api-mapper` (four fields complete, 11 features / 97 endpoints / COMPLETE) / P2-10 DYNAMIC_VERIFY (NOT_RUN + four-zero red lines verified item by item + 7 dynamic-unit items staying OPEN) / P1-4 Phase 0.7 (search_scope six-pattern self-evidence + dual-stack AGREE(65)) / P2-12 whitelist (adrs 3 hits / rfcs 0 verified) / P1-5 Phase 6 order (consuming contract_map buckets without contradiction) / P1-7 pending_pool (74/72 buckets + §7 mandatory references) / P2-13 embedded foreign stack (three-state registration + M-CRYPTO-002) / specialty dispatch verification (dual-stack 51/49 rows all three-state, no bare "not triggered") / dotnet-config-audit configuration exposure extension (three dimensions complete); 5 items stay pending verification with failure root causes registered (account enumeration / log tampering flooding / signed replay / integer overflow zero mention on the dotnet side without negative evidence + P2-11 half-passed with node fields complete but dotnet missing the literal field); pending-verification count 15 → 5
2. **Option A**: the dual-channel discipline for negative conclusions in Q&A scenarios written into the 4 agent definitions + dual pipeline 0.7 existence-check mandatory clause (5 commits the same day: `f32cd3e` / `16ec33c` / `c125b46` / `63910ae` / `a89956a`); not a new mechanism, ledger maintenance log records by batch

### Key Constraints

- One-sentence systemic root cause of the 5 failures: dimension-level enumeration had not entered the mandatory specialty lists, so silent dimension misses within specialties were not covered by dispatch verification (which only covers the specialty level) — merged into the defect-batch input
- Ledger: 10 status rows + verification evidence rows flipped, 5 verification evidence rows updated, maintenance log appended with the playback batch record; mechanism text unchanged
- Next step: defect-batch kickoff (colleague's 12 items + these 5 failures merged into the plan, including the design of the new "dimension-level dispatch verification" mechanism)

> Verification time: 2026-09-20

## Round 45 (2026-09-20 Defect Fix Batch, 17 Defects Delivered in 3 Batches via SDD)

Based on `docs/superpowers/specs/2026-09-20-defect-fix-batch-design.md`, the 5 playback failures + 12 colleague feedback items merged into 17 defects, delivered spec→plan→SDD in three batches (two-stage review between batches ×3 all passed + 2 review leftover supplement sentences each in an independent commit):

1. **Batch 1 count and criteria closure**: pending_pool one ID per row, alias merging forbidden + three formulas solidified (`pool_total` = unique pool_id count / statistics table count = detail enumeration count / closed = sum of non-false-positive non-pending items) + final_anchor three machine-verification lines + `run_timestamp` unified fullstack issuance to both stacks + SEVERITY rating enum closure C/H/M/L (range values forbidden; upgrade-channel annotation "suggest upgrade to M")
2. **Batch 2 process gap fixes**: stack_detect sub-pipeline mandatory delivery + end-of-Phase-0 Test-Path checklist (missing item = BLOCKED) + shared index single-writer principle (sharded naming, merging by orchestration layer) + "pool rows precede references" mandatory clause + Phase 0 preflight environment check (`preflight_{timestamp}.md` dual stacks) + wait-timeout quantified formula (estimated minutes = 2 + (total files / 1000) × 8) + Phase 6 P2 hidden-surface trace executed directly by the orchestration layer + node-route-mapper method-level pairing mandatory (conservative dual-method upper bound forbidden from flowing downstream)
3. **Batch 3 dimension-level dispatch verification (core of this batch)**: IO status model "Dimension Verification" clause (ledger-registered mechanism-extension dimensions checked one by one in three states; bare "not covered" forbidden; source of truth = the ledger's mechanisms-covered field; referenced by both pipelines in Phase 4) + 4 specialties' mandatory enumeration lists gain dimension entries (auth error-response consistency / logging tampering + flooding / crypto + webapi signed replay / logic integer overflow) + field-level compliance matrix (`knowledge_cutoff_date` / `offline_report_source` literal fields mandatory + dynamic verification report red-line table header verbatim alignment with the four-zero clauses)

### Key Constraints

- Dimension-level dispatch verification = preventing "silent dimension misses within specialties" sinks from the specialty level to the dimension level; it does not change the semantics of the existing specialty-level dispatch verification
- The whole batch: zero code, zero validate additions: counts 53/50/107 unchanged, baseline `PASS=1 FAIL=4 WARN=17` unchanged, zero new EVIDs; red-line regression (specialty dispatch verification semantics / existing SEVERITY level definitions / pending_pool eight fields / §9 four rules / the 10 playback evidence rows) zero deletions
- Ledger: Round 45 batch 1 / batch 2 / batch 3 three entries flipped to "implemented, pending verification (delivered in Round 45, 2026-09-20)"; pending-verification count 5 → 8
- Delivery: 24 implementation commits + 2 review supplement commits + 1 wrap-up commit, 27 commits total
- Leftover input: `node-route-mapper` frontend_outbound outbound entries mixed into the unmapped column structure, pending normalization

> Verification time: 2026-09-20

## Round 46 (2026-09-21 Review Fix Batch, Driven by Three Independent Pre-Packaging Reviews)

Based on `docs/superpowers/specs/2026-09-21-review-fix-batch-design.md`, three independent pre-packaging reviews (design soundness / landing authenticity / consistency regression) exposed 20 gaps (2 high, 8 medium, 10 low), delivered spec→SDD in two batches (inter-batch review: snapshot-ledger consistency self-check A8/B11 fully reconciled + no-op check passed):

1. **Batch 1 execution-loop breakpoint fixes**: dimension list in-package snapshot (IO_PATH_CONVENTION appendix A8+B9, dual-track execution source / registration source) + dual-mode sub-stack run_timestamp handling (fullstack orchestration mode receives the issued value without self-producing / single-stack mode self-produces, closing the dual-timestamp revival hole) + BLOCKED recovery loop single-stack broken-ring fix (end-of-Phase-0 checklist gains dual-mode recovery actions) + manifest mapping table format registration + milestone-line timestamp pinned to run_timestamp + formula ③ chain status criteria registration (closed/open/false_positive/pending four-state mapping table) + final_anchor three machine-verification fields + preflight artifact template
2. **Batch 2 dimension list in-packaging + record-layer polish**: snapshot registration of B10/B11 + completeness criteria sentence / unmapped landing normalization (uncertain methods go into the frontend_outbound self-contained list section, forbidden from being written into unmapped_routes) / pending-pool CLOSED enum (closed within static audit or this phase) + closed_count bucket merging / frontend_outbound IO path source-of-truth registration (route_mapping artifact table adds a row) / Option A discipline exclusion clause (rg zero hits are non asset-existence conclusions; one line added to each of the 4 agents) / wait-timeout rounding rule (no rounding during computation, round to the nearest minute at the end) + total-file-count GC6 scope / preflight cascade rules registration / SEVERITY rating statistics grouping by enum value / chain status name alignment (pending ↔ open synonymous and same-set) / node pipeline single-stack dimension verification reference sentence / maintenance log + CHANGELOG record-layer corrections (defect count 16 criteria)

### Key Constraints

- Dimension list dual-track system: in-package snapshot = execution source of truth, ledger = registration source of truth (new dimensions are registered first → snapshot synced, reconciled at packaging; on drift the ledger is the final source of truth and the snapshot must be synced)
- The whole batch: zero code, zero validate additions: counts 53/50/107 unchanged, baseline `PASS=1 FAIL=4 WARN=17` unchanged, zero new EVIDs
- Ledger Round 46 entry flipped to "implemented, pending verification (delivered in Round 46, 2026-09-21)"; pending-verification count 8 → 9
- Defect count criteria unified to 16 (11 colleague feedback items + 5 playback failures; the earlier "17 items" arose from splitting colleague item #2 into two counts; the criteria-unification explanation sentence is in the ledger maintenance log and the Round 45 erratum in CHANGELOG)
- Leftover inputs cleared: Round 45's "node-route-mapper frontend_outbound outbound entries mixed into the unmapped column structure" leftover was cleared by Batch 2 normalization
- Delivery: 18 implementation commits + 1 criteria-unification commit + 1 wrap-up commit, 20 commits total

> Verification time: 2026-09-21

## Round 47 (2026-09-21 Gate Closing Batch)

Ledger machine verification landed (validate adds Ledger checks: status enums / mandatory fields / pending-verification count reconciliation, passing silently to keep the baseline PASS=1) + W check enhancement (ledger ACTIVE specialty count vs verification-section row count, triggered by one-way missed checks) + final_anchor machine verification scripted (X check: pool_check / stat_check / chain_check FAIL detection + pool count = unique ID count recomputation) + `traces_index_{timestamp}.md` output template section (batch list includes the feature column, Round 46 rules landed in the template); baseline `PASS=1 FAIL=4 WARN=17` unchanged, counts 53/50/107 unchanged, zero new EVIDs, pending-verification count 9 → 10.

> Verification time: 2026-09-21
