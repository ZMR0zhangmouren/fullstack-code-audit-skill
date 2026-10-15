#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate_audit.py — Gate validation script for .NET white-box security audit
output directories (pure standard library).

Usage:
    python scripts/validate_audit.py <audit_output_dir> [--stack auto|dotnet|node|fullstack]
                                     [--skill-root <path>] [--json]

Arguments:
    audit_output_dir   The output directory of one audit run (containing phase
                       directories such as route_tracer/ quality/ vuln_audit/)
    --stack            Audit stack type (auto: probe the output tree, default;
                       dotnet keeps the existing single-stack behavior;
                       node enables check N; fullstack runs checks F/F2 against
                       the output root and reuses the dual-stack A-F/N checks)
    --skill-root       Skill library root (used to locate
                       skills/shared/EVIDENCE_POINT_IDS.md and
                       skills/shared/IO_PATH_CONVENTION.md); defaults to the
                       parent directory of the script's directory
    --json             Output machine-readable JSON instead of the
                       human-readable report

Checks:
    A. Trace contract check    The 5 mandatory sections of
                               route_tracer/**/trace_*.md, the trace_status
                               value domain, and EVID_* ID validity in ## 9)
                               (contract: dotnet-route-tracer/SKILL.md)
    B. Placeholder residue     Recursively scan all .md files, reporting
                               unreplaced ${var} / {{var}}
                               (contract: dotnet-audit-pipeline/SKILL.md
                               integrity constraints)
    C. Gate consistency        Conflicts among api_coverage_status /
                               api_coverage_percent / coverage_mode and
                               pipeline_execution (contract:
                               dotnet-audit-pipeline/SKILL.md API Coverage
                               Gate, IO_PATH_CONVENTION.md coverage gate and
                               completion-state conventions)
    D. Final report check      The dual completion-state declarations of
                               *code_audit*.md, the existence of
                               unmapped_routes when PARTIAL, and EVID_* ID
                               validity (contract:
                               DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md)
    E. Degradation semantics   WARN when a route_id with
                               trace_status=PARTIAL/UNRESOLVED is marked
                               ✅Confirmed in vuln_audit (contract:
                               dotnet-audit-pipeline/SKILL.md mandatory
                               constraints)
    F. Stage directory         Check stage directories and index files per
       completeness            IO_PATH_CONVENTION (missing / empty
                               directories reported as WARN)

    N. Node trace contract     The 10 minimal sections of
                               node/route_tracer/**/trace_*.md, the five-state
                               trace_status (NOT_STARTED/IN_PROGRESS/
                               DONE_OPEN/DONE_CLOSED/BLOCKED), EVID validity
    F. Fullstack check         The four completion-state fields are traceable
                               (dotnet_/node_/contract_ gate artifacts) + the
                               four declarations in the final report + the
                               three-bucket counts and percent alignment of
                               cross/contract_coverage_gate (executed against
                               the output root when --stack=fullstack; the
                               dual-stack subdirectories reuse the A-F/N checks)
    R. Route count reconcil.   Compare the three header fields of
                               route_mapping/routes_*.md (declared_route_count /
                               expanded_route_count / count_self_check) with
                               the actual number of detail entries;
                               count_self_check=FAIL → FAIL; contradiction
                               between the two fields unique/method_path_count
                               → WARN (contract: DOTNET_ROUTE_OUTPUT_TEMPLATES.md
                               §1.1 / IO_PATH_CONVENTION.md dual-field route
                               counting standard)
    S. Exploit count reconcil. Compare the declared consistency_check_counts
                               of exploit_chain/exploit_chains_*.md with the
                               row-by-row counts of the chain overview table;
                               the final report's write-back of
                               exploit_chain_consistency_check_counts is
                               reconciled in sync (inconsistency → WARN)
    T. final_anchor reconcil.  Compare the summary counts / decision of
                               quality/final_anchor_checklist_*.md with the
                               final report §4.6 write-back values field by
                               field (inconsistency → WARN)
    U. Consistency merge mark  No standalone coverage_consistency_check_*.md
                               and no MERGED_FROM: coverage_consistency_check
                               marker line in any quality/ file → WARN
                               (P1-8 merge marker format, contract:
                               DOTNET_ROUTE_OUTPUT_TEMPLATES.md §8)

    Note: R/S/T/U are checks added in the P0-1/P0-3 batches; they uniformly
    "skip when fields/files are missing, no WARN", ensuring backward
    compatibility with historical artifacts; passing checks produce no PASS
    records, keeping the existing baseline summary stable.
    V/W are checks added in batch B (2026-09-18); they likewise skip when
    missing: V reconciles the final report risk pool count with the
    pending_pool pool_total; W probes the existence of the
    "## Specialty Dispatch Verification" section in vuln_audit/index.

Exit code conventions:
    0 = all PASS or only WARNs exist
    1 = at least one FAIL exists
    2 = usage error or environment error (directory does not exist, EVID
        dictionary unreadable, etc.)
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Windows console UTF-8 output fallback
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------------- Constants (contract semantics; no hard-coded line numbers)

REQUIRED_TRACE_SECTIONS = [
    "## 5) Parameter Controllability Matrix",
    "## 6) Sink Location",
    "## 7) Sink Summary",
    "## 8) Trace Completeness Statement",
    "## 9) Sink Evidence Type Checklist",
]

TRACE_STATUS_DOMAIN = {"COMPLETE", "PARTIAL", "UNRESOLVED"}

# ---- Stack-aware extension (P0-5) ----

NODE_TRACE_SECTIONS = [
    "Parameter Controllability Matrix",
    "Sink Location",
    "Sink Summary",
    "Trace Completeness Statement",
    "Sink Evidence Type Checklist",
]

NODE_TRACE_STATUS_DOMAIN = {"NOT_STARTED", "IN_PROGRESS", "DONE_OPEN", "DONE_CLOSED", "BLOCKED"}


def parse_status_field(text, field):
    """Prefix-aware completion-state field parsing: allows dotnet_/node_/contract_
    prefixes (full-stack four declarations).

    Fixes the check-D field-name boundary misjudgment: `\\bapi_coverage_status\\b`
    cannot match `dotnet_api_coverage_status` (`_` is a word character, so there
    is no boundary at the prefix).
    """
    m = re.search(r"(?<![A-Za-z0-9_])(?:(?:dotnet|node|contract)_)?" + re.escape(field)
                  + r"\s*[:：=]\s*\**\s*`?([A-Za-z_]+)", text)
    return m.group(1) if m else None


