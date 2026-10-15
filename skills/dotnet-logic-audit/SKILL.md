---
name: dotnet-logic-audit
description: .NET business logic audit tool. Identifies non-authorization flow bypasses, race conditions, state machine flaws, Mass Assignment, tenant isolation flaws, and business timing vulnerabilities.
---

# .NET Business Logic Audit

## Shared Grabber Index References

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as this Skill's base retrieval index
- By default, use shared/DOTNET_SINK_REFERENCE.md as this specialty's sink type definition and trace-gate validation baseline
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover shared grabbers related to business state transitions, tenant boundaries, amount calculation, approval bypasses, batch operations, and replay protection
- If the project has secondary encapsulations such as DomainService, WorkflowEngine, ApprovalService, OrderManager, they must be added to the in-project grabbers section of the output
- When this Skill's specialty enumeration rules are more detailed than the shared index, this Skill prevails, but the shared index's base coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to correlate business action entries, batch endpoints, and `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to correlate business pre-permissions, tenant boundaries, and resource ownership)
- Optional: `design_intent/design_intent_{timestamp}.md` (intent-layer reference: determination baseline for business rules, state machines, and permission intent; used only to generate hypotheses and narrow enumeration scope; forbidden as an EVID citation source, see `shared/AUDIT_EXECUTION_COMMON.md` §9)
- Optional: `route_tracer/{route_id}/trace_{timestamp}.md` and `route_tracer/{route_id}/trace_summary_{timestamp}.md` (can serve as cross evidence of business state transitions mapping to specific side-effect entries; not a hard prerequisite)

Key checks:

- Over-posting, field pollution, and mass assignment issues caused by DTO / ModelBinder / JSON Patch / FormCollection / GraphQL Input objects
- Concurrent updates, duplicate submissions, inventory deductions, coupon redemption, approval flow step skipping, missing idempotency keys, and missing distributed locks
- Multi-tenant tenantId, organizationId, resource owner, branch, project space, and data isolation alignment issues
- Inconsistencies and race windows between business validation and final writes, async messages, background tasks, and cache updates
- Whether key business actions such as state machine legal transitions, rollback, cancellation, refunds, shipping, activation, and unbinding have illegal paths
- Permission and constraint inconsistencies between admin backends, batch endpoints, import/export, scheduled tasks, webhook callbacks, and frontend endpoints
- Whether audit logs, alerts, compensation logic, and failure fallbacks are sufficient to prevent logic flaws from being continuously exploited

## Key Checks

- Mass Assignment: DTOs missing [BindNever]/[JsonIgnore] on sensitive fields (roles, balances, statuses)
- Race conditions: check-then-act patterns on balances/inventory/counters lacking concurrency control
- State machine flaws: illegal state jumps in order/payment/approval flows
- Missing idempotency: duplicate submissions causing duplicate charges/issuance/approvals
- Batch operations: batch endpoints lacking per-item permission checks or quantity limits
- Business rule bypass: coupon stacking, negative amounts, boundary values, type confusion
- JsonPatchDocument.ApplyTo: Patch operations overwriting protected fields
- Multiple entries operating on the same resource: different endpoints modifying the same entity lack consistency checks

## Evidence References

- EVID_LOGIC_STATE_TRANSITION

## Enumeration Rules (Mandatory Refinement)

- If `design_intent` artifacts exist, first check item by item the implementation and deviation of its "business rule list / state machine and process constraints" in code (deviations are registered as documentation-implementation drift and are not directly escalated to vulnerability conclusions)
- Enumerate all business endpoints involving state changes, batch processing, import/export, payments, inventory, approvals, tenant switches, coupons, invitations, and permission grants
- Search with priority: business actions such as create/update/batch/approve/reject/pay/refund/confirm/cancel/assign/import/export/replay/retry
- Enumerate multi-entry operation paths to the same resource in controllers, background tasks, message consumers, webhooks, and Hub methods
- For each business action record: pre-validation, state machine constraints, concurrency control, idempotency protection, permission boundaries, compensation logic
- **Dimension bar (mandatory, 2026-09-20): integer overflow** — item-by-item check of the overflow surface where user-controllable numbers enter arithmetic operations (add/subtract/multiply), length/offset calculations (array allocation, Span slicing, pagination parameters), and currency/point conversion boundaries (enumeration surface, verification matrix, and determination threshold see the "Mechanism Extension: Integer Overflow" section of this file). Not-applicable determination condition: the target has no user-controllable numbers entering arithmetic/length/conversion scenarios at all, and an rg negative-evidence citation (scope + pattern, e.g. `rg "int\.Parse|Convert\.ToInt32|checked" {scope}` with zero hits) is attached before marking `Not Applicable`; otherwise a bare "not covered" is forbidden

Evidence suggestion: focus on recording the chain between state transitions, business conditions, and final sensitive actions.

## Barrier Verification Matrix (Mandatory)

Assess against the fail-close three-tier standard in `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Tier | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Tier 1 | Business state-change entries exist | State-change business endpoints involving payment/inventory/approval/permission/tenant exist and are user-triggerable | BLOCKED → no business state-change entries; the specialty ends |
| Tier 2 | State machine/concurrency/idempotency has flaws | State machine has illegal jumps, check-then-act has no concurrency control, idempotency keys missing, batch operations lack per-item validation | BLOCKED → state machine/concurrency/idempotency controls are complete; conclusion degraded |
| Tier 3 | Flaws can cause actual business loss | Illegal state jumps/races/replays can cause duplicate charges/over-issuance/unauthorized approvals/data pollution | PARTIAL → only potential risks and verification steps are output |

