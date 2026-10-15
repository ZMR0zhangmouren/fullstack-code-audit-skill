---
name: node-route-tracer
description: Node.js entry-to-Sink data-flow tracing tool. Consumes routes and parameters from node-route-mapper, determines Sinks per NODE_SINK_REFERENCE, and outputs trace evidence and trace_status without outputting vulnerability conclusions.
---

# Node.js Route Tracer

## Shared Grabber Index Reference

The Source keywords, parameter sources, and Sink determination of this skill uniformly reference the following shared indexes:

- `skills/shared/NODE_AUDIT_GRABBER_INDEX.md`: source of truth for Source and parameter grabbers.
- `skills/shared/NODE_SINK_REFERENCE.md`: sole baseline for Sink APIs, controllable parameter positions, and reference Barriers.
- `skills/shared/EVIDENCE_POINT_IDS.md`: source of truth for EVID_NODE_* evidence point IDs.
- `skills/shared/IO_PATH_CONVENTION.md`: artifact path and naming conventions.

## Input Dependencies

- `node_source_path`: Node.js project root (containing `package.json`).
- `node/route_mapping/routes_{timestamp}.md`: upstream route list, containing `route_id`.
- `node/route_mapping/params_{timestamp}.md`: parameter structures corresponding item by item with `routes`.
- `node/route_mapping/middleware_inventory_{timestamp}.md`: middleware inventory, used to trace the precondition control plane.
- `node/cross_analysis/trace_batch_plan_{timestamp}.md`: batched tracing plan (batch size, route_id sets, execution order).
- `node/stack_detect/stack_detect_{timestamp}.md` (optional): tech-stack detection result, used to select adapters and Sink package names.
- `node/route_mapping/index_{timestamp}.md` (optional): phase index, used to confirm upstream artifact version consistency.

## Source Definition

A Source is the position where externally controllable input first enters the processing chain. This skill covers the entire "Binding & Parameter Grabbers" table of `NODE_AUDIT_GRABBER_INDEX.md`, and additionally covers `process.env` value-read points injected at runtime rather than hardcoded on the configuration surface.

| Type | Priority Keywords / Value Points | Key Records |
| ---- | ---- | ---- |
| Express family | `req.params`, `req.query`, `req.body`, `req.headers`, `req.cookies` | parameter names, binding sources, whether converted by body-parser / cookie-parser |
| Koa family | `ctx.params`, `ctx.query`, `ctx.request.body`, `ctx.headers`, `ctx.cookies` | same as above |
| NestJS | expanded fields of `@Body()`, `@Query()`, `@Param()`, `@Headers()` | DTO field mappings, ValidationPipe whitelist |
| Next/Nuxt | `await request.json()`, `request.nextUrl.searchParams`, `getQuery()`, `readBody()`, `getRouterParam()` | async read points and field names |
| File input | `req.file` / `req.files` of `multer`, `info.filename` of `busboy`, `file.originalFilename` of `formidable` | original file names, Content-Type, landing configuration |
| Environment variables | `process.env.{NAME}` (runtime injection surface) | value points, whether entering branch conditions / target URLs / commands / template paths |

`process.env` exclusions: reads serving only as static configuration thresholds, switch defaults, log levels, and similar configuration surfaces are not treated as Sources; once a `process.env` value enters response construction, command concatenation, URL assembly, template path selection, or permission checks, it is traced as a Source.

## Propagator Rules

A Propagator is the form of data transfer, splitting, merging, or transformation between a Source reaching a Sink. The following patterns must be recognized during tracing, recording variable name changes:

| Propagation Form | Typical Code Pattern | Tracing Requirement |
| ---- | ---- | ---- |
| Destructuring assignment | `const { id, name } = req.body` | record the mapping from original Source fields to local variable names |
| JSON.parse | `const obj = JSON.parse(req.body)` | record the correspondence between parsed field paths and the Source |
| await chains | `const data = await service.foo(param)` | record variable passing before and after await, and intermediate return object fields |
| Middleware attaching to req | `req.user = decoded`, `req.tenant = header`, `req.locals.x = y` | record the mount point, the source of the mounted value, and downstream read positions |
| lodash merge / assign / clone | `_.merge(target, source)`, `_.assign(a, b)`, `_.cloneDeep(obj)` | record object fields before and after merging, and whether the Source enters the target object |
| Template string concatenation | `` `SELECT * FROM t WHERE id = ${id}` ``, `url + path` | record the concatenation position, the Source fields participating, and the final string usage point |

During tracing, give the following in data-flow order: Source point → first assignment / destructuring → intermediate conversions (parse / await / merge) → final variable form before entering the Sink.

## Sink Determination

