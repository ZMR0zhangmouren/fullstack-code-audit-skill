---
name: dotnet-briefing-agent
description: .NET code audit candidate-parameter checklist generation phase Skill. Generates a non-skippable parameter checklist for each sink, turning "don't miss any parameter" into input that the downstream Taint phase must process item by item. Only lists all parameters; does not judge safety.
---

# .NET Candidate Parameter Checklist (Briefing)

## Objective

Generate a **non-skippable parameter checklist** for each sink, turning "don't miss any parameter" into input that the downstream Taint phase must process item by item.

**Briefing does not judge whether parameters are safe; it only lists them all.**

## Core Principles

- Briefing **only lists parameters; it does not judge safety**
- Every parameter must be annotated with: source, position where it enters the sink, and the barrier to verify downstream
- This checklist is the input to Taint; a missing parameter = downstream verification is impossible

## Inputs

- `scan_audit/scan_{filename}_{timestamp}.md`: risks (including taint_candidates) output by the Scan phase
- `route_mapping/params_{timestamp}.md`: route parameter mapping (if it exists)
- `source_path`: project source code path

## Output Schema

### briefing_{sink_id}_{timestamp}.md

A separate checklist must be generated for each sink:

## Candidate Parameter Checklist

| Candidate Parameter | Parameter Source | Position Where It Enters the Sink | Parameter Type | Follow-up Check (Taint Phase Must Verify) |
|---------|---------|-----------------|---------|---------------------------|
| `column["column_key"]` | Config table read | SQL column identifier position | Structure position | Server-side field whitelist |
| `keyword` | Request Query parameter | LIKE value position | Value position | `escape_like_literal()` actual implementation |
| `category_id` | Request Route parameter | WHERE equality condition | Value position | `strict_int()` actual implementation |
| `sort_key` | Request Query parameter | ORDER BY clause | Structure position | Server-side whitelist mapping |
| `limit` | Request Query parameter | LIMIT clause | Value position | `strict_int()` actual implementation |
| `offset` | Request Query parameter | OFFSET clause | Value position | `strict_int()` actual implementation |

### Parameter Source Classification

| Source Type | Description | Examples |
|---------|------|------|
| `REQUEST` | Directly from the HTTP request | Query, Route, Body, Header, Cookie, Form |
| `CONFIG` | From config file / config table | appsettings.json, database config table |
| `STORAGE_READ` | From persistent storage read | database query results, cache reads, session reads |
| `COMPUTED` | Computed in code | concatenation, conversion, derived fields |
| `CONSTANT` | Hardcoded constant | literal strings, enum values |

### Position Where Parameter Enters the Sink Classification

| Position Type | Description | Risk Level |
|---------|------|---------|
| `VALUE_POSITION` | Value position (e.g. WHERE condition value, LIKE value) | Medium (depends on barrier) |
| `STRUCTURE_POSITION` | Structure position (e.g. column name, table name, ORDER BY) | High (usually no barrier) |
| `DIRECT_SQL_TEXT` | Directly into SQL text | High |
| `COMMAND_ARGUMENT` | Command argument | High |
| `FILE_PATH` | File path | High |
| `URL` | URL / URI | High |
| `TEMPLATE_EXPRESSION` | Template expression | High |

## Handoff to the Downstream Taint Phase

```
Briefing outputs checklist
    → Taint phase verifies each parameter in the checklist item by item
    → Verify STRUCTURE_POSITION parameters with priority
    → Verify actual barrier behavior for VALUE_POSITION parameters
    → Output taint_nodes after verification completes
```

## Anti-Patterns (Forbidden)

- ❌ **Excluding parameters in the Briefing phase**: e.g. "category_id is already handled by strict_int, so don't include it in the checklist"
- ❌ **Missing parameters**: e.g. listing only 2 parameters when the sink actually has 6 dynamic parameters
- ❌ **Vague parameter sources**: e.g. writing "from request" without specifying whether it is Query/Body/Header
- ❌ **Not annotating the entry position**: e.g. writing only the parameter name without saying whether it is a value position or structure position

## Quality Gate

- [ ] Each sink has its own briefing_{sink_id}_{timestamp}.md
- [ ] The checklist lists all dynamic parameters in the sink, with none missing
- [ ] Every parameter has an explicit source, position, and follow-up check item
- [ ] No parameter has been prematurely excluded
- [ ] The checklist is grouped by parameter type (STRUCTURE_POSITION first)

## Output Paths

- `briefing/briefing_{sink_id}_{timestamp}.md` (one per sink)
- `briefing/index_{timestamp}.md` (batch master index)