## Two-Phase Determination Flow (Mandatory)

- **Phase 1 (Initial Screening Hit)**: business state-change entry + state machine/concurrency/idempotency configuration + business impact surface hit; output `Hit ID: M{hash}`.
- **Phase 2 (Refined Confirmation)**:
  1. Trace in reverse: business action entry → pre-validation → state machine constraints → final sensitive operation chain;
  2. Verify state machine legal/illegal branches, check-then-act race windows, idempotency keys, and distributed lock coverage;
  3. Assess whether illegal state jumps/races/replays can cause actual business loss (duplicate charges/over-issuance/over-privilege);
  4. If all three barrier tiers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priority (Mandatory)

1. **Confirmed Vulnerability**: business state-change entry triggerable + state machine/concurrency/idempotency flaw + can cause actual business loss. Output `Confirmed Vulnerability`.
2. **Pending Confirmation**: business entry exists but state machine/concurrency/idempotency evidence is partially missing. Output `Pending Confirmation`.
3. **False Positive / No Risk**: state machine strictly validates all branches, check-then-act has distributed locks/optimistic locks, idempotency keys complete, batch operations authorized per item. Output `False Positive` with determination basis.

## Testing Suggestions and Minimum Trigger Conditions (Mandatory)

- **Minimum Trigger Conditions**:
  - A business state-change endpoint exists (payment/inventory/approval/permission/tenant switch)
  - The user can trigger it
  - The state machine has illegal jumps, or check-then-act has no concurrency control, or idempotency keys are missing
- **Test Case Suggestions**:
  - Happy Path: a normal business request flows through the state machine with concurrency control and idempotency protection in effect
  - Edge/Ambiguity: concurrent duplicate submissions (double submit), state machine skipping intermediate states, JsonPatch overwriting protected fields, negative amounts/coupon stacking, batch endpoint over-privilege
