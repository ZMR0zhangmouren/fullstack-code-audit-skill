---
name: cross-stack-taint-linker
description: Cross-stack taint chain splicing Skill. Uses the matched records of contract-mapper as the chain starting pool, splices the node-side entry-to-outbound-call taint flow with the dotnet-side route-tracer evidence into cross-stack forward/reverse chains, is constrained by the trace-gate dual-evidence rule, and sends unclosed chains to the risk pool.
---

# Cross-Stack Taint Linker

## Shared Grabber Index References

This Skill's artifact paths take `skills/shared/IO_PATH_CONVENTION.md` as the single source of truth (`cross_taint_links_{timestamp}.md` is registered at :252). Node-side outbound call-site grabbers reference the HTTP client sections of `skills/shared/NODE_AUDIT_GRABBER_INDEX.md`; evidence point references follow `skills/shared/EVIDENCE_POINT_IDS.md` (node side `EVID_NODE_*`, dotnet side existing `EVID_*`). The evidence consumption format for frontend rendering sinks and dotnet response fields follows the outputs of the corresponding vulnerability specialties (node side `node-xss-audit`, dotnet side `dotnet-xss-audit/SKILL.md`).

## Input Dependencies

| Input | Path | Necessity |
| ---- | ---- | ---- |
| Contract reconciliation three-bucket table | `{output_root}/cross/api_contract_map_{timestamp}.md` | **Required**; `matched` records are the chain starting pool |
| node-side route-tracer artifacts | `{output_root}/node/route_tracer/` trace artifacts | Read as needed by chain (must exist for closed chains) |
| dotnet-side route-tracer artifacts | `{output_root}/dotnet/route_tracer/` trace artifacts | Read as needed by chain (must exist for closed chains) |
| node-side outbound call-site list | route-tracer aggregation or this Skill's enumeration of `axios` / `fetch(` / `got(` and other outbound calls | Required (forward chain positioning) |
| Stack detection | `{output_root}/node/stack_detect/stack_detect_{timestamp}.md` | Recommended (determine frontend form and SSR surface) |

- Prerequisite constraint: when `cross/api_contract_map_{timestamp}.md` does not exist or `matched_count=0`, this Skill degrades to executing only reverse chains (dotnet response → frontend rendering sink does not require contract records), and declares `forward_chain_skipped=NO_MATCHED_RECORD` in the artifact.
- Cross-stack chain splicing depends on dual-stack trace timestamps: node and dotnet route-tracer artifact timestamps must belong to the same audit batch as contract_map; chains with inconsistent batches are annotated `trace_batch_mismatch` in `missing_evidence`.

## Forward Chain Tracing (Browser → BFF → dotnet sink)

Forward chain definition: **node source → BFF internal passing → outbound call parameters → (aligned via contract_map matched records) → dotnet corresponding route parameters → dotnet sink**, direction annotated `forward`. Chain sketch:

```
req.* (node source, user-controllable)
  → BFF internal passing (middleware / route handlers / data assembly)
  → outbound call parameters (axios/fetch/got request body or query)
  → contract_map matched record ((METHOD, normalized_path) alignment)
  → dotnet corresponding route parameters (route_id + parameter name alignment)
  → dotnet sink (SQL/command/file/deserialization, etc.)
```

Execution steps (mandatory):

