---
name: dotnet-route-tracer
description: .NET multi-layer data flow tracing tool from entry to sink. Traces the evidence chain from Controllers, Minimal APIs, Hubs, GraphQL Resolvers, and WCF Services to final sensitive operation points by route_id; does not output vulnerability conclusions.
---

# .NET Route Tracer

## Objective

Based on routes from `dotnet-route-mapper` (or synthetic entries given by `dotnet-audit-pipeline`), trace from the **entry handler / CLI entry / designated symbol** to the final sensitive operation point (SQL/commands/files/SSRF/XSS/template rendering/deserialization, etc.), outputting the complete data flow chain, parameter variable name changes, and controllability analysis.

## CRITICAL Rules

- Only output tracing; do not output vulnerability suggestions
- Giving "vulnerability conclusions / risk levels / CVSS / remediation suggestions" is forbidden
- Only output: data flow chain evidence, branch execution paths, sink locations, and the parameter controllability determination table (controllability ≠ vulnerability conclusion)
- External entries such as Controller / Minimal API / Hub / GraphQL Resolver / WCF Operation must be covered with priority; tracing sinks directly without confirming entry attribution is forbidden
- Each trace must answer at least six questions: who receives the request, who completes binding, who performs pre-validation, who executes the business logic, who initiates the sensitive operation, and who controls the key parameters
- Controller scenarios must explicitly trace the six layers of Route Metadata, ModelBinder, Filter, Controller/Action, Service/Repository, and Sink; any missing layer must be explained in the Trace Completeness Statement
- Framework-level short-circuit points such as Middleware / Endpoint Filter / Delegating Handler / Message Inspector / HubFilter must be recorded as independent branches; writing only "may pass through middleware" is forbidden
- If a DI-injected object carries key parameters or determines the sink type, drilling must continue into implementation classes, factories, decorators, and proxy layers until the final execution point is determined or declared unresolvable

## Input Dependencies

- `routes_{timestamp}.md`: route definitions (when written standalone, usually `route_mapping/routes_{timestamp}.md`, see `shared/IO_PATH_CONVENTION.md`)
- `params_{timestamp}.md`: parameter structures (when written standalone, usually `route_mapping/params_{timestamp}.md`)
- `source_path`: source code root directory
- `route_id`: from `cross_analysis/high_risk_routes_{timestamp}.md`; can be an HTTP route sequence number, or a synthetic ID written into that file by dotnet-audit-pipeline (`ENTRY_CLI:` / `ENTRY_CRON:` / `ENTRY_QUEUE:` / `ENTRY_HOOK:` / `ENTRY_INCLUDE:` / `SINK_ONLY:`, etc.).
- `codegraph_index_status_{timestamp}.md` (optional): if it exists and `codegraph_status = AVAILABLE`, CodeGraph tools can be used preferentially to obtain cross-file call chains and DI resolution chains
- **Synthetic entries (required when not an HTTP route)**: `entry_file` (relative to `source_path`), `entry_symbol` (function/method or `Main` / top-level statements), `trace_from` (description of where to start tracing toward sensitive operation points).

## CodeGraph Acceleration Branch (Optional)

If `codegraph_index_status_{timestamp}.md` exists and `codegraph_status = AVAILABLE`:

1. For the handler symbol corresponding to each traced `route_id`:
   - Obtain the upstream call chain via `codegraph_callers {handler_symbol}` (including cross-file calls)
   - Obtain the impact radius via `codegraph_impact {handler_symbol} --depth 3` (including dynamic dispatch, interface → implementation jumps)
2. For DI chains:
   - Locate implementation classes, decorators, and factories of interfaces via `codegraph explore "implementation of {interface_name}"`
   - Record the candidate implementation set and inference basis
3. For async chains:
   - Trace post-await calls and event publish points via `codegraph explore "callers of {async_method}"`
4. Merge the CodeGraph call chain with the manual trace results:
   - Chains consistent between CodeGraph and manual analysis: output normally
   - Cross-file edges unique to CodeGraph (especially dynamic dispatch, Source Generators, DI resolution): annotate `source: codegraph`, keep them but cross-validate with source code fragments
   - Conflicting items: mark `⚠️Needs manual review`, with manual analysis prevailing