- Each hit output appends `Hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Workflow (Input → Execution → Output)

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (e.g. `route_mapping` / `route_tracer` / `framework_audit`), confirm dependencies are available and timestamps are consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: write to the agreed path per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing-evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (Action Entry Confirmation)**: state-change action entries and resource objects must be confirmed first.
- 🔴 **CHECKPOINT B (State Transition Confirmation)**: legal/illegal transition branch evidence must be given.
- 🔴 **CHECKPOINT C (Concurrency and Idempotency Confirmation)**: whether race and duplicate-submission protections are in effect must be stated.
- 🛑 **STOP**: if the state chain or constraint chain is incomplete, the conclusion is degraded to `⚠️Pending Verification`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback if Still Failing |
|---|---|---|
| State transition chain incomplete | Fill in legal/illegal state branches and trigger conditions | Degrade to `⚠️Pending Verification` |
| Insufficient concurrency and idempotency evidence | Verify locks, version numbers, idempotency keys, and replay protection | Output only suspected race windows; no strong conclusion |
| Resource ownership boundary not closed | Trace to the tenant/ownership validation execution point | Describe the risk conservatively and keep a verification path |

🔴 **STOP: when any fallback is triggered, outputting "business security confirmed" is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Required shared index references: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber sources) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
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

- Anti-pattern: equating passed authorization with business security. Correct approach: continue verifying state machine, idempotency, and resource ownership constraints.
- Anti-pattern: ignoring per-item validation in batch endpoints. Correct approach: verify permissions and boundaries for each resource.
- Anti-pattern: not auditing concurrency windows. Correct approach: assess check-then-act and race exploitability.
- Anti-pattern: drawing conclusions from business descriptions alone. Correct approach: give state transition and side-effect evidence chains.

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

## Output

- vuln_audit/logic_{timestamp}.md
- Optional: vuln_poc/logic_{timestamp}.md (if a reproduction request, race steps, or an environment-dependent verification chain can be constructed)

## Mechanism Extension: Integer Overflow (2026-09-14 Ledger Round)

### Mechanism Description and Boundary

User number → integer arithmetic → overflow causes logic failure/availability loss. The attacker submits out-of-range values (extremely large values, negative values), causing unchecked arithmetic to wrap around on fixed-width types such as `int` / `uint` / `long`, leading to price calculation errors, length/offset anomalies, permission check bypasses, or denial of service.

Ledger boundary (verbatim: incorporated into the existing numeric validation dimension; no new arithmetic Skill is created).

### Key Checks and Enumeration Grabbers

Record for each hit: file, line number, arithmetic point, involved types, and boundary source.

- **User-controllable numbers entering arithmetic**: values parsed from request parameters via `int.Parse` / `Convert.ToInt32` / `int.TryParse` participating in add/subtract/multiply; numeric fields obtained directly from model binding entering computations.
- **Unchecked default context**: key arithmetic points lack `checked` blocks or project-level `<CheckForOverflowUnderflow>` is not enabled; default unchecked wraparound.
- **Length/offset calculations**: array allocation (`new byte[len]`), `Span` slicing, `Skip` / `Take` pagination parameters participating in arithmetic before being used as lengths; multiplication overflow causing undersized allocation.
- **Currency/point conversion**: cent↔yuan multiplication/division (`amount * 100` / `cents / 100`), exchange-rate multiplication/division, intermediate results exceeding the `int` range.
- **Increment/counters**: counters and sequence generators without upper-bound protection, wrapping after reaching `int.MaxValue`.

### Verification Matrix

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Boundary check first** | Confirm whether min/max boundary validation (e.g. `amount > 0 && amount <= LIMIT`) is performed before arithmetic, and whether validation is fail-close | Fail-close pre-validation → ✅ Safe; no validation or bypassable validation → 🔴 High-risk Pending Confirmation |
| **checked context enforcement** | Confirm whether key arithmetic points are wrapped in `checked` or project-level overflow checking is enabled | Key arithmetic checked → ✅ Safe; key arithmetic unchecked without pre-validation → 🔴 High-risk Pending Confirmation |
| **Type width matching** | Confirm whether operands are promoted to `long` / `decimal` before operations, and whether intermediate results exceed the `int` range | Sufficient width → ✅ Safe; intermediate result overflow → ⚠️ Pending Confirmation |
| **Wraparound protection** | Confirm the handling when counters reach their upper bound (reject, reset, alert), not silent wraparound | Safe handling → ✅ Safe; silent wraparound → ⚠️ Pending Confirmation |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion "Confirmed Safe" or "False Positive" is forbidden.**

### Determination Rules

Confirmation requires simultaneously closing the following three EVIDs; none may be missing:

1. **User source closure**: source-location evidence of user-controllable numbers entering arithmetic operations (`EVID_LOGIC_NUMERIC_USER_SOURCE`).
2. **Arithmetic point closure**: evidence of arithmetic operation points such as add/subtract/multiply/length-offset/currency-point conversion (`EVID_LOGIC_ARITHMETIC_POINT`).
3. **Impact closure**: impact evidence of overflow or boundary bypass causing logic failure/availability loss (`EVID_LOGIC_OVERFLOW_IMPACT`).

🔴 **Confirmation threshold (ledger verbatim): must prove overflow or boundary bypass, not merely the presence of numeric conversion.**

Checked + pre-validation present → False Positive.

### Testing Suggestions

- **Positive**: trigger boundary inputs with `int.MaxValue` amounts, negative lengths, and oversized pagination parameters, confirming overflow changes logic results (price wraparound, allocation anomalies, check bypass).
- **Negative**: under `checked` + pre-validation, boundary inputs throw exceptions or are rejected and logic results are unchanged.
- **Regression**: when adding numeric fields, pagination parameters, or amount/point conversions, re-verify boundary validation and checked coverage.

### Evidence References

- `EVID_LOGIC_NUMERIC_USER_SOURCE`: source-location evidence of user-controllable numbers entering arithmetic operations
- `EVID_LOGIC_ARITHMETIC_POINT`: evidence of arithmetic operation points such as add/subtract/multiply/length-offset/currency-point conversion
- `EVID_LOGIC_OVERFLOW_IMPACT`: impact evidence of overflow or boundary bypass causing logic failure/availability loss
