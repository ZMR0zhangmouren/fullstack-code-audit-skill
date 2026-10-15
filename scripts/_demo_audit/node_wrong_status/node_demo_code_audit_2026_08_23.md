# node-demo Project Code Audit Report

Generated at: 2026_08_23_12_00

## 1) Dual Completion-State Declaration
- audit_surface_status: COMPLETE
- api_coverage_status: COMPLETE
- coverage_mode: FULL

## 2) Coverage Gate Summary
- api_coverage_percent: 100%
- pipeline_execution: COMPLETED
- gate_decision: ALLOW_COMPLETED
- gate_reason: Full mapping completed
- unmapped_routes_source: N/A

## 3) Coverage Wording Declaration (Must Be Retained)
- This report represents conclusions for "mapped entries" only, and does not represent conclusions for the full active APIs.

## 4.6) Closing Anchor Check Result References
- final_anchor_checklist_source: quality/final_anchor_checklist_2026_01_01_12_00.md
- final_anchor_decision: PASS
- final_anchor_checklist_counts: {PASS:5, BLOCKED:0, PENDING:0}
- exploit_chain_consistency_check_counts: {PASS:2, BLOCKED:0, N/A:0}

## 4) Vulnerability List Overview

| ID | Vulnerability | Severity | route_id | Exploitability |
|------|------|----------|----------|----------|
| H-NOSQL-001 | NoSQL injection in the order query endpoint | 🟠 (CVSS 8.1) | R2 | ✅ Confirmed |

- Evidence: EVID_NODE_NOSQL_QUERY_POINT

<!-- Compliant file (node_wrong_status): ensures check D passes, keeping the FAIL attribution single -->
