---
name: dotnet-deser-audit
description: .NET deserialization audit tool. Identifies dangerous deserialization paths such as BinaryFormatter, NetDataContractSerializer, Newtonsoft.Json TypeNameHandling, and LosFormatter.
---

# .NET Deserialization Audit

## Shared Grabber Index Reference

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as the basic retrieval index for this skill
- By default, use shared/DOTNET_SINK_REFERENCE.md as the baseline for this specialty's Sink type definitions and trace-gate validation
- By default, follow the general execution standard of `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the shared grabbers related to type information, polymorphic resolution, serializer selection, KnownType whitelists, and input sources
- If the project has secondary encapsulations such as SerializerHelper, MessageCodec, CacheSerializer, or StateFormatter, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align entries, deserialization input sources, and `route_id`)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement the host, serialization configuration, and runtime control plane)
- Under trace-gate scenarios, prioritize consuming: `route_tracer/{route_id}/trace_{timestamp}.md`; if `route_tracer/{route_id}/trace_summary_{timestamp}.md` exists, it may serve as a summary index
- If executed via `dotnet-audit-pipeline`, the `route_id` referenced by this specialty should be consistent with `cross_analysis/high_risk_routes_{timestamp}.md`

## Key Checks

- any use of BinaryFormatter, NetDataContractSerializer, SoapFormatter, or LosFormatter (high-risk prohibited class)
- Newtonsoft.Json TypeNameHandling != None configuration (global or local)
- deserialization input sources: HTTP body, cookies, session, cache, message queues, uploaded files, ViewState
- whether the SerializationBinder / KnownTypes whitelist is complete and non-bypassable
- polymorphic type deserialization: type resolution when interfaces / abstract classes are parameter types
- gadget chain reachability: whether known gadget types exist in project dependencies
- legacy WebForms ViewState MAC validation and encryption configuration

## Evidence References

- EVID_DESER_CALLSITE
- EVID_DESER_INPUT_SOURCE
- EVID_DESER_OBJECT_TYPE_MAGIC_TRIGGER_CHAIN

## Enumeration Rules (Mandatory Refinement)

- Enumerate entry points related to BinaryFormatter, NetDataContractSerializer, SoapFormatter, LosFormatter, ObjectStateFormatter, and Json.NET TypeNameHandling
- Search Deserialize, TypeNameHandling, SerializationBinder, KnownTypes, AssemblyQualifiedName, ViewState, Session, and message payload keywords first
- Enumerate deserialization chains of cookies, session, cache, message queues, uploaded files, API bodies, GraphQL / Hub messages, and custom RPC
- For each deserialization point record: type information source, whitelist / blacklist strategy, subsequent side-effect chain, host framework, and runtime environment

## Barrier Verification Matrix (Mandatory)

This specialty must verify the following barrier types, evaluated per the fail-close standard of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Type whitelist (KnownTypes / SerializationBinder)** | Read the whitelist implementation source, confirming whether it is fail-close (unknown types rejected from deserialization) | fail-close (unknown types throw / are rejected) → ✅ safe; blacklist (only known dangerous types intercepted) → ⚠️ bypassable; no whitelist → 🔴 high risk |
| **TypeNameHandling configuration** | Confirm whether `Newtonsoft.Json`'s `TypeNameHandling` is `None`, or is `Auto` / `All` / `Objects` with a safe SerializationBinder | `TypeNameHandling.None` → ✅ safe; `Auto` / `All` / `Objects` without a safe Binder → 🔴 high risk; Binder present but implementation not visible → ⚠️ to be confirmed |
| **High-risk serializer prohibition** | Confirm whether high-risk serializers such as `BinaryFormatter`, `NetDataContractSerializer`, `SoapFormatter`, and `LosFormatter` are used | not used → ✅ safe; used but input uncontrollable → 🟠 to be confirmed; used with controllable input → 🔴 high risk |
| **Input source controllability** | Confirm whether deserialization data comes from user-controllable input (HTTP body, cookies, query, uploaded files, etc.) | from user-controllable sources → 🔴 high risk (assess with the type barrier); only from internal cache / database and validated → 🟠 to be confirmed; only from trusted internal sources → ✅ safe |
| **Gadget chain reachability** | Check whether known gadget types exist in project dependencies (NuGet packages, such as `ObjectDataProvider`, `PSObject`, `TextFormattingRunProperties`) | no known gadgets → 🟠 assess with the type barrier; known gadgets present and the type barrier bypassable → 🔴 high risk |
| **ViewState MAC / encryption** | Confirm whether legacy WebForms ViewState has MAC validation and encryption enabled | MAC + encryption enabled → ✅ safe; MAC only without encryption → ⚠️ to be confirmed; neither enabled → 🔴 high risk |
| **Post-deserialization side-effect chain** | Trace whether the deserialized object triggers `OnDeserialized`, `ISerializable`, `IDisposable`, property setters, dependency injection, and other side effects | no side-effect chain → 🟠 needs confirmation; side-effect chain entering command execution / file operations / database → 🔴 high risk |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion as "Confirmed Safe" or "False Positive" is forbidden.**

## Two-Phase Determination (Mandatory)

Follow the two-phase determination process of `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

