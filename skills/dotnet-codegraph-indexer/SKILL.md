---
name: dotnet-codegraph-indexer
description: .NET project CodeGraph index management tool. Detects the CodeGraph environment of the target project, builds/refreshes the code knowledge graph index, and produces index status and metadata files for call-chain acceleration by dotnet-route-mapper and dotnet-route-tracer.
---

# .NET CodeGraph Index Management

## Objective

Build or refresh a CodeGraph local code knowledge graph index (`.codegraph/`) for the target .NET project, so that subsequent `dotnet-route-mapper` and `dotnet-route-tracer` can obtain cross-file call chains via `codegraph_explore` / `codegraph_callers` / `codegraph_impact`, replacing part of the manual grep + Read combination.

## CRITICAL: The Index Is Not an Audit Replacement

- CodeGraph is an **execution-layer acceleration tool**, not the audit rules themselves
- Route identification, parameter binding, sink determination, and evidence closure remain the responsibility of the existing Skills
- Without a CodeGraph index, fall back 100% to the existing static analysis flow

## Core Inputs

Provided by the user:

- `source_path`: .NET project, solution, or repository root directory

## Output Directory Structure

```text
{output_path}/
├── codegraph/
│   └── codegraph_index_status_{timestamp}.md
└── quality/
    └── codegraph_index_validation_{timestamp}.md
```

## Execution Steps

### Step 1: Detect the CodeGraph Environment

1. Check whether a `.codegraph/` directory already exists under the target directory `source_path`
   - If it exists: read the modification time of `.codegraph/codegraph.db` and record `index_exists: true`
   - If it does not exist: record `index_exists: false`
2. Check whether the `codegraph` command exists in the system PATH
   - If it exists: record `cli_available: true` and obtain the version number
   - If it does not exist: record `cli_available: false`

### Step 2: Build or Refresh the Index

#### Scenario A: `.codegraph/` already exists and CLI is available

- Run `codegraph sync {source_path}` for an incremental update
- Record `sync_status` and the update timestamp

#### Scenario B: No `.codegraph/` but CLI is available

- Run `codegraph init {source_path}` to build a complete index
- Record `init_status` and elapsed time

#### Scenario C: CLI unavailable

- Record `codegraph_status: NOT_AVAILABLE` in `codegraph_index_status_{timestamp}.md`
- Provide installation instructions (does not affect the subsequent flow; subsequent Skills fall back to existing static analysis)

### Step 3: Index Quality Validation

Perform the following validations regardless of whether the index was newly built:

1. **File coverage validation**: check that `codegraph.db` exists under `.codegraph/` and is non-empty
2. **C# symbol extraction validation**: confirm C# class symbols have been extracted via `codegraph query --kind class --limit 5` (or an equivalent method)
3. **Route identification validation**: confirm route-level symbols are searchable via `codegraph explore "ASP.NET controllers and routes"` (or an equivalent query)
4. **Key file coverage**: compare the number of `.cs` files under `source_path` with the number of files in the index, and record the coverage rate

### Step 4: Index Metadata Recording

Write the index information to `codegraph/codegraph_index_status_{timestamp}.md`:

```md
# CodeGraph Index Status

- source_path: {source_path}
- timestamp: {timestamp}
- codegraph_status: {AVAILABLE|NOT_AVAILABLE|INIT_FAILED|SYNC_FAILED}
- cli_version: {version or N/A}
- index_exists: {true|false}
- init_or_sync: {init|sync|none}
- csharp_file_count_on_disk: {n}
- csharp_file_count_in_index: {n}
- coverage_percent: {n}%
- route_symbols_found: {n}
- controller_symbols_found: {n}
- action_symbols_found: {n}
- notes: {any warnings or failures}
```

## Consumption Contract for Downstream Skills

### How dotnet-route-mapper Consumes It

- If `codegraph_status = AVAILABLE` and `route_symbols_found > 0`:
  - Prefer obtaining the Controller/Action/route mapping via `codegraph explore "ASP.NET controllers and routes in {source_path}"`
  - Supplement the action method list via `codegraph query --kind method`
  - Cross-validate the route symbols returned by CodeGraph with manual static analysis results; mark differences `⚠️Needs manual review`
- If `codegraph_status != AVAILABLE`: fall back completely to the existing static analysis flow

### How dotnet-route-tracer Consumes It

- If `codegraph_status = AVAILABLE`:
  - For each `route_id`, prefer obtaining the upstream call chain via `codegraph_callers {handler_symbol}`
  - Obtain the impact radius via `codegraph_impact {handler_symbol} --depth 3` (including cross-file calls)
  - For DI chains, locate the implementation class via `codegraph explore "implementation of {interface_name}"`
  - Merge the CodeGraph call chain with the manual trace results; cross-file edges unique to CodeGraph are annotated with `source: codegraph`
- If `codegraph_status != AVAILABLE`: fall back completely to the existing trace flow

## Shared Grabber Index References

- By default, use `shared/DOTNET_AUDIT_GRABBER_INDEX.md` as this Skill's base retrieval index
- This Skill does not directly audit vulnerabilities, so it does not reference the sink evidence points in `EVIDENCE_POINT_IDS.md`

## Input Dependencies

- Required: `source_path`
- No other upstream dependencies; this Skill sits at pipeline stage 0 and executes before route-mapper

## Output

- `codegraph/codegraph_index_status_{timestamp}.md`: index status and metadata
- `quality/codegraph_index_validation_{timestamp}.md`: index quality validation results

## Checkpoint Design

- 🔴 **CHECKPOINT A (Environment Detection)**: confirm `codegraph` CLI availability and `.codegraph/` existence
- 🔴 **CHECKPOINT B (Index Quality)**: confirm C# symbols are extracted and route-level symbols are searchable
- 🟡 **CHECKPOINT C (Degradation Confirmation)**: if the index is unavailable, confirm downstream Skills are aware and fall back

## Failure and Degradation Branches

| Trigger Condition | First-Line Handling | Fallback if Still Failing |
|---|---|---|
| `codegraph` CLI not installed | Output installation instructions, mark `codegraph_status: NOT_AVAILABLE` | Does not affect the subsequent flow; downstream Skills use static analysis |
| `codegraph init` fails | Record the error log, mark `codegraph_status: INIT_FAILED` | Downstream Skills use static analysis |
| C# symbol extraction is empty | Check whether `.cs` files exist; if they exist, mark `PARTIAL` | Downstream Skills use static analysis |
| Route symbol identification is 0 | Confirm whether the project is truly an ASP.NET project; if not, mark `NOT_APPLICABLE` | If it is an ASP.NET project but identification is 0, mark `PARTIAL` |

## Do NOT Do

- Anti-pattern: blocking the entire pipeline because the CodeGraph index failed. Correct approach: mark the status and fall back.
- Anti-pattern: using CodeGraph results to replace route-mapper's complete output. Correct approach: use only as acceleration input; the final routes/params are still uniformly formatted and output by route-mapper.
- Anti-pattern: doing sink determination or vulnerability analysis during the indexing phase. Correct approach: only build the index; leave auditing to subsequent Skills.