If `codegraph_status != AVAILABLE` or the index status file does not exist: fall back completely to the existing trace flow without errors or blocking.

**Constraint**: CodeGraph acceleration does not change the trace output format or field requirements; it only serves as a supplementary source of call chain evidence. The Trace Completeness Statement is still based on actual source code evidence.

## Core Tracing Scope (Mandatory)

- Entry definitions: Controller Actions, Minimal API Delegates, Hub methods, GraphQL Resolvers, WCF Operations
- Parameter binding: FromRoute, FromQuery, FromBody, FromForm, FromHeader, IFormFile, complex object binding, custom ModelBinders, ValueProviders, JSON Patch
- Pre-controls: Middleware, Endpoint Filters, ActionFilters, AuthorizationFilters, ResourceFilters, ExceptionFilters, HubFilters, GraphQL middleware, WCF Message Inspectors
- Business and dependencies: Controller / entry handler / Service / Domain Service / Repository / Client / Background Dispatcher / Template Engine
- Sensitive operations: database, files, commands, network, templates, deserialization, expressions, authentication/authorization, configuration switching, log output
- .NET entry handler functions (e.g. Controller Actions, Minimal API Delegates, SignalR Hub methods, GraphQL Resolvers, WCF Operations; non-HTTP scenarios also include CLI/Main, BackgroundService/HostedService, scheduled task callbacks, message consumption functions, etc.); for **non-HTTP tasks**, use the `entry_file` + `entry_symbol` from the inputs as the tracing starting point (see "Input Dependencies")
- Positions where external input enters the entry handler function (e.g. binding, deserialization, type conversion, and object assignment of Route/Query/Form/Header/Body/Cookie/Claims/Session/Hub payload/GraphQL variables/SOAP Body)
- Parameter passing and transformation between Controller/Endpoint/Hub/Resolver/Service/Repository/Client methods (local variable assignment, object property writes, collection element access, DTO mapping, anonymous object wrapping, async task payload passing)
- Branches and short-circuit points affecting the execution chain (e.g. if/switch/try/catch/return/throw, plus Filter, Middleware, Endpoint Filter, authorization/tenant checks, feature switches, null fallbacks, exception swallowing)
- Actual call sites of the final sink and key argument positions (specific API/method, parameter name/index, instance source, and whether concatenation, encoding, whitelisting, configuration, or permission constraints are applied before the call)

## Enumeration Rules (Mandatory Refinement)

- First go back from route_id to the route definition, confirming the endpoint type, route template, HTTP method, Area, version, authorization metadata, and return type, before starting the trace
- Enumerate all parameters in the Controller / entry handler signature, distinguishing raw scalars, complex objects, collections, files, and service injection parameters; mark binding sources and default values
- If custom ModelBinders, TypeConverters, JsonConverters, BindAsync, TryParse, IParsable, or ValueProviders exist, tracing must reach field assignment and conversion logic
- If Filters or Middleware exist, the five behaviors of read-only observation, intercepting short-circuit, parameter modification, context injection, and return value overriding must be distinguished, with branch conditions recorded
- For DI chains, the path from interface to implementation class, named/conditional registration, Decorator, Factory, Proxy, HttpClient typed client, and Repository encapsulation must be located until the actual execution point is found
- For async chains, tracing must continue into post-await calls, queue delivery, background tasks, event publishing, SignalR broadcasts, and notification sending, marking synchronous vs delayed async triggering
- If data enters Views, Razor, JsonResult, FileResult, RedirectResult, ContentResult, Hub broadcasts, or GraphQL response fields, the context must be explicitly output rather than just writing "returns to frontend"

## Failure and Degradation Branches (Mandatory)

