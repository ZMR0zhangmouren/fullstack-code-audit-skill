# scripts/validate_audit.py — .NET Audit Output Gate Validation

A standalone programmatic quality gate script that puts "the model produces, the
script judges the gate" into practice: it performs contract consistency and gate
consistency validation on the output directory of one dotnet-audit-pipeline
audit run, and outputs three-level results (PASS / FAIL / WARN) with fix
suggestions. Implemented with the pure Python standard library
(`re` / `argparse` / `pathlib` / `json`), with no third-party dependencies;
works with Chinese paths on Windows.

## Usage

```bash
# Basic usage (the skill library root defaults to the parent directory of the script's directory)
python scripts/validate_audit.py <audit_output_dir>

# Explicitly specify the skill library root (used to locate EVIDENCE_POINT_IDS.md)
python scripts/validate_audit.py <audit_output_dir> --skill-root <skill_root>

# Machine-readable JSON output (for CI / aggregation scripts)
python scripts/validate_audit.py <audit_output_dir> --json
```

## Exit Code Conventions

| Exit code | Meaning |
| ------ | ---- |
| 0 | All PASS, or only WARNs exist (WARNs do not block delivery, but need manual review) |
| 1 | At least one FAIL exists; the gate did not pass |
| 2 | Usage error or environment error (output directory does not exist, EVID dictionary unreadable, etc.) |

## Checks and Contract Sources

| # | Check | Contract source |
| - | ------ | -------- |
| A | Trace contract: `route_tracer/**/trace_*.md` must contain the 5 mandatory sections (`## 5) Parameter Controllability Matrix`, `## 6) Sink Location`, `## 7) Sink Summary`, `## 8) Trace Completeness Statement`, `## 9) Sink Evidence Type Checklist`); `trace_status` must be parseable and ∈ {COMPLETE, PARTIAL, UNRESOLVED}; `EVID_*` IDs cited in `## 9)` must be registered | `skills/dotnet-route-tracer/SKILL.md` "Single-Route Report Template (Mandatory)" / "Trace Status"; `skills/dotnet-audit-pipeline/SKILL.md` phase 3 "Trace contract validation"; the legal ID dictionary `skills/shared/EVIDENCE_POINT_IDS.md` (parsed dynamically at runtime, not hard-coded) |
| B | Placeholder residue: recursively scan all `.md` files, reporting unreplaced `${var}` and `{{var}}` (single-brace `{host}` `{cookie}` `{token}` `{apiKey}` `{jwt}` and template fields such as `{timestamp}` do not report) | `skills/dotnet-audit-pipeline/SKILL.md` "Integrity Constraints" item 2; `skills/shared/IO_PATH_CONVENTION.md` "PoC placeholder rules" |
| C | Gate consistency: reconcile `api_coverage_status` / `api_coverage_percent` / `coverage_mode` of `quality/api_coverage_gate_*.md` with `pipeline_execution` of `quality/pipeline_execution_*.md` — when `api_coverage_status != COMPLETE`, when `percent < 100%` in FULL mode, or when `coverage_mode=SAMPLE`, `pipeline_execution=COMPLETED` is judged FAIL | `skills/dotnet-audit-pipeline/SKILL.md` "API Coverage Gate (Mandatory)" / "Entry Coverage Mode and Gate"; `skills/shared/IO_PATH_CONVENTION.md` "Coverage gate and completion-state conventions"; `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md` "Acceptance Points" |
| D | Final report: `*code_audit*.md` must declare both `audit_surface_status` and `api_coverage_status` (dual completion states); when `api_coverage_status=PARTIAL`, `quality/unmapped_routes_*.md` must exist; the validity of `EVID_*` references in the report is the same as check A | `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md` "Fixed Template (Mandatory Fields)"; `skills/dotnet-audit-pipeline/SKILL.md` "Dual Completion-State Declaration (Mandatory)" / "Route Mapping Loop Backfill Gate" |
| E | Degradation semantics: WARN when "Confirmed" appears near the same entries of a `route_id` with `trace_status=PARTIAL/UNRESOLVED` in `vuln_audit/*.md` (text-level approximate attribution; cannot be pinned to a specific vulnerability entry, hence WARN rather than FAIL) | `skills/dotnet-audit-pipeline/SKILL.md` "Mandatory Constraints" / "Trace completeness fallback rule"; `skills/dotnet-route-tracer/SKILL.md` "Failure and Degradation Branches" |
| F | Stage directory completeness: 16 stage directories are expected by convention (codegraph/scan_audit/coverage_audit/route_mapping/auth_audit/route_tracer/briefing/vuln_audit/vuln_poc/framework_audit/cross_analysis/vuln_report/exploit_chain/global_sink_fallback/review/quality); missing ones are reported as WARN; empty directories, or directories with artifacts but without an `index_*` / `empty_result_*` index file, are reported as WARN | `skills/shared/IO_PATH_CONVENTION.md` "Default Execution Mode (Mandatory Persistence)" / "Phase Index Files and Empty-Result Files (Mandatory)"; `skills/dotnet-audit-pipeline/SKILL.md` "Output Directory Structure" |

## Recommended Integration Point in the Pipeline

It is recommended to run this script **before finalizing phase 5 (aggregation
report)**, as a programmatic step of the closing double-safety:

```
Phase 4.5 evidence quality review → phase 5 aggregation draft → 【python scripts/validate_audit.py <output_path>】
→ fix FAILs → review WARNs → persist quality/final_anchor_checklist_{timestamp}.md → deliver
```

- When the exit code is 1 (FAIL exists), align with the BLOCKED semantics of
  `final_anchor_decision`; outputting a "deliverable / closing complete"
  conclusion is forbidden;
