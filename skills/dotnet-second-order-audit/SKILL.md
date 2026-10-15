---
name: dotnet-second-order-audit
description: .NET second-order injection audit. Identifies injection risks triggered a second time after data storage (second-trigger stored XSS, second-execution SQL injection, second-access file operations, etc.), traces data flows from storage entry to trigger entry, and outputs grading, evidence, and remediation suggestions.
---

# .NET Second-Order Injection Audit

## Shared Grabber Index References

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as this Skill's base retrieval index
- By default, use shared/DOTNET_SINK_REFERENCE.md as this specialty's sink type definition and trace-gate validation baseline
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover the following Second-Order-related shared grabbers:
  - **Entry definition grabbers**: Controller Actions, Minimal API Endpoints, SignalR Hubs, BackgroundJob/HostedService
  - **Sensitive operation grabbers**: SQL execution, file operations, command execution, template rendering, serialization operations
  - **Business execution grabbers**: database writes, cache writes, session storage, cookie storage, file writes
  - **Pre-control grabbers**: Authorize, AllowAnonymous, ActionFilter, data validation
- If the project has a data storage abstraction layer (Repository, UnitOfWork, Cache Service, Message Queue), it must be added to the in-project grabbers section of the output

## Input Dependencies

- Required: `source_path`
- Required: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to align route_ids of storage entries and trigger entries)
- Required: `route_tracer/*_{timestamp}.md` (used to trace the complete data flow from storage to trigger)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to supplement authorization state differences between storage entries and trigger entries)
- Optional: `framework_audit/*_{timestamp}.md` (used to supplement Session, Cache, and BackgroundJob configuration)
- This specialty is a **cross-entry trace-gate type**; the complete data flow from storage entry to trigger entry must be traced
- Multiple route_ids in `route_mapping` must be analyzed simultaneously to discover storage-trigger pairings

## Key Checks

### 1. Second-Trigger of Stored XSS

- **Storage entry**: user input written to databases, sessions, cookies, caches, or files
- **Trigger entry**: read from the storage backend and rendered into View / JSON / HTML responses
- Common scenarios:
  - User profile updates displayed globally afterwards
  - Comments/posts displayed in bulk on list pages after publication
  - Global broadcast when message notifications are rendered
  - Rich text editor content saved and output without HTML sanitization

### 2. Second-Execution of SQL Injection

- **Storage entry**: user input written to a database field
- **Trigger entry**: that field is used as part of a subsequent SQL query (not as a bound parameter)
- Common scenarios:
  - Dynamic column/table names: column names read from config tables and concatenated into SQL
  - Dynamic sort fields: ORDER BY parameters from database configuration
  - Report generation: database-stored SQL fragments executed again
  - Dynamic filters: stored filter rules concatenated directly into SQL

### 3. Second-Execution of Command Injection

- **Storage entry**: file names/paths written to the database
- **Trigger entry**: that path is used in `Process.Start` or shell execution
- Common scenarios:
  - File processing queues: database-stored file paths read and executed by subsequent Jobs
  - Image processing: database-stored image paths processed by ImageMagick/FFmpeg
  - Log analysis: database-stored log file paths processed by tail/grep

### 4. Second-Access of File Operations

- **Storage entry**: user-uploaded files with paths/content written to the database
- **Trigger entry**: paths used in `File.ReadAllText`, `PhysicalFile`, `StaticFiles`
- Common scenarios:
  - Dynamic resource loading: file paths read from the database then returned as static files
  - Template file management: database-stored template paths loaded by Razor/Roslyn
  - Configuration hot-reload: database-stored configuration paths loaded by Configuration

### 5. Persistence of Reflected Vulnerabilities

- **Storage entry**: dangerous input written to Session/Cache/database
- **Trigger entry**: subsequent requests read from storage and trigger dangerous operations
- Common scenarios:
  - ViewState / serialized object persistence: stored dangerous objects deserialized in subsequent requests
  - Privilege escalation: cached roles/Claims used in subsequent requests
  - Path traversal: stored file paths accessed in subsequent requests

