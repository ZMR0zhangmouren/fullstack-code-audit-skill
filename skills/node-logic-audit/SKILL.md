---
name: node-logic-audit
description: Node.js business logic audit tool. Identifies check-then-act races, client-modifiable amounts / quantities, coupon reuse, multi-step workflow skipping, and BullMQ duplicate consumption risks; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js Business Logic Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to business state transitions, concurrency control, idempotency protection, and amount / quantity re-verification
- If the project has secondary encapsulations such as orderService, paymentService, promotionService, or queueConsumer, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align business action entries, batch endpoints, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used to confirm client-side sources of amount / quantity fields and upstream/downstream linkage)
- Optional: `node/design_intent/design_intent_{timestamp}.md` (intent-layer reference: determination baseline for business rules, state machines, and permission intent; used only for generating hypotheses and narrowing enumeration scope; forbidden as an EVID citation source, see `shared/AUDIT_EXECUTION_COMMON.md` §9)
- Optional: `node/route_mapping/feature_api_map_{timestamp}.md` (feature view: organizes logic determination baselines by feature surface; view-layer references are forbidden as EVID citation sources, see `shared/AUDIT_EXECUTION_COMMON.md` §9)
- This specialty is **static-evidence-driven**: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`
- Responsibility boundary: interface-level identity and resource-ownership authorization belongs to `node-auth-audit`; this specialty covers business constraint surfaces beyond authorization (races, idempotency, state machines, limit re-verification)

## Key Checks

- check-then-act races: check balance → deduct, check inventory → place order, with two non-atomic steps
- Client-modifiable amounts / quantities without server-side re-verification (price, quantity, total trusted directly from the request body)
- Coupon / invitation code reuse: redemption without idempotency keys, unique indexes, or state machine preconditions
- Multi-step workflow skipping: `state` / `step` parameters controlled by the frontend, with the server not validating prerequisite states
- Duplicate consumption and missing idempotency in BullMQ / node-cron / setInterval scheduled tasks (at-least-once redelivery)
- Duplicate submission (double submit) causing repeated deductions and repeated issuance
- Batch operations missing per-item quantity and business validation (per-item permission validation belongs to `node-auth-audit`)

## Enumeration Rules (Mandatory Refinement)

- If `node/design_intent/` artifacts exist, first verify item by item that their "business rule list / state machine and process constraints" are implemented in code and note deviations (deviations are registered as documentation-implementation drift and are not directly escalated to vulnerability conclusions)
- Enumerate state-changing routes and business actions: rg searches for `router.post(`, `pay`, `refund`, `confirm`, `cancel`, `redeem`, `coupon`, `invite`, `withdraw`, `approve`
- rg searches for concurrency and idempotency grabbers: `findOneAndUpdate(`, `$inc`, `startSession(`, `transaction(`, `redlock`, `SET NX`, `idempotency`, `version`
- rg searches for queues and scheduled tasks: `BullMQ`, `new Worker(`, `queue.add(`, `node-cron`, `setInterval(`
- For each business action record: whether the three segments of precondition validation → state update → side effects are atomic, the idempotency key, concurrency control, and amount / quantity data sources
- Distinguish server-side recalculation from client direct passthrough: verify whether price / quantity / total in `req.body` are overridden by server-side data sources
- If business actions go through secondary encapsulation or message queues, they must be unwrapped layer by layer to the real DB write points
- **Organize determinations by feature surface (2026-09-19)**: for each P0/P1 feature within coverage that involves write operations / funds / tenant boundaries, list business constraint assertions (derived from design_intent rules + feature name semantics) and verify them one by one at the trace layer on that feature's endpoints; endpoints without feature-surface assertions fall back to the existing code-evidence path, **and must not be skipped due to missing feature views**

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Atomic updates | `findOneAndUpdate` conditional updates / DB transactions / optimistic locking version | Verify whether validation and writes are atomic (conditional update / transaction / lock) | conditional atomic update or transaction wrapping → ✅ safe; check-then-write separation → 🔴 high risk |
| Idempotency control | idempotency keys / unique indexes / state machine preconditions | Resubmit the same request and verify the result | unique constraints or state machine rejection → ✅ safe; no idempotency → 🔴 high risk |
| Server-side re-verification | amounts / quantities recalculated from server-side data sources | Replay a request with tampered price / quantity / total | server-side recalculation overriding → ✅ safe; trusting client fields → 🔴 high risk |
| Workflow state machine | `state` / `step` held by server-side session or DB | Skip steps by calling subsequent endpoints directly | server validating prerequisite states → ✅ safe; step parameter passthrough → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: validation and sensitive actions appear non-atomic, or workflow states / limits appear client-controllable
- `Pending`: the context shows a suspicious pattern, but the external input source, barrier behavior, or call chain is unclear
- `False Positive`: the input comes from fixed constants / enum mappings, or the barrier has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found that externally controllable input enters the Sink position → `Confirmed Vulnerability`
- Fixed whitelist mapping / fail-close evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_LOGIC_RACE_WINDOW` + `EVID_NODE_LOGIC_LIMIT_CONTROL`: check balance → deduct is non-atomic in two steps, and the amount is not server-side re-verified
- `EVID_NODE_LOGIC_TOCTOU_PAIR`: inventory validation point separated from the order placement point, with no transaction / lock / conditional update
- `EVID_NODE_LOGIC_WORKFLOW_BYPASS`: `state` / `step` passed straight from the frontend and the server does not validate prerequisite states
- `EVID_NODE_LOGIC_LIMIT_CONTROL`: coupon redemption has no idempotency key or unique index and can be reused

### ⚠️Pending Verification

- A race window exists, but the redis lock / transaction implementation and coverage are unclear
- Queue consumption has retry configuration, but idempotency and deduplication evidence is insufficient
- Amount field sources need `cross/api_contract_map_{timestamp}.md` or call chain supplementation

### False Positive

- Updates go through conditional atomic operations (`$inc` + conditions / unique indexes), and duplicate requests are rejected by idempotency keys
- Amounts / quantities are fully recalculated server-side, with client fields used only for display
- Workflow states are held server-side, and skipped-step requests are rejected by the state machine

## Testing Recommendations (Mandatory)

### Positive Testing

- Send N concurrent duplicate deduction / order requests to verify over-deduction and over-issuance; tamper with `price=0.01` to verify the transaction price
- Replay coupon redemption requests to verify reuse; skip steps to verify workflow bypass
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Duplicate submissions are rejected under transactions / unique indexes; tampered amounts are overridden by server-side recalculation
- Skipped-step requests are intercepted by the state machine with explicit errors

### Regression Testing

- Retest after remediation, confirming race windows and idempotency have not regressed
- Newly added queue consumers and scheduled tasks integrate idempotency keys by default

## Evidence References

- `EVID_NODE_LOGIC_RACE_WINDOW`
- `EVID_NODE_LOGIC_TOCTOU_PAIR`
- `EVID_NODE_LOGIC_WORKFLOW_BYPASS`
- `EVID_NODE_LOGIC_LIMIT_CONTROL`

## Output

- `node/vuln_audit/logic_{timestamp}.md`
- `node/vuln_poc/logic_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)

## Mechanism Extension: Integer Overflow (2026-09-14 Ledger Round)

### Mechanism Description and Boundary

User numeric value → numeric arithmetic → overflow / precision loss causing logic failure / availability loss. Attackers submit out-of-bounds values (extremely large values, negative values), causing paths such as JS `Number` (IEEE 754 double precision, losing integer precision beyond `Number.MAX_SAFE_INTEGER` (2^53)), bitwise truncation (`| 0` wrapping to 32 bits), and fixed-width Buffer length / offset calculations to produce wrong results, leading to price calculation errors, length / offset anomalies, permission check bypasses, or denial of service.

Ledger boundary (verbatim): incorporated into the existing numeric validation dimension; no new arithmetic skill is created.

### Key Checks and Enumeration Grabbers

Record for each hit: file, line number, arithmetic point, involved numeric semantics, and boundary source.

- **User-controllable values entering arithmetic**: `parseInt(req.query.n)` (beware of non-decimal radix misuse) / `Number(req.body.x)` parsing request parameters then participating in addition / subtraction / multiplication; values from model fields entering operations directly.
- **2^53 precision loss contexts**: amount / counter / ID accumulation silently losing precision beyond `Number.MAX_SAFE_INTEGER`, lacking `BigInt` (large integer IDs, snowflake ID arithmetic, cents ↔ yuan conversion accumulation).
- **Length / offset calculations**: controllable parameters of Buffer operations (`buf.slice(offset, offset + len)`, `buf.readUInt32BE(offset)`) participating in arithmetic before being used as lengths / offsets; allocation sizes of `new Array(len)` / `Buffer.alloc(len)` decided by controllable arithmetic results, where multiplication overflow / precision loss causes undersized allocation or exceptions.
- **Bitwise truncation**: `| 0`, `>>> 0`, `& 0xffffffff` truncating values to 32 bits, with large numbers changing semantics after wrapping.
- **Currency / points conversion**: cents ↔ yuan multiplication / division (`amount * 100` / `cents / 100`), exchange-rate multiplication / division, with intermediate results exceeding the safe integer range.
- **Increment / accumulation**: counters and sequence generators without upper-bound protection, losing precision or raising exceptions at 2^53.

### Verification Matrix

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Boundary checks first** | Confirm whether min / max boundary validation is performed before arithmetic (e.g., `amount > 0 && amount <= LIMIT`), and whether the validation is fail-close | fail-close precondition validation → ✅ safe; no validation or bypassable validation → 🔴 high-risk candidate |
| **Safe integer range enforcement** | Confirm whether key arithmetic points use `BigInt` / string big-number arithmetic, or `Number.isSafeInteger` precondition validation | key arithmetic not relying on precision within 2^53 → ✅ safe; key arithmetic beyond 2^53 without protection → 🔴 high-risk candidate |
| **Bitwise semantics matching** | Confirm whether inputs of `| 0` / `>>>` truncation operations are validated within 32 bits, and whether large numbers are truncated and wrapped | input domain constrained → ✅ safe; large-number truncation changing semantics → ⚠️ to be confirmed |
| **Wraparound protection** | Confirm the handling when accumulators / counters reach their upper bound (reject, reset, alert), not silent precision loss | safe handling → ✅ safe; silent loss → ⚠️ to be confirmed |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion as "Confirmed Safe" or "False Positive" is forbidden.**

### Determination Rules

Confirmation requires closing all three of the following EVIDs, all indispensable:

1. **User source closure**: evidence locating user-controllable numeric values entering arithmetic operations (`EVID_NODE_LOGIC_NUMERIC_USER_SOURCE`).
2. **Arithmetic point closure**: evidence of arithmetic operation points such as addition / subtraction / multiplication, length offsets, and currency / points conversion (`EVID_NODE_LOGIC_ARITHMETIC_POINT`).
3. **Impact closure**: evidence of logic failure / availability loss caused by overflow / precision loss or boundary bypass (`EVID_NODE_LOGIC_OVERFLOW_IMPACT`).

🔴 **Confirmation threshold (ledger verbatim): it must be proven that overflow / precision loss / boundary bypass causes logic failure, not merely that a numeric conversion exists.**

Safe-integer validation (`Number.isSafeInteger`) + precondition boundary validation constitutes a false positive.

### Testing Recommendations

- **Positive**: trigger boundary inputs with amounts exceeding `Number.MAX_SAFE_INTEGER`, negative lengths, oversized pagination parameters, and non-decimal strings, confirming precision loss / wraparound changes logic results (price errors, Buffer out-of-bounds / allocation anomalies, check bypasses).
- **Negative**: under `Number.isSafeInteger` precondition validation + boundary validation, boundary inputs throw exceptions or are rejected, and logic results are unchanged.
- **Regression**: when new numeric fields, pagination parameters, amount / points conversions, or Buffer offset calculations are added, re-verify boundary validation and safe-integer coverage.

### Evidence References

- `EVID_NODE_LOGIC_NUMERIC_USER_SOURCE`: evidence locating user-controllable numeric values entering arithmetic operations
- `EVID_NODE_LOGIC_ARITHMETIC_POINT`: evidence of arithmetic operation points such as addition / subtraction / multiplication, length offsets, and currency / points conversion
- `EVID_NODE_LOGIC_OVERFLOW_IMPACT`: evidence of logic failure / availability loss caused by overflow / precision loss or boundary bypass
