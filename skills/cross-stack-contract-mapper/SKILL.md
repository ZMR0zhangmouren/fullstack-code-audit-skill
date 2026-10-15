---
name: cross-stack-contract-mapper
description: Cross-stack contract reconciliation Skill for frontend/backend. Reconciles frontend/BFF outbound calls against the dotnet backend route list item by item, producing three buckets (matched / frontend_only / backend_only), where backend_only is written directly into the high-risk entry pool suggestions as a hidden attack surface.
---

# Cross-Stack Contract Mapper

## Shared Grabber Index References

This Skill's enumeration keywords, normalization rules, and artifact paths take `skills/shared/IO_PATH_CONVENTION.md` as the single source of truth; frontend call-site grabbers also reference the cross-stack / HTTP client sections of `skills/shared/NODE_AUDIT_GRABBER_INDEX.md`. The dotnet-side route consumption format follows `route_mapping/routes_{timestamp}.md` output by `skills/dotnet-route-mapper/SKILL.md`, and parameter structures consume `route_mapping/params_{timestamp}.md`.

## Input Dependencies

- `dotnet_source_path` and `dotnet/route_mapping/routes_{timestamp}.md`: the dotnet-side mapped route list (required).
- `node_source_path`: the frontend/BFF source code root directory (required).
- `dotnet/route_mapping/params_{timestamp}.md`: dotnet-side parameter structures (required for parameter-level reconciliation).
- `node/stack_detect/stack_detect_{timestamp}.md`: phase 0 stack detection, used to select framework-specific call patterns (recommended).
- `context_path` / baseURL environment variable names: reverse proxies, gateway prefixes, Next.js basePath, vite/webpack devServer proxy prefixes, etc. (optional; a configuration or code evidence source is required).

## Frontend Call-Site Enumeration (Mandatory Refinement)

Locate every outbound HTTP call in the frontend/BFF source code item by item; silently discarding is forbidden. Priority grabbers:

| Category | Priority Keywords / Patterns | Record Requirements |
| ---- | ---- | ---- |
| Generic HTTP clients | `axios.`, `fetch(`, `$fetch`, `useFetch`, `got(`, `request(` | Method, URL template or call chain, source file location |
| Project encapsulation | `apiClient`, `request`, and other internal encapsulations (per actual naming) | Trace the baseURL inside the encapsulation and the final request assembly |
| Next.js specific | `rewrites()`, `middleware.ts` rewrite targets | Record the real target path after rewriting |
| Proxy middleware | `http-proxy-middleware`, vite/webpack `devServer.proxy` | Expand the proxy prefix and target mapping |
| baseURL environment variables | `process.env.API_BASE_URL`, `import.meta.env.VITE_API_BASE_URL`, etc. | The baseURL value evidence must be recorded for later assembly expansion |

The following must be recorded simultaneously during enumeration:

- `call_id`: globally unique call-site identifier.
- `frontend_site`: the project subdirectory/module where the call site lives (e.g. `web/`, `bff/`, `admin/`).
- `method`: HTTP method; dynamic methods must be annotated `DYNAMIC` and listed in the unnormalized list.
- `raw_path`: the URL template or concatenation fragment visible in source code.
- `base_url`: the actually effective baseURL (including the environment variable name and default value).
- `source_file:line`: the call-site location.

## Normalization Rules (Mandatory)

Construct a reconciliation key `(HTTP_METHOD, normalized_path)` for each frontend call:

1. **baseURL assembly expansion**: concatenate `baseURL + url` or template prefixes with path fragments into a complete path; environment variables must be expanded per their actual values or defaults; if undeterminable, annotate `base_url_unknown`.
2. **Static prefix of template strings**: for dynamic concatenations such as `` `/api/users/${id}` `` or `` `/api/users/` + userId ``, take the statically determinable path prefix `/api/users/`; purely dynamic paths (e.g. a variable used as the whole path) that cannot be normalized are listed in the "Unnormalized List".
3. **Path parameter normalization**: unify path parameter placeholders such as `:id`, `:name`, `[id]`, `*`, `{id}` into `{param}`.
4. **Method normalization**: HTTP methods are uniformly uppercased; methods that cannot be statically determined are annotated `DYNAMIC` and listed in the unnormalized list.
5. **Trailing slash and query string handling**: trailing slash differences are removed (only for reconciliation key comparison; the original path is kept in `notes`); query parameters keep only the path portion in `normalized_path`, with query field names handled in parameter-level reconciliation.

## Three-Bucket Reconciliation (Mandatory)

Using `(HTTP_METHOD, normalized_path)` as the key, compare frontend calls item by item against `route_method` + normalized `route_path_template` in dotnet's `routes_{timestamp}.md`, and output three buckets:

| Bucket | Meaning | Downstream Action |
| ---- | ---- | ---- |
| `matched` | Frontend and backend contracts are consistent | Enter parameter-level reconciliation and serve as the input pool for `cross-stack-taint-linker` |
| `frontend_only` | A frontend call exists, but the dotnet backend has no corresponding route | Ghost-call clue; write into `cross/api_contract_map_{timestamp}.md` with possible causes annotated (zombie endpoint / version drift / gateway proxy / BFF forwarding) |
| `backend_only` | The dotnet backend exposes a route, but no corresponding call appears in the frontend/BFF | Hidden attack surface; must be written into `cross_analysis/high_risk_routes_{timestamp}.md` (or `cross_analysis/sampled_high_risk_routes_{timestamp}.md`) suggestions, preferentially entering the dotnet-side route-tracer |