### 6. Second Processing by Message Queues/Caches

- **Storage entry**: messages/cache written to Message Queues, Redis, MemoryCache
- **Trigger entry**: Consumers read from the queue and execute dangerous operations
- Common scenarios:
  - Async task queues: stored task parameters executed by BackgroundJob
  - Publish-subscribe patterns: stored message content processed by multiple subscribers
  - Cache invalidation triggers: stored cache keys used by Dependency Injection

### 7. Storage-Entry and Trigger-Entry Pairing Analysis

- **Storage entry identification**: DB Write, Cache Set, File Write, Session Set
- **Trigger entry identification**: DB Read, Cache Get, File Read, Session Get
- **Data flow tracing**: from the storage point through propagation paths to the trigger point
- **Trust boundary difference**: whether the storage entry requires authorization vs whether the trigger entry requires authorization

## Enumeration Rules (Mandatory Refinement)

### Storage Entry Enumeration

Search keywords:
- `INSERT`, `UPDATE`, `SaveChanges`, `ExecuteSqlRaw` (write scenarios)
- `Add`, `Update`, `Remove` (EF Core)
- `SetString`, `SetObject` (Redis)
- `Set`, `Add` (MemoryCache / IMemoryCache)
- `Session.SetString`, `Session.SetObject`
- `Response.Cookies.Append` (cookie writes)
- `File.WriteAllText`, `File.WriteAllBytes`, `CopyToAsync`
- `StreamWriter.Write`
- `JsonSerializer.Serialize` (write scenarios)

Enumeration record requirements:
- Record the entry route_id of each write operation
- Record the source of written data (user input, computed, mixed)
- Record the write target (database table/field, cache key, file path, session key)
- Record whether input sanitization before writing is missing

### Trigger Entry Enumeration

Search keywords:
- `SELECT`, `Query`, `FromSqlRaw`, `ExecuteSqlQuery` (read scenarios)
- `Find`, `FirstOrDefault`, `SingleOrDefault`, `ToList`
- `GetString`, `GetObject` (Redis)
- `Get`, `TryGetValue` (MemoryCache)
- `Session.GetString`, `Session.GetObject`
- `Request.Cookies`
- `File.ReadAllText`, `File.ReadAllBytes`, `OpenRead`
- `StreamReader.Read`
- `JsonSerializer.Deserialize`

Enumeration record requirements:
- Record the entry route_id of each read operation
- Record where read data flows (template rendering, SQL concatenation, command execution, file access, serialization)
- Record whether read data is sanitized or parameterized
- Record whether authorization is required at trigger time

### Storage-Trigger Pairing Enumeration

Search keyword combinations:
- Database table names (the table written at storage time = the table read at trigger time)
- Cache key patterns
- Session key patterns
- File path patterns
- Message queue topics / channels

Enumeration record requirements:
- Build the complete chain: storage entry → data propagation path → trigger entry
- Record trust boundary differences (storage entry authorization state vs trigger entry authorization state)
- Record whether data undergoes intermediate transformation or persistence
- Assess the exploitability of each pairing

### Missing Input Sanitization Enumeration

Search keywords:
- `Html.Raw`, `MarkupString`, `@Html.Raw`
- `innerHTML`, `textContent`
- `Dynamic` + SQL fragment concatenation
- String-concatenated SQL (not in parameter binding)
- `Process.Start` + string paths
- `eval`, `Execute`, `DynamicExpression`

Enumeration record requirements:
- Record each combination point where unsanitized input enters a dangerous operation
- Record missing or ineffective sanitization scenarios
- Assess the correlation between missing sanitization and storage-trigger pairings

### Async/Background Processing Enumeration

Search keywords:
- `BackgroundService`
- `IHostedService`
- `IConsumer`, `Handle` (MassTransit / MediatR)
- `Publish` (message publishing)
- `Enqueue`, `QueueBackgroundWorkItem`
- `Hangfire`, `Quartz`
- `IBackgroundTask`, `PeriodicTimer`
- `Channel<T>.Reader`