def detect_stack(audit_dir):
    """auto probing: an output tree containing dotnet/ and node/ subdirectories →
    fullstack; otherwise decide node by directory name / substructure."""
    if (audit_dir / "dotnet").is_dir() and (audit_dir / "node").is_dir():
        return "fullstack"
    if (audit_dir / "node").is_dir() or audit_dir.name == "node":
        return "node"
    return "dotnet"


def has_node_section(text, title):
    """Loose matching of node trace artifact section headings: the line start
    allows ## / ### / numbered-list prefixes."""
    pat = re.compile(r"^#{0,3}\s*\d*\.?\s*" + re.escape(title) + r"\b", re.M)
    return pat.search(text) is not None

# Union of the IO_PATH_CONVENTION.md "default execution mode" and the
# dotnet-audit-pipeline "output directory structure"
STAGE_DIRS = [
    "codegraph", "scan_audit", "coverage_audit", "route_mapping", "auth_audit",
    "route_tracer", "briefing", "vuln_audit", "vuln_poc", "framework_audit",
    "cross_analysis", "vuln_report", "exploit_chain", "global_sink_fallback",
    "review", "quality",
]

EVID_TOKEN = re.compile(r"\bEVID_[A-Z0-9_]+\b")

RESULTS = []  # {check, level, message, file, line, fix}


def add(check, level, message, file=None, line=None, fix=None):
    RESULTS.append({
        "check": check, "level": level, "message": message,
        "file": str(file) if file else None, "line": line, "fix": fix,
    })


def read_text(p):
    return p.read_text(encoding="utf-8", errors="replace")


def parse_field(text, field):
    """Parse a scalar field of the form `field: VALUE` / `field：VALUE` / `field = VALUE`."""
    m = re.search(r"\b" + re.escape(field) + r"\b\s*[:：=]\s*\**\s*`?([A-Za-z_]+)", text)
    return m.group(1) if m else None


def parse_percent(text, field="api_coverage_percent"):
    m = re.search(r"\b" + re.escape(field) + r"\b\s*[:：=]\s*([0-9]+(?:\.[0-9]+)?)\s*%?", text)
    return float(m.group(1)) if m else None


def parse_int_field(text, field):
    """Parse an integer count field (e.g. the contract three buckets `matched_count: 3`).

    The parse_field value regex ([A-Za-z_]+) does not support numeric values, so
    pure numeric counts must go through this function.
    """
    m = re.search(r"(?<![A-Za-z0-9_])" + re.escape(field)
                  + r"\s*[:：=]\s*([0-9]+)", text)
    return m.group(1) if m else None


def parse_trace_status(text):
    """Parse the trace_status declaration from a trace file. Prefer the explicit
    assignment form."""
    m = re.search(r"\btrace_status\b\s*[:：=]\s*\**\s*`?([A-Z]+)", text)
    if m:
        return m.group(1)
    # Fallback: trace_status adjacent to a legal value (tolerating the table-cell
    # form `| trace_status | PARTIAL |`)
    m = re.search(r"\btrace_status\b[^A-Za-z0-9_]{0,8}\b(COMPLETE|PARTIAL|UNRESOLVED)\b", text)
    return m.group(1) if m else None


def has_heading(text, heading):
    """Exact section heading match: line-start ## N) heading text (trailing
    whitespace and full-width parenthetical notes allowed)."""
    num, title = heading.split(")", 1)
    num = num.lstrip("# ").strip()
    title = title.strip()
    pat = re.compile(r"^##\s+" + re.escape(num) + r"\)\s*" + re.escape(title), re.M)
    return pat.search(text) is not None


def section_slice(text, heading):
    """Slice the content between heading and the next heading of the same or a
    higher level."""
    idx = text.find(heading)
    if idx < 0:
        return ""
    rest = text[idx + len(heading):]
    m = re.search(r"^##\s", rest, re.M)
    return rest[:m.start()] if m else rest


# ---------------------------------------------------------------- Contract dictionary loading

def load_evid_ids(skill_root):
    path = Path(skill_root) / "skills" / "shared" / "EVIDENCE_POINT_IDS.md"
    if not path.is_file():
        return None, path
    return set(EVID_TOKEN.findall(read_text(path))), path


# ---------------------------------------------------------------- Check A: trace contract

def check_trace_contract(audit_dir, evid_ids):
    cid = "A_trace_contract"
    tracer_dir = audit_dir / "route_tracer"
    traces = []
    if tracer_dir.is_dir():
        traces = sorted(p for p in tracer_dir.rglob("trace_*.md")
                        if not p.name.startswith("trace_summary"))
    if not traces:
        add(cid, "WARN", "No route_tracer/**/trace_*.md found; trace contract check skipped",
            file=tracer_dir)
        return {}

    route_status = {}  # route_id -> trace_status (used by check E)
    for p in traces:
        rel = p.relative_to(audit_dir)
        text = read_text(p)
        ok = True

        missing = [h for h in REQUIRED_TRACE_SECTIONS if not has_heading(text, h)]
        if missing:
            ok = False
            add(cid, "FAIL", "Trace file is missing mandatory sections: " + "; ".join(missing),
                file=rel,
                fix="Complete the 5 mandatory sections per the dotnet-route-tracer SKILL.md "
                    "single-route report template (## 5) Parameter Controllability Matrix / "
                    "## 6) Sink Location / ## 7) Sink Summary / ## 8) Trace Completeness "
                    "Statement / ## 9) Sink Evidence Type Checklist); field names must not "
                    "be rewritten")

        status = parse_trace_status(text)
        if status is None:
            ok = False
            add(cid, "FAIL", "Cannot parse the trace_status declaration", file=rel,
                fix="Explicitly write `trace_status: COMPLETE|PARTIAL|UNRESOLVED` in "
                    "## 8) Trace Completeness Statement")
        elif status not in TRACE_STATUS_DOMAIN:
            ok = False
            add(cid, "FAIL", "Illegal trace_status value: %s (legal domain: COMPLETE/PARTIAL/UNRESOLVED)"
                % status,
                file=rel, fix="Correct trace_status to one of the legal values")
        else:
            route_id = p.parent.name
            route_status[route_id] = status

        sec9 = section_slice(text, "## 9) Sink Evidence Type Checklist")
        if sec9 and evid_ids is not None:
            unknown = sorted(set(EVID_TOKEN.findall(sec9)) - evid_ids)
            if unknown:
                ok = False
                add(cid, "FAIL", "## 9) checklist cites unregistered EVID IDs: " + ", ".join(unknown),
                    file=rel,
                    fix="EVID_* IDs must be verbatim identical to skills/shared/EVIDENCE_POINT_IDS.md; "
                        "fix the spelling or register the new evidence point first")

        if ok:
            add(cid, "PASS", "Trace contract passed (sections complete, trace_status=%s, EVID references valid)"
                % status,
                file=rel)
    return route_status


