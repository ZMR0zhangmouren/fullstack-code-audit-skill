---
name: dotnet-scan-audit
description: .NET code security scanning phase Skill. Responsible for identifying all suspicious sink points in a file while marking inspected safe regions, outputting risks + safe_regions for the downstream Coverage phase to compute uncovered gaps. Only discovers; does not judge whether a risk holds.
---

# .NET Security Scan (Scan)

## Objective

Perform risk-discovery scanning on each source file, **only responsible for discovering suspicious sink points; not judging whether a risk holds**.

Core outputs:
- `risks`: all suspicious sink points in the file and the dynamic parameters involved
- `safe_regions`: code regions that have been inspected and are temporarily considered risk-free

## Core Principles

**Scan is only responsible for discovery, not verification.**

- When you see a sink, **do not rush to judge whether there is an injection**
- Only list the names of all dynamic parameters participating in the sink
- Leave the "is it safe" judgment to the downstream Taint phase
- Both `risks` and `safe_regions` must be output; otherwise Coverage cannot compute gaps

## Shared Grabber Index References

- By default, use `shared/DOTNET_AUDIT_GRABBER_INDEX.md` as this Skill's base retrieval index
- By default, use `shared/DOTNET_SINK_REFERENCE.md` as the sink type definition reference
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)

## Inputs

- `source_path`: .NET project source code path
- `target_file`: the single source file currently being scanned
- `timestamp`: generation timestamp

## Output Schema

Output to the `scan_audit/` directory:

### 1. scan_audit/scan_{filename}_{timestamp}.md

A structured scan report must be output for each scanned file.

#### risks section

Each sink must contain:

| Field | Description | Required |
|------|------|------|
| `sink_type` | Risk type: `SQL_INJECTION` / `CMD_INJECTION` / `SSRF` / `XSS` / `FILE_READ` / `FILE_WRITE` / `DESER` / `XXE` / `SSTI` / `LDAP_INJECTION` / `EXPR_INJECTION` / `XPATH_INJECTION` / `NOSQL_INJECTION` / `AUTH_BYPASS` / `CSRF` / `OPEN_REDIRECT` / `CRLF_INJECTION` / `SECOND_ORDER` / `OTHER` | Yes |
| `line_range` | Code line number range, e.g. `45-52` | Yes |
| `dangerous_call` | Dangerous call code snippet (verbatim excerpt, no more than 5 lines) | Yes |
| `taint_candidates` | List of names of all dynamic parameters participating in the sink (**only list names; do not judge safety**) | Yes |
| `audit_focus` | Direction hints for what needs verification downstream | Yes |
| `is_structure_position` | Whether any parameter enters a structure position of SQL/command/template etc. (column names, table names, ORDER BY, etc.) | Recommended |

#### safe_regions section

Each inspected region must contain:

| Field | Description | Required |
|------|------|------|
| `line_range` | Code line number range | Yes |
| `reason` | Why it is temporarily safe | Yes |

`reason` must be specific; writing "safe" is not allowed. Recommended phrasings:
- `pure utility function, no external input` (e.g. `DateTime.Now.ToString()`)
- `constant hardcoded, no dynamic parameters` (e.g. `"SELECT * FROM users"`)
- `parameterized query confirmed, dynamic parameters bound` (parameter binding method must be noted)
- `string literal concatenation, no user input involved`

### 2. scan_audit/index_{timestamp}.md

Master index of the scan batch, containing:
- Total number of files scanned in this batch
- Number of files with risks found
- Number of files with no findings (safe_regions only)
- List of files that failed to scan

## Scan Scope

The following file types must be covered:
- `*.cs`: C# source files
- `*.cshtml`: Razor views
- `*.razor`: Blazor components
- `*.config` / `*.json`: configuration files (check dangerous switches)
- `*.vb`: VB.NET (if present)

Excluded directories: `bin/`, `obj/`, `.vs/`, `publish/`, `test/` snapshots and cache directories.

## Common Sink Type Recognition Checklist

The following common sink patterns must be checked during scanning (based on `DOTNET_SINK_REFERENCE.md`):
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)

### SQL Injection
- `SqlCommand`, `DbCommand`, `ExecuteReader`, `ExecuteScalar`, `ExecuteNonQuery`
- `FromSqlRaw`, `ExecuteSqlRaw`, `SqlQueryRaw`
- Dapper's `Query` / `Execute` (when parameters are non-parameterized)
- String-concatenated SQL construction: `+` concatenation, `$"..."` interpolation, `StringBuilder.Append`

### Command Injection
- `Process.Start`, `Process.StartInfo`
- `cmd.exe`, `powershell.exe` argument concatenation
- `ShellExecute`, `CreateProcess`

### SSRF
- `HttpClient.GetAsync`, `WebRequest.Create`, `HttpWebRequest`
- `Uri` construction concatenating user input

### File Operations
- `File.ReadAllText`, `File.OpenRead`, `FileStream` with controllable path
- `File.WriteAllText`, `FileStream` with controllable write path
- `IFormFile.SaveAs`, `IFormFile.CopyTo`
- `ZipArchive.ExtractToDirectory`

### Deserialization
- `BinaryFormatter.Deserialize`
- `JsonConvert.DeserializeObject` (when `TypeNameHandling` is not None)
- `DataContractSerializer.ReadObject`
- `JavaScriptSerializer.Deserialize`

### XSS
- `@Html.Raw`, `MarkupString`
- `Response.Write`, `HttpResponse.Write`
- Direct output of user input during template rendering

### XXE
- `XmlDocument.Load`, `XmlReader.Create`
- `XDocument.Parse`

### Template Injection / SSTI
- `Razor.Parse`, `Engine.Razor.RunCompile`
- `Scriban.Template.Parse`, `FluidTemplate.Parse`

### Expression Injection
- `CSharpScript.EvaluateAsync`
- `DataTable.Compute`
- `NCalc.Evaluate`
- `Dynamic LINQ`

### LDAP Injection
- `DirectorySearcher.Filter`
- `LdapConnection.SendRequest`

### XPath Injection
- `XmlNode.SelectNodes`, `XPathNavigator.Select`

### NoSQL Injection
- `IMongoCollection.Find` with controllable `BsonDocument`
- `FilterDefinition` construction via concatenation

## Anti-Patterns (Forbidden)

- ❌ **Judging whether parameters are safe in the Scan phase**: e.g. marking something safe upon seeing `escape_like_literal()` — that is the Taint phase's responsibility
- ❌ **Outputting only risks without safe_regions**: Coverage cannot compute uncovered gaps
- ❌ **Missing safe region marks**: risk-free regions in the file also need to be marked; otherwise Coverage will require re-inspection
- ❌ **Vague safe_regions reasons**: writing "safe" is not allowed; the reason must be specific

## Handoff to Downstream Phases

```
Scan output (risks + safe_regions)
    → Coverage phase computes uncovered gaps
    → Large gaps sent back to Scan for re-inspection
    → risks / safe_regions updated after re-inspection
    → Final Scan artifacts handed to the Briefing phase to generate candidate parameter checklists
```

## Quality Gate

- [ ] Each scanned file has a scan_{filename}_{timestamp}.md output
- [ ] Each file contains both risks and safe_regions (either may be empty, but the fields must exist)
- [ ] safe_regions reasons are specific and verifiable
- [ ] taint_candidates list all dynamic parameters participating in the sink, with none missing
- [ ] No conclusions that prematurely judge safety

## Output Paths

- `scan_audit/scan_{filename}_{timestamp}.md` (one per file)
- `scan_audit/index_{timestamp}.md` (batch master index)