Enumeration record requirements:
- Record the trigger source of background jobs (time-driven, event-driven, manual)
- Record the data sources read during background processing (database, cache, files)
- Record dangerous operations in background processing (SQL, commands, files, templates)
- Assess dangerous data flows in message queues

## Evidence References

### Second-Order Data Chain Core Concepts (New)

Second-order injection is not as simple as "stored then triggered". The different responsibilities of the two entries must be distinguished:

| Entry Type | Responsibility | Verification Question |
|---------|------|---------|
| `source_write_entry` | Where does the dangerous data come from; is it attacker-controlled | Can the attacker control it through a real write boundary? |
| `source_trigger_entry` | When is it read; who triggers it | When is the stored value read? Who is the trigger? |

### Three-Layer Verification Conditions (Mandatory)

Every second-order injection conclusion must verify the following three conditions layer by layer:

**Layer 1: Data chain holds**
- The attacker can control data writes
- The write path reaches persistent storage

**Layer 2: Trigger path holds**
- The stored value reaches the sink along the execution path
- The trigger entry's permission/identity differs from the write entry (trust boundary difference)

**Layer 3: Syntax permits injection**
- The database/command/template syntax allows closing boundaries and re-entering structure
- E.g.: SQL allows backtick closing, commands allow separators

### Evidence Points

- `EVID_SECOND_ORDER_STORAGE`: evidence of data second storage
- `EVID_SECOND_ORDER_TRIGGER`: evidence of second-trigger execution
- `EVID_SECOND_ORDER_STORE_ENTRANCE`: evidence of the storage entry point
- `EVID_SECOND_ORDER_TRIGGER_ENTRANCE`: evidence of the trigger entry point
- `EVID_SECOND_ORDER_DATA_FLOW_MAPPING`: evidence of the data flow mapping from storage to trigger

### taint_nodes Step-by-Step Records (New)

Aligned with `taint_nodes` in `DOTNET_ROUTE_OUTPUT_TEMPLATES.md`; every second-order chain must record:

```json
{
  "taint_nodes": [
    {
      "taint_type": "source_write_entry",
      "filepath": "Controllers/ConfigController.cs",
      "line_range": "45-48",
      "description": "User writes column_key via the SaveFieldConfig interface",
      "is_attacker_controllable": true,
      "write_permission": "business_config_manager"
    },
    {
      "taint_type": "storage_read",
      "filepath": "Services/SearchService.cs",
      "line_range": "30-33",
      "description": "Reads column_key from the field_config table"
    },
    {
      "taint_type": "source_trigger_entry",
      "filepath": "Controllers/SearchController.cs",
      "line_range": "20-25",
      "description": "Search request triggers reading the config table",
      "trigger_condition": "User initiates a search request",
      "trigger_permission": "anonymous_or_authenticated"
    },
    {
      "taint_type": "transfer",
      "filepath": "Services/SearchService.cs",
      "line_range": "40-44",
      "description": "column_key is concatenated into the SQL query condition"
    },
    {
      "taint_type": "barrier",
      "line_range": "40-44",
      "barrier_type": "column_whitelist",
      "actual_behavior": "no whitelist validation",
      "status": "FAILED"
    },
    {
      "taint_type": "sink",
      "filepath": "Services/SearchService.cs",
      "line_range": "45-48",
      "description": "SQL execution: column_key enters the column identifier position"
    }
  ]
}
```

## Failure and Degradation Branches (Mandatory, by Three-Layer Verification)

| Trigger Condition | Layer | First-Line Handling | Fallback if Still Failing |
|---|---|---|---|
| source_write_entry cannot be proven attacker-controllable | Layer 1 | Output write evidence and permission boundary analysis | Mark `Layer 1 not established`, degrade to `⚠️Pending Verification` |
| Cannot confirm persistence after data write | Layer 1 | Trace storage medium write confirmation | Mark `data chain not closed`, degrade to `⚠️Pending Verification` |
| source_trigger_entry trigger timing unconfirmable | Layer 2 | Output trigger evidence and candidate trigger points | Mark `Layer 2 not established`, degrade to `⚠️Pending Verification` |
| Storage and trigger permission boundaries identical (no trust difference) | Layer 2 | Output permission comparison analysis | Risk downgraded; not marked as over-privileged second-order injection |
| Syntax does not permit closing boundaries (e.g. parameterized queries) | Layer 3 | Output syntax analysis | Mark `Layer 3 not established`, rule out injection possibility |
| Async/queue consumption chain cannot be reconstructed | Cross-layer | Output delivery point and consumption point candidate sets | Explicitly mark "Environment-Dependent / runtime-dependent"; confirmed conclusions are forbidden |