# ---------------------------------------------------------------- Check N: node trace contract (P0-5)

def check_node_trace_contract(audit_dir, evid_ids):
    cid = "N_node_trace_contract"
    tracer_dir = audit_dir / "route_tracer"
    traces = []
    if tracer_dir.is_dir():
        traces = sorted(p for p in tracer_dir.rglob("trace_*.md")
                        if not p.name.startswith("trace_summary"))
    if not traces:
        add(cid, "WARN", "No node/route_tracer/**/trace_*.md found; node trace contract check skipped",
            file=tracer_dir)
        return {}

    route_status = {}
    for p in traces:
        rel = p.relative_to(audit_dir)
        text = read_text(p)
        ok = True

        missing = [h for h in NODE_TRACE_SECTIONS if not has_node_section(text, h)]
        if missing:
            ok = False
            add(cid, "FAIL", "Node trace file is missing mandatory sections: " + "; ".join(missing),
                file=rel,
                fix="Complete the mandatory sections (see the node-route-tracer SKILL.md "
                    "'trace_{timestamp}.md minimal sections' definition of 10 sections, of "
                    "which the 5 minimal sections are always checked: Parameter "
                    "Controllability Matrix / Sink Location / Sink Summary / Trace "
                    "Completeness Statement / Sink Evidence Type Checklist)")

        # Adaptation: the node five-state includes DONE_OPEN/DONE_CLOSED (underscored
        # values) that the ([A-Z]+) value regex of parse_trace_status cannot capture
        # fully, so parse it with the prefix-aware parse_status_field
        status = parse_status_field(text, "trace_status")
        if status is None:
            ok = False
            add(cid, "FAIL", "Cannot parse the node trace_status declaration", file=rel,
                fix="Explicitly write one of the five `trace_status` states in "
                    "'Trace Completeness Statement'")
        elif status not in NODE_TRACE_STATUS_DOMAIN:
            ok = False
            add(cid, "FAIL", "Illegal node trace_status value: %s (legal domain: %s)"
                % (status, "/".join(sorted(NODE_TRACE_STATUS_DOMAIN))),
                file=rel, fix="Correct to NOT_STARTED/IN_PROGRESS/DONE_OPEN/DONE_CLOSED/BLOCKED")
        else:
            route_status[p.parent.name] = status

        sec = section_slice(text, "Sink Evidence Type Checklist")
        if sec and evid_ids is not None:
            unknown = sorted(set(EVID_TOKEN.findall(sec)) - evid_ids)
            if unknown:
                ok = False
                add(cid, "FAIL", "Node checklist cites unregistered EVID IDs: " + ", ".join(unknown),
                    file=rel,
                    fix="EVID_* IDs must be verbatim identical to skills/shared/EVIDENCE_POINT_IDS.md")

        if ok:
            add(cid, "PASS", "Node trace contract passed (sections complete, trace_status=%s, "
                "EVID references valid)" % status,
                file=rel)
    return route_status


# ---------------------------------------------------------------- Check B: placeholder residue

PLACEHOLDER_PATTERNS = [
    (re.compile(r"\$\{[^}\n]*\}"), "${var}"),
    (re.compile(r"\{\{[^}\n]*\}\}"), "{{var}}"),
]


def check_placeholders(audit_dir):
    cid = "B_placeholder_residue"
    md_files = sorted(audit_dir.rglob("*.md"))
    total_findings = 0
    for p in md_files:
        rel = p.relative_to(audit_dir)
        hits = []
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            for pat, kind in PLACEHOLDER_PATTERNS:
                for m in pat.finditer(line):
                    hits.append((lineno, kind, m.group(0)))
        if hits:
            total_findings += len(hits)
            shown = "; ".join("L%d %s %s" % (ln, kind, tok) for ln, kind, tok in hits[:10])
            more = " (%d more not listed)" % (len(hits) - 10) if len(hits) > 10 else ""
            add(cid, "FAIL", "Found %d unreplaced placeholders: %s%s" % (len(hits), shown, more),
                file=rel,
                fix="Replace ${var} and {{var}} with real routes/parameters; session fields "
                    "allow only single-brace {host}/{cookie}/{token}/{apiKey}/{jwt}")
    if total_findings == 0:
        add(cid, "PASS", "Scanned %d .md files in total; no ${var}/{{var}} placeholder residue found"
            % len(md_files))


# ---------------------------------------------------------------- Check C: gate consistency

def check_gate_consistency(audit_dir):
    cid = "C_gate_consistency"
    quality = audit_dir / "quality"
    gate_files = sorted(quality.glob("api_coverage_gate_*.md")) if quality.is_dir() else []
    pe_files = sorted(quality.glob("pipeline_execution_*.md")) if quality.is_dir() else []

    if not pe_files:
        add(cid, "WARN", "No quality/pipeline_execution_*.md found; gate consistency check skipped",
            file=quality)
        return
    pe = pe_files[-1]
    pe_text = read_text(pe)
    pipeline_execution = parse_field(pe_text, "pipeline_execution")
    if pipeline_execution is None:
        add(cid, "FAIL", "Cannot parse the pipeline_execution field in pipeline_execution_*.md",
            file=pe.relative_to(audit_dir),
            fix="Explicitly write `pipeline_execution: COMPLETED|PARTIAL`")
        return

    gate_status = gate_percent = None
    coverage_mode = parse_field(pe_text, "coverage_mode")
    if gate_files:
        gate = gate_files[-1]
        gate_text = read_text(gate)
        gate_status = parse_status_field(gate_text, "api_coverage_status")
        gate_percent = parse_percent(gate_text)
        coverage_mode = coverage_mode or parse_field(gate_text, "coverage_mode")
    else:
        add(cid, "WARN", "No quality/api_coverage_gate_*.md found; can only validate against "
            "pipeline_execution alone",
            file=quality)

    if coverage_mode is None:
        coverage_mode = "FULL"  # The contract default must be FULL

    problems = []
    if pipeline_execution == "COMPLETED":
        if coverage_mode == "SAMPLE":
            problems.append("pipeline_execution must not be COMPLETED when coverage_mode=SAMPLE")
        if gate_status is not None and gate_status != "COMPLETE":
            problems.append("pipeline_execution must not be COMPLETED when api_coverage_status=%s"
                            % gate_status)
        if coverage_mode == "FULL" and gate_percent is not None and gate_percent < 100:
            problems.append("In FULL mode, pipeline_execution must not be COMPLETED when "
                            "api_coverage_percent=%g%% < 100%%" % gate_percent)

    if problems:
        add(cid, "FAIL", "Gate conflict: " + "; ".join(problems),
            file=pe.relative_to(audit_dir),
            fix="Degrade pipeline_execution to PARTIAL, or first complete route mapping so "
                "that api_coverage_status=COMPLETE and api_coverage_percent=100%")
    else:
        add(cid, "PASS",
            "Gates consistent (pipeline_execution=%s, api_coverage_status=%s, percent=%s, "
            "coverage_mode=%s)"
            % (pipeline_execution, gate_status, gate_percent, coverage_mode),
            file=pe.relative_to(audit_dir))


