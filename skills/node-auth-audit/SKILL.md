---
name: node-auth-audit
description: Node.js authentication static bucketing tool. Consumes routes and middleware_inventory produced by node-route-mapper, identifies four buckets — global middleware coverage, route-level authentication, anonymous allowance, and authentication missing — and outputs an auth_mapping covering 100% of the routes list.
---

# Node.js Auth Audit

## Shared Grabber Index Reference

- The enumeration keywords, priority targets, and record criteria of this skill take `skills/shared/NODE_AUDIT_GRABBER_INDEX.md` as the single source of truth, focusing on its "Precondition Control Grabbers" section.
- Paths and artifact naming follow the `node/` subtree conventions in `skills/shared/IO_PATH_CONVENTION.md`.
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced.
- If the project has secondary encapsulations such as `AuthService`, `PermissionChecker`, `JwtGuard`, or `SessionManager`, they must be added to the project-internal grabbers section of the output.

## Input Dependencies

User provides:

- `node_source_path`: Node.js project, repository root, or a directory containing `package.json` (required).
- `node/route_mapping/routes_{timestamp}.md`: complete entry list produced by the upstream node-route-mapper (required).
- `node/route_mapping/middleware_inventory_{timestamp}.md`: middleware inventory produced by the upstream node-route-mapper (required).
- `node/route_mapping/params_{timestamp}.md`: parameter structures produced by the upstream node-route-mapper (optional, used to verify authentication-related parameter sources).
- `node/stack_detect/stack_detect_{timestamp}.md`: Phase 0 tech-stack detection result (optional, used to select the adapter).
- `node/design_intent/design_intent_{timestamp}.md`: design-intent summary (optional; intent-layer reference: the permission matrix and tenant boundary declarations in the design, used to complete enumeration; forbidden as an EVID citation source, see `shared/AUDIT_EXECUTION_COMMON.md` §9).
- `node/route_mapping/feature_api_map_{timestamp}.md`: feature view (optional; used for sensitivity-grading feature view rules, see the block at the end of the "Bucketing Rules (Mandatory)" section; view-layer references are forbidden as EVID citation sources, see `shared/AUDIT_EXECUTION_COMMON.md` §9).

## Authentication Mechanism Identification

If `node/design_intent/` artifacts exist, first verify the differences between their "permission and tenant boundary intent" and the identification points (differences are registered as documentation-implementation drift and are not directly escalated to vulnerability conclusions).

Enumerate and classify the authentication control points of the project, covering at least the following keywords and patterns:

| Category | Keywords / Patterns | Identification Focus |
| ---- | ---- | ---- |
| Express auth middleware | `passport.authenticate`, `express-jwt`, `expressjwt`, `jwt.verify` | mount path, scope, failure callback, secret / key source |
| Session authentication | `express-session`, `cookie-session` | global / route-level mounting, cookie signing, session store configuration |
| Next.js authentication | `next-auth`, `getServerSession` | API route / Server Action / page-level coverage, public route configuration |
| NestJS auth decorators | `@UseGuards`, `AuthGuard`, `@Public`, `CanActivate` | Controller / Method-level Guard coverage, Public exceptions |
| Custom naming heuristics | `auth\|login\|token\|guard\|permission\|session` | project-internal wrapper functions, authentication utility classes, permission validation middleware |

Record for each identification point:

- `auth_id`: `A{sequence number}`, globally unique.
- `auth_mechanism`: the specific keyword or pattern name.
- `scope`: `global` / `route` / `module`.
- `covered_route_ids`: the list of covered `route_id`s; global middleware may write `*` and expand the actually matching routes.
- `source_file:line`: declaration location.
- `is_fail_close`: **mandatory field**, must be `true` / `false` / `unknown`. `true`: unauthorized requests are rejected and cannot bypass the bucketing; `false`: authentication failure can degrade to allow (explicit fallback exists); `unknown`: cannot be confirmed from code; a `fail_close_evidence_gap` must be persisted stating the missing evidence.

## Bucketing Rules (Mandatory)

Assign each `route_id` to one of the following four buckets:

