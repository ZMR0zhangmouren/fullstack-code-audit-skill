---
name: node-feature-api-mapper
description: UI feature surface ↔ API mapping collection tool. Starting from the SPA route table and component tree import chains, builds a three-layer mapping of "feature surface → frontend client methods → (method, path) endpoints → backend route_id", producing node/route_mapping/feature_api_map_{timestamp}.md for logic audits to organize determinations by feature surface and for authentication sensitivity grading reference.
---

# Feature ↔ API Mapper

## Shared Grabber Index Reference

The paths and artifact naming of this skill follow the `node/` subtree conventions in `skills/shared/IO_PATH_CONVENTION.md`; the collection criteria are consistent with the upstream node-route-mapper artifacts (`routes_{timestamp}.md` / `frontend_outbound_{timestamp}.md`) and do not reinvent collection rules.

## Goal

Build a three-layer mapping of feature surface → endpoints → backend route_id:

1. **Feature surface**: an SPA route / page component corresponds to a user-perceivable feature (backup, export, tenant management, etc.).
2. **Endpoints**: the frontend client methods actually invoked in the component tree and their (method, path) endpoints.
3. **Backend route_id**: the backend route identifier of the endpoint in the node routes artifact or contract_map, for tracer / logic-audit reverse lookup.

**Artifact positioning red line (same as design_intent, mandatory)**: all artifacts of this skill are **view-layer references** and **must not be used as EVID evidence sources** (the same red line in `skills/shared/AUDIT_EXECUTION_COMMON.md` §9 applies); when artifacts disagree with code, **code wins**, and the disagreement is registered as a "feature view - implementation drift" governance finding — the code facts must not be modified in reverse. This skill only collects and maps; it makes no vulnerability determinations.

## Input Dependencies

User provides or upstream artifacts provide:

- `node_source_path`: Node.js project root (required).
- `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/frontend_outbound_{timestamp}.md` (required; upstream node-route-mapper artifacts; this skill reuses their route enumeration and frontend outbound collection results and does not re-enumerate).
- `cross/api_contract_map_{timestamp}.md` (optional in fullstack mode; the matched bucket is the preferred alignment source of endpoint → backend route_id).
- `node/design_intent/design_intent_{timestamp}.md` (optional; used for business-rule keyword matching of feature name heuristics and filling the "design_intent alignment reference" column).

## Collection Rule ①: SPA Route Table Extension

- **Route declaration source**: React Router route declarations (Routes.tsx / route* configuration files / framework equivalents), excluding `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`, `coverage/`.
- **Feature name column**: extend the existing route table (path / component / guard) with a fourth column **feature name**.
- **Feature name heuristic bases (by priority)**:
  1. The semantics of the trailing path segment of the route (e.g., `/backup` → "Backup Management").
  2. The semantics of the page component name (e.g., `BackupPage` → "Backup Management").
  3. design_intent business rule list keyword matching (record the rule number when hit).
- **Annotate the naming basis item by item**: every feature must annotate `naming basis` (path segment / component name / design_intent rule number); when none of the three bases hit, write `heuristic (non-evidence)` — disguising it as evidenced naming is forbidden.

## Collection Rule ②: Component Tree Import Reverse Index

- Starting from the route table page components, recursively resolve the import chain (page component → child components → …), **maximum depth 6 levels to prevent cycles**; branches that reach the depth limit without hitting a call site record the broken-link reason "indirect encapsulation deeper than one layer".
- Upon hitting an api client call site (client method references / `authorizedFetch` wrapper calls), record the three elements: **component name, call site file:line, method name**.
- Exclude `node_modules/` and build artifact directories; multiple call sites in the same component are recorded item by item and must not be merged or elided.

## Penetration Whitelist

The following three categories are identified as **relay layers**; penetrate one layer to take the internal real endpoint calls:

| Whitelist Pattern | Typical Form | Penetration Semantics |
| ---- | ---- | ---- |
| `api/index.ts`-style wrapper modules | barrel encapsulations centrally exporting client methods | penetrate one layer, taking the internal calls to real endpoints (`baseUrl + '...'`) inside the wrapper |
| `useXxx` data hooks | data fetching hooks such as `useBackup` / `useFetch` | penetrate one layer, taking the internal calls to client methods or `authorizedFetch` inside the hook |
| `authorizedFetch` wrapper functions | unified fetch wrappers / interceptor encapsulations | penetrate one layer, taking the real request paths and parameters inside the wrapper function |

**Constraints**: each layer of penetration must land on a specific call site (file:line) of the next layer; penetration depth is **limited to one layer** only; call sites that still cannot locate an endpoint after one layer of penetration are broken links, entering `unmapped_feature_calls_{timestamp}.md` — continuing to guess a second penetration layer or silently dropping them is forbidden.

**Ruling (2026-09-19)**: parsing client method definition bodies (endpoint literals inside barrels) belongs to collection rule ③ (reusing the rg rules of the "frontend_outbound Outbound Endpoint Collection" section of `node-route-mapper`) and does not count toward penetration layers.

## Broken-Link Fallback (Mandatory)

Call sites that still cannot locate an endpoint after penetration fall item by item into `node/route_mapping/unmapped_feature_calls_{timestamp}.md`, each containing (component, call site file:line, broken-link reason). The broken-link reasons fall into three classes:

1. **Dynamic string endpoints**: endpoints are template variables or runtime values (e.g., `` `/api/${mod}` ``) that cannot be closed statically. **Classification priority (2026-09-19 ruling)**: when the endpoint is a template variable / interpolation as a whole and completely unevaluable statically, it belongs to this class (①); when the path body is statically determinable but the final path cannot be reconstructed due to multi-fragment concatenation or conditional branches, it belongs to "runtime concatenation" (③).
2. **Indirect encapsulation deeper than one layer**: the call site goes through indirect encapsulation outside the whitelist or deeper than one layer, and the real endpoint cannot be located.
3. **Runtime concatenation**: endpoints are concatenated at runtime from multiple fragments (string concatenation / array join / conditional branch concatenation), and the final path cannot be reconstructed statically.

Constraints (following the unmapped semantics):

- **Silent dropping forbidden**: any unclosed call site must appear in the unmapped list or the mapping table and must not be elided.
- When `unmapped_count > 0`, `coverage_status=PARTIAL`, and entering the remapping loop is recommended (refreshing the mapping and the unmapped list each round); stopping is allowed only when unmapped is cleared or the user explicitly accepts it.
- When `coverage_status=PARTIAL`, claiming the feature view is complete is forbidden.

## Collection Rule ③: client method → endpoint → backend route_id

- **client method → endpoint**: reuse the rg rules of the "frontend_outbound Outbound Endpoint Collection" section of `node-route-mapper` (the `baseUrl + '...'` pattern + generated client method table + client construction review; see that skill's body); do not reinvent them.
- **endpoint → backend route_id**:
  - fullstack mode: prefer consuming the **matched bucket** of `cross/api_contract_map_{timestamp}.md`;
  - single-stack node mode: align directly with `routes_{timestamp}.md` by (method, path);
  - when neither matches, write `backend_route_id: N/A` and count it as a broken link (into the unmapped list).
- The backend controller domain is taken from the handler attribution of the routes artifact; write `N/A` when it cannot be attributed.

## Artifact Contract

Artifact: `node/route_mapping/feature_api_map_{timestamp}.md`. Four mandatory header fields:

```md
feature_total: {N}
endpoint_link_count: {M}
unmapped_count: {K}
coverage_status: COMPLETE | PARTIAL | NOT_APPLICABLE
```

The complete template of the three-section structure:

```md
# feature_api_map_{timestamp}

feature_total: {N}
endpoint_link_count: {M}
unmapped_count: {K}
coverage_status: COMPLETE | PARTIAL | NOT_APPLICABLE

## 1. Feature List

| feature_id | Feature Name | SPA Route | Page Component file:line | Guard | design_intent Alignment Reference | Naming Basis |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| F001 | … | … | … | … | rule number or "none" | path segment / component name / design_intent rule number / heuristic (non-evidence) |

## 2. Feature → Endpoint Mapping Table

| feature_id | Frontend Client Method | (method, path) Endpoint | backend_route_id | Backend Controller Domain | Channel (Direct / BFF Relay) |
| ---- | ---- | ---- | ---- | ---- | ---- |
| F001 | … | … | R{sequence} or N/A | … | Direct / BFF Relay |

## 3. Coverage Statistics and Broken Links

- Distribution of endpoint counts per feature (min / median / max, and the list of features with zero endpoints).
- unmapped_feature_calls reference path: `node/route_mapping/unmapped_feature_calls_{timestamp}.md` (must be persisted and referenced when unmapped_count > 0).
- Coverage conclusion: proportion of features within coverage, which encapsulation patterns the broken links concentrate in, and next-round remapping suggestions.
```

Red line restated: the artifact is a view-layer reference and must not be used as an EVID evidence source; when it disagrees with code, code wins, and the disagreement is registered as a "feature view - implementation drift" governance finding.

## fail-open

Pure BFF / no-SPA-frontend projects are not blocked: first execute the probing evidence rg commands (such as `rg --files -g 'Routes.tsx' -g 'route*.{ts,tsx,js,jsx}' -g '!node_modules'` and `rg -n "createBrowserRouter|<Route|path=" src/`), persist the probing evidence (no route declaration files) as an explanation, and write in the artifact header:

```md
feature_total: 0
endpoint_link_count: 0
unmapped_count: 0
coverage_status: NOT_APPLICABLE
```

And state the probing commands and the determination basis of "no SPA route declarations" in the body; this explanation file does not block subsequent pipeline phases.

## Acceptance

1. The four mandatory header fields are complete: `feature_total` / `endpoint_link_count` / `unmapped_count` / `coverage_status`.
2. All three sections are present, and the mapping table column names are verbatim identical to the artifact contract template (`feature_id | Frontend Client Method | (method, path) Endpoint | backend_route_id | Backend Controller Domain | Channel`).
3. Every feature list entry has a `naming basis`; entries without basis must write `heuristic (non-evidence)`.
4. Import chain recursion depth ≤ 6 levels; the penetration whitelist penetrates only one layer.
5. `unmapped_count` is consistent with the entry count of `unmapped_feature_calls_{timestamp}.md`; every broken link has one of the three-class reasons, with no silent dropping.
6. When `coverage_status=PARTIAL`, there is a remapping loop suggestion; when `NOT_APPLICABLE`, there are probing evidence rg commands and outputs.
7. Red line self-check: the body contains no EVID definitions and no vulnerability determination conclusions; the artifact positioning states view-layer reference, forbidden as an EVID evidence source, and code wins on inconsistency.

## Do NOT Do

- Make no vulnerability determinations and no traces (determinations and tracing stay in logic-audit / route-tracer).
- No adaptation for frameworks other than React (start a project for Vue / Angular when real demand appears, YAGNI).
- Do not modify the existing artifact structure of the upstream route-mapper or the three-bucket semantics of contract-mapper; do not re-enumerate routes (reuse routes / frontend_outbound).
- Do not add EVID IDs; artifacts must not be used as EVID evidence sources.
- Do not silently drop broken-link call sites; do not disguise heuristic naming as evidenced naming.