# ---------------------------------------------------------------- Check D: final report

def check_final_report(audit_dir, evid_ids):
    cid = "D_final_report"
    reports = sorted(audit_dir.rglob("*code_audit*.md"))
    if not reports:
        add(cid, "WARN", "No *code_audit*.md final report found; final report check skipped",
            file=audit_dir)
        return
    p = reports[-1]
    rel = p.relative_to(audit_dir)
    text = read_text(p)
    ok = True

    for field in ("audit_surface_status", "api_coverage_status"):
        if parse_status_field(text, field) is None:
            ok = False
            add(cid, "FAIL", "Final report is missing the completion-state declaration field: %s"
                % field, file=rel,
                fix="Per DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md '1) Dual completion-state "
                    "declaration', declare both audit_surface_status and api_coverage_status; "
                    "replacing them with a single 'completed' is forbidden")

    coverage_status = parse_status_field(text, "api_coverage_status")
    if coverage_status == "PARTIAL":
        quality = audit_dir / "quality"
        unmapped = list(quality.glob("unmapped_routes_*.md")) if quality.is_dir() else []
        if not unmapped:
            ok = False
            add(cid, "FAIL",
                "api_coverage_status=PARTIAL but quality/unmapped_routes_*.md is missing",
                file=rel,
                fix="Output quality/unmapped_routes_{timestamp}.md (unmapped controllers / "
                    "actions / reasons / backfill suggestions)")

    if evid_ids is not None:
        unknown = sorted(set(EVID_TOKEN.findall(text)) - evid_ids)
        if unknown:
            ok = False
            add(cid, "FAIL", "Final report cites unregistered EVID IDs: " + ", ".join(unknown),
                file=rel,
                fix="EVID_* IDs must be verbatim identical to skills/shared/EVIDENCE_POINT_IDS.md")

    if ok:
        add(cid, "PASS", "Final report has both completion-state declarations; unmapped_routes "
            "and EVID references are compliant", file=rel)


# ---------------------------------------------------------------- Check E: degradation semantics

def check_downgrade_semantics(audit_dir, route_status):
    cid = "E_degradation_semantics"
    degraded = {rid: st for rid, st in route_status.items() if st in ("PARTIAL", "UNRESOLVED")}
    if not degraded:
        add(cid, "PASS", "No routes with trace_status=PARTIAL/UNRESOLVED; the degradation "
            "semantics check has nothing to do")
        return
    vuln_dir = audit_dir / "vuln_audit"
    vuln_files = sorted(vuln_dir.glob("*.md")) if vuln_dir.is_dir() else []
    if not vuln_files:
        add(cid, "WARN", "Degraded traces exist (%s) but vuln_audit/ has no artifacts; cannot "
            "check whether they were mislabeled as confirmed"
            % ", ".join(sorted(degraded)), file=vuln_dir)
        return

    hits = 0
    for p in vuln_files:
        rel = p.relative_to(audit_dir)
        lines = read_text(p).splitlines()
        for rid, st in sorted(degraded.items()):
            rid_pat = re.compile(r"(?<![\w\-])" + re.escape(rid) + r"(?![\w\-])")
            hit_lines = []
            for i, line in enumerate(lines):
                if not rid_pat.search(line):
                    continue
                # Purely numeric short IDs are prone to false positives: require a
                # route context word on the same line
                if rid.isdigit() and len(rid) < 3 and not re.search(r"route|entry|endpoint", line, re.I):
                    continue
                window = "\n".join(lines[max(0, i - 2):i + 3])
                if "Confirmed" in window:
                    hit_lines.append(i + 1)
            if hit_lines:  # Report only once per (file, route_id) to avoid noise
                hits += 1
                add(cid, "WARN",
                    "route_id=%s has trace_status=%s, but 'Confirmed' appears near its "
                    "vulnerability entries (hit lines: %s); this is suspected to violate "
                    "the degradation semantics (precise attribution is difficult, handled "
                    "as WARN)"
                    % (rid, st, ", ".join("L%d" % n for n in hit_lines[:5])),
                    file=rel, line=hit_lines[0],
                    fix="Entries with trace_status=PARTIAL/UNRESOLVED must not be marked "
                        "✅Confirmed; degrade them to ⚠️Pending Verification and list them "
                        "in the 'Unclosed Traces / Pending Evidence Risk Pool'")
    if hits == 0:
        add(cid, "PASS", "Degraded routes (%s) were not labeled 'Confirmed' in vuln_audit"
            % ", ".join(sorted(degraded)))


# ---------------------------------------------------------------- Check F: stage directory completeness

def check_stage_dirs(audit_dir):
    cid = "F_stage_dirs"
    missing, warned = 0, 0
    for name in STAGE_DIRS:
        d = audit_dir / name
        if not d.is_dir():
            missing += 1
            add(cid, "WARN", "Stage directory missing: %s/" % name, file=d,
                fix="Create the directory per the IO_PATH_CONVENTION mandatory persistence "
                    "mode; when there is no output, write index_{timestamp}.md or "
                    "empty_result_{timestamp}.md stating the reason")
            continue
        files = [f for f in d.rglob("*") if f.is_file()]
        has_index = any(f.name.startswith(("index_", "empty_result_")) for f in files)
        if not files:
            warned += 1
            add(cid, "WARN", "Stage directory is empty and has no index file: %s/" % name, file=d,
                fix="Empty-result phases must persist index_{timestamp}.md or "
                    "empty_result_{timestamp}.md stating the reason")
        elif not has_index:
            warned += 1
            add(cid, "WARN", "Stage directory lacks an index/empty_result index file: %s/ "
                "(%d files in total)"
                % (name, len(files)), file=d,
                fix="Add %s/index_{timestamp}.md recording this phase's execution status "
                    "and artifact list" % name)
    if missing == 0 and warned == 0:
        add(cid, "PASS", "All %d stage directories exist and each has an index file"
            % len(STAGE_DIRS))