| Bucket | Determination Condition | Record Fields |
| ---- | ---- | ---- |
| **Global middleware coverage** | the route is under the mount path of middleware with `is_global=true` and `is_auth=true` | `auth_id`, middleware name, mount prefix, scope evidence |
| **Route-level authentication** | the route itself or its owning Controller / Module explicitly declares `passport.authenticate`, `express-jwt`, `expressjwt`, `jwt.verify`, session validation, `@UseGuards`, `AuthGuard`, etc. | `auth_id`, authentication mechanism, declaration location, covered methods |
| **Anonymous allowance** | the route is explicitly annotated with `@Public`, `AllowAnonymous`, in a public whitelist, or configured as an `unprotected` / `public` route | `auth_id`, allowance reason, configuration source, business necessity statement |
| **Authentication missing** | the route has neither global authentication middleware coverage nor route-level authentication, and is not annotated as anonymously allowed | `route_id`, missing evidence, risk level, suggested action |

Bucketing priority:

1. Judge "anonymous allowance" first (explicit public > implicit missing).
2. Then judge "global middleware coverage".
3. Then judge "route-level authentication".
4. The rest fall into "authentication missing".

**Feature view priority (2026-09-19)**: export / delete / bulk-operation / tenant-management / credential endpoints go straight to P0; endpoints not covered by the feature view fall back to naming / write-operation heuristics, and the artifact annotates the source of the grading basis (feature_api_map / heuristic).

## Reconciliation Requirements (Mandatory)

- The authentication mapping must **cover 100%** of the `route_id` list in `routes_{timestamp}.md`.
- Output one bucketing record per `route_id`; omission is forbidden.
- "Non-entry / static resource" routes (such as static files, `/health`, `/favicon.ico`, `/_next/static/**`, etc.) are likewise recorded, with `non-asset-remark=non-entry / static resource` annotated next to the `bucket`.
- Output `auth_mapping_summary`:
  - `total_routes`: total number of routes in the list
  - `global_middleware_count`: number of global middleware coverage
  - `route_level_count`: number of route-level authentication
  - `anonymous_count`: number of anonymous allowance
  - `missing_count`: number of authentication missing
  - `coverage_percent`: `(global_middleware_count + route_level_count) / total_routes * 100%` (real authentication coverage: the proportion of routes protected by authentication middleware or route-level authentication)
  - `classification_completeness`: `(global_middleware_count + route_level_count + anonymous_count + missing_count) / total_routes * 100%`, which must be 100% (classification completeness self-check: all routes fall into the four buckets, measuring classification completeness rather than authentication coverage)
  - `uncovered_route_ids`: an empty array passes; non-empty means `auth_mapping_status=BLOCKED`
- When an authentication middleware in `middleware_inventory` has `is_auth=true` but cannot be associated with any `route_id`, write it into the `orphan_auth_middleware` list with the reason.

**Middleware mount order verification (mandatory)**: for middleware with `is_auth=true` in `middleware_inventory`, the mount order must be verified — global middleware is mounted via `app.use(...)` before route registration; route-level middleware is passed at the specific route registration; confirm that no "routes registered before middleware mounted" situation exists that would let some routes bypass the authentication middleware. Order issues found are written into `orphan_auth_middleware` or the notes column of the bucketing record.

## Output

Persist per the Node.js artifact paths in `skills/shared/IO_PATH_CONVENTION.md`:

| Artifact | Physical Path |
| ---- | ---- |
| Authentication static bucketing | `node/auth_audit/auth_mapping_{timestamp}.md` |
| Phase index | `node/auth_audit/index_{timestamp}.md` |
| Empty-result explanation (if applicable) | `node/auth_audit/empty_result_{timestamp}.md` |

### Minimum Fields of auth_mapping_{timestamp}.md

- `auth_id`: unique authentication control point ID
- `route_id`: the associated `R{sequence number}`; many-to-many relationships may be expanded into multiple rows
- `bucket`: global middleware coverage / route-level authentication / anonymous allowance / authentication missing
- `auth_mechanism`: the identified keyword or pattern
- `scope`: global / route / module
- `source_file:line`
- `non-asset-remark`: empty or "non-entry / static resource"
- `confidence`: HIGH / MEDIUM / LOW
- `next_action`: supplementary testing, supplementary trace, or no action needed
- `notes`: records of order issues / mount verification findings (filled when mount order verification finds something)

### Pre-Output Self-Check

- [ ] All `route_id`s are recorded, with nothing missed.
- [ ] The four buckets are unambiguous, and anonymous allowance has explicit evidence.
- [ ] `classification_completeness = 100%` (four-bucket sum self-check, measuring classification completeness rather than authentication coverage).
- [ ] `coverage_percent` is computed per the real authentication criteria, with the numerator containing only `global_middleware_count + route_level_count`.
- [ ] `uncovered_route_ids` is empty.
- [ ] The custom naming heuristics (`auth|login|token|guard|permission|session`) have been included in the project-internal grabbers list.