- The `--json` output can be parsed directly by downstream automation (e.g. CI
  or an aggregation agent); the `results[].check` field corresponds to the A–F
  checks in the table above;
- The script only reads; it does not modify any file in the audit output directory.

## Pre-Commit Gate Entry (T3-13)

`scripts/pre_commit_check.ps1` is the gate check entry for pre-commit scenarios:
it invokes `validate_audit.py --stack auto` and **passes through the exit code**
(0 = passed / WARN only, allowed; 1 = FAIL exists, blocked; 2 = usage error).
The default target is the self-test sample baseline; passing an audit output
directory validates that run's artifacts. Whether to wire it into git hooks is
up to the user (point `git config core.hooksPath` at a custom hooks directory,
or append it to the existing `.git/hooks/pre-commit`); this repository does
**not** create a `.github/` workflow.

```powershell
.\scripts\pre_commit_check.ps1                        # Validate the self-test sample baseline by default (expected exit code 1: the samples intentionally FAIL)
.\scripts\pre_commit_check.ps1 D:\targets\eshop_audit # Validate the specified audit output directory (0 = committable/deliverable, 1 = blocked)
```

## Self-Test Samples scripts/_demo_audit/

`scripts/_demo_audit/` is a retained set of self-test samples (not real audit
artifacts), manually constructed with the following counterexamples:

- `route_tracer/R0001/trace_*.md`: missing the `## 9)` section → check A FAIL
- `route_tracer/R0002/trace_*.md`: `trace_status=UNRESOLVED` and `## 9)` cites a
  fabricated `EVID_SQL_TOTALLY_FAKE_ID` → check A FAIL
- `demo_code_audit_*.md`: contains `${gate_reason_text}`, `${user_id}`,
  `{{session_cookie}}` residue → check B FAIL; declares
  `api_coverage_status=PARTIAL` but lacks `unmapped_routes_*.md` and cites a
  fabricated `EVID_SQL_FAKE_POINT` → check D FAIL
- `quality/pipeline_execution_*.md`: `pipeline_execution=COMPLETED` conflicts
  with `api_coverage_status=PARTIAL` / `percent=80%` → check C FAIL
- `vuln_audit/sql_*.md`: R0001 with `trace_status=PARTIAL` is marked ✅Confirmed
  → check E WARN
- Many stage directories missing / lacking index files → check F WARN

Contract drift counterexample suites (2026-08-23, supplemented per stack):

- `dotnet_missing_section/`: trace missing the mandatory section `## 7) Sink Summary` → check A detects the "missing section" type of drift
- `node_wrong_status/`: `trace_status: COMPLETE` is not in the node five-state domain (NOT_STARTED / IN_PROGRESS / DONE_OPEN / DONE_CLOSED / BLOCKED) → regression for cross-stack status-domain confusion
- `fullstack_bad_contract/`: contract three-bucket counts inconsistent with `contract_coverage_percent` (declared 50% ≠ 4/6≈66.7%) → regression for contract alignment rules
- `fullstack_missing_decl/`: missing per-stack completion-state declarations → regression for the dual/four completion-state checks
- `fullstack_ok/`: full-stack positive example, used to confirm the gate does not harm compliant artifacts

Regression self-test commands (baseline measured 2026-09-03):

```bash
python scripts/validate_audit.py scripts/_demo_audit                        # Root-level full samples: PASS=1 FAIL=4 WARN=17, exit code 1
python scripts/validate_audit.py scripts/_demo_audit/dotnet_missing_section  # PASS=4 FAIL=1 WARN=17, exit code 1
python scripts/validate_audit.py scripts/_demo_audit/node_wrong_status       # PASS=3 FAIL=1 WARN=17, exit code 1
python scripts/validate_audit.py scripts/_demo_audit/node_bad_trace          # PASS=1 FAIL=2 WARN=18, exit code 1
python scripts/validate_audit.py scripts/_demo_audit/newskill_ok             # PASS=1 FAIL=0 WARN=19, exit code 0
python scripts/validate_audit.py scripts/_demo_audit/fullstack_bad_contract  # PASS=5 FAIL=1 WARN=40, exit code 1
python scripts/validate_audit.py scripts/_demo_audit/fullstack_missing_decl  # PASS=5 FAIL=1 WARN=40, exit code 1
python scripts/validate_audit.py scripts/_demo_audit/fullstack_ok            # Positive example: PASS=6 FAIL=0 WARN=40, exit code 0
```

## Known Limitations (Still Requiring Human / Model Judgment)

- Check E is an approximate text-window match and cannot attribute "Confirmed"
  to a specific vulnerability entry precisely; it may produce false positives
  (e.g. adjacent entries sharing a paragraph) and false negatives (entries split
  across files) — hence WARN only.
- Purely numeric short route_ids (e.g. `1`, `12`) are hard to match uniquely in
  vuln_audit; the script adds a context-word constraint for them but may still
  miss some.
- Section headings are matched by the "line-start `## N) heading text`" prefix;
  rewritten headings (e.g. synonym substitution) are judged as missing — this is
  exactly the contract intent, but judging semantic equivalence of headings is
  beyond the script's ability.
- Field parsing is based on the `field: value` / `field = value` text
  convention; if an artifact writes states into prose sentences without field
  names, the script cannot recognize them.
- The quality of evidence point content (an EVID cites a legal ID but the
  evidence fragment is empty / irrelevant), the truthfulness of coverage
  numbers, and whether the "pending evidence risk pool" is complete cannot be
  programmatically judged; they still rely on model discipline and manual review.