Sink determination takes `skills/shared/NODE_SINK_REFERENCE.md` as the sole baseline; extending Sink definitions on your own is forbidden.

Determination actions:

1. Locate call sites in source code per the Sink API list of `NODE_SINK_REFERENCE.md`.
2. Verify whether the call site parameters come from Sources or variables passed through Propagators.
3. Upon a hit, record the corresponding `EVID_NODE_*` evidence point ID (verbatim per the NODE namespace of `skills/shared/EVIDENCE_POINT_IDS.md`).

| Sink Type | Typical APIs | Corresponding EVID_NODE_* IDs (record upon hit) |
| ---- | ---- | ---- |
| PROTO | `_.merge`, `_.assign`, `_.defaultsDeep`, `Object.assign` receiving untrusted objects | `EVID_NODE_PROTO_MERGE_SINK`, `EVID_NODE_PROTO_MAGIC_KEY_CONTROL`, `EVID_NODE_PROTO_KEY_FILTER_ABSENT_OR_BYPASS`, `EVID_NODE_PROTO_GADGET_TRIGGER` |
| CMD | `child_process.exec`, `execSync`, `spawn({shell:true})`, `execFile` | `EVID_NODE_CMD_EXEC_POINT`, `EVID_NODE_CMD_STRING_CONSTRUCTION`, `EVID_NODE_CMD_USER_PARAM_TO_CMD`, `EVID_NODE_CMD_ARG_ARRAY_OR_ALLOWLIST` |
| SSRF | `axios.get`, `fetch`, `got`, `request`, `undici.request`, `http.get` | `EVID_NODE_SSRF_HTTP_CALL_POINT`, `EVID_NODE_SSRF_URL_CONSTRUCTION`, `EVID_NODE_SSRF_ALLOWLIST`, `EVID_NODE_SSRF_REDIRECT_FOLLOW` |
| NOSQL | `Model.find(query)`, `collection.findOne`, `$where`, `$regex` | `EVID_NODE_NOSQL_QUERY_POINT`, `EVID_NODE_NOSQL_RAW_OBJECT_PASS`, `EVID_NODE_NOSQL_OPERATOR_INJECTION`, `EVID_NODE_NOSQL_TYPE_COERCE_GUARD` |
| UPLOAD | `multer`, `busboy`, `formidable` | `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG`, `EVID_NODE_UPLOAD_FILENAME_SANITIZE`, `EVID_NODE_UPLOAD_FILTER_LIMITS`, `EVID_NODE_UPLOAD_ACCESSIBILITY` |
| XSS | server-side: `res.send(markup)`, `res.render(view, locals)`; client-side in SSR / isomorphic rendering contexts: `dangerouslySetInnerHTML`, `v-html` | `EVID_NODE_XSS_OUTPUT_POINT`, `EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT`, `EVID_NODE_XSS_ENCODE_OR_SANITIZE`, `EVID_NODE_XSS_SSR_HYDRATION` |
| SSTI | `ejs.render`, `pug.compile`, `nunjucks.renderString`, `handlebars.compile` | `EVID_NODE_SSTI_RENDER_POINT`, `EVID_NODE_SSTI_TEMPLATE_CONCAT`, `EVID_NODE_SSTI_TEMPLATE_NAME_CONTROL` |
| SESS | `jwt.sign`, `jwt.verify`, `res.cookie` | `EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG`, `EVID_NODE_SESS_JWT_ALG_PINNED`, `EVID_NODE_SESS_SECRET_SOURCE`, `EVID_NODE_SESS_COOKIE_FLAGS`, `EVID_NODE_SESS_LIFECYCLE` |

After hitting a Sink, the trace must give: Sink type, specific API, call site `file:line`, parameter source mapping, whether encoding / whitelist / authorization / configuration protection was applied, and evidence completeness / credibility (referring only to the completeness and credibility of the evidence chain, not equivalent to the vulnerability risk level).

The table above is only a type sample of IDs currently registered in the NODE namespace of `EVIDENCE_POINT_IDS.md`; when hitting types not listed (SQL / FILE / WRITE / ARCHIVE / REDIR / DESER / EXPR / REDOS / CRYPTO / CSRF / CFG / DOMXSS, etc.), record the call site and controllable parameter positions per the Sink API list of `NODE_SINK_REFERENCE.md`, and provisionally mark an `EVID_NODE_*` to-be-registered flag to be backfilled after the corresponding P2 specialty evidence IDs are registered; skipping recording because the table has no row is forbidden.

## Batched Tracing (Mandatory)