| Trigger Condition | First-Line Handling | Fallback if Still Failing |
|---|---|---|
| `route_id` does not exist in the routes file | Fall back to `entry_file + entry_symbol + trace_from` synthetic entry tracing | Record `trace_status=UNRESOLVED` and write "entry mapping failed" in the missing items |
| Custom ModelBinder/JsonConverter unresolvable | First output binding evidence for confirmed fields | Unconfirmed fields uniformly marked `⚠️Binding Uncertain`; trace_status degraded to at least PARTIAL |
| DI runtime implementation cannot be uniquely located | Output candidate implementation set and inference basis | If still unconverged, keep all candidate chains and annotate `⚠️Needs Manual Review` |
| Async chain (queue/event) unreachable in the current context | Output the synchronous chain up to the delivery point | Mark the post-delivery chain as `PARTIAL`; writing "fully closed" is forbidden |
| Sink call site exists but parameter mapping missing | Keep sink location and call site evidence | The corresponding item in the parameter controllability matrix is marked `Undeterminable`; outputting COMPLETE is forbidden |
| Branch conditions exist but execution path unprovable | Output all possible branches and condition summaries | Trace Completeness Statement marked `PARTIAL`, listing branches needing follow-up evidence |

🔴 **STOP: if any of the above fallback branches is triggered, marking trace_status as COMPLETE is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Required shared index references: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber sources), `skills/shared/DOTNET_SINK_REFERENCE.md` (sink types and trace-gate validation baseline), and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements).
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

| # | Anti-Pattern | Why Not | Correct Approach |
|---|---|---|---|
| 1 | Only writing "may pass through middleware" | Without branch evidence, downstream specialties cannot consume it | Must give the hit branch condition and before/after state differences |
| 2 | Stopping at the "calls service" layer | The real sink cannot be located; the evidence chain breaks | Continue drilling to the final execution point of Repository/Client/Executor |
| 3 | Treating "uncontrollable" as "no risk" | The tracer is only responsible for controllability, not vulnerability conclusions | Only annotate controllability levels and blocking conditions; give no security conclusions |
| 4 | Reusing HTTP templates for synthetic entries | Causes route_id and entry semantics mismatch | Use `ENTRY_*`/`SINK_ONLY:*` and state the entry_symbol starting point |
| 5 | Marking COMPLETE with insufficient evidence | Misleads the pipeline into high-severity conclusions | Degrade to PARTIAL/UNRESOLVED per the rules and list missing evidence |

## Controller / Binder / Filter / Middleware / DI Tracing Rules

### Controller Tracing

- Record Controller, Action, route template, HTTP method, Area, ApiVersion, Authorize/AllowAnonymous, Consumes/Produces, return type
- Trace direct reads and branch usage of Request, RouteData, HttpContext, User, TempData, ViewData, ModelState, and Session inside the Action
- If the Action only forwards, continue tracing to Service, Repository, Domain Service, and Client; stopping at the "calls service" layer is forbidden

### ModelBinder Tracing

- Record each parameter's binding source, binding name, prefix, complex object expanded fields, nullability, default value fallback, and model validation results
- Custom ModelBinders / BinderProviders must record binding conditions, supported types, data sources, field assignment rules, and exception swallowing and fallback behavior
- For file upload parameters record file name, content type, length limit, staging location, landing function, and subsequent consumption points

### Filter Tracing

- Distinguish AuthorizationFilter, ResourceFilter, ActionFilter, ExceptionFilter, ResultFilter, EndpointFilter, HubFilter, and GraphQL Field Middleware
- Record their execution order, scope, whether they can short-circuit, whether they modify parameters/results/context, and whether they attach authorization or audit semantics
- If a Filter affects the model, identity, tenant, audit switches, or return value encoding, its before/after state differences must be marked on the main call chain

### Middleware Tracing

- Record the branch pipeline hit by routing, UseWhen/MapWhen conditions, PathBase rewrites, ForwardedHeaders, authentication, Session, CORS, exception handling middleware, and static file short-circuits
- If middleware modifies HttpContext.Items, User, Request.Path, Request.Scheme, RemoteIpAddress, Headers, or Body, it must enter the parameter controllability matrix
- For Minimal API / Endpoint Routing, the final metadata after Route Group and Endpoint Filter stacking must be recorded

### DI Chain Tracing