## Mechanism Extension: Account Enumeration (2026-09-14 Ledger Round)

### Mechanism Description and Boundary

Untrusted login request → authentication error response → distinguishable signals of account existence / authentication state / error type. By comparing the differences among the success, failure, and nonexistent-account paths in status codes, response bodies, and timing, attackers can infer whether an account exists, whether it is locked, and the authentication method.

Ledger boundary (verbatim): incorporated into the existing authentication audit error-response consistency dimension; no new enumeration skill is created; not part of this extension: authentication bypass / password brute force (belonging to the existing authentication dimension).

### Key Checks and Enumeration Grabbers

Cover at least the following four enumeration surfaces; record for each hit: file, line number, endpoint, and difference signal type (status code / response body / timing):

- **Login endpoint error response branches**: whether a self-built login route returns differentiated response bodies for "user does not exist" / "wrong password" / "account locked" (e.g., `res.status(401).json({ error: "user_not_found" })` vs `{ error: "wrong_password" }`), or differentiated status codes; whether the branch messages of `done(null, false, { message })` in the passport `localStrategy` callback leak account state.
- **Missing timing equalization**: whether `bcrypt.compare` short-circuits when the user does not exist, making nonexistent-account responses noticeably faster; whether JWT issuance timing differences (extra delay when the user does not exist) create observable time differences.
- **Password-recovery flow response differences**: whether the two paths — querying the user by email returning null versus sending a reset email — return identical responses; whether prompts such as "this email is not registered" directly expose existence.
- **Registration flow existence hints**: whether username / email uniqueness checks return distinguishable prompts such as "this username is already taken", and whether the prompt granularity reaches specific field values.

### Verification Matrix

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Response consistency unification** | Submit correct password + existing account / wrong password + existing account / arbitrary password + nonexistent account respectively, and compare the fingerprints of the three responses' status codes and bodies | fingerprints of all three paths completely identical → ✅ safe; any distinguishable difference → 🔴 high-risk candidate |
| **Timing equalization** | Measure the response time distributions for existing and nonexistent accounts, confirming whether nonexistent accounts go through the same-cost path (bcrypt comparison not short-circuited) | constant timing or unified cost → ✅ safe; nonexistent accounts noticeably faster → ⚠️ to be confirmed |
| **Error message generalization** | Check whether error messages and codes distinguish "user does not exist" / "wrong password" / "account locked" | unified into generalized wording (e.g., "incorrect username or password") with no status code differentiation → ✅ safe; wording or code values distinguishable → 🔴 high-risk candidate |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion as "Confirmed Safe" or "False Positive" is forbidden.**

### Determination Rules

Confirmation requires closing all three of the following EVIDs, all indispensable:

1. **Endpoint surface closure**: evidence of the login / recovery / registration enumeration surface (`EVID_NODE_AUTH_ENUM_ENDPOINT_SURFACE`).
2. **Observable difference closure**: evidence of observable differences (at least one of status code / response body / timing) between success / failure / nonexistent accounts (`EVID_NODE_AUTH_ENUM_OBSERVABLE_DIFF`).
3. **Impact closure**: evidence that account existence or authentication state can be inferred (`EVID_NODE_AUTH_ENUM_IMPACT_CONFIRM`).

🔴 **Confirmation threshold (ledger verbatim): theoretical differences alone must not be confirmed — observable differences (at least one of response body / status code / timing) must be proven.**

Unified responses with timing equalization constitute a false positive.

### Testing Recommendations

- **Positive**: send one login request each with a nonexistent account and a wrong password, confirming that the response difference (at least one of status code / response body / timing) is observable.
- **Negative**: with unified responses + timing equalization, the two paths are indistinguishable.
- **Regression**: when new authentication endpoints are added (including password recovery, registration, and 2FA verification), re-verify response consistency.

### Evidence References

- `EVID_NODE_AUTH_ENUM_ENDPOINT_SURFACE`: evidence of the login / recovery / registration enumeration surface
- `EVID_NODE_AUTH_ENUM_OBSERVABLE_DIFF`: evidence of observable differences (at least one of status code / response body / timing) between success / failure / nonexistent accounts
- `EVID_NODE_AUTH_ENUM_IMPACT_CONFIRM`: evidence that account existence or authentication state can be inferred
