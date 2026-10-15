---
name: node-codegraph-indexer
description: Node.js project CodeGraph index management tool. Detects the CodeGraph environment of the target project, builds / refreshes the code knowledge graph index, and produces the index body, status, and metadata files for call-chain acceleration by node-route-mapper and node-route-tracer.
---

# Node.js CodeGraph Index Management

## Goal

Build or refresh a CodeGraph local code knowledge graph index (`.codegraph/`) for the target Node.js project, so that subsequent `node-route-mapper` and `node-route-tracer` can obtain cross-file call chains (entry definitions, middleware chains, require / import dependency relationships) via `codegraph_explore` / `codegraph_callers` / `codegraph_impact`, replacing part of the manual grep + Read combinations.

## CRITICAL: The Index Is Not an Audit Substitute

- CodeGraph is an **execution-layer acceleration tool**, not the audit rules themselves
- Route identification, parameter binding, Sink determination, and evidence closure remain the responsibility of existing skills
- Without a CodeGraph index, fall back 100% to the existing static analysis process (consistent with the dotnet-side Phase 0 semantics)

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill; the retrieval keywords of this skill (the five layers of entry definitions / binding & parameters / precondition controls / sensitive operations / security configuration) are aligned with that index and are used to confirm index coverage rather than directly enumerate vulnerabilities
- This skill does not directly audit vulnerabilities, so it does not reference the Sink evidence points in `shared/EVIDENCE_POINT_IDS.md`; the Sink evidence contract is referenced by each `node-vuln-audit` specialty per its own EVID_NODE_*
- **By default, follow the general execution standards of `shared/AUDIT_EXECUTION_COMMON.md` (stack-agnostic execution standard source of truth, shared evolution decision 3) and `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention (`node/codegraph/*`, `node/quality/*`)
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline (this skill involves index availability grading and produces no vulnerability-level conclusions)

## Input Dependencies

- Required: `node_source_path` (Node.js project or repository root, which should contain `package.json`)
- Optional: `package.json` (reads `dependencies` / `devDependencies`, used for tech-stack determination and index coverage confirmation; excludes non-audit directories such as `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`, and `coverage`)
- Optional: tech-stack detection result (`node/stack_detect/stack_detect_{timestamp}.md`, produced by the `node-audit-pipeline` Phase 0 or `node-route-mapper` reconnaissance; if it already exists, use it to align framework surfaces and entry types, narrowing the scope of index symbol verification)
- This skill sits at pipeline Phase 0 and executes before route-mapper / route-tracer; it has no other mandatory upstream dependencies

## Key Checks

- CodeGraph environment availability: whether the `codegraph` CLI is in PATH, and whether `.codegraph/` already exists under `node_source_path`
- JS / TS symbol extraction completeness: whether `codegraph query --kind function` / `--kind class` can hit source code symbols
- Entry and middleware symbol retrievability: confirm route-level symbols are retrievable by framework surface (Express / NestJS / Next.js / Koa / Fastify / Nuxt)
- Dependency edges: whether `require` / `import` cross-file references enter the index (for route-tracer cross-file chain tracing)
- Key file coverage: compare the count of `.js` / `.ts` / `.jsx` / `.tsx` files on disk with the count in the index, and record the coverage
- Degradation record: when the index is unavailable, an `UNAVAILABLE` status and reason must be persisted; pretending the index is available is forbidden

## Enumeration Rules (Mandatory Refinement)

### 1. Entry and middleware symbols

- Retrieval keywords: CodeGraph queries such as `codegraph query --kind function --limit 5`, combined with the entry-definition grabber keywords of `shared/NODE_AUDIT_GRABBER_INDEX.md` (`app.get` / `Router()` / `@Controller` / `@Get` / `export function GET` / `defineEventHandler` / `fastify.route`, etc.)
- Record requirements: entry symbol names, route templates, HTTP methods, middleware chain symbols (`app.use` / `router.use` / `@UseGuards` / `addHook`, etc.), written item by item into `node/codegraph/codegraph_index_{timestamp}.md`

### 2. Dependency edges

- Retrieval methods: `codegraph_callers {symbol}` / `codegraph_explore "module imports of {file}"` (or equivalent queries)
- Record requirements: module-level dependencies, inter-file reference edges, project-internal secondary encapsulation chains; CodeGraph-unique cross-file edges are annotated `source: codegraph`

### 3. Index coverage and quality

- Compare the count of JS / TS files on disk with the count in the index, recording `coverage_percent`
- Record requirements: missing directory lists, missing symbol types (e.g., only functions extracted but no classes), route symbol counts — all written into `node/quality/codegraph_index_validation_{timestamp}.md`

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| codegraph CLI availability | `codegraph` command in PATH | Run `codegraph --version` | version output present → pass; command missing → degrade to `UNAVAILABLE(NOT_AVAILABLE)` |
| `.codegraph/` existence | `.codegraph/` directory under the target directory | Check whether `codegraph.db` exists and is non-empty | exists and non-empty → pass; missing → enter the init scenario or degrade |
| JS / TS symbol extraction | `codegraph query --kind function` | Sample-query 5 symbols | ≥1 hit → pass; all empty → `PARTIAL` and check whether the source directory exists |
| Route-level symbol retrieval | `codegraph explore` route queries | Retrieve route / middleware symbols by the detected framework surface | hits → pass; 0 hits and the project is indeed a server-side project → `PARTIAL`; non-server-side project → `NOT_APPLICABLE` |
| File coverage | disk file count vs index file count | count comparison | record `coverage_percent`, noting excluded directories; significantly low (e.g., <50%) → `PARTIAL` with reasons attached |

## Two-Phase Determination (Mandatory)

This skill follows the two-phase determination process of `shared/AUDIT_EXECUTION_COMMON.md` (stack-agnostic source of truth) and `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`. Since this skill is of the **index management type**, two-phase determination applies to "index availability conclusions" rather than vulnerability conclusions:

### Phase 1: Interim Conclusion

For each check item, first give one of three interim conclusions:

- `Confirmed Available`: CLI available and index symbols retrievable
- `Pending`: CLI available but `.codegraph/` missing or symbols empty; init / sync needs to be attempted
- `Unavailable`: CLI missing or init / sync failed

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue executing at least one more step (init or sync) and re-verify until any of the following holds:

- ✅ Evidence is found that the index is built successfully and symbols are retrievable → `AVAILABLE`
- ✅ A clear failure reason is found (CLI missing / init error / project not server-side) → `UNAVAILABLE`; the reason must be persisted
- ❌ A key step is still missing → remain `UNAVAILABLE(PARTIAL)`, but you must state which step is missing

**fail-close semantics**: when the index is unavailable, downstream skills must fall back 100% to static analysis; any silent-fallback such as "pretending the index is available / substituting empty index results for the audit surface" is treated as an error. Degradation must not block the pipeline, but the status and reason must be persisted.

## Determination Rules (Mandatory Refinement)

### Confirmed (AVAILABLE)

- The `codegraph` CLI is available, and the `.codegraph/` index exists and has been successfully init / synced
- JS / TS symbols and route-level symbols are retrievable (`route_symbols_found > 0` for server-side projects)
- File coverage has been recorded, and the counts of `codegraph_index_status` and `codegraph_index_validation` reconcile

### Pending (PARTIAL)

- The index exists but some symbols are missing (e.g., only functions, no classes / no route symbols), or coverage is significantly low (<50%)
- Mark `codegraph_status: UNAVAILABLE(PARTIAL)` and state the missing surface; downstream may use it partially but key chains still go through static analysis

### False Positive / Unavailable (UNAVAILABLE)

- `NOT_AVAILABLE`: CLI not installed (installation guide attached; does not affect subsequent flow)
- `INIT_FAILED` / `SYNC_FAILED`: init / sync execution failed (error log summary attached)
- `NOT_APPLICABLE`: the project is indeed not a Node.js server-side project (e.g., a pure SPA; see the exclusion rules of `NODE_AUDIT_GRABBER_INDEX.md`)
- The reason must be recorded; downstream skills fall back completely to static analysis

## Testing Recommendations (Mandatory)

### Positive Testing

- The target directory already has `.codegraph/` and the CLI is available: sync executes successfully, outputting `codegraph_status: AVAILABLE` with symbols retrievable
- The target directory has no `.codegraph/` but the CLI is available: init executes successfully, outputting `AVAILABLE`, with `coverage_percent` reasonable compared to disk

### Negative Testing

- CLI missing: output `UNAVAILABLE(NOT_AVAILABLE)` + installation guide; the pipeline is not blocked and downstream goes static analysis
- init / sync failure: output `UNAVAILABLE(INIT_FAILED/SYNC_FAILED)` + error summary
- Symbol extraction empty while source exists on disk: output `UNAVAILABLE(PARTIAL)`; passing off an empty index as audit completion is forbidden

### Regression Testing

- In P1 without a CodeGraph environment, pipeline Phase 0 still outputs `node/codegraph/codegraph_index_status_{timestamp}.md` (`codegraph_status: NOT_RUN` + reason), consistent with the existing Phase 0 semantics of `node-audit-pipeline`
- After this skill is delivered, the P1 execution flow does not change the existing static analysis path due to the new ACTIVE status

## Evidence References

- This skill is of the index management type and does not directly audit vulnerabilities, so it **does not reference** the Sink evidence points in `shared/EVIDENCE_POINT_IDS.md` (including EVID_NODE_*); the Sink evidence contract is the responsibility of each `node-vuln-audit` specialty
- The evidence contract is verified by the index artifact triad: `node/codegraph/codegraph_index_{timestamp}.md` (index body), `node/codegraph/codegraph_index_status_{timestamp}.md` (status metadata), and `node/quality/codegraph_index_validation_{timestamp}.md` (quality validation) must reconcile with each other — the symbol counts / coverage in the status file must be traceable to the statistics in the quality validation file; reconciliation failures are handled per the fail-close semantics of `shared/AUDIT_EXECUTION_COMMON.md`

## Output

- `node/codegraph/codegraph_index_{timestamp}.md`: index body snapshot (entry symbols, middleware chains, dependency edges, for route-mapper / route-tracer acceleration)
- `node/codegraph/codegraph_index_status_{timestamp}.md`: index status and metadata (`codegraph_status: AVAILABLE|UNAVAILABLE` and sub-statuses)
- `node/quality/codegraph_index_validation_{timestamp}.md`: index quality validation results (symbol extraction, route symbols, file coverage)

### Status File Field Template (`node/codegraph/codegraph_index_status_{timestamp}.md`)

```md
# CodeGraph Index Status (node)

- node_source_path: {node_source_path}
- timestamp: {timestamp}
- codegraph_status: {AVAILABLE|UNAVAILABLE}
- unavailable_reason: {N/A|NOT_AVAILABLE|INIT_FAILED|SYNC_FAILED|PARTIAL|NOT_APPLICABLE}
- cli_version: {version or N/A}
- index_exists: {true|false}
- init_or_sync: {init|sync|none}
- js_ts_file_count_on_disk: {n}
- file_count_in_index: {n}
- coverage_percent: {n}%
- route_symbols_found: {n}
- middleware_symbols_found: {n}
- framework_detected: {express|nestjs|nextjs|koa|fastify|nuxt|none|N/A}
- notes: {any warnings or failures}
```

## Core Inputs

User provides:

- `node_source_path`: Node.js project or repository root (same as the required item in "Input Dependencies")
- Optional: `package.json` and the tech-stack detection result (used for index scope confirmation and symbol verification)

## Execution Steps

### Step 1: Detect the CodeGraph environment

1. Check whether the `.codegraph/` directory already exists under the target directory `node_source_path`
   - If it exists: read the modification time of `.codegraph/codegraph.db` and record `index_exists: true`
   - If it does not exist: record `index_exists: false`
2. Detect whether the `codegraph` command exists in the system PATH
   - If it exists: record `cli_available: true` and obtain the version number
   - If it does not exist: record `cli_available: false`

### Step 2: Index building or refresh

#### Scenario A: `.codegraph/` already exists and the CLI is available

- Run `codegraph sync {node_source_path}` for an incremental update
- Record `sync_status` and the update timestamp

#### Scenario B: no `.codegraph/` but the CLI is available

- Run `codegraph init {node_source_path}` to build a complete index
- Record `init_status` and the elapsed time

#### Scenario C: CLI unavailable

- Record `codegraph_status: UNAVAILABLE` and `unavailable_reason: NOT_AVAILABLE` in `codegraph_index_status_{timestamp}.md`
- Provide an installation guide (does not affect subsequent flow; subsequent skills fall back to the existing static analysis)

### Step 3: Index quality validation

Regardless of whether the index is newly built, execute the following validations (results written into `node/quality/codegraph_index_validation_{timestamp}.md`):

1. **File coverage validation**: check whether `codegraph.db` under `.codegraph/` exists and is non-empty
2. **JS / TS symbol extraction validation**: confirm function / class symbols have been extracted via `codegraph query --kind function --limit 5` (or an equivalent method)
3. **Route identification validation**: confirm route-level symbols are retrievable via `codegraph explore "express routes in {node_source_path}"` (or an equivalent query) according to the `framework_detected` surface
4. **Key file coverage**: confirm the comparison between the count of `.js` / `.ts` / `.jsx` / `.tsx` files under `node_source_path` and the count of files in the index, recording the coverage (excluding `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`, and `coverage` by default)

### Step 4: Index body and metadata recording

1. Write entry symbols, middleware chain symbols, and dependency edges into `node/codegraph/codegraph_index_{timestamp}.md`
2. Write index status and metadata into `node/codegraph/codegraph_index_status_{timestamp}.md` (fields see "Status File Field Template")

## Consumption Conventions for Downstream Skills

### node-route-mapper consumption

- If `codegraph_status = AVAILABLE` and `route_symbols_found > 0`:
  - Prefer obtaining the entry / route mapping via `codegraph explore "{framework} routes in {node_source_path}"`
  - Supplement the handler function list via `codegraph query --kind function`
  - Cross-validate the route symbols returned by CodeGraph with manual static analysis results; differences are marked `⚠️manual review required`
- If `codegraph_status != AVAILABLE`: fall back completely to the existing static analysis process

### node-route-tracer consumption

- If `codegraph_status = AVAILABLE`:
  - For each `route_id`, prefer obtaining the upstream call chain via `codegraph_callers {handler_symbol}`
  - Obtain the impact radius (including cross-file calls) via `codegraph_impact {handler_symbol} --depth 3`
  - For middleware chains, locate the middleware mount order via `codegraph_explore "middleware chain of {app_symbol}"`
  - Merge the CodeGraph call chain with manual trace results; CodeGraph-unique cross-file edges are annotated `source: codegraph`
- If `codegraph_status != AVAILABLE`: fall back completely to the existing trace process

## Checkpoint Design

- 🔴 **CHECKPOINT A (environment detection)**: confirm `codegraph` CLI availability and `.codegraph/` existence
- 🔴 **CHECKPOINT B (index quality)**: confirm JS / TS symbols have been extracted and route-level symbols are retrievable
- 🟡 **CHECKPOINT C (degradation confirmation)**: if the index is unavailable, confirm downstream skills are aware and fall back to static analysis

## Failure and Degradation Branches

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| `codegraph` CLI not installed | Output installation guide, mark `UNAVAILABLE(NOT_AVAILABLE)` | Does not affect subsequent flow; downstream skills go static analysis |
| `codegraph init` failure | Record error log, mark `UNAVAILABLE(INIT_FAILED)` | Downstream skills go static analysis |
| JS / TS symbol extraction empty | Check whether source files exist; if they exist, mark `UNAVAILABLE(PARTIAL)` | Downstream skills go static analysis |
| Route symbol identification is 0 | Confirm whether the project is truly a Node.js server-side project; if not, mark `NOT_APPLICABLE` | If it is a server-side project but identification is 0, mark `UNAVAILABLE(PARTIAL)` |

## Do NOT Do

- Anti-pattern: blocking the entire pipeline because of a CodeGraph index failure. Correct practice: mark the status and fall back.
- Anti-pattern: using CodeGraph results to replace the complete output of route-mapper. Correct practice: use it only as an acceleration input; the final routes / params are still uniformly formatted and output by route-mapper.
- Anti-pattern: performing Sink determination or vulnerability analysis during the indexing phase. Correct practice: build the index only; auditing is left to subsequent skills.
- Anti-pattern: counting `node_modules/` into the audit surface in index coverage statistics. Correct practice: exclude `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`, and `coverage` by default (lockfiles are an exception under supply chain auditing).
