# .NET Vulnerability Audit General Execution Standard

Stack-agnostic general rules take `AUDIT_EXECUTION_COMMON.md` as their source of truth; this file retains dotnet-stack-specific differences.

This file provides a unified execution standard, determination process, and quality requirements for all `dotnet-*-audit` vulnerability specialties.

Each vulnerability specialty SKILL.md should declare compliance with this standard in its "Resource References & Reachability Validation" section; specifics may be adapted to the specialty's characteristics, but the core process and determination semantics must not deviate.

---

## 1. Two-Phase Determination (Mandatory)

All trace-gate and static-evidence-driven vulnerability specialties must execute two-phase determination before giving a final conclusion.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: externally controllable input appears to enter a Sink construction or sensitive operation point
- `Pending`: the context shows a suspicious pattern, but the external input source, barrier behavior, or call chain is unclear
- `False Positive`: the input comes from fixed constants / enum mappings, or the barrier has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- ✅ Evidence is found that externally controllable input enters the Sink position → `Confirmed Vulnerability`
- ✅ Fixed whitelist mapping / fail-close evidence is found → `False Positive`
- ❌ A key call chain is still missing → remain `Pending`, but you must state which hop is missing

🔴 **STOP: Phase 2 must not stop at surface phenomena; you must chase evidence until a determination can be made.**

**Dynamic verification mandatory (C/H severity)**: dynamic re-verification of C/H-severity conclusions is mandatory — if not performed, the reason must be persisted, otherwise the conclusion is capped at "Confirmed (Static Evidence)"; consistent with the "Dynamic Verification (Mandatory for C/H Severity)" section of the PoC template.

---

## 2. Determination Rules (Structured Framework)

Each specialty should define its own determination rules in SKILL.md following the framework below, filling in specialty-specific trigger conditions.

### Confirmed Vulnerability (Template)

At least one of the following conditions holds:

1. An externally controllable parameter directly enters Sink construction (concatenation / interpolation / dynamic construction)
2. A sensitive position (identifier slot, command slot, path slot, template slot, etc.) has no whitelist mapping, or barrier validation fails
3. In nested/recursive structures: the top level has validation, but sub-levels do not perform equivalent validation
4. Other specialty-specific confirmation conditions (supplemented by the specialty SKILL.md)

### Pending

1. The context shows a suspicious pattern, but the external input source is unclear (trace or call chain needs to be supplemented)
2. A barrier function exists, but whether the current branch invokes it and whether the return value is used cannot be confirmed
3. Parameter passing in asynchronous / queue / event chains is not closed
4. Other specialty-specific pending conditions (supplemented by the specialty SKILL.md)

### False Positive

1. The final value or identifier comes from fixed constants / enum mappings, and unknown input is rejected (fail-close)
2. All recursive levels reuse the same validator and strictly fail closed
3. Parameters are bound via safe APIs (not string interpolation/concatenation), and sensitive positions are whitelist-protected
4. Other specialty-specific false-positive conditions (supplemented by the specialty SKILL.md)

---

## 3. fail-close Determination Standard (Mandatory)

For all specialties involving barriers, whitelists, validators, and filters, security must be evaluated in the "failure mode":

| Mode | Definition | Determination |
|------|------|------|
| **fail-close (safe)** | Unknown/illegal input → throws exception / returns empty / refuses execution / logs alert, **never passes through the raw value** | ✅ Safe |
| **fail-open (bypassable)** | Unknown/illegal input → allowed by default / silently falls back to the raw value / only returns false but the caller does not check | ⚠️ Bypassable |
| **silent-fallback (high risk)** | Unknown input → passes through to the Sink position without interception | 🔴 High risk; no further barrier verification needed |

### Barrier Verification Generic Actions (Choose One of Three)

For each barrier, at least one of the following actions must be performed:

1. **Inspect the implementation**: use the Read tool to read the barrier function's actual source code and confirm its behavior
2. **Inspect the call site**: confirm the barrier is used correctly at the call site (no missing parameters, not skipped by conditional branches, return value used)
3. **Test boundaries**: try to construct bypass inputs to verify whether the barrier is effective

### Anti-Patterns (Forbidden)

- ❌ Judging safe upon seeing an escape/validation function name → **the implementation source must be read**
- ❌ Judging safe upon seeing `int.TryParse()` / `Enum.Parse()` → **you must confirm the return value is used correctly**
- ❌ Judging whitelist upon seeing `switch` / `if-else` → **you must confirm there is a `default` branch and no fallthrough**
- ❌ Judging safe upon seeing a safe API call → **you must check whether external input is mixed in via string interpolation/concatenation** (e.g., `FromSqlRaw($"... {input}")`, `Process.Start($"cmd /c {input}")`)

---

## 4. Testing Recommendations (Mandatory)

For each confirmed vulnerability or pending-verification item, at least the following test coverage must be given:

- **Positive testing**: construct input that confirms exploitability, verifying the vulnerability truly exists
- **Negative testing**: construct input intercepted by the barrier, verifying the protection mechanism works (e.g., out-of-whitelist fields, illegal formats, over-length/boundary inputs)
- **Regression testing**: retest after remediation, confirming the barrier still works and no new bypass path has been introduced

Test cases should carry a `test_id` and be associated with the corresponding hit ID in the audit report.

---

## 5. Hit ID Convention

To facilitate cross-phase tracking and regression alignment, hit IDs are recommended in audit reports:

```markdown
- Hit ID: M{hash} (optional, used for cross-phase tracking and regression alignment)
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameter=...; key call=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement the parameter-propagation evidence of trace_id=...
```

For `{hash}`, a stable generation method of file path fragment + line number + sequence number is recommended, ensuring the same hit can be correlated across multiple executions.

---

## 6. Pre-Screening Script Integration (Optional)

If an automated pre-screening tool exists in the environment, the specialty may declare pre-screening artifacts in "Input Dependencies":

```markdown
- Optional (if automated pre-screening exists): `scan_audit/{type}_matches_{timestamp}.jsonl` (pre-screening hits, used for prioritization and quick location)
```

Pre-screening artifacts must not replace the specialty audit and are only used for:
- Prioritization (audit high-confidence hits first)
- Quick location (reduce initial screening time)
- Omission checking (compare pre-screening results with specialty audit results to confirm nothing is missed)

---

## 7. Output Format Consistency

The minimum output of all vulnerability specialties must include:

- Audit conclusion level: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose one of three; blank is forbidden)
- Minimum evidence set: the five items `Entry Point`, `Controllable Parameter`, `Key Call`, `Security Boundary`, `Missing Evidence`
- Next action: if gaps exist, state the evidence-supplementing action and the responsible party explicitly

Output file naming uniformly uses `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.

---

## How to Reference

Each vulnerability specialty SKILL.md should add the following in its "Resource References & Reachability Validation" section:

```markdown
- By default, follow the general execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
```