# ---------------------------------------------------------------- Check F: fullstack four completion states and contract counts (P0-5)

def check_fullstack_statuses(root):
    cid = "F_fullstack_four_states"
    specs = [
        ("dotnet_api_coverage_status", ["dotnet", "quality", "api_coverage_gate_*.md"], "api_coverage_status"),
        ("node_api_coverage_status", ["node", "quality", "api_coverage_gate_*.md"], "api_coverage_status"),
        ("contract_coverage_status", ["cross", "contract_coverage_gate_*.md"], "contract_coverage_status"),
    ]
    ok = True
    for full_field, rel_parts, inner_field in specs:
        pattern = root.joinpath(*rel_parts)
        files = sorted(pattern.parent.glob(pattern.name)) if pattern.parent.is_dir() else []
        if not files:
            add(cid, "FAIL", "Missing the source artifact for %s: %s"
                % (full_field, "/".join(rel_parts)),
                file=pattern, fix="The four completion-state fields must be traceable to "
                "the corresponding gate artifacts")
            ok = False
            continue
        val = parse_status_field(read_text(files[-1]), inner_field)
        if val is None:
            add(cid, "FAIL", "%s cannot be parsed (%s lacks the %s field)"
                % (full_field, files[-1].relative_to(root), inner_field),
                file=files[-1].relative_to(root),
                fix="Explicitly write the %s field per the gate template" % inner_field)
            ok = False

    reports = sorted(root.rglob("*code_audit*.md"))
    if reports:
        text = read_text(reports[-1])
        for field in ("dotnet_api_coverage_status", "node_api_coverage_status",
                      "contract_coverage_status", "audit_surface_status"):
            if parse_status_field(text, field) is None:
                ok = False
                add(cid, "FAIL", "Full-stack final report is missing the completion-state "
                    "declaration field: %s" % field,
                    file=reports[-1].relative_to(root),
                    fix="Per FULLSTACK_FINAL_REPORT_FIXED_TEMPLATE, all four declarations "
                        "must be present; replacing them with a single 'completed' is forbidden")
    else:
        add(cid, "WARN", "No full-stack final report *code_audit*.md found; the report "
            "four-declaration check is skipped", file=root)

    if ok:
        add(cid, "PASS", "The four completion-state fields are complete and traceable to "
            "the gate artifacts")
    return ok


def check_contract_gate_counts(cross_dir):
    cid = "F2_contract_bucket_counts"
    files = sorted(cross_dir.glob("contract_coverage_gate_*.md")) if cross_dir.is_dir() else []
    if not files:
        add(cid, "WARN", "No cross/contract_coverage_gate_*.md found; contract count check "
            "skipped", file=cross_dir)
        return
    p = files[-1]
    text = read_text(p)
    m = parse_int_field(text, "matched_count")
    f = parse_int_field(text, "frontend_only_count")
    b = parse_int_field(text, "backend_only_count")
    pct = parse_percent(text, "contract_coverage_percent")
    if m is None or f is None or b is None:
        add(cid, "FAIL", "contract_coverage_gate is missing the three bucket count fields "
            "(matched_count/frontend_only_count/backend_only_count)",
            file=p.relative_to(cross_dir.parent),
            fix="Output the three bucket counts and percent per the cross-stack-contract-mapper "
                "SKILL.md")
        return
    m, f, b = int(m), int(f), int(b)
    total = m + f + b
    if total == 0:
        add(cid, "WARN", "All three bucket counts are 0; cannot validate percent",
            file=p.relative_to(cross_dir.parent))
        return
    expect = m / total * 100
    if pct is None:
        add(cid, "WARN", "contract_coverage_gate does not declare the contract_coverage_percent field",
            file=p.relative_to(cross_dir.parent),
            fix="Output contract_coverage_percent=matched/(matched+frontend_only+backend_only) "
                "per the cross-stack-contract-mapper SKILL.md")
    elif abs(pct - expect) > 0.5:
        add(cid, "FAIL", "contract_coverage_percent=%.1f%% does not match the three bucket counts "
            "(expected %.1f%% = matched/total)"
            % (pct, expect), file=p.relative_to(cross_dir.parent),
            fix="contract_coverage_percent must equal matched/(matched+frontend_only+backend_only)")
    else:
        add(cid, "PASS", "Contract three bucket counts align with percent (matched=%d, total=%d)"
            % (m, total))
    if parse_percent(text, "unnormalized_rate") is None:
        add(cid, "WARN", "contract_coverage_gate does not declare unnormalized_rate (required "
            "after the P1-11 landing)",
            file=p.relative_to(cross_dir.parent),
            fix="Add unnormalized_rate=the share of unnormalized calls; >10%% forces PARTIAL")


# ---------------------------------------------------------------- Checks R/S/T/U: count reconciliation and merge probing (P0-1/P0-3)

def parse_count_dict(text, field):
    """Parse a count dictionary of the form `{PASS:0, BLOCKED:1, N/A:0}` (used by
    the exploit/final_anchor reconciliation).

    Keys allow uppercase letters and slashes (N/A); returns {key: int}, or None
    when the field is missing.
    """
    m = re.search(re.escape(field) + r"\s*[:：]\s*\{([^{}]*)\}", text)
    if not m:
        return None
    pairs = re.findall(r"\b([A-Z][A-Z/]*)\b\s*[:：]\s*(\d+)", m.group(1))
    return {k: int(v) for k, v in pairs} or None


def _count_diffs(declared, actual):
    """Return the difference subset {key: (declared, actual)}; return None when
    neither dict has keys (cannot reconcile)."""
    keys = set(declared or {}) | set(actual or {})
    if not keys:
        return None
    return {k: (declared.get(k, 0), actual.get(k, 0)) for k in sorted(keys)
            if declared.get(k, 0) != actual.get(k, 0)}


def _fmt_count_diffs(diffs):
    return "; ".join("%s declared=%d/actual=%d" % (k, d[0], d[1]) for k, d in sorted(diffs.items()))