- Record interfaces, implementation classes, lifetimes, named registrations, closed generic types, decorators, factory proxies, and conditional branch registrations
- If the final execution point comes from HttpClientFactory, DbContext, Repository, Template Service, Message Publisher, or a custom Executor, tracing must continue to the specific method
- When the runtime implementation cannot be resolved, the candidate implementation set, inference basis, and missing evidence must be written, and trace_status is degraded to at least PARTIAL

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (e.g. `route_mapping` / `route_tracer` / `framework_audit`), confirm dependencies are available and timestamps are consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: write to the agreed path per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing-evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (Entry-to-Sink Closure)**: must confirm each high-risk path's source → transform → sink is traceable.
- 🔴 **CHECKPOINT B (Cross-Layer Evidence Closure)**: must confirm the controller, service, repository, and external call chains all have evidence points.
- 🔴 **CHECKPOINT C (Degradation Semantics Confirmation)**: must confirm insufficient-evidence scenarios use `⚠️Pending Verification / Environment-Dependent`.
- 🛑 **STOP**: if key paths lack evidence, outputting a strong "confirmed exploitable" conclusion is forbidden.

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

## Output Requirements

- Main output file: route_tracer/{route_id}/trace_{timestamp}.md
- Optional index file: route_tracer/{route_id}/trace_summary_{timestamp}.md
- Must be organized according to the 1)-9) template sections below (field names and numbering must not be changed)
- The Parameter Controllability Matrix must include at least: parameter name, binding source, converter/binder, first validation point, final use point, controllability level, and affected sink
- Sink Summary must include at least: sink type, specific API, code location, upstream parameters, whether encoding/whitelist/authorization/configuration protection is applied, and evidence strength
- The Trace Completeness Statement must clearly state COMPLETE / PARTIAL / UNRESOLVED, and explain which layer it is stuck at: routing, binding, filter, DI, async dispatch, or reflection/dynamic invocation
- The standard skeletons of trace_{timestamp}.md and trace_summary_{timestamp}.md are governed by shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md
- The traces_index (batch-level summary index) adds a `feature` column: the functional domain name — in fullstack mode, reverse-lookup the feature name from `node/route_mapping/feature_api_map_{timestamp}.md` by `backend_route_id` (controller domain prefix ↔ feature_api_map functional domain alignment); in dotnet-only mode, use the controller domain naming heuristic; column values are annotated `heuristic (not evidence)`

## Output File Structure (Recommended)
```
{output_path}/route_tracer/
└── {route_id}/
    ├── trace_{timestamp}.md
    └── trace_summary_{timestamp}.md
```
Notes: **HTTP routes**: `route_id` should match the sequence number `N` of `=== [N] {route_summary} ===` in `routes_{timestamp}.md` of `dotnet-route-mapper`. **CLI / hook / sink-only, etc.**: use the pipeline-synthesized `route_id`; the tracing starting point is based on the `entry_file` + `entry_symbol` + `trace_from` from the inputs, and is not required to correspond to a URI.

## Single-Route Report Template (Mandatory)

```markdown
# Route Trace

Tracing entry: {HTTP_METHOD} {route_rule} / {entry_symbol}
Generated at: {timestamp}
Project path: {source_path}
```
---

## 1) Complete Request Template (from route-mapper)
```http
{complete request template}
```

---
## 2) Parameter Entry Points
| Parameter Name | HTTP Input Source | Variable/Property Entering the Handler | Location |
|------|----------|------------------------|------|
|      |          |                        |      |

---
## 3) Call Chain Layer Evidence (layer by layer, no omission)
Layer 1: {file}:{line} {Class/Type}.{Member}({args})
Key code:
```csharp
// Show the key fragment of how the parameter continues to the next layer or the final sink
```

Layer 2: {file}:{line} {Class/Type}.{Member}({args})

---
## 4) Branch Path Tracing (branch execution proof, must be output)
Branch A:
Condition: {summary of the if/switch/try/catch/return/throw condition}
Execution: {summary of how the parameter continues flowing to the sensitive operation point under this branch}
Sensitive operation point: executed = yes/no

Branch B:
Condition: {summary of another branch condition}
Execution: {summary of parameter handling / early exit under the other branch}