This skill executes batched tracing per `node/cross_analysis/trace_batch_plan_{timestamp}.md` and does not process everything at once. Batch sizes must comply with the `trace_batch_max_size` coverage mode thresholds in `shared/IO_PATH_CONVENTION.md` (FULL 10–30; SAMPLE 5–10 and must not exceed 10); they are enforced in the plan by `node-audit-pipeline` Phase 3, and this skill only executes per plan.

Each batch executes:

1. Read the current batch's `route_id` set.
2. Restore entries and request templates from `routes_{timestamp}.md` and `params_{timestamp}.md`.
3. Trace layer by layer per "Source → Propagator → Sink", recording call chain layers and branch paths.
4. Write `node/route_tracer/{route_id}/trace_{timestamp}.md` for each `route_id`.
5. Update `trace_status`.

The five states of `trace_status`:

| Status | Meaning |
| ---- | ---- |
| NOT_STARTED | listed in the batch plan but tracing not yet started |
| IN_PROGRESS | tracing in progress, with partial chain evidence |
| DONE_OPEN | tracing complete, with open chains reaching Sinks (parameter controllability proven) |
| DONE_CLOSED | tracing complete, Sink absent or parameters not controllable (chain closed as risk-free) |
| BLOCKED | tracing blocked (missing key upstream artifacts, source code inaccessible, dependencies unresolvable) |

`trace_status` must be written back to the corresponding `route_id` row of `node/quality/manifest_{run_id}.md` for pipeline and trace-gate consumption.

## Unclosed Trace Risk Pool (Mandatory)

Unclosed traces must be retained with missing evidence stated; silent deletion is forbidden.

Unclosed scenarios include:

- The Source enters the handler but subsequent usage points cannot be located.
- The Propagator chain contains asynchronous branches, queue dispatches, or event publications that cannot be continued in the current context.
- The Sink call site exists, but parameter source mapping is missing or controllability cannot be proven.
- Branch conditions exist but execution paths cannot be proven.
- Runtime implementations (such as DI implementations and middleware order) cannot be confirmed statically.

Handling requirements:

1. In the "Trace Completeness Statement" of `node/route_tracer/{route_id}/trace_{timestamp}.md`, mark per the five trace_status states: a Sink reachable but the chain not fully closed → `DONE_OPEN`; controllability unprovable or Sink absent → `DONE_CLOSED`; upstream artifacts missing → `BLOCKED`, with "partial chain" stated among the missing items.
2. List missing evidence item by item: call chain layers / branches / mappings / configurations / environment dependencies.
3. Aggregate the `route_id`, `missing evidence summary`, and `suggested evidence-supplementing actions` of unclosed traces into `node/route_tracer/unclosed_trace_pool_{timestamp}.md`.
4. `unclosed_trace_pool_{timestamp}.md` must be updated with every batch; clearing unresolved items is forbidden.
5. Unclosed traces must not be used to support "Confirmed Exploitable" or high-strength vulnerability conclusions; they may only serve as a pending-verification risk pool for later specialties or dynamic re-verification.

## Output

Persist per the `node/route_tracer/{route_id}/...` conventions in `skills/shared/IO_PATH_CONVENTION.md`.

| Artifact | Physical Path |
| ---- | ---- |
| Single-route trace | `node/route_tracer/{route_id}/trace_{timestamp}.md` |
| Single-route trace summary | `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` |
| Unclosed risk pool | `node/route_tracer/unclosed_trace_pool_{timestamp}.md` |
| Phase index | `node/route_tracer/index_{timestamp}.md` |
| Empty-result explanation (if no trace output) | `node/route_tracer/empty_result_{timestamp}.md` |

Minimum sections of `trace_{timestamp}.md`:

1. Tracing entry (method / path / handler from route-mapper)
2. Full request template
3. Parameter entry points (Source table)
4. Call chain layer evidence (layer by layer, including middleware, handler, service, util)
5. Branch path tracing
6. Parameter controllability matrix
7. Sink location (parameter mapping)
8. Sink Summary
9. Trace completeness statement (including `trace_status` and the missing items list)
10. Sink Evidence Type Checklist (EVID_NODE_* evidence points listed by hit Sink type)

`trace_summary_{timestamp}.md` contains at least:

- `route_id`
- `trace_status`
- hit Sink type set
- hit EVID_NODE_* ID set
- highest parameter controllability level
- missing evidence summary
- next action

Pre-output self-check:

- [ ] `trace_status` has been written per one of the five states.
- [ ] Hit Sinks have their corresponding `EVID_NODE_*` IDs recorded.
- [ ] Unclosed traces have been written into `unclosed_trace_pool_{timestamp}.md`.
- [ ] Artifact paths and naming comply with the `node/` subtree conventions of `IO_PATH_CONVENTION.md`.
- [ ] No vulnerability conclusions, risk levels, or remediation recommendations have been output.
