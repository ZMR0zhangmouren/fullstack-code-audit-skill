---
name: node-scan-audit
description: Node.js code security scanning phase skill. Responsible for identifying all suspicious sink points in a file while marking checked safe regions, outputting risks + safe_regions for the downstream Coverage phase to compute uncovered gaps. Discovery only — it does not judge whether risks hold.
---

# Node.js Security Scan (Scan)

## Goal

Perform risk-discovery scanning on each source file; **responsible only for discovering suspicious sink points, not for judging whether risks hold**.

Core outputs:
- `risks`: all suspicious sink points in the file and the dynamic parameters participating in them
- `safe_regions`: code regions that have been checked and are temporarily risk-free

## Core Principles

**Scan is responsible only for discovery, not for verification.**

- When seeing a sink, **do not rush to judge whether injection exists**
- Only list the names of all dynamic parameters participating in the sink
- Leave the "is it safe" judgment to the downstream Taint / specialty phases
- Both `risks` and `safe_regions` must be output; otherwise Coverage cannot compute gaps

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the Sink type definition reference
- By default, follow the general execution standards of `shared/AUDIT_EXECUTION_COMMON.md` and `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (stack-agnostic)

## Input

- `node_source_path`: Node.js project source path
- `target_file`: the single source file currently being scanned
- `timestamp`: generation timestamp

## Output Schema

Output to the `node/scan_audit/` directory:

### 1. node/scan_audit/scan_{filename|module}_{timestamp}.md

Each scanned file must have one structured scan report output.

#### risks section

Each sink must contain:

| Field | Description | Required |
|------|------|------|
| `sink_type` | risk type: `CMD_INJECTION` / `EVAL_EXEC` / `SSRF` / `XSS` / `SSTI` / `FILE_READ` / `FILE_WRITE` / `FILE_UPLOAD` / `ARCHIVE_EXTRACT` / `DESER` / `XXE` / `SQL_INJECTION` / `NOSQL_INJECTION` / `LDAP_INJECTION` / `EXPR_INJECTION` / `XPATH_INJECTION` / `PROTO_POLLUTION` / `AUTH_BYPASS` / `CSRF` / `OPEN_REDIRECT` / `CRLF_INJECTION` / `SECOND_ORDER` / `OTHER` | yes |
| `line_range` | code line number range, e.g., `45-52` | yes |
| `dangerous_call` | dangerous call code snippet (verbatim excerpt, no more than 5 lines) | yes |
| `taint_candidates` | list of names of all dynamic parameters participating in the sink (**names only; safety is not judged**) | yes |
| `audit_focus` | follow-up verification direction hints | yes |
| `is_structure_position` | whether any parameter enters structure positions such as object keys / query field names / template expressions | recommended |

#### safe_regions section

Each checked region must contain:

| Field | Description | Required |
|------|------|------|
| `line_range` | code line number range | yes |
| `reason` | why it is temporarily safe | yes |

`reason` must be specific; writing "safe" is forbidden. Recommended wording:
- `pure utility function, no external input` (e.g., `dayjs(ts).format()`)
- `constant hardcoded, no dynamic parameters` (e.g., `db.query('SELECT * FROM users')` with a fixed string)
- `parameterized / placeholder query used, dynamic parameters bound` (note the driver and binding method)
- `object keys come from a fixed enum, no user input participates`

### 2. node/scan_audit/index_{timestamp}.md

Scan batch master index, containing:
- total number of files scanned this batch
- number of files with risks found
- number of files with no findings (safe_regions only)
- list of files that failed to scan

## Scan Scope

The following file types must be covered:
- `*.js` / `*.mjs` / `*.cjs`: JavaScript source files (CommonJS and ESM)
- `*.ts` / `*.tsx` / `*.jsx`: TypeScript / JSX source files
- `package.json`: `scripts` (postinstall / preinstall lifecycle hooks), anomalous sources of `dependencies`
- `.env*` / `*.config.js` / `*.config.ts`: configuration files (dangerous switches, hardcoded keys)

Excluded directories: `node_modules/`, `dist/`, `build/`, `coverage/`, `.next/`, `.nuxt/`, `vendor/`.

## Common Sink Type Identification Checklist

The following common sink patterns must be checked during scanning (based on `NODE_SINK_REFERENCE.md`):

### Command Injection
- `child_process.exec`, `execSync`, `spawn(shell:true)`, `execFile`
- same-family calls after aliased imports of `node:child_process`

### Code / Expression Execution
- `eval(`, `new Function(`, `vm.runInNewContext`, `vm.runInThisContext`
- `require(dynamic string)`, `import(dynamic string)`
- expression engine evaluation points such as `expr-eval`, `mathjs.evaluate`, `jexl`, `jsonata`

### SSRF
- `axios(`, `axios.get/post`, `fetch(`, `got(`, `request(`, `undici`, `http.get`, `https.get`
- URLs constructed via concatenation or user input; `followRedirects` / `maxRedirects` configuration

### File Operations
- `fs.readFile`, `fs.readFileSync`, `fs.createReadStream` with controllable paths
- `fs.writeFile`, `fs.writeFileSync`, `fs.appendFile` with controllable write paths
- upload landing paths of `multer` / `busboy` / `formidable`
- extraction paths of `unzipper`, `adm-zip`, `yauzl`, `tar-stream` (Zip Slip)

### Deserialization / Object Injection
- `yaml.load` (js-yaml <4 without `schema` set), `js-yaml.load(unsafe)`
- `node-serialize.unserialize`, the deserialization direction of `serialize-javascript`, `funcster`
- `Object.assign`, `lodash.merge/set/defaultsDeep`, `deepmerge`, `@zurawiki/deep-copy` with controllable recursive merge targets

### SQL / NoSQL Injection
- SQL built via string concatenation: `+` concatenation, template string `` `${var}` `` interpolation
- `query(concatenated)` rather than `execute(placeholder)` of `mysql` / `mysql2`
- `knex.raw`, `sequelize.literal`, `prisma.$queryRawUnsafe`
- `collection.find(object passthrough)`, `$where`, `$regex` controllable of `mongodb`

### XSS / SSTI
- `res.send(user input)`, `innerHTML =`, `dangerouslySetInnerHTML`
- `ejs.render(user input)`, `pug.render(user input)`, `Handlebars.compile(user input)`, `nunjucks.renderString`

### XXE / XPath / LDAP
- `xml2js`, `sax`, `fast-xml-parser`, `libxmljs` parsing untrusted XML
- `xpath.select(concatenated)`
- `search({filter: concatenated})` of `ldapjs`

### Open Redirect / CRLF
- `res.redirect(user input)`, `location = user input`
- `res.setHeader(`, `res.append(`, `res.writeHead(` values containing `\r\n`

## Anti-Patterns (Forbidden)

- ❌ **Judging parameter safety at the Scan stage**: e.g., marking something safe upon seeing `escapeHtml()` — that is the specialty phase's responsibility
- ❌ **Outputting only risks without safe_regions**: Coverage cannot compute uncovered gaps
- ❌ **Missing safe-region marking**: risk-free regions in the file also need marking; otherwise Coverage will require backfill
- ❌ **Vague safe_regions reasons**: writing "safe" is forbidden; a specific reason is required

## Handoff to Downstream Phases

```
Scan output (risks + safe_regions)
    → the Coverage phase computes uncovered gaps
    → larger gaps sent back to Scan for backfill
    → risks / safe_regions updated after backfill
    → final Scan artifacts handed to the Briefing phase to generate candidate parameter lists
```

## Quality Gate

- [ ] Every scanned file has a scan_{filename|module}_{timestamp}.md output
- [ ] Every file contains both risks and safe_regions (either may be empty, but the fields must exist)
- [ ] safe_regions reasons are specific and verifiable
- [ ] taint_candidates list all dynamic parameters participating in the sink, with nothing missed
- [ ] No premature safety conclusions

## Output Paths

- `node/scan_audit/scan_{filename|module}_{timestamp}.md` (one per file / module)
- `node/scan_audit/index_{timestamp}.md` (batch master index)