---
## 5) Parameter Controllability Matrix (mandatory: field names and columns must be consistent)
| Parameter Name | Input Field/Binding Name | Binding Source | Preprocessing/Conversion | First Validation Point | Final Use Point | Affected Sink | Controllability Level | Constraints or Blocking Conditions | Actually Used (yes/no) |
|------|----------------|--------|-------------|------------|------------|---------------|----------|------------------|------------------|

---
## 6) Sink Location (parameter mapping; mandatory: field names and columns must be consistent)
| Sink Type | API/Method | Call Site (file:line) | Sink Parameter Name/Position | Parameter Mapping (sink parameter <- controllable parameter) | Evidence (key code/config fragment) |
|----------|----------|----------------|-------------------|----------------------------------|----------------------------|
```

---

## 7) Sink Summary (mandatory: used for the pipeline's hard-gate validation)
A summary table must be output (omission not allowed):
| route_id | Sink Type | Sink API/Statement | Executed (yes/no) | Trigger Branch (condition summary) | Related Parameters (from the controllability matrix) | Evidence (code/config fragment) |
|----------|---------|---------------|----------------|--------------------|--------------------------|----------------------|

---
## 8) Trace Completeness Statement (mandatory)
| trace_status | Meaning |
|-------------|------|
| COMPLETE | Call chain and sink evidence complete; parameter controllability determinable |
| PARTIAL | Only partial chain evidence or incomplete branch evidence, but the sink exists or part of the parameter flow is provable |
| UNRESOLVED | Unable to locate a clear sink or insufficient controllability evidence |

And provide:
- Missing items list (must list each missing item: call chain layer / branch / mapping / evidence)
- Fallback suggestions (allowed fallbacks: re-execute route-tracer, or enter the ⚠️Pending Verification mode of the corresponding sub-skill)

## Mandatory "Forbidden Items"
- Using ellipses to omit call chain layers is forbidden
- Keeping unreplaced template variables is forbidden (e.g. `${route}` not replaced with the real route_id)
- Conflating "uncontrollable" with "no risk" is forbidden: this Skill only outputs controllability, not vulnerability conclusions

## 9) Sink Evidence Type Checklist (mandatory: used for the pipeline hard gate)
This checklist must be output in every trace report (content may be empty, but the heading and table header must exist; and for actually hit sinks, write the evidence source and evidence fragment).

| Sink Type | Required Evidence Points (evidence fragments from code/config) | Evidence Location |
|----------|----------------------------------------------------|----------|
| FILE | `EVID_FILE_RESOLVED_TARGET`: final read target path or resource location evidence (e.g. actual targets of `File.ReadAllText`, `FileStream`, `PhysicalFileResult`); `EVID_FILE_PATH_NORMALIZATION`: path concatenation, `Path.GetFullPath`, base path constraints, and normalization evidence; `EVID_FILE_EXECUTION_BOUNDARY`: boundary evidence between reading, downloading, view rendering, or dynamic execution | file:line |
| WRITE | `EVID_WRITE_CALLSITE`: write call site evidence (e.g. `File.WriteAllText`, `FileStream`, `CopyToAsync`, `Move/Copy`); `EVID_WRITE_DESTPATH_JOIN_AND_NORMALIZATION`: destination path concatenation, normalization, and out-of-bounds determination evidence; `EVID_WRITE_CONTENT_SOURCE_INTO_WRITE`: mapping evidence of write content from user input; `EVID_WRITE_EXECUTION_ACCESSIBILITY_PROOF`: evidence whether the landed file sits in the web root, static files directory, downloadable directory, or is consumable by subsequent processing chains | file:line |
| UPLOAD | `EVID_UPLOAD_DESTPATH`: upload save directory and final landing point evidence; `EVID_UPLOAD_FILENAME_EXTENSION_PARSING_SANITIZE`: file name, extension, content-type, and server-side rename/sanitization logic evidence; `EVID_UPLOAD_ACCESSIBILITY_PROOF`: evidence whether a static access surface, download surface, or subsequent processing surface forms after writing | file:line |
| ARCHIVE | `EVID_ARCHIVE_EXTRACT_CALLSITE`: extraction call site evidence (e.g. `ZipArchive.ExtractToDirectory`); `EVID_ARCHIVE_ENTRY_NAME_SOURCE`: archive entry name or the source of the to-be-extracted entry list; `EVID_ARCHIVE_FINAL_TARGET`: final target path after `base directory + entry` merging and directory constraint determination evidence | file:line |
| SSRF | `EVID_SSRF_URL_NORMALIZATION`: URL concatenation, normalization, and protocol handling evidence; `EVID_SSRF_FINAL_URL_HOST_PORT`: final URL / Host / Port evidence before issuing requests via `HttpClient`, `WebRequest.Create`, etc.; `EVID_SSRF_DNSIP_AND_INNER_BLOCK`: DNS resolution, IP determination, and intranet blocking / allowlist evidence | file:line |
| SQL | `EVID_SQL_EXEC_POINT`: SQL execution point evidence (e.g. `SqlCommand.ExecuteReader`, `FromSqlRaw`, `ExecuteSqlRaw`, Dapper `Query/Execute`); `EVID_SQL_STRING_CONSTRUCTION`: SQL string construction, concatenation, or raw SQL entry evidence; `EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT`: mapping evidence of user input into SQL fragments or parameter positions | file:line |
| NOSQL | `EVID_NOSQL_QUERY_CONSTRUCTION`: NoSQL query construction point evidence (e.g. `FilterDefinition`, `BsonDocument`, Cosmos query strings); `EVID_NOSQL_USER_INPUT_INTO_QUERY_STRUCTURE`: evidence of user input entering the query structure; `EVID_NOSQL_OPERATOR_INJECTION_FIELDS`: operator, expression, or special field injection evidence | file:line |
| KQL | `EVID_KQL_EXEC_POINT`: KQL execution point evidence (e.g. `LogsQueryClient.QueryWorkspaceAsync`, `QueryResource`, `MetricsQueryClient`, `OperationalInsightsDataClient.Query`); `EVID_KQL_STRING_CONSTRUCTION`: KQL query string construction, concatenation, or interpolation evidence; `EVID_KQL_USER_PARAM_TO_KQL_FRAGMENT`: mapping evidence of user input into KQL fragments or pipeline operations (such as `\n| union` appends) | file:line |
| CMD | `EVID_CMD_EXEC_POINT`: command execution point evidence (e.g. `Process.Start`, shell wrappers, script launchers); `EVID_CMD_COMMAND_STRING_CONSTRUCTION`: command line string or key argument construction evidence; `EVID_CMD_USER_PARAM_TO_CMD_FRAGMENT`: mapping evidence of user input into command fragments or argument arrays | file:line |
| XSS | `EVID_XSS_OUTPUT_POINT`: output point evidence (e.g. Razor `Html.Raw`, `HtmlString`, Blazor `MarkupString`, `ContentResult`, hand-built HTML / JS); `EVID_XSS_USER_INPUT_INTO_OUTPUT`: evidence of user input entering a specific output context; `EVID_XSS_ESCAPE_OR_RAW_CONTROL`: HTML encoding, raw output, template default escaping, or escaping-disabled evidence | file:line |
| REDIR | `EVID_REDIR_OUTPUT_POINT`: redirect output point evidence (e.g. `Redirect`, `LocalRedirect`, `Results.Redirect`, `Challenge`, `SignOut`); `EVID_REDIR_DEST_SOURCE_MAPPING`: destination address source and variable mapping evidence; `EVID_REDIR_DEST_VALIDATION_NORMALIZATION`: `IsLocalUrl`, allowlist, scheme / host / port restrictions, and normalization evidence | file:line |
| CRLF | `EVID_CRLF_OUTPUT_POINT`: header / cookie / location / content-disposition write point evidence; `EVID_CRLF_USER_INPUT_INTO_HEADER_COOKIE`: mapping evidence of user input entering header or cookie values; `EVID_CRLF_CONTROL_CHAR_FILTERING_ENCODING`: `\r`, `\n`, encoding, framework interception, and proxy-layer normalization evidence | file:line |
| XXE | `EVID_XXE_PARSER_CALL`: XML parser call site evidence (e.g. `XmlDocument.LoadXml`, `XDocument.Parse`, `XmlReader.Create`); `EVID_XXE_INPUT_SOURCE`: input source evidence (e.g. `Request.Body`, uploaded files, string parameters, message bodies); `EVID_XXE_ENTITY_DOCTYPE_SAFETY_AND_ECHO`: `DtdProcessing`, `XmlResolver`, external entity-related configuration, and parsing result echo evidence | file:line |
| DESER | `EVID_DESER_CALLSITE`: deserialization call site evidence (e.g. `BinaryFormatter`, `NetDataContractSerializer`, Newtonsoft.Json with `TypeNameHandling` enabled); `EVID_DESER_INPUT_SOURCE`: deserialization input source evidence; `EVID_DESER_OBJECT_TYPE_MAGIC_TRIGGER_CHAIN`: target type, subsequent method calls, reflection, or sensitive operation trigger chain evidence | file:line |
| TPL | `EVID_TPL_ENGINE_RENDER_OR_PARSE_ENTRY`: template rendering or parsing entry evidence (e.g. Razor Runtime Compilation, mail template renderers); `EVID_TPL_TEMPLATE_OR_EXPR_CONTROL`: template name, template content, or expression controllability evidence; `EVID_TPL_EXEC_CHAIN_ENTRY`: compilation, evaluation, and execution chain entry and sandbox / restriction policy evidence | file:line |
| LDAP | `EVID_LDAP_EXEC_POINT`: LDAP query execution point evidence (e.g. `DirectorySearcher.FindAll`, `PrincipalContext`-related calls); `EVID_LDAP_FILTER_STRING_CONSTRUCTION`: filter / DN construction evidence; `EVID_LDAP_USER_PARAM_TO_FILTER_FRAGMENT`: mapping evidence of user input into filter / DN fragments | file:line |
| EXPR | `EVID_EXPR_EVAL_ENTRY`: expression evaluation entry evidence (e.g. Dynamic LINQ, `CSharpScript.EvaluateAsync`, `DataTable.Compute`); `EVID_EXPR_EXPR_CONTROL`: expression string controllability evidence; `EVID_EXPR_EXEC_CHAIN_ENTRY`: evidence of evaluation results entering sensitive semantics or subsequent execution chains | file:line |
| AUTH | `EVID_AUTH_PATH_PROTECTED_MATCH`: evidence of routes entering protected handler endpoints; `EVID_AUTH_TOKEN_DECODE_JUDGMENT`: cookie / JWT / ClaimsPrincipal parsing and judgment evidence; `EVID_AUTH_PERMISSION_CHECK_EXEC`: `Authorize`, policy, role, claim, or custom permission check evidence; `EVID_AUTH_IDOR_OWNERSHIP_CONDITION`: resource ownership fields, tenant isolation, or owner condition constraint evidence | file:line |
| CSRF | `EVID_CSRF_STATE_CHANGE_HANDLER_EXEC`: state-change handler method or handler endpoint execution evidence; `EVID_CSRF_TOKEN_SOURCE`: antiforgery token or equivalent token generation / storage source evidence; `EVID_CSRF_TOKEN_VERIFY`: server-side verification, comparison, fail-early-exit, and validation branch evidence; `EVID_CSRF_BYPASS_BRANCH`: bypass branches where only certain content types / AJAX / specific endpoints are validated | file:line |
| SESS | `EVID_SESS_COOKIE_FLAGS`: cookie `HttpOnly`, `Secure`, `SameSite`, and expiration policy evidence; `EVID_SESS_TICKET_REGEN_ROTATION`: post-login ticket rotation, refresh, or re-issuance evidence; `EVID_SESS_JWT_VERIFY_CLAIMS`: JWT signature algorithm and `exp/nbf/iss/aud` validation evidence; `EVID_SESS_LOGOUT_CLEAR`: logout-time cookie, ticket, session, or refresh token cleanup evidence | file:line |
| CFG | `EVID_CFG_CONFIG_LOCATION`: configuration location evidence (e.g. `appsettings.json`, `web.config`, environment variables, container configuration); `EVID_CFG_RUNTIME_SETTING_CODE`: runtime setting code evidence (e.g. middleware order, CORS, security headers, exception handling); `EVID_CFG_IMPACT_ASSOCIATION`: association evidence of configuration affecting entries, responses, or components; `EVID_CFG_SECURITY_SWITCH_EVIDENCE`: key security switch evidence such as debug switches, error exposure, security headers, and proxy trust | file:line |
| SSTI | `EVID_SSTI_TEMPLATE_SOURCE`: template source controllability evidence (template name, template content, or expression source); `EVID_SSTI_USER_INPUT_TO_TEMPLATE`: mapping evidence of user input to template injection points; `EVID_SSTI_RENDER_EXEC_CHAIN`: template rendering execution chain evidence (compilation, evaluation, execution entry); `EVID_SSTI_SANDBOX_ESCAPE`: sandbox escape or restriction policy evidence | file:line |
| XPATH | `EVID_XPATH_EXEC_POINT`: XPath query execution point evidence (e.g. `XPathNavigator.Select`, `XmlNode.SelectNodes`); `EVID_XPATH_EXPR_CONSTRUCTION`: XPath expression construction, concatenation, or interpolation evidence; `EVID_XPATH_USER_PARAM_TO_XPATH_FRAGMENT`: mapping evidence of user input into XPath fragments or predicates | file:line |
| DOMXSS | `EVID_DOMXSS_SINK_OUTPUT_POINT`: client-side output sink point evidence (e.g. `innerHTML`, `document.write`, `location`, `eval`, or JS interpolation output); `EVID_DOMXSS_USER_INPUT_SOURCE`: user input source evidence (e.g. URL parameters, fragments, postMessage, data injected into JS contexts by the server); `EVID_DOMXSS_ENCODING_SANITIZE_PROOF`: pre-output encoding / sanitization / safe API usage evidence (e.g. `textContent`, DOMPurify, encoding functions) | file:line |
| SECOND | `EVID_SECOND_ORDER_STORE_ENTRANCE`: write entry evidence (where the dangerous data comes from, whether attacker-controllable); `EVID_SECOND_ORDER_TRIGGER_ENTRANCE`: trigger entry evidence (when read, who triggers); `EVID_SECOND_ORDER_DATA_FLOW_MAPPING`: data flow mapping evidence from storage to sink; `EVID_SECOND_ORDER_STORAGE`: data second-storage evidence; `EVID_SECOND_ORDER_TRIGGER`: second-trigger execution evidence | file:line |
| DESYNC | `EVID_DESYNC_CL_T_CONFLICT`: Content-Length vs Transfer-Encoding conflict evidence; `EVID_DESYNC_PROXY_INCONSISTENCY`: proxy-layer inconsistency evidence; `EVID_DESYNC_REQUEST_PREFIX_TRUNCATION`: request prefix truncation evidence; `EVID_DESYNC_HTTP2_SMUGGLING`: HTTP/2 request smuggling evidence | file:line |


## Output Template Constraints

### Complete Request Template

- The real route templates and parameter names confirmed by route-mapper must be used
- Query, Body, Form, Header, Cookie, File, WebSocket/Hub payload, GraphQL variables, and SOAP Body must be distinguished
- The only allowed placeholders are {host}, {cookie}, {token}, {apiKey}, {jwt}

### Sink Evidence Type Checklist

- Call site evidence: whether a specific API/method was found
- Parameter source evidence: whether user input can be mapped to key arguments
- Constraint evidence: whether whitelists, encoding, permissions, configuration, or length/format validation exist
- Branch evidence: whether the protection logic is confirmed to always execute, conditionally execute, or be bypassable
- Environment evidence: whether it depends on deployment mode, proxies, configuration files, registration order, or runtime implementations

## Output Template Unified Rules

- route_id, entry identifier, return template type, and handler identifier must be consistent with route-mapper artifacts
- If additional specialty fields are needed, they must be appended while preserving the shared template sections; reordering core section semantics is not allowed
- The final trace artifact format consumed by the pipeline is governed by shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md

## Trace Status

- COMPLETE: call chain, execution points, and controllability evidence complete
- PARTIAL: partial chain provable, but branches or mappings incomplete
- UNRESOLVED: unable to locate a clear execution point or key mappings missing
