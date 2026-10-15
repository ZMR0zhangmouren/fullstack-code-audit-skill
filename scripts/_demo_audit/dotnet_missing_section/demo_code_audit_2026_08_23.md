# Demo Project .NET Code Audit Report

Generated at: 2026_08_23_12_00

## Quality Report Section (Fixed)

### 1) Dual Completion-State Declaration
- audit_surface_status: COMPLETE
- api_coverage_status: COMPLETE
- coverage_mode: FULL

### 2) Coverage Gate Summary
- api_coverage_percent: 100%
- pipeline_execution: COMPLETED
- gate_decision: ALLOW_COMPLETED
- gate_reason: Full mapping completed
- unmapped_routes_source: N/A

### 3) Coverage Wording Declaration (Must Be Retained)
- This report represents conclusions for "mapped entries" only, and does not represent conclusions for the full active APIs.

### 6) Vulnerability List Overview

| ID | Vulnerability | Severity | route_id | Exploitability |
|------|------|----------|----------|----------|
| H-SQL-001 | SQL injection in the user query endpoint | 🟠 (CVSS 8.1) | R1 | ✅ Confirmed |

- Evidence: EVID_SQL_EXEC_POINT

<!-- Compliant file (dotnet_missing_section): ensures check D passes, keeping the FAIL attribution single -->
