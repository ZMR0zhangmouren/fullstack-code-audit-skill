# Node.js Vulnerability Specialty Skill Template

This template is used to create new node-{type}-audit vulnerability specialty skills, serving as the drafting baseline for each vulnerability specialty in the P1 Node.js full-stack extension.

## Usage Instructions

- Replace {type} with the specific vulnerability type identifier (e.g., sql, cmd, ssrf, xss)
- Supplement key checks, enumeration rules, Barrier verification matrix, determination rules, testing recommendations, evidence references, and output requirements as needed for the specialty
- By default, integrate shared/NODE_AUDIT_GRABBER_INDEX.md, shared/NODE_SINK_REFERENCE.md, shared/SEVERITY_RATING.md, shared/IO_PATH_CONVENTION.md
- **You must explicitly follow the general execution standard in shared/DOTNET_AUDIT_EXECUTION_STANDARD.md (two-phase determination, fail-close determination, hit ID conventions, testing requirements); the standard is stack-agnostic and is referenced directly by the Node.js side**
- You must explicitly write out `## Input Dependencies`; do not leave the relationships among `node_source_path`, `node/route_mapping/*`, `node/route_tracer/*`, `node/auth_audit/*` as implicit conventions
- If the specialty is of the trace-gate type, state in `## Input Dependencies` that it primarily consumes `node/route_tracer/{route_id}/trace_{timestamp}.md`, and may optionally consume `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`
- If the specialty is static-evidence-driven, state in `## Input Dependencies` that `node/route_tracer/*` serves only as cross-reference evidence, not as a hard precondition
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), state in `## Input Dependencies` that the `route_id` referenced by this specialty must be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`
- If the specialty relates to authentication, anonymous entry points, or P0/P1 prioritization, list `node/auth_audit/auth_mapping_{timestamp}.md` as an optional input
- If the specialty is affected by the host, framework control plane, serialization configuration, static directories, or middleware ordering, list `node/framework_audit/*_{timestamp}.md` as an optional input
- If cross-stack linkage scenarios exist (frontend parameters, API contracts, BFF forwarding), list `cross/api_contract_map_{timestamp}.md` as an optional input
- If reproducible conditions exist or at least a verifiable request can be constructed, also generate `node/vuln_poc/{type}_{timestamp}.md`, referencing shared/DOTNET_VULN_POC_TEMPLATE.md (the PoC structure is stack-agnostic and is referenced directly by the Node.js side)
- If the specialty depends on route_tracer or framework_audit, its consumption relationship must be stated explicitly in the body
- If the specialty requires new EVID_NODE_* IDs or new shared grabbers, update shared first and then land the skill

## Template

```md
---
name: node-{type}-audit
description: Node.js {type} audit tool. Identifies ... risks; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js {type} Audit

## Shared Grabber Index Reference

- By default, use shared/NODE_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/NODE_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in shared/DOTNET_AUDIT_EXECUTION_STANDARD.md (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use shared/SEVERITY_RATING.md as the severity rating and ID convention baseline
- By default, use shared/IO_PATH_CONVENTION.md as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to {type}
- If the project has secondary encapsulation, a project-internal grabbers section must be added to the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align entry points, parameter bindings, and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entry points, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement host, framework control plane, serialization configuration, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- If it is a trace-gate specialty: primarily consume `node/route_tracer/{route_id}/trace_{timestamp}.md`; if `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If it is a static-evidence-driven specialty: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via pipeline, the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- ...

## Enumeration Rules (Mandatory Refinement)

- ...

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| ... | ... | ... | ... |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in shared/DOTNET_AUDIT_EXECUTION_STANDARD.md:

> The general execution standard takes shared/AUDIT_EXECUTION_COMMON.md as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter a Sink construction or sensitive operation point
- `Pending`: the context shows a suspicious pattern, but the external input source, barrier behavior, or call chain is unclear
- `False Positive`: the input comes from fixed constants / enum mappings, or the barrier has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found that externally controllable input enters the Sink position → `Confirmed Vulnerability`
- Fixed whitelist mapping / fail-close evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown/illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- ...

### ⚠️Pending Verification

- ...

### False Positive

- ...

## Testing Recommendations (Mandatory)

### Positive Testing

- ...

### Negative Testing

- ...

### Regression Testing

- ...

## Evidence References

- EVID_NODE_...

## Output

- `node/vuln_audit/{type}_{timestamp}.md`
- `node/vuln_poc/{type}_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)
```

## Minimum Acceptance Requirements

- Name, description, and responsibility boundaries are clear
- shared/NODE_AUDIT_GRABBER_INDEX.md, shared/NODE_SINK_REFERENCE.md, shared/DOTNET_AUDIT_EXECUTION_STANDARD.md, shared/SEVERITY_RATING.md, shared/IO_PATH_CONVENTION.md are referenced
- The complete ten-layer structure exists: shared grabber index reference + input dependencies + key checks + enumeration rules (mandatory refinement) + Barrier verification matrix (mandatory) + two-phase determination (mandatory) + determination rules (mandatory refinement) + testing recommendations (mandatory) + evidence references + output
- The evidence reference criteria are stated (including EVID_NODE_* placeholders or real evidence points)
- The relationships with node/route_tracer / node/framework_audit / pipeline / cross stack are stated
- It is stated whether the specialty is trace-gate or static-evidence-driven, and whether `node/route_tracer/*` is a hard precondition or cross-reference evidence
- The Barrier verification matrix header is exactly `| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |`
- Output paths comply with shared/IO_PATH_CONVENTION.md and are explicitly written as `node/vuln_audit/{type}_{timestamp}.md` and `node/vuln_poc/{type}_{timestamp}.md`
- If a reproducible PoC or a constructible request template exists, a vuln_poc artifact must also be produced
- Boundaries are distinguishable from existing specialties without large-scale overlapping responsibilities