🔴 **STOP: when any of the three-layer verification conditions is not met, marking as confirmed second-order injection is forbidden.**

### Three-Layer Verification Determination Matrix

| Layer 1 | Layer 2 | Layer 3 | Conclusion |
|--------|--------|--------|------|
| ✅ Holds | ✅ Holds | ✅ Holds | 🔴 Confirmed second-order injection |
| ✅ Holds | ✅ Holds | ❌ Not established | ⚠️ Pending Verification (syntax unconfirmed) |
| ✅ Holds | ❌ Not established | - | ⚠️ Pending Verification (trigger path not closed) |
| ❌ Not established | - | - | ⚠️ Pending Verification (write boundary unconfirmed) |
| ⚠️ Partial | ⚠️ Partial | ⚠️ Partial | ⚠️ Pending Verification (multi-layer gaps) |

## Barrier Verification Matrix (Mandatory, Complementary to the Three-Layer Verification)

On top of the three-layer verification, this specialty must perform verification on the following barrier types, assessed against the fail-close standard in `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Pre-write sanitization** | Confirm whether `source_write_entry` performs input sanitization (e.g. HTML encoding, SQL parameterization, path validation) before writing to persistent storage | Fail-close sanitization present → Layer 1 may not hold; no sanitization or fail-open sanitization → Layer 1 holds |
| **Post-read sanitization** | Confirm whether `source_trigger_entry` performs secondary sanitization after reading from storage | Fail-close secondary sanitization present → Layer 3 may not hold; no secondary sanitization → Layer 3 needs priority assessment |
| **Storage-trigger trust boundary difference** | Compare the authorization requirements of the storage entry and trigger entry, confirming whether a trust boundary difference exists | Storage requires high privilege but trigger is low-privilege/anonymous → 🔴 High-risk; identical permissions → risk downgraded |
| **Persistent storage isolation** | Confirm whether database/cache/file storage has tenant/user isolation, and whether attacker data can be triggered by the target user | No isolation → 🔴 High-risk; strict isolation → risk downgraded |
| **Background task execution privilege** | Confirm the execution account privileges of BackgroundJob/Queue Consumers, and whether they are higher than web entries | High-privilege execution → 🔴 High-risk amplification; same or lower privilege → normal assessment |
| **Syntax closure verification (Layer 3)** | Confirm whether the target sink's syntax allows closing boundaries and re-entering structure (e.g. SQL backticks, HTML tag closing, command separators) | Syntax permits closing → Layer 3 holds; strictly parameterized syntax → Layer 3 not established |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion "Confirmed Safe" or "False Positive" is forbidden.**

## Two-Phase Determination (Mandatory)

Follow the two-phase determination flow in `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

1. **Phase 1 (Interim Conclusion)**: for each storage-trigger pairing, first mark `Confirmed Vulnerability Candidate` / `Pending Confirmation` / `False Positive`
2. **Phase 2 (Mandatory Evidence Chasing)**:
   - If Phase 1 is `Confirmed Vulnerability Candidate` → the three-layer verification + all relevant items of the Barrier Verification Matrix must be completed and passed before marking `Confirmed`
   - If Phase 1 is `Pending Confirmation` → at least one more hop of the call chain or downstream parser must be traced until a determination is possible
   - If Phase 2 still cannot close the case → keep `Pending Confirmation`, and explicitly record which layer / which hop of evidence is missing

## Testing Suggestions (Mandatory)

Follow the testing requirements in `DOTNET_AUDIT_EXECUTION_STANDARD.md`; for each confirmed vulnerability or pending-verification item provide:

- **Positive test**: construct a second-order injection PoC (step 1: write malicious data via the storage entry; step 2: trigger execution via the trigger entry) to verify the vulnerability actually exists
  - Stored XSS: write `<script>alert(1)</script>`, then view the trigger page
  - SQL second-order injection: write a malicious column name, then trigger a report query
  - Command second-order injection: write a malicious path, then trigger backend file processing
- **Negative test**: construct input intercepted by a barrier (e.g. pre-write sanitization in effect, post-read secondary sanitization in effect, syntax does not permit closing) to verify the protection is effective
- **Regression test**: retest after remediation, confirming the barrier still works and no new bypass path is introduced

Test cases must be annotated with `test_id` and linked to the corresponding hit ID in the audit report.

## Resource References & Reachability Validation (Mandatory)

- Required shared index references: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber sources) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: on-disk paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from the directory structure are not allowed.
- Evidence consistency validation: if severity-graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: before submission, confirm at least once that key referenced files are accessible (e.g. `DOTNET_AUDIT_GRABBER_INDEX.md`, `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Each skill must maintain at least 2 typical test cases (happy path + one complex scenario), and annotate the case ID in the results.
- Each evaluation round must execute `full_test` for at least 1 case; if only `dry_run` is possible, `dry_run_reason` and a make-up test plan must be recorded.
- Pass criteria must simultaneously satisfy: `intent achieved`, `key evidence hit`, `output format compliant`; if any one is not met, "pass" must not be given.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `Input Constraints` → `Execution Steps` → `Output and Acceptance`; no layer may be missing or mixed across layers.
- A single paragraph should not exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into a single source-of-truth section.
- AI-isms and empty filler transitions are forbidden (e.g. "first/second/finally/in summary/put simply/in other words"); any found must be rewritten as executable statements.

## Quality Gate & Assessment Consistency (Mandatory)

- A minimal gate self-check must be executed before producing output: `input completeness`, `key evidence hit`, `output path valid` — all three must be PASS.
- If any of `key evidence missing`, `chain not closed`, `consistency_check_status=BLOCKED` holds, the conclusion must be degraded to `BLOCKED`; outputting "confirmed exploitable/deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with the `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

| # | Anti-Pattern | Why Not | Correct Approach |
|---|---|---|---|
| 1 | Drawing a vulnerability conclusion upon finding only a storage point | Second-order requires all three layers of verification to hold | Verify source_write_entry, source_trigger_entry, and permitted syntax simultaneously |
| 2 | Ignoring the permission difference between source_write_entry and source_trigger_entry | Risk strength will be over- or underestimated | Record permission/tenant boundary differences and assess trust boundary transfer |
| 3 | Ignoring async consumption chains | Real triggers often happen in background tasks | Delivery-consumption chains must be listed |
| 4 | Not verifying whether syntax permits injection | Even with controllable data and a reachable path, injection is impossible if syntax does not permit it | Confirm database/command/template syntax allows closing boundaries |
| 5 | Conflating source_write_entry and source_trigger_entry | The writer ≠ the trigger; responsibilities differ | Record and verify separately |
| 6 | Considering second-order established upon seeing storage → read → sink | The trigger entry lacks independent verification | The trigger entry's trigger conditions and triggerer identity must be verified |

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (e.g. `route_mapping` / `route_tracer` / `framework_audit`), confirm dependencies are available and timestamps are consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: write to the agreed path per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing-evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (source_write_entry Confirmation)**: must confirm whether the attacker can control data through a real write boundary; record write permissions and attack surface.
- 🔴 **CHECKPOINT B (storage_read Confirmation)**: must confirm data is successfully read from persistent storage; record read paths and intermediate propagation nodes.
- 🔴 **CHECKPOINT C (source_trigger_entry Confirmation)**: must confirm the trigger entry's permission/identity differs from the write entry (trust boundary difference); record trigger conditions and triggerer.
- 🔴 **CHECKPOINT D (Syntax Permitted Confirmation)**: must confirm the database/command/template syntax allows closing boundaries and re-entering structure (e.g. SQL backtick closing).
- 🛑 **STOP**: if any of the three-layer verification conditions is not met, neither a "second-order injection does not hold" nor a "confirmed second-order injection" conclusion is allowed; only `⚠️Pending Verification` may be marked.

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion level: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose exactly one; leaving blank is forbidden).
- Minimum evidence set: must include at least the five items `entry point`, `controllable parameters`, `key calls`, `security boundary`, `missing evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softening wording is forbidden: e.g. "possibly at risk / worth noting / depends on the situation / very likely"; when evidence is insufficient, must explicitly write `⚠️Pending Verification` and the next follow-up confirmation action.

Minimal output snippet (directly reusable):

```md
- Hit ID: M{hash} (file path fragment + line number + sequence number, for cross-phase tracking and regression alignment)
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameters=...; key calls=...; security boundary=...; missing evidence=none
- test_id: T{hash} (associated test case)
- Next action: if gaps exist, supplement parameter propagation evidence for trace_id=...
```
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameters=...; key calls=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement parameter propagation evidence for trace_id=...
```

