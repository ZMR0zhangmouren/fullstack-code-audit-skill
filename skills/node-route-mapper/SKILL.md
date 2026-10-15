---
name: node-route-mapper
description: Node.js web entry and parameter mapping analysis tool. Extracts complete entries, parameter structures, and request templates from http.createServer, Express, and other source code, and generates route and middleware inventories for downstream consumption.
---

# Node.js Route & Endpoint Mapper

## Shared Grabber Index Reference

The enumeration keywords, priority targets, and record criteria of this skill take `skills/shared/NODE_AUDIT_GRABBER_INDEX.md` as the single source of truth, searching by the three layers of entry definitions / binding & parameters / precondition controls. Paths and artifact naming follow the `node/` subtree conventions in `skills/shared/IO_PATH_CONVENTION.md`.

## Input Dependencies

User provides:

- `node_source_path`: Node.js project, repository root, or a directory containing `package.json` (required).
- `node/stack_detect/stack_detect_{timestamp}.md`: Phase 0 tech-stack detection result, used to select the adapter (optional, recommended).
- `context_path`: external path prefixes such as reverse proxies, gateway prefixes, and Next.js basePath (optional; must have a configuration or code-evidence source).

## Adapter Strategy

The P1 built-in adapters cover only generic Node (`http.createServer`) and Express. When NestJS / Next.js / Koa / Fastify / Nuxt is detected, enumerate per the corresponding keywords of `NODE_AUDIT_GRABBER_INDEX.md`; modules that cannot be closed are recorded in the unmapped list of `route_module_inventory`, and fabricating routes is forbidden.

- Generic Node: parse `req.url`, `req.method`, and manual route dispatch within the `createServer` callback.
- Express: parse `express()`, `app` / `router.get|post|put|delete|patch|all|use`, mount prefix chains, and middleware order.
- NestJS / Next.js / Koa / Fastify / Nuxt: use the corresponding decorators, file conventions, and plugin registration keywords; if the final path and handler cannot be precisely reconstructed at the current stage, record the `adapter_unresolved` reason.
- Exclude `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`, and `coverage/` directories by default; `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` are used only for supply chain auditing and are not part of the route enumeration surface.

## Enumeration Rules (Mandatory Refinement)

Record item by item the entry-definition and binding-parameter grabbers of `NODE_AUDIT_GRABBER_INDEX.md`:

### Entry Definition Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| Generic Node | http.createServer, createServer, req.url, req.method | native route dispatch, method determination |
| Express | express(), Router(), app.get, app.post, app.put, app.delete, app.patch, app.all, app.use, router.use | route templates, HTTP methods, mount prefixes, middleware chains |
| NestJS | @Controller, @Get, @Post, @Put, @Delete, @Patch, @All, @UseGuards, @UseInterceptors | decorator routes, Guard / Interceptor coverage |
| Next.js | app/api/**/route.{js,ts}, pages/api/**, export function GET, export function POST, NextRequest, middleware.ts | file-convention routes, HTTP method exports, edge middleware |
| Koa | new Koa(), koa-router, router.get, router.post, app.use | routes, ctx passing |
| Fastify | fastify.route, fastify.get, fastify.post, fastify.register, addHook | route registration, plugin scoping, hooks |
| Nuxt/Nitro | defineEventHandler, getQuery, readBody, server/api/** | server entries, parameter reads |

### Binding & Parameter Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| Express family | req.params, req.query, req.body, req.headers, req.cookies | parameter sources, name mapping |
| Koa family | ctx.params, ctx.query, ctx.request.body, ctx.headers, ctx.cookies | same as above |
| NestJS | @Body(), @Query(), @Param(), @Headers(), ValidationPipe | DTO expanded fields, validation pipe whitelist |
| Next/Nuxt | await request.json(), request.nextUrl.searchParams, getQuery(), readBody(), getRouterParam() | parameter sources |
| File input | multer, busboy, formidable, multipart | file name, dest, limits |

Every route must record:

- `route_id`: `R{sequence number}`, globally unique, corresponding item by item with `params_{timestamp}.md`.
- `route_method`: HTTP method or operation name.
- `route_path_template`: the final path template (including the mount prefix chain).
- `source_file:line`: declaration location.
- `mount_prefix_chain`: the `app.use` / `router.use` prefix chain from the application root to the handler.
- `param_source`: `req.params` / `req.query` / `req.body` / `req.headers` / `req.cookies` or framework equivalents.
- `handler_identifier`: function name, controller method, or handler identifier.
- `adapter_type`: `generic-node` / `express` / `nestjs` / `nextjs` / `koa` / `fastify` / `nuxt`.

### Middleware as the Authentication Surface

`middleware_inventory` records item by item:

- `middleware_name`: middleware function name or imported module name.
- `mount_path_prefix`: mount path prefix; global middleware is written as `/`.
- `is_auth`: whether it is of the authentication class (`passport.authenticate`, `express-jwt`, `expressjwt`, `jwt.verify`, `express-session`, `cookie-session`, `next-auth`, `getServerSession`, `@UseGuards`, etc.).
- `is_global`: whether it is mounted globally.

## frontend_outbound Outbound Endpoint Collection (Mandatory, 2026-09-20)

Collect the full set of external API call endpoints initiated by the frontend (or the node BFF), for consumption by cross-stack contract reconciliation (cross-stack-contract-mapper) and feature mapping (node-feature-api-mapper). Mature method samples are in the 2026-09-17 run artifact `frontend_outbound_2026_09_17_15_18.md` (the three-piece method set):

1. **rg endpoint enumeration**: `rg -o "baseUrl \+ '[^']+'" {src scope}` (excluding `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`, `coverage/`), deduplicating results by path to obtain the full set of baseUrl-relative paths; replace the `baseUrl` variable name per the actual project (e.g., `apiUrl`, `API_BASE`).
2. **Generated client method table**: for generative API clients (NSwag / Swagger codegen / openapi-typescript artifacts), record item by item **method name → HTTP method → endpoint path**, based on generated signatures and file line numbers (do not guess methods from method names).
3. **Client construction review**: locate the client construction entry (e.g., `src/api/index.ts`), record the baseUrl source (config-issued / hardcoded / environment variables), the authentication injection method (fetch wrapper / Bearer header / interceptors), and the outbound channels of non-generated clients (SSO browser redirects, `window.open`, forwarding by this BFF, etc.), listing each channel in the "Outbound Channels" table.

Artifact: `node/route_mapping/frontend_outbound_{timestamp}.md` (the output table is registered); structure: header method statement (rg patterns + client construction review locations) → outbound channels table (channel / target / location / description) → endpoint list grouped by baseUrl (methods follow the generated client method table; the endpoint list must annotate (method, path) per method — entries with uncertain methods are listed item by item in the next section; double-method conservative upper-bound placeholders are forbidden) → a "## Uncertain Method List" section (with component / call site / reason columns) → statistics (total outbound endpoints / outbound target count).

Execute the "frontend_outbound Outbound Endpoint Method-Level Pairing (Mandatory, 2026-09-20)" section below on the method set of each endpoint: pair method by method; the landing point of entries with uncertain methods is in that section (written into the artifact's own "## Uncertain Method List" section; double-method conservative upper bounds are forbidden).

## Coverage Gate (Mandatory)

Mirroring the Controller Inventory and API Coverage Gate semantics of `dotnet-route-mapper`.

1. Before generating `node/route_mapping/routes_{timestamp}.md`, `node/route_mapping/route_module_inventory_{timestamp}.md` must be generated first.
2. `route_module_inventory` contains at least:

| Field | Description |
| ---- | ---- |
| module_name | route module / controller / file-convention directory name |
| module_file | file path |
| route_prefix | mount prefix |
| route_count | total routes declared by this module |
| mapped_routes | number of mapped routes |
| in_route_mapping | whether it has been included in routes |
| unmapped_reason | unmapped reason |

3. As long as unmapped active route modules exist, `api_coverage_status` must be `PARTIAL`.
4. `node/quality/api_coverage_gate_{timestamp}.md` must be generated, containing at least:
   - `active_route_module_total`
   - `mapped_route_module_count`
   - `mapped_route_count`
   - `unmapped_route_modules`
   - `unmapped_routes`
   - `api_coverage_percent`
   - `api_coverage_status`
   - `unique_path_count`
   - `method_path_count`
   - `pipeline_execution_allowed_completed`
   - `reason`
5. When `api_coverage_status=PARTIAL`:
   - `node/quality/unmapped_routes_{timestamp}.md` must be persisted, containing unmapped modules, unmapped routes, reasons, and next-round remapping batch suggestions.
   - The remapping loop must be entered, refreshing `route_module_inventory`, `api_coverage_gate`, and `unmapped_routes` each round.
   - Stopping is allowed only when both unmapped active modules and routes are 0, or the user explicitly accepts `PARTIAL`.
6. When `api_coverage_percent < 100%`, marking `pipeline_execution` as `COMPLETED` is forbidden, and wording such as "full audit complete" is forbidden.

### frontend_outbound Outbound Endpoint Method-Level Pairing (Mandatory, 2026-09-20)

- The collection rules themselves (the three-piece set of rg endpoint enumeration / generated client method table / client construction review) are in the "frontend_outbound Outbound Endpoint Collection" section above; this section governs pairing and counting criteria
- The method set of each outbound endpoint in `node/route_mapping/frontend_outbound_{timestamp}.md` must undergo **method-level pairing**: reconcile each HTTP method one by one against backend routes, with each confirmed method counted as a separate (method, path) pairing record
- **Double-method conservative upper-bound annotations are forbidden**: when a method cannot be determined from source code, writing the entry as a double-method conservative upper bound such as "GET/POST" for padding is forbidden
- Entries with uncertain methods are written into the artifact's own "## Uncertain Method List" section of `frontend_outbound_{timestamp}.md` (with component / call site / reason columns); writing them into `unmapped_routes` is forbidden — `unmapped_routes` carries the inbound-unmapped semantics, and writing them in would pollute the inbound gate statistics of api_coverage_gate; entries with uncertain methods must not be counted into matched
- Counting criteria are consistent with the route count dual-field criteria of `IO_PATH_CONVENTION.md`: `method_path_count` counts only (method, path) combinations with confirmed methods

## Output

Persist per the Node.js and cross-stack artifact paths in `skills/shared/IO_PATH_CONVENTION.md`:

| Artifact | Physical Path |
| ---- | ---- |
| route_module_inventory | `node/route_mapping/route_module_inventory_{timestamp}.md` |
| routes | `node/route_mapping/routes_{timestamp}.md` |
| frontend_outbound | `node/route_mapping/frontend_outbound_{timestamp}.md` |
| params | `node/route_mapping/params_{timestamp}.md` |
| middleware_inventory | `node/route_mapping/middleware_inventory_{timestamp}.md` |
| Phase index | `node/route_mapping/index_{timestamp}.md` |
| API coverage gate | `node/quality/api_coverage_gate_{timestamp}.md` |
| Unmapped list (mandatory when PARTIAL) | `node/quality/unmapped_routes_{timestamp}.md` |
| Remapping loop record (recommended) | `node/quality/route_mapping_backfill_loop_{timestamp}.md` |

The `route_id` rule `R{sequence number}` is globally unique and consumed by downstream Tasks 8 / 9 / 11–18. `routes` and `params` entries must correspond one-to-one, and `route_id` must not drift.

### Minimum Fields of a routes Entry

The routes file header must contain the dual fields `unique_path_count` / `method_path_count`; the criteria are in the route count dual-field section of `IO_PATH_CONVENTION.md`.

- `route_id`
- Entry type: `HTTP` / `HUB` / `GRAPHQL` / `SERVERLESS` / `CLI`
- HTTP method or operation name
- Route path rule
- Route declaration style: `attribute` / `convention` / `file-based` / `manual`
- Handler identifier
- Location: `file:line`
- Mount prefix chain
- Parameter overview
- Return template type

### Minimum Fields of a params Entry

- `route_id`
- Path / Query / Body / Header / Cookie / File parameter tables
- Full request template or call template

### Pre-Output Self-Check

- [ ] `routes` and `params` have consistent `route_id`s with item-by-item correspondence.
- [ ] No elided placeholders.
- [ ] Mount prefix chains have been expanded.
- [ ] The middleware inventory distinguishes authentication-class from global.
- [ ] `api_coverage_status` is correctly linked with `unmapped_routes` / `pipeline_execution` statuses.
- [ ] `frontend_outbound` outbound endpoints have been paired at method level, without double-method conservative upper-bound annotations; entries with uncertain methods have been written into the artifact's own "## Uncertain Method List" section and not into `unmapped_routes`.