def check_route_count_reconciliation(audit_dir):
    """R: reconcile the three header count fields of routes with the actual number
    of detail entries (skip when fields are missing, no WARN)."""
    cid = "R_route_count_reconciliation"
    rm_dir = audit_dir / "route_mapping"
    files = sorted(rm_dir.glob("routes_*.md")) if rm_dir.is_dir() else []
    if not files:
        return  # No routes artifact → skip
    p = files[-1]
    rel = p.relative_to(audit_dir)
    text = read_text(p)

    declared = parse_int_field(text, "declared_route_count")
    if declared is None:
        return  # Historical artifacts without the three-field header → skip
    expanded = parse_int_field(text, "expanded_route_count")

    # Actual number of detail entries: prefer `=== [N]` entry lines; fall back to
    # the table data rows of the "Route List" section when no entry lines exist
    detail = len(re.findall(r"^===\s*\[\d+\]", text, re.M))
    if detail == 0:
        first_row = True
        for line in section_slice(text, "## Route List").splitlines():
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not cells[0] or set(cells[0]) <= set("-: "):
                continue  # table separator row
            if first_row:
                first_row = False  # header
                continue
            detail += 1

    if expanded is not None and int(expanded) != detail:
        add(cid, "WARN", "expanded_route_count=%s does not match the actual detail count %d"
            % (expanded, detail), file=rel,
            fix="Per DOTNET_ROUTE_OUTPUT_TEMPLATES.md §1.1, correct expanded_route_count so "
                "that it equals the actual number of `=== [N]` entry lines (or Route List "
                "table rows)")
    if expanded is not None and int(declared) != int(expanded):
        add(cid, "WARN", "declared_route_count=%s does not match expanded_route_count=%s"
            % (declared, expanded), file=rel,
            fix="Check the per-controller formulas in the 'Count Reconciliation' section; "
                "correct the declared total or the expanded details so the two values are equal")
    self_check = parse_field(text, "count_self_check")
    if self_check == "FAIL":
        add(cid, "FAIL", "count_self_check=FAIL: the route count self-check did not pass; "
            "delivery to downstream phases is forbidden",
            file=rel,
            fix="Go back to route-mapper and fix the count reconciliation section "
                "(declared/expanded_route_count and the per-controller formulas) so that "
                "count_self_check=PASS before entering route-tracer")

    # Dual-field standard: WARN only when both fields are present and contradictory
    # (method < unique); missing fields are not held accountable (backward compatible)
    unique = parse_int_field(text, "unique_path_count")
    method = parse_int_field(text, "method_path_count")
    if unique is not None and method is not None and int(method) < int(unique):
        add(cid, "WARN", "Route count dual-field standard contradiction: method_path_count=%s "
            "< unique_path_count=%s"
            % (method, unique), file=rel,
            fix="Per IO_PATH_CONVENTION.md route count dual-field standard: the (method,path) "
                "expanded total must not be less than the unique path count")


def check_exploit_count_reconciliation(audit_dir):
    """S: exploit consistency-check count declarations vs the actual rows of the
    chain overview table (skip when missing, no WARN).

    Consumption anchors (skills/dotnet-exploit-chain-audit/SKILL.md,
    DOTNET_ROUTE_OUTPUT_TEMPLATES.md §10):
    - The row-by-row count of the last column consistency_check_status of the
      "Chain Overview Table" in exploit_chain/exploit_chains_{timestamp}.md is the
      actual value; `consistency_check_counts: {PASS:n, BLOCKED:n, N/A:n}` in the
      file is the declared value.
    - The final report write-back of `exploit_chain_consistency_check_counts` is
      compared in sync.
    """
    cid = "S_exploit_count_reconciliation"
    ec_dir = audit_dir / "exploit_chain"
    files = sorted(ec_dir.glob("exploit_chains_*.md")) if ec_dir.is_dir() else []
    if not files:
        return  # No exploit_chain artifact → skip
    p = files[-1]
    rel = p.relative_to(audit_dir)
    text = read_text(p)

    tally = {}
    chain_rows = 0
    for line in section_slice(text, "Chain Overview Table").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells[0] or set(cells[0]) <= set("-: ") or "Chain ID" in cells[0]:
            continue  # separator row / header
        status = cells[-1]
        if status not in ("PASS", "BLOCKED", "N/A"):
            continue  # old-format overview tables without this column → cannot count, skip
        chain_rows += 1
        tally[status] = tally.get(status, 0) + 1

    declared = parse_count_dict(text, "consistency_check_counts")
    if chain_rows and declared is not None:
        diffs = _count_diffs(declared, tally)
        if diffs:
            add(cid, "WARN", "consistency_check_counts does not match the actual counts of the "
                "chain overview table: %s"
                % _fmt_count_diffs(diffs), file=rel,
                fix="Re-count row by row per the consistency_check_status column of the chain "
                    "overview table and write back consistency_check_counts")

    reports = sorted(audit_dir.rglob("*code_audit*.md"))
    if reports:
        rp = reports[-1]
        rep = parse_count_dict(read_text(rp), "exploit_chain_consistency_check_counts")
        if chain_rows and rep is not None:
            diffs = _count_diffs(rep, tally)
            if diffs:
                add(cid, "WARN", "The final report write-back of "
                    "exploit_chain_consistency_check_counts does not match the actual counts "
                    "of the chain overview table: %s"
                    % _fmt_count_diffs(diffs), file=rp.relative_to(audit_dir),
                    fix="Re-count the chain overview table and write back "
                        "exploit_chain_consistency_check_counts in the final report (fix the "
                        "report first, then re-run quick_validation)")


