---
name: phase-status
description: Single source of truth for P-phase delivery status; the unified reference for "delivery status" cited by pipelines / agents.
---

# PHASE_STATUS — Single Source of Truth for Delivery Status

> All pipelines / agents referencing "P-phase delivery status" must read this file uniformly; scattering time-coupled wording in individual places is forbidden.
> Update trigger: after adding/delivering a skill, this file must be updated in sync (grep the whole repo for `DEFERRED(P` as the rescan action).

| Skill | Delivery Status | Notes |
| ---- | ---- | ---- |
| node-express/koa/fastify/nextjs/nuxt/nestjs/graphql-audit | ACTIVE | Delivered in P2 |
| cross-stack-taint-linker / cross-stack-consistency-audit | ACTIVE | Delivered in P2 |
| node-review-agent | ACTIVE | Delivered in P1 (2026-08-23) |
| node-scan-audit / node-coverage-audit / node-briefing-agent / node-exploit-chain-audit | ACTIVE | Delivered in P3 (2026-09-04) |
| node-codegraph-indexer | ACTIVE | Delivered in P3 (2026-08-23) |
| node vulnerability specialties #27-47 (21 items) | ACTIVE | Delivered in P3 (2026-09-04) |
| dotnet-query-injection-audit | ACTIVE | Delivered in the 2026-09-14 ledger round (approved -> implemented, pending verification) |
| dotnet-spreadsheet-export-audit | ACTIVE | Delivered in the 2026-09-14 ledger round (approved -> implemented, pending verification) |
| dotnet-ai-prompt-audit | ACTIVE | Delivered in the 2026-09-14 ledger round (approved -> implemented, pending verification) |
| node-spreadsheet-export-audit | ACTIVE | Delivered in the 2026-09-14 ledger round (approved -> implemented, pending verification) |
| node-ai-prompt-audit | ACTIVE | Delivered in the 2026-09-14 ledger round (approved -> implemented, pending verification) |
| node-feature-api-mapper | ACTIVE | Delivered in round 43 on 2026-09-19 (approved -> implemented, pending verification) |

**Runtime detection rule**: at execution time, "whether the skill exists" governs — if the corresponding directory is missing under `skills/`, the skill is unavailable → record `NOT_RUN + reason` (or adapt per the degradation instruction); do not pre-judge based on stale time-based wording outside this table.

**Manifest milestone line format (single source of truth)**: `Phase N: DONE ({file count} files, {key status field} | {timestamp})`
Example: `Phase 3: DONE (34 files, api_coverage_status=COMPLETED | 2026-09-17T15:40:00)`
The dotnet / node / fullstack pipelines reference this format; writing literal variants in individual skills is forbidden.
Inline timestamps always use run_timestamp (2026-09-21): in fullstack orchestration mode it is the value issued by the orchestration layer; in single-stack mode it is the timestamp self-produced by the executor — substituting the actual sub-stack start time is forbidden.

**Manifest mapping table format (2026-09-21, mandatory for fullstack)**: in fullstack mode, both sub-stacks' `quality/manifest_*.md` must contain a mapping table of run_timestamp to actual start times, with fixed column headers:

| run_timestamp | Sub-stack Actual Start Time | Deviation (minutes) |
| ---- | ---- | ---- |
| 2026_09_20_10_38 | 2026_09_20_11_45 | +67 |

`Phase 0.7 recheck: AGREE ({hit count}) | {timestamp}` / `Phase 0.7 recheck: MISMATCH ({hit directory count}) | {timestamp}` (negative-conclusion recheck for `design_intent_recheck`; semantics see AUDIT_EXECUTION_COMMON.md §9 rule ⑤)

**Wait-timeout formula (2026-09-20, single source of truth)**: the expected duration for the orchestration layer to wait for a sub-pipeline phase report. In FULL mode, compute `estimated minutes = 2 + (total file count / 1000) × 8` (per thousand files ≈ 8 minutes; e.g., 8110 files ≈ 67 minutes). Rounding rule (2026-09-21): do not round during the computation; round the final result to the nearest minute. Total file count scope (2026-09-21): GC6-excluded directories (`node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`, `coverage/` and lockfile exceptions) are not counted; source code / configuration / frontend assets are counted. If no report is received by timeout → only one proactive check is allowed (do not escalate to periodic disk polling), and the check reason must be recorded in the manifest using the format: `Timeout check: Phase {N} exceeded the estimated {m} minutes without reporting | check reason={...} | {timestamp}`. The fullstack-audit-pipeline references this formula; scattering ad-hoc estimation criteria is forbidden.
