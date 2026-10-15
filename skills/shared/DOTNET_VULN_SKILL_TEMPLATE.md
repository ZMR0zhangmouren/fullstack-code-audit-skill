# .NET Vulnerability Specialty Skill Template

This template is used to create new dotnet-{type}-audit vulnerability specialty skills.

## Usage Instructions

- Replace {type} with the specific vulnerability type identifier
- Supplement key checks, enumeration rules, evidence references, and output requirements as needed for the specialty
- By default, integrate shared/DOTNET_AUDIT_GRABBER_INDEX.md, shared/EVIDENCE_POINT_IDS.md, shared/IO_PATH_CONVENTION.md, shared/SEVERITY_RATING.md, shared/DOTNET_SINK_REFERENCE.md
- You must explicitly write out `## Input Dependencies`; do not leave the relationships among `source_path`, `route_mapping/*`, `route_tracer/*`, `auth_audit/*`, `framework_audit/*` as implicit conventions
- If the specialty is of the trace-gate type, state in `## Input Dependencies` that it primarily consumes `route_tracer/{route_id}/trace_{timestamp}.md`, and may optionally consume `route_tracer/{route_id}/trace_summary_{timestamp}.md`
- If the specialty is static-evidence-driven, state in `## Input Dependencies` that `route_tracer/*` serves only as cross-reference evidence, not as a hard precondition
- If executed via `dotnet-audit-pipeline`, state in `## Input Dependencies` that the `route_id` referenced by this specialty must be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`
- If the specialty relates to authentication, anonymous entry points, or P0/P1 prioritization, list `auth_audit/auth_mapping_{timestamp}.md` as an optional input
- If the specialty is affected by the host, framework control plane, serialization configuration, static directories, or middleware ordering, list `framework_audit/*_{timestamp}.md` as an optional input
- If reproducible conditions exist or at least a verifiable request can be constructed, also generate vuln_poc/{type}_{timestamp}.md, referencing shared/DOTNET_VULN_POC_TEMPLATE.md
- If the specialty depends on route_tracer or framework_audit, its consumption relationship must be stated explicitly in the body
- If the specialty requires new EVID_* IDs or new shared grabbers, update shared first and then land the skill

## Template

```md
---
name: dotnet-{type}-audit
description: .NET {type} audit tool. Identifies ... risks; outputs severity rating, evidence, and remediation recommendations.
---

# .NET {type} Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in shared/DOTNET_AUDIT_EXECUTION_STANDARD.md (two-phase determination, fail-close determination, testing requirements)**
- Enumeration must at least cover the shared grabbers related to {type}
- If the project has secondary encapsulation, a project-internal grabbers section must be added to the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- Enumeration must at least cover the shared grabbers related to {type}
- Enumeration must at least cover the shared grabbers related to {type}
- If the project has secondary encapsulation, a project-internal grabbers section must be added to the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align entry points, parameter bindings, and `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entry points, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement host, framework control plane, serialization configuration, static directories, or runtime boundaries)
- If it is a trace-gate specialty: primarily consume `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If it is a static-evidence-driven specialty: `route_tracer/{route_id}/trace_{timestamp}.md` and `route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- ...

## Enumeration Rules (Mandatory Refinement)

- ...

## Evidence References

- EVID_...

## Output

- vuln_audit/{type}_{timestamp}.md
- vuln_poc/{type}_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC)
```

## Minimum Acceptance Requirements

- Name, description, and responsibility boundaries are clear
- The shared grabber index and other necessary shared rules are referenced
- The four-layer structure exists: input dependencies + key checks + enumeration rules + output requirements
- The evidence reference criteria are stated
- The relationships with route_tracer / framework_audit / pipeline are stated
- It is stated whether the specialty is trace-gate or static-evidence-driven, and whether `route_tracer/*` is a hard precondition or cross-reference evidence
- Output paths comply with shared/IO_PATH_CONVENTION.md
- If a reproducible PoC or a constructible request template exists, a vuln_poc artifact must also be produced
- Boundaries are distinguishable from existing specialties without large-scale overlapping responsibilities