def check_final_anchor_reconciliation(audit_dir):
    """T: final_anchor_checklist summary counts vs the final report §4.6 write-back
    values (skip when missing, no WARN).

    Consumption anchors (DOTNET_ROUTE_OUTPUT_TEMPLATES.md §11 /
    DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md §4.6):
    - Checklist summary block: checklist_pass_count / checklist_blocked_count /
      checklist_pending_count / final_anchor_decision;
    - Final report §4.6 write-back: final_anchor_decision and
      final_anchor_checklist_counts: {PASS:n, BLOCKED:n, PENDING:n}.
    """
    cid = "T_final_anchor_reconciliation"
    quality = audit_dir / "quality"
    files = sorted(quality.glob("final_anchor_checklist_*.md")) if quality.is_dir() else []
    if not files:
        return  # No checklist artifact → skip
    text = read_text(files[-1])
    c_pass = parse_int_field(text, "checklist_pass_count")
    c_blocked = parse_int_field(text, "checklist_blocked_count")
    c_pending = parse_int_field(text, "checklist_pending_count")
    decision = parse_field(text, "final_anchor_decision")
    if decision is None and c_pass is None and c_blocked is None and c_pending is None:
        return  # Summary block fields missing → skip

    reports = sorted(audit_dir.rglob("*code_audit*.md"))
    if not reports:
        return
    rp = reports[-1]
    rel = rp.relative_to(audit_dir)
    rtext = read_text(rp)
    m = re.search(r"^#{2,4}\s*4\.6\)", rtext, re.M)
    sec = rtext[m.start():] if m else rtext  # Fall back to the full text when there is no §4.6 heading (field names do not overlap)
    r_decision = parse_field(sec, "final_anchor_decision")
    r_counts = parse_count_dict(sec, "final_anchor_checklist_counts")
    if r_decision is None and r_counts is None:
        return  # Final report did not write back §4.6 → skip

    if decision is not None and r_decision is not None and decision != r_decision:
        add(cid, "WARN", "final_anchor_decision inconsistent: checklist=%s vs final report §4.6=%s"
            % (decision, r_decision), file=rel,
            fix="Write back the final report §4.6 final_anchor_decision per the checklist "
                "summary block; the two must be identical field by field")
    if r_counts is not None:
        declared = {"PASS": c_pass, "BLOCKED": c_blocked, "PENDING": c_pending}
        diffs = {k: (r_counts.get(k, 0), int(v)) for k, v in declared.items()
                 if v is not None and r_counts.get(k, 0) != int(v)}
        if diffs:
            add(cid, "WARN", "final_anchor_checklist_counts does not match the checklist summary "
                "counts: %s"
                % _fmt_count_diffs(diffs), file=rel,
                fix="Write back the final report §4.6 final_anchor_checklist_counts="
                    "{PASS, BLOCKED, PENDING} per the quality/final_anchor_checklist_*.md "
                    "summary block")


def check_consistency_merge_marker(audit_dir):
    """U: coverage_consistency_check standalone artifact / merge marker probing (P1-8).

    Contract (DOTNET_ROUTE_OUTPUT_TEMPLATES.md §8 dual-stack isomorphism (mandatory)):
    when there is no standalone coverage_consistency_check_*.md, the merged file
    must contain the marker line
    `MERGED_FROM: coverage_consistency_check_{timestamp}.md`; neither present is
    treated as a missing artifact.
    """
    cid = "U_consistency_merge_marker"
    quality = audit_dir / "quality"
    if not quality.is_dir():
        return
    if any(quality.glob("coverage_consistency_check_*.md")):
        return  # Standalone file exists → pass (produces no record, keeping the baseline summary stable)
    for f in sorted(quality.rglob("*.md")):
        if "MERGED_FROM: coverage_consistency_check" in read_text(f):
            return  # Merge marker exists → pass
    add(cid, "WARN", "quality/ has no standalone coverage_consistency_check_*.md, and none of "
        "the quality files contains a MERGED_FROM: coverage_consistency_check merge "
        "marker line (P1-8 merge marker format); treated as a missing artifact",
        file=quality,
        fix="Per DOTNET_ROUTE_OUTPUT_TEMPLATES.md §8, persist a standalone "
            "coverage_consistency_check_{timestamp}.md; if merging is truly necessary, add "
            "the marker line MERGED_FROM: coverage_consistency_check_{timestamp}.md and "
            "MERGE_REASON: {merge reason} to the merged file, and the merged path must "
            "still be registered in the manifest")


# ---------------------------------------------------------------- Checks V/W: pending_pool reconciliation and dispatch verification (P1-7)

def check_pending_pool_reconciliation(audit_dir):
    """V: pending_pool single source of truth pool_total vs the final report risk
    pool count (skip when missing, no WARN).

    Contract (IO_PATH_CONVENTION.md "Pending evidence risk pool single source of
    truth (2026-09-18)" / spec §4.2-§4.3):
    - The single source of truth quality/pending_pool_{timestamp}.md header must
      contain `pool_total: {N}`;
    - The final report "Unclosed Traces / Pending Evidence Risk Pool" section cites
      only the pending_pool counts and paths.
    On the final report side, the count is tried in the order pending_pool_count /
    pool_total / risk_pool_total; if all three are absent, skip (historical
    artifacts are not held accountable).
    """
    cid = "V_pending_pool_reconciliation"
    quality = audit_dir / "quality"
    pool_files = sorted(quality.glob("pending_pool_*.md")) if quality.is_dir() else []
    if not pool_files:
        return  # No pending_pool source artifact → skip
    total = parse_int_field(read_text(pool_files[-1]), "pool_total")
    if total is None:
        return  # Source header field missing → skip

    reports = sorted(audit_dir.rglob("*code_audit*.md"))
    if not reports:
        return
    rp = reports[-1]
    rel = rp.relative_to(audit_dir)
    rtext = read_text(rp)
    rep_total = None
    for field in ("pending_pool_count", "pool_total", "risk_pool_total"):
        v = parse_int_field(rtext, field)
        if v is not None:
            rep_total = int(v)
            break
    if rep_total is None:
        return  # Final report does not cite a risk pool count → skip

    if rep_total != int(total):
        add(cid, "WARN",
            "Final report risk pool count=%d does not match the pending_pool pool_total=%d"
            % (rep_total, int(total)), file=rel,
            fix="Write back the final report risk pool section per the pool_total of "
                "quality/pending_pool_{timestamp}.md; the final report cites only the "
                "pending_pool counts and paths (IO_PATH_CONVENTION.md pending evidence risk "
                "pool single source of truth)")


def check_dispatch_roster(audit_dir):
    """W: existence of the Specialty Dispatch Verification section in
    vuln_audit/index (skip when the index is missing, no WARN).

    Contract (IO_PATH_CONVENTION.md vulnerability specialty state model section /
    spec §7): the vulnerability index (vuln_audit/index_{timestamp}.md) must contain
    a "## Specialty Dispatch Verification" section, checking off every ACTIVE
    specialty of PHASE_STATUS one by one (three states: triggered / negative
    evidence / not applicable).
    This check only does "verification section existence"; reconciling the number
    of ACTIVE specialties with the number of check rows is not yet implemented
    (PHASE_STATUS table parsing is left to a later round), as noted in this
    docstring.
    """
    cid = "W_dispatch_verification"
    va_dir = audit_dir / "vuln_audit"
    files = sorted(va_dir.glob("index_*.md")) if va_dir.is_dir() else []
    if not files:
        return  # No vuln_audit/index artifact → skip
    for p in files:
        if "## Specialty Dispatch Verification" in read_text(p):
            continue
        add(cid, "WARN", "vuln_audit/index is missing the '## Specialty Dispatch "
            "Verification' section",
            file=p.relative_to(audit_dir),
            fix="Per the IO_PATH_CONVENTION.md vulnerability specialty state model section, "
                "add the '## Specialty Dispatch Verification' section: check off every "
                "ACTIVE specialty of PHASE_STATUS one by one (three states: triggered / "
                "negative evidence / not applicable); bare wording such as 'not triggered' "
                "or 'not executed' is forbidden")