1. **Phase 1 (interim conclusion)**: mark each hit as `Confirmed Vulnerability Candidate` / `Pending` / `False Positive` first
2. **Phase 2 (mandatory evidence chasing)**:
   - if Phase 1 is `Confirmed Vulnerability Candidate` → all relevant items of the Barrier verification matrix must be completed before `Confirmed` may be marked
   - if Phase 1 is `Pending` → chase at least one more hop of the call chain or downstream parser downward, until a determination can be made
   - if Phase 2 still cannot close → remain `Pending`, and explicitly record which hop of evidence is missing

## Determination Rules (Mandatory Refinement)

### Confirmed Vulnerability

At least one of the following conditions holds:

1. user-controllable input enters high-risk serializers such as `BinaryFormatter.Deserialize`, with no type whitelist or a fail-open whitelist
2. `Newtonsoft.Json`'s `TypeNameHandling` is `Auto` / `All` / `Objects` without a safe `SerializationBinder`
3. the type whitelist is a blacklist mode (only intercepting known dangerous types), bypassable via unknown gadget types
4. known gadget types exist in project dependencies, and the type barrier is bypassable
5. in nested / recursive structures (such as multi-layer SerializerHelper wrappers), the top level has validation but sub-levels do not perform equivalent validation
6. the deserialized object enters sensitive side-effect chains such as command execution, file operations, or template rendering

### Pending

1. the context shows a suspicious pattern (such as a `Deserialize` call), but the external input source is unclear (trace or call chain needs to be supplemented)
2. a barrier function (such as `SerializationBinder`) exists, but its implementation is not visible or whether the current branch invokes it cannot be confirmed
3. parameter passing in asynchronous / queue / event chains (such as message queue consumers deserializing data) is not closed
4. gadget chain reachability is affected by dependency versions; confirming whether the specific version has known gadgets is needed

### False Positive

1. deserialization input comes only from fixed constants / internal trusted sources, and users cannot influence the deserialization data
2. all recursive levels reuse the same fail-close type whitelist validator
3. `TypeNameHandling.None` with no dynamic type resolution logic
4. high-risk serializers are used only internally, with completely uncontrollable input and no external entry able to influence them

## Testing Recommendations (Mandatory)

Follow the testing requirements of `DOTNET_AUDIT_EXECUTION_STANDARD.md`, giving for each confirmed vulnerability or pending item:

- **Positive testing**: construct deserialization payloads containing malicious types (such as `ObjectDataProvider` gadgets) and verify RCE / command execution really exists
- **Negative testing**: construct inputs intercepted by barriers (such as unknown types, types not in KnownTypes) and verify the protection mechanism is effective
- **Regression testing**: retest after remediation, confirming barriers remain effective and no new bypass paths were introduced (such as new gadgets or Binder bypasses)

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (such as `route_mapping` / `route_tracer` / `framework_audit`), confirming dependencies are available and timestamps consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: persist to the agreed paths per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (entry confirmation)**: the deserialization call site and input source must be confirmed first.
- 🔴 **CHECKPOINT B (type chain confirmation)**: the type information source and binding strategy (Binder / KnownTypes / TypeNameHandling) must be given.
- 🔴 **CHECKPOINT C (side-effect confirmation)**: whether the landed object triggers a sensitive side-effect chain must be stated.
- 🛑 **STOP**: if the "input → deserialization → side effect" chain cannot be closed, the conclusion is downgraded to `⚠️Pending Verification`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback on Continued Failure |
|---|---|---|
| only a Deserialize call hit, input source unknown | back-trace to input boundaries such as HTTP / messages / cache | downgrade to `⚠️Pending Verification`, retaining the suspicious call site |
| type control chain incomplete (Binder / KnownTypes) | complete type resolution and whitelist constraint evidence | no strong RCE conclusion; give verification paths only |
| side-effect chain not closed | trace to subsequent operations such as commands / files / templates / databases | only output potential impact and evidence-supplementation requirements |

🔴 **STOP: when any fallback triggers, outputting "Confirmed Exploitable" is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Mandatory shared indexes: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber source) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: persistence paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from directories are forbidden.
- Evidence consistency validation: if graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: confirm at least once before submission that key referenced files are accessible (such as `DOTNET_AUDIT_GRABBER_INDEX.md` and `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Execute at least 2 typical test cases before each output (one happy path + one boundary / ambiguity scenario), and record expected vs actual differences.
- `full_test >= 1` is required by default; if only `dry_run` is possible, `confidence=LOW` must be marked in the conclusion, with a supplementary test plan and owner given.
- Pass criteria: key fields complete, evidence chains traceable, conclusion levels consistent with gate status; if any fails, marking "passed / deliverable" is forbidden.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `input constraints` → `execution steps` → `output and acceptance`; missing layers or cross-layer mixing are forbidden.
- A single paragraph is recommended not to exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into the single-source-of-truth section.
- AI-style filler and empty connectives are forbidden (such as "first / second / finally / in summary / to put it simply / in other words"); rewrite them into executable statements upon discovery.

## Quality Gate & Assessment Consistency (Mandatory)

- Execute the minimal gate self-check before output: `input completeness`, `key evidence hit`, and `output path valid` must all be PASS.
- If any of `key evidence missing`, `chain not closed`, or `consistency_check_status=BLOCKED` exists, the conclusion must be downgraded to `BLOCKED`; outputting "Confirmed Exploitable / Deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

- Anti-pattern: drawing an RCE conclusion upon seeing only a Deserialize call. Correct practice: close the input source, type control, and side-effect chain.
- Anti-pattern: ignoring Binder / KnownTypes / TypeNameHandling constraints. Correct practice: verify whether the type boundary is bypassable.
- Anti-pattern: treating historical high-risk components as currently exploitable. Correct practice: judge reachability combining runtime paths and dependency versions.
- Anti-pattern: writing evidence chain gaps as "no risk". Correct practice: downgrade to `⚠️Pending Verification` and record the missing evidence.

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion levels: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose one of three; blank is forbidden).
- Minimum evidence set: at least the five items `Entry Point`, `Controllable Parameter`, `Key Call`, `Security Boundary`, and `Missing Evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softened wording is forbidden: such as "may be at risk / suggested attention / depends on the situation / most likely"; when evidence is insufficient, `⚠️Pending Verification` and the next evidence-supplementing action must be explicitly written.

Minimal output fragment (directly reusable):

```md
- Hit ID: M{hash} (file path fragment + line number + sequence, used for cross-phase tracking and regression alignment)
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameter=...; key call=...; security boundary=...; missing evidence=none
- test_id: T{hash} (associated test case)
- Next action: if gaps exist, supplement the parameter-propagation evidence of trace_id=...
```

## Output

- vuln_audit/deser_{timestamp}.md
- Optional: vuln_poc/deser_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC; if a direct request is not suitable, at least give verification steps)
