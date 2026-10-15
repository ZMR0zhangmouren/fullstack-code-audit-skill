---
name: cross-stack-consistency-audit
description: Two-sided configuration consistency audit Skill. Performs five groups of reconciliation (JWT/Cookie/CORS/CSRF/error handling) between the node side and the dotnet side; differences are vulnerability clues, and the output cross/consistency_findings_{timestamp}.md is consumed by the full-stack closing consistency check.
---

# Cross-Stack Consistency Audit

## Shared Grabber Index References

This Skill's artifact paths take `skills/shared/IO_PATH_CONVENTION.md` as the single source of truth (`consistency_findings_{timestamp}.md` is registered at :253). Evidence point references follow `skills/shared/EVIDENCE_POINT_IDS.md`: the node side cites `EVID_NODE_CFG_*` / `EVID_NODE_SESS_*`, and the dotnet side cites the existing `EVID_CFG_*` / `EVID_AUTH_*` — cross-stack citation of each side's own evidence points is the legitimate use of this Skill (each side collects its own evidence, then reconcile).

## Input Dependencies

| Input | Path | Necessity |
| ---- | ---- | ---- |
| dotnet-side authentication audit artifacts | `{output_root}/dotnet/auth_audit/` (or equivalent) | Required (JWT/CSRF reconciliation) |
| dotnet-side configuration audit artifacts | `{output_root}/dotnet/config_audit/` (or equivalent) | Required (Cookie/CORS/error handling reconciliation) |
| node-side authentication audit artifacts | `{output_root}/node/auth_audit/` (or equivalent) | Required (JWT/CSRF reconciliation) |
| node-side configuration audit artifacts | `{output_root}/node/config_audit/` (or equivalent) | Required (Cookie/CORS/error handling reconciliation) |
| Stack detection | `{output_root}/node/stack_detect/stack_detect_{timestamp}.md` | Required (determine frontend deployment form and SSR surface; CORS/CSRF reconciliation depends on it) |
| Contract reconciliation three-bucket table | `{output_root}/cross/api_contract_map_{timestamp}.md` | Optional (corroboration of whether the BFF forwards/relays requests) |