1. **Take the chain starting pool**: read all `matched` records from `cross/api_contract_map_{timestamp}.md`; `backend_only` records are not in this pool (their chains belong to dotnet single-stack traces); `frontend_only` records are listed separately as "ghost calls" remarks and do not participate in splicing.
2. **Locate outbound call sites**: go back to the frontend/BFF source code by `call_id`, confirming whether the call site's actual request body/query contains user-controllable fields (`req.*` or data injected by upstream middleware); enumeration keywords `axios.`, `fetch(`, `$fetch`, `got(`, `request(` and project encapsulations.
3. **Trace the node-side taint flow**: the internal passing path from node source → outbound call parameters, forming the node-side half-chain (cite `node/route_tracer/` trace artifacts or `EVID_NODE_*` evidence, e.g. `EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT`, `EVID_NODE_SESS_*`, taking the evidence point corresponding to the pollution type).
4. **Align the contract record**: reconcile the outbound call's `(METHOD, normalized_path)` with the matched record; record the line number / record key as the `contract_record` reference (format: `api_contract_map_{ts}.md line/record`).
5. **Trace the dotnet-side half-chain**: starting from the matched `matched_route_id`, consume the trace of that route in `dotnet/route_tracer/`, confirming the path by which parameters reach the sink; when no ready trace exists, cite the dotnet route-mapper parameter structure and annotate `dotnet_trace_pending`.
6. **Numbering and registration**: a hit generates a `XTRACE-{n}` cross-stack chain ID. Numbering independently starts from `XTRACE-1` (contract-mapper has no global chain numbering convention); forward and reverse chains share the same numbering sequence; one chain one ID, reuse is forbidden.

## Reverse Chain Tracing (dotnet response → frontend rendering sink)

Reverse chain definition: **dotnet response field (e.g. passthrough of user-controllable fields) → frontend rendering sink → the main channel of the stored XSS exploit chain**, direction annotated `reverse`. Chain sketch:

```
dotnet response field (e.g. user-controllable field passed through verbatim)
  → BFF passthrough/wrapping (fetch response forwarding)
  → frontend rendering sink
    ├── dangerouslySetInnerHTML
    ├── v-html
    └── SSR hydration (__NEXT_DATA__ / __NUXT__)
  → the main channel of the stored XSS exploit chain
```

Execution steps (mandatory):

1. **Locate passthrough response fields**: take the evidence of "response fields controllable and unsanitized" from the dotnet-side route-tracer / XSS specialty artifacts (cite `EVID_XSS_*` or dotnet route-tracer file line numbers).
2. **Confirm the BFF passthrough form**: whether the BFF forwards the response body verbatim (no re-encoding, no sanitization) — cite the node-side outbound call site and the response handling code location.
3. **Locate the frontend rendering sink**: the position where `dangerouslySetInnerHTML` / `v-html` / SSR hydration (`__NEXT_DATA__` / `__NUXT__`) renders this field, citing `EVID_NODE_XSS_SSR_HYDRATION` and other evidence; combine with `node/stack_detect/stack_detect_{timestamp}.md` to determine whether it is a pure SPA or an SSR surface.
4. **Numbering and registration**: a hit generates `XTRACE-{n}`, the direction field is `reverse`, the conclusion is annotated as the main channel of the stored XSS exploit chain, for consumption by `cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md`.

## Trace-Gate Dual-Evidence Constraint (Mandatory)

Cross-stack high-severity conclusions (closed chains) must hold **both** sides' evidence simultaneously; neither is dispensable:

| Evidence Side | Requirement | Acceptable Forms |
| ---- | ---- | ---- |
| node side | must exist | `EVID_NODE_*` evidence points or `node/route_tracer/` trace file references (including file path and line number) |
| dotnet side | must exist | dotnet route-tracer trace file references or existing `EVID_*` evidence points (including file path and line number) |

Constraint rules (mandatory):

- Chains with only single-side evidence uniformly enter the **pending evidence risk pool**; silent deletion is forbidden (consistent with the false-negative suppression principle).
- Closed states may only be annotated as: `closed` (both evidence sets complete) / `pending` (evidence missing); `closed` and `False Positive (both sides' protection evidence complete and fail-close)` are mutually exclusive — when both-side protection evidence exists, go through the false-positive determination instead of closure.
- Cited evidence must truly exist: this Skill is forbidden from citing evidence points that have not been persisted; cited `file:line` references must be existence-checked before delivery.

## Determination Rules

Three-state determination (for each XTRACE chain):

| Conclusion | Condition |
| ---- | ---- |
| `Confirmed (dual-evidence closed)` | node-side trace evidence + dotnet-side route-tracer evidence are both complete, the contract record is precisely matched (`param_diff` has no missing frontend fields causing chain breakage), and neither side has protection evidence |
| `Pending Verification (single-side evidence or contract record imprecise)` | Only single-side evidence; or the contract record is unmatched / loosely aligned; or trace_batch_mismatch |
| `False Positive (both sides' protection evidence complete and fail-close)` | Either side has complete protection evidence (parameterized queries, encoding sanitization, output escaping, strict validation, etc.), and the chain is blocked fail-close |