## Output

- vuln_audit/second-order_{timestamp}.md
- vuln_poc/second-order_{timestamp}.md (Confirmed / Pending Verification / Environment-Dependent PoC)

### Output File Structure

```
vuln_audit/second-order_{timestamp}.md
├── # Second-Order Injection Audit Report
├── ## Summary
│   ├── Number of findings
│   ├── High-risk item list
│   └── Storage-trigger pairing statistics
├── ## Storage-Trigger Pairing Analysis
│   ├── Pairing list (storage entry, trigger entry, danger type, route_id)
│   ├── Trust boundary difference assessment
│   ├── Exploitability assessment
│   └── taint_nodes step-by-step records (each pairing must include the complete taint_nodes JSON)
├── ## Second-Trigger of Stored XSS
│   ├── Pairing details (with taint_nodes)
│   ├── Data flow path
│   └── Risk rating
├── ## SQL Second-Order Injection
│   ├── Pairing details (with taint_nodes)
│   ├── Dynamic column/table name analysis
│   └── Risk rating
├── ## Command Second-Order Injection
│   ├── Pairing details (with taint_nodes)
│   ├── File path propagation path
│   └── Risk rating
├── ## Second-Access of File Operations
│   ├── Pairing details (with taint_nodes)
│   ├── Path propagation path
│   └── Risk rating
├── ## Persistence of Reflected Vulnerabilities
│   ├── Pairing details (with taint_nodes)
│   ├── Deserialization chain
│   └── Risk rating
├── ## Second Processing by Message Queues/Caches
│   ├── Pairing details (with taint_nodes)
│   ├── Async data flow
│   └── Risk rating
├── ## Async/Background Processing Analysis
│   ├── BackgroundJob list
│   ├── Trigger source analysis
│   └── Dangerous operation assessment
├── ## In-Project Grabber Supplements
│   ├── Private encapsulation
│   ├── Data access layer
│   └── Message queue configuration
└── ## Remediation Suggestions
    ├── Input sanitization strengthening
    ├── Data isolation suggestions
    ├── Async processing security hardening
    └── Monitoring and alerting suggestions
```

### vuln_poc Structure

```
vuln_poc/second-order_{timestamp}.md
├── # Second-Order Injection PoC Templates
├── ## Stored XSS PoC
│   ├── Step 1: Storage phase (route_id + request template)
│   ├── Step 2: Trigger phase (route_id + request template)
│   └── Expected result
├── ## SQL Second-Order Injection PoC
│   ├── Step 1: Write a malicious column name
│   ├── Step 2: Trigger the query
│   └── Expected result
├── ## Command Second-Order Injection PoC
│   ├── Step 1: Store a malicious path
│   ├── Step 2: Trigger command execution
│   └── Expected result
├── ## Message Queue Second-Processing PoC
│   ├── Step 1: Publish a malicious message
│   ├── Step 2: Trigger consumption processing
│   └── Expected result
└── ## Verification Methods
    └── Test steps
```