- Prerequisite constraint: when either side's audit artifacts are missing, the reconciliation item conclusions for that side are uniformly `Pending Verification (one side's evidence missing)`; inferring a difference from a single side is forbidden; for reconciliation items where both sides' artifacts are missing, declare `audit_side_missing=both` in the artifact and suspend the whole group.

## Reconciliation Items (Five Groups, Mandatory)

Differences are vulnerability clues; output a comparison table per group. The comparison table skeleton is fixed: **check point column + node-side evidence collection guide column + dotnet-side evidence collection guide column**.

| Reconciliation Item | Check Points | Node-Side Evidence Guide | Dotnet-Side Evidence Guide |
| ---- | ---- | ---- | ---- |
| JWT | Consistency of key sources between the issuing side and the verifying side; algorithm pinning (forbidding `alg:none` / algorithm confusion); whether expiration (exp) and audience (aud) validation are consistent | `EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG` (jwt.sign/jwt.verify configuration), `EVID_NODE_SESS_JWT_ALG_PINNED` (algorithm pinning), `EVID_NODE_SESS_SECRET_SOURCE` (key source) | `EVID_AUTH_TOKEN_DECODE_JUDGMENT` (ticket parsing judgment), `EVID_CFG_RUNTIME_SETTING_CODE`, `EVID_CFG_CONFIG_LOCATION` (key configuration location and source) |
| Cookie | Whether the two sides' Set-Cookie HttpOnly / Secure / SameSite / Domain / Path weaken each other (e.g. flags lost when the BFF rewrites cookies) | `EVID_NODE_SESS_COOKIE_FLAGS` (cookie flags evidence) | `EVID_CFG_SECURITY_SWITCH_EVIDENCE` and framework cookie configuration artifacts |
| CORS | Backend origin whitelist vs the frontend's real deployment domain; the `Access-Control-Allow-Credentials` and wildcard combination (**explicitly forbidden combination**: `Allow-Credentials: true` + `*` wildcard) | `EVID_NODE_CFG_SECURITY_SWITCH` (CORS wildcard+credentials evidence) | `EVID_CFG_SECURITY_SWITCH_EVIDENCE` (dotnet CORS policy configuration) |
| CSRF | Whether the BFF performs token relay; whether the two sides' SameSite dependencies are consistent; whether a replacement is missing after csurf deprecation | `EVID_NODE_CFG_MIDDLEWARE_ORDER` (middleware order and short-circuit conditions), csurf/csrf library usage | `EVID_AUTH_PERMISSION_CHECK_EXEC`, dotnet-side CSRF/anti-forgery token configuration artifacts |
| Error handling | Whether the two sides' error responses leak stacks / internal paths / version fingerprints | `EVID_NODE_CFG_ERR_HANDLER` (global exception handling and error response leakage) | `EVID_CFG_IMPACT_ASSOCIATION` (configuration impact association, including error handling switches) |

Reconciliation semantics: **a consistency difference ≠ necessarily a vulnerability**; a difference is only a vulnerability clue; whether it holds must be argued in the `risk impact` field in combination with entry reachability (whether the configuration path has a reachable attack surface).

## Execution Steps

Execute group by group per reconciliation item (all five groups must produce comparison tables; skipping groups is forbidden):

1. **Preparation**: confirm both sides' audit artifacts are complete; confirm the frontend deployment form (pure SPA / SSR / BFF) and the source of the real deployment domain (configuration file or deployment evidence) from `stack_detect`, as the frame of reference for CORS/CSRF reconciliation.
2. **JWT reconciliation**: determine the actual issuer (node or dotnet); compare the two sides' `key sources` (hardcoded / environment variables / certificates) and algorithm pinning policies (rejecting `alg:none`, algorithm whitelists); compare exp/aud validation parameters (the side that is missing or relaxed is the clue).
3. **Cookie reconciliation**: compare the two sides' Set-Cookie HttpOnly/Secure/SameSite/Domain/Path settings; focus on whether flags are lost in BFF rewrite/relay scenarios (e.g. the dotnet side sets Secure but the BFF re-set does not carry it).
4. **CORS reconciliation**: take the backend's actually effective origin whitelist vs the frontend's real deployment domain (including devServer proxy expansion); check whether the `Allow-Credentials` and wildcard combination falls into the explicitly forbidden combination.
5. **CSRF reconciliation**: confirm whether the BFF has a CSRF token relay (receiving the frontend token and forwarding it to the backend, or relying on session cookie direct pass-through); compare whether the two sides' SameSite dependencies are consistent (one side relying on SameSite=Strict while the other is Lax is a weakening); whether a replacement is missing after csurf deprecation (`double-submit` / custom middleware / SameSite + custom header).
6. **Error handling reconciliation**: compare the two sides' error response forms — whether stack traces, internal physical paths, and framework version fingerprints are exposed; the coverage of exception handlers.
7. **Aggregate and register**: register the comparison table conclusions group by group into `cross/consistency_findings_{timestamp}.md`, generating one `CONS-{n}` per difference.

## Determination Rules

Three-state determination (for each `CONS-{n}` difference clue):

| Conclusion | Condition |
| ---- | ---- |
| `Confirmed Difference (both sides' evidence is explicit and the difference holds)` | Both sides' evidence is complete (both stacks' audit artifacts persisted), the difference objectively holds, and combined with entry reachability it can be argued to constitute a risk |
| `Pending Verification (one side's evidence missing)` | Either side's audit artifacts are missing, configuration values cannot be confirmed, or whether the difference holds needs dynamic re-verification |
| `False Positive (both sides' configurations are consistent or the difference is offset by protection)` | Both sides' configurations are consistent; or a difference exists but is offset by protection (e.g. the CORS whitelist does not include the frontend domain but same-origin deployment has no cross-origin surface; cookie flags missing but protected by another layer) |

Determination semantics (mandatory):

- "Differences are vulnerability clues" only means the difference **deserves registration and deeper investigation**; it must not be automatically escalated to a vulnerability conclusion; vulnerability-level conclusions must cite back to the corresponding stack's vulnerability specialty evidence.
- Protection offset must cite evidence (the location and configuration evidence of the protection); inferring offset without evidence is forbidden.
- All three states must leave traces in the artifact; `Pending Verification` items must not be silently deleted.

### CONS-{n} → Cross-Stack Exploit Chain Linkage Rules

- The "difference (needs fixing)" class of CONS-{n} in the three states automatically enters the cross-stack chain candidate pool: when the difference involves authentication (JWT/cookie lifecycle inconsistency), CORS (origin and credential policy inconsistency), or CSRF (asymmetric protection on the two sides), it must be assessed whether it can form a cross-stack exploit chain (frontend forges → backend accepts).
- Linkage output: annotate `consistency_clue=CONS-{n}` for each linked candidate chain in `cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md`; the feasibility determination is consistent with the T2-5 formal artifacts.
- Linkage threshold: when a single CONS-{n} is insufficient to close the chain, record `clue_open` into the pending evidence risk pool; giving "confirmed feasible" directly is forbidden.

## Evidence References

| Evidence Point | Side | Purpose |
| ---- | ---- | ---- |
| `EVID_NODE_CFG_SECURITY_SWITCH` | node | Security switches / default configuration (helmet, CORS wildcard+credentials) |
| `EVID_NODE_CFG_RUNTIME_SETTING` | node | Runtime configuration (process.env, dotenv, .env leakage) |
| `EVID_NODE_CFG_MIDDLEWARE_ORDER` | node | Middleware / guard order and short-circuit conditions |
| `EVID_NODE_CFG_SSR_MODE` | node | SSR / isomorphic rendering mode (auxiliary for CORS same-origin determination) |
| `EVID_NODE_CFG_ERR_HANDLER` | node | Error handling and stack leakage evidence |
| `EVID_NODE_SESS_JWT_*`, `EVID_NODE_SESS_COOKIE_FLAGS` | node | JWT configuration and cookie flags evidence |
| `EVID_CFG_CONFIG_LOCATION` / `EVID_CFG_RUNTIME_SETTING_CODE` / `EVID_CFG_IMPACT_ASSOCIATION` / `EVID_CFG_SECURITY_SWITCH_EVIDENCE` | dotnet | Configuration location, runtime settings, impact association, and security switch evidence |
| `EVID_AUTH_*` (e.g. `EVID_AUTH_TOKEN_DECODE_JUDGMENT`) | dotnet | Authentication ticket parsing and permission check evidence |

Before citing `EVID_NODE_CFG_*`, confirm it is registered in the NODE namespace CFG group of `skills/shared/EVIDENCE_POINT_IDS.md` (SECURITY_SWITCH / RUNTIME_SETTING / MIDDLEWARE_ORDER / SSR_MODE / ERR_HANDLER are all registered).

## Output

Persist `cross/consistency_findings_{timestamp}.md` per `skills/shared/IO_PATH_CONVENTION.md` (:253), fields:

| Field | Description |
| ---- | ---- |
| `finding_id` | `CONS-{n}`, unique reconciliation clue ID |
| Reconciliation item | one of `JWT` / `Cookie` / `CORS` / `CSRF` / `Error Handling` |
| Node-side evidence | corresponding `EVID_NODE_*` or node audit artifact reference (path:line) |
| Dotnet-side evidence | corresponding `EVID_CFG_*` / `EVID_AUTH_*` or dotnet audit artifact reference (path:line) |
| Difference description | Objective description of the two sides' value/configuration differences |
| Risk impact | Risk argument combined with entry reachability (difference ≠ necessarily a vulnerability) |
| Three-state conclusion | `Confirmed Difference` / `Pending Verification` / `False Positive` |

Artifact structure (mandatory): reconciliation scope declaration (timestamps and sources of both sides' artifacts), five comparison tables (group by group), `CONS-{n}` details, three-state summary counts, and a declaration of the relationship with the fullstack closing.

Relationship with the fullstack closing double-safety: this Skill is invoked by fullstack phase 6 (cross-stack correlation); its output `cross/consistency_findings_{timestamp}.md` serves as a **supplementary input** to the full-stack layer's `coverage_consistency_check`, not its replacement — the gate determination, BLOCKED linkage, and final report reconciliation of consistency_check still follow the existing closing double-safety flow.