**Follow-up actions for frontend_only (mandatory)**: classify each frontend_only record by possible cause and give a disposal action — zombie endpoint: check recent git log to confirm deletion or retention and record the decision; version drift: check frontend and backend release versions, upgrade-align or record the baseline difference; gateway proxy: check the external gateway routing table to confirm whether it is consumed by the gateway; BFF forwarding: check the BFF-layer forwarding target to confirm link integrity. The classification and actions must be written into the notes column of `cross/api_contract_map_{timestamp}.md`.

The `api_contract_map` header is fixed:

| call_id | method | normalized_path | frontend_site | matched_route_id | bucket | param_diff | notes |

- `matched_route_id`: the matched dotnet `route_id`; write `N/A` for `frontend_only`.
- `param_diff`: see the next section; `N/A` is acceptable for `frontend_only`.
- `notes`: unnormalized reasons, baseURL evidence, ghost-call inference, hidden attack surface annotations, etc.

## Parameter-Level Reconciliation

Perform a second-pass reconciliation on `matched` records: compare the set of query/body field names actually sent by the frontend call with the set of parameters declared as accepted by that route_id in dotnet's `params_{timestamp}.md`.

- Write fields "accepted by the backend but never sent by the frontend" into the `param_diff` subsection.
- Write fields "sent by the frontend but not declared by the backend" as potential hidden parameters / Mass Assignment / version drift clues into `notes`.
- Annotate field name mapping differences (e.g. frontend `userId` vs backend `user_id`) in `notes`.

`param_diff` output format example:

```md
- param_diff:
  - backend_only_params: [field_a, field_b]
  - frontend_only_params: [field_x]
  - mapping_mismatch: [{frontend: userId, backend: user_id}]
```

## Coverage Gate (Mandatory)

`cross/contract_coverage_gate_{timestamp}.md` must be persisted, containing at least:

- Three-bucket counts: `matched_count`, `frontend_only_count`, `backend_only_count`. The denominator of all three buckets uniformly takes `method_path_count` (the (method,path) expansion standard); consuming `unique_path_count` is a standard violation.
- Unnormalized call-site list: `unnormalized_calls`; call sites that cannot be normalized due to dynamic concatenation must be listed; silent discarding is forbidden.
- Contract coverage:

```
contract_coverage_percent = matched / (matched + frontend_only + backend_only)
```

- `unnormalized_rate`: `unnormalized_calls count / total frontend outbound calls × 100%`; when > 10%, `contract_coverage_status` is forced to `PARTIAL` (the coverage statistics standard is distorted and must be declared as a conditional value).
- `contract_coverage_status`: `COMPLETE` / `PARTIAL`.
- Per-stack declaration: if `dotnet_api_coverage_status=PARTIAL` or `node_api_coverage_status=PARTIAL`, its `matched` rate conclusion must be annotated "affected by that stack's PARTIAL status; contract coverage is a conditional value".
- `cross_analysis/high_risk_routes_source`: the source file path where `backend_only` entries are written into the high-risk entry pool.
- When `params_{timestamp}.md` is missing: parameter-level reconciliation cannot be executed; `contract_coverage_status` is degraded and annotated `audit_side_missing=dotnet_params` (or `=node_params`); matched records keep only path-level conclusions.
- `pipeline_execution_allowed_completed`: allowed to be `true` only when `contract_coverage_status=COMPLETE` and both stacks' `api_coverage_status` (i.e. `dotnet_api_coverage_status` and `node_api_coverage_status`, corresponding to each stack's `quality/api_coverage_gate_{timestamp}.md`) are not PARTIAL (or the user explicitly accepts).

## Output

Persist per the cross-stack artifact paths in `skills/shared/IO_PATH_CONVENTION.md`:

| Artifact | Physical Path |
| ---- | ---- |
| Contract reconciliation three-bucket table | `cross/api_contract_map_{timestamp}.md` |
| Contract coverage gate | `cross/contract_coverage_gate_{timestamp}.md` |
| Phase index | `cross_analysis/index_{timestamp}.md` (records the execution status and artifact list of cross-stack-contract-mapper) |
| Empty-result statement | `cross_analysis/empty_result_{timestamp}.md` (when there are no valid call sites or in single-stack mode) |

`cross/api_contract_map_{timestamp}.md` must contain:

- Reconciliation scope statement (dotnet routes timestamp, node source scope, baseURL evidence).
- `api_contract_map` master table (fixed header).
- Subsections by `bucket`: `matched`, `frontend_only`, `backend_only`.
- `param_diff` subsection (aggregating parameter differences of matched records).
- `unnormalized_calls` subsection.
- Conclusions and next actions (entering `cross-stack-taint-linker`, `backend_only` high-risk entry pool suggestions).