# ---------------------------------------------------------------- Report and entry

def print_human_report(audit_dir):
    level_mark = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}
    print("=" * 72)
    print(".NET Audit Output Gate Validation Report")
    print("Audit output directory: %s" % audit_dir)
    print("=" * 72)
    current = None
    for r in RESULTS:
        if r["check"] != current:
            current = r["check"]
            print("\n■ Check %s" % current)
        loc = ""
        if r["file"]:
            loc = "  @ %s" % r["file"]
            if r["line"]:
                loc += ":%d" % r["line"]
        print("  %s %s%s" % (level_mark[r["level"]], r["message"], loc))
        if r["level"] == "FAIL" and r["fix"]:
            print("         Fix suggestion: %s" % r["fix"])

    counts = {lv: sum(1 for r in RESULTS if r["level"] == lv) for lv in ("PASS", "FAIL", "WARN")}
    print("\n" + "-" * 72)
    print("Summary: PASS=%d  FAIL=%d  WARN=%d" % (counts["PASS"], counts["FAIL"], counts["WARN"]))
    verdict = "FAILs exist; the gate did not pass" if counts["FAIL"] else "No FAIL (WARNs do not block delivery, but need review)"
    print("Verdict: %s" % verdict)
    print("-" * 72)
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=".NET white-box security audit output directory gate validation "
                    "(trace contract / placeholders / gate consistency / final report / "
                    "degradation semantics / stage directories)")
    ap.add_argument("audit_output_dir", help="The output directory of one audit run")
    ap.add_argument("--stack", default="auto", choices=["auto", "dotnet", "node", "fullstack"],
                    help="Audit stack type (auto: probe the output tree; dotnet keeps the "
                         "existing single-stack behavior)")
    ap.add_argument("--skill-root", default=None,
                    help="Skill library root (default: the parent directory of the script's "
                         "directory)")
    ap.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = ap.parse_args(argv)

    audit_dir = Path(args.audit_output_dir)
    if not audit_dir.is_dir():
        print("Error: audit output directory does not exist or is not a directory: %s"
              % audit_dir, file=sys.stderr)
        return 2

    skill_root = Path(args.skill_root) if args.skill_root else Path(__file__).resolve().parent.parent
    evid_ids, evid_path = load_evid_ids(skill_root)
    if evid_ids is None:
        print("Error: cannot read the EVID dictionary: %s (use --skill-root to specify the "
              "skill library root)" % evid_path,
              file=sys.stderr)
        return 2

    stack = args.stack if args.stack != "auto" else detect_stack(audit_dir)
    if stack == "fullstack":
        dotnet_dir = audit_dir / "dotnet"
        node_dir = audit_dir / "node"
        if dotnet_dir.is_dir():
            route_status = check_trace_contract(dotnet_dir, evid_ids)
            check_placeholders(dotnet_dir)
            check_gate_consistency(dotnet_dir)
            check_final_report(dotnet_dir, evid_ids)
            check_downgrade_semantics(dotnet_dir, route_status)
            check_stage_dirs(dotnet_dir)
            check_route_count_reconciliation(dotnet_dir)
            check_exploit_count_reconciliation(dotnet_dir)
            check_final_anchor_reconciliation(dotnet_dir)
            check_consistency_merge_marker(dotnet_dir)
            check_pending_pool_reconciliation(dotnet_dir)
            check_dispatch_roster(dotnet_dir)
        else:
            add("F_fullstack_four_states", "WARN", "The fullstack output tree lacks the dotnet/ subtree",
                file=dotnet_dir)
        if node_dir.is_dir():
            check_node_trace_contract(node_dir, evid_ids)
            check_placeholders(node_dir)
            check_gate_consistency(node_dir)
            check_final_report(node_dir, evid_ids)
            check_stage_dirs(node_dir)
            check_route_count_reconciliation(node_dir)
            check_exploit_count_reconciliation(node_dir)
            check_final_anchor_reconciliation(node_dir)
            check_consistency_merge_marker(node_dir)
            check_pending_pool_reconciliation(node_dir)
            check_dispatch_roster(node_dir)
        else:
            add("F_fullstack_four_states", "WARN", "The fullstack output tree lacks the node/ subtree",
                file=node_dir)
        check_fullstack_statuses(audit_dir)
        check_contract_gate_counts(audit_dir / "cross")
        check_exploit_count_reconciliation(audit_dir / "cross")
        check_placeholders(audit_dir / "cross")
    elif stack == "node":
        check_node_trace_contract(audit_dir, evid_ids)
        check_placeholders(audit_dir)
        check_gate_consistency(audit_dir)
        check_final_report(audit_dir, evid_ids)
        check_stage_dirs(audit_dir)
        check_route_count_reconciliation(audit_dir)
        check_exploit_count_reconciliation(audit_dir)
        check_final_anchor_reconciliation(audit_dir)
        check_consistency_merge_marker(audit_dir)
        check_pending_pool_reconciliation(audit_dir)
        check_dispatch_roster(audit_dir)
    else:  # dotnet (existing behavior, kept for regression)
        route_status = check_trace_contract(audit_dir, evid_ids)
        check_placeholders(audit_dir)
        check_gate_consistency(audit_dir)
        check_final_report(audit_dir, evid_ids)
        check_downgrade_semantics(audit_dir, route_status)
        check_stage_dirs(audit_dir)
        check_route_count_reconciliation(audit_dir)
        check_exploit_count_reconciliation(audit_dir)
        check_final_anchor_reconciliation(audit_dir)
        check_consistency_merge_marker(audit_dir)
        check_pending_pool_reconciliation(audit_dir)
        check_dispatch_roster(audit_dir)

    counts = {lv: sum(1 for r in RESULTS if r["level"] == lv) for lv in ("PASS", "FAIL", "WARN")}
    exit_code = 1 if counts["FAIL"] else 0

    if args.json:
        print(json.dumps({
            "audit_dir": str(audit_dir),
            "stack": stack,
            "skill_root": str(skill_root),
            "evid_dict": str(evid_path),
            "summary": counts,
            "exit_code": exit_code,
            "results": RESULTS,
        }, ensure_ascii=False, indent=2))
    else:
        print_human_report(audit_dir)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