The determination order is mandatory: check protection first (false positive) → then check evidence completeness (confirmed / pending verification) → everything else enters the risk pool. All three-state conclusions must leave traces in the artifact; omitting `Pending Verification` chains is forbidden.

## Risk Pool and Unclosed Handling

- Unclosed chains (`Pending Verification`) are written into the `open` section of `cross/cross_taint_links_{timestamp}.md`, displayed alongside the `closed` section.
- The missing evidence list is enumerated item by item, classified:
  - `missing_node_trace`: missing node-side trace / outbound call-site evidence.
  - `missing_dotnet_trace`: missing dotnet-side route-tracer evidence.
  - `contract_record_unmatched`: contract record unmatched (including `frontend_only` ghost calls and `param_diff` breakage).
- Next actions for chains in the open section: after backfilling the corresponding stack's route-tracer, roll back and re-run this Skill; deletion is forbidden.
- When all chains are closed but open chains exist, the artifact conclusion must declare `trace_closure_status=PARTIAL`; writing it as fully closed is forbidden.

## Evidence References

Evidence points directly cited by this Skill (citation standard follows `skills/shared/EVIDENCE_POINT_IDS.md`):

| Evidence Point | Purpose |
| ---- | ---- |
| `EVID_NODE_*` (e.g. `EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT`, `EVID_NODE_SESS_*`) | node-side taint propagation / injection surface evidence |
| dotnet-side existing `EVID_*` (e.g. `EVID_XSS_*`, `EVID_SQL_*`, etc. by sink type) | dotnet-side sink evidence |
| contract_map record line numbers | `contract_record` reference (`cross/api_contract_map_{timestamp}.md`) |
| `node/route_tracer/`, `dotnet/route_tracer/` trace file references | the carrier of the dual-evidence constraint |

## Output

Persist `cross/cross_taint_links_{timestamp}.md` per `skills/shared/IO_PATH_CONVENTION.md` (:252), fields:

| Field | Description |
| ---- | ---- |
| `cross_trace_id` | `XTRACE-{n}`, unique cross-stack chain ID |
| Direction | `forward` / `reverse` |
| Node-side evidence | `EVID_NODE_*` or node trace file reference (path:line) |
| Contract record reference | contract_map line/record (the matched record of `api_contract_map_{ts}.md`) |
| Dotnet-side evidence | dotnet route-tracer file reference or `EVID_*` (path:line) |
| Closure status | `closed` / `pending` |
| Missing evidence list | `missing_node_trace` / `missing_dotnet_trace` / `contract_record_unmatched` enumerated item by item |

Artifact structure (mandatory): reconciliation scope and batch declaration, `closed` section (confirmed chains master table + per-chain details), `open` section (pending-verification chains + missing evidence list), false-positive section (three-state traces), `trace_closure_status` and next actions.

Relationship with fullstack-audit-pipeline phase 6: this Skill is invoked by fullstack phase 6 (cross-stack correlation); the XTRACE chains in its output `cross/cross_taint_links_{timestamp}.md` are consumed by `cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md` as the input of cross-stack exploit chain aggregation.

**XTRACE chain formal artifact (P1 deliverable, replacing the NOT_RUN placeholder)**: each chain in `cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md` must contain:
- `chain_id`: `XTRACE-{n}`
- Chain feasibility: `Confirmed Feasible` (all C/H-grade single points on the chain have completed dynamic re-verification) / `Inferred Feasible` (contains static-evidence-only single points) / `Theoretically Feasible` (assumption links exist that are not closed)
- Impact assessment: impact scope (frontend session / backend data / tenant boundary), attack complexity, precondition list
- Evidence anchors: each link carries `file:line` or the upstream artifact path (frontend Source trace, backend route trace, contract_map line)
- The conclusion must not be stronger than the weakest evidence strength on the chain (mandatorily linked with POC dynamic verification)
