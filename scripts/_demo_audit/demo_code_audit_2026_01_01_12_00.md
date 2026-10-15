# Demo Project .NET Code Audit Report

Generated at: 2026_01_01_12_00

## Quality Report Section (Fixed)

### 1) Dual Completion-State Declaration
- audit_surface_status: PARTIAL
- api_coverage_status: PARTIAL
- coverage_mode: FULL

### 2) Coverage Gate Summary
- api_coverage_percent: 80%
- pipeline_execution: COMPLETED
- gate_decision: ALLOW_COMPLETED
- gate_reason: ${gate_reason_text}
- unmapped_routes_source: N/A

### 3) Coverage Wording Declaration (Must Be Retained)
- This report represents conclusions for "mapped entries" only, and does not represent conclusions for the full active APIs.

### 4.6) Closing Anchor Check Result References
- final_anchor_checklist_source: quality/final_anchor_checklist_2026_01_01_12_00.md
- final_anchor_decision: PASS
- final_anchor_checklist_counts: {PASS:5, BLOCKED:0, PENDING:0}
- exploit_chain_consistency_check_counts: {PASS:2, BLOCKED:0, N/A:0}

### 6) Vulnerability List Overview

#### Verification PoC

```http
GET /api/user/${user_id} HTTP/1.1
Host: {host}
Cookie: {{session_cookie}}
```

### 7) Unclosed Traces / Pending Evidence Risk Pool

- R0002: trace_status=UNRESOLVED, missing sink evidence EVID_SQL_FAKE_POINT; a SINK_ONLY static deep audit is suggested.

<!-- Demo issues:
  1. ${gate_reason_text}, ${user_id}, {{session_cookie}} placeholder residue → check B FAIL
  2. api_coverage_status=PARTIAL but no unmapped_routes_*.md under quality/ → check D FAIL
  3. EVID_SQL_FAKE_POINT not registered → check D FAIL
-->
