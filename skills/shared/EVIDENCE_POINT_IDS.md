# Evidence Point ID Unified Dictionary (.NET)

Notes:

- This file enables field-level name alignment between the Sink Evidence Checklist output of dotnet-route-tracer and the evidence references of each sub-skill.
- Without a trace, static source-code evidence may be aligned to the same EVID_* keys, but the conclusion can only be ⚠️Pending Verification or 🔍Environment-Dependent.

## SQL

- EVID_SQL_EXEC_POINT: SQL execution point evidence
- EVID_SQL_STRING_CONSTRUCTION: SQL string construction or RawSQL evidence
- EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT: user-parameter-to-SQL-fragment mapping evidence

## NOSQL

- EVID_NOSQL_QUERY_CONSTRUCTION: NoSQL query construction point evidence
- EVID_NOSQL_USER_INPUT_INTO_QUERY_STRUCTURE: user input entering query structure evidence
- EVID_NOSQL_OPERATOR_INJECTION_FIELDS: operator injection field evidence

## KQL

- EVID_KQL_EXEC_POINT: KQL execution point evidence (e.g., `LogsQueryClient.QueryWorkspaceAsync`, `QueryResource`, `OperationalInsightsDataClient.Query`)
- EVID_KQL_STRING_CONSTRUCTION: KQL query string construction or concatenation evidence
- EVID_KQL_USER_PARAM_TO_KQL_FRAGMENT: user input to KQL fragment or pipeline operation mapping evidence

## CMD

- EVID_CMD_EXEC_POINT: Process.Start or shell execution point evidence
- EVID_CMD_COMMAND_STRING_CONSTRUCTION: command argument construction evidence
- EVID_CMD_USER_PARAM_TO_CMD_FRAGMENT: user input to command fragment mapping evidence

## SSRF

- EVID_SSRF_URL_NORMALIZATION: URL normalization and concatenation evidence
- EVID_SSRF_FINAL_URL_HOST_PORT: final request URL / Host / Port evidence
- EVID_SSRF_DNSIP_AND_INNER_BLOCK: DNS / IP resolution and intranet blocking evidence

## XSS

- EVID_XSS_OUTPUT_POINT: output point evidence
- EVID_XSS_USER_INPUT_INTO_OUTPUT: user input entering output context evidence
- EVID_XSS_ESCAPE_OR_RAW_CONTROL: encoding, raw output, or safe template control evidence

## DOM-XSS

- EVID_DOMXSS_SINK_OUTPUT_POINT: client-side output sink point evidence (e.g., `innerHTML`, `document.write`, `location`, `eval`, or JS interpolated output)
- EVID_DOMXSS_USER_INPUT_SOURCE: user input source evidence (e.g., URL parameters, fragment, postMessage, data injected into a JS context by the server)
- EVID_DOMXSS_ENCODING_SANITIZE_PROOF: pre-output encoding / sanitization / safe API usage evidence (e.g., `textContent`, DOMPurify, encoding functions)

## REDIR

- EVID_REDIR_OUTPUT_POINT: redirect output point evidence
- EVID_REDIR_DEST_SOURCE_MAPPING: destination source mapping evidence
- EVID_REDIR_DEST_VALIDATION_NORMALIZATION: destination validation and normalization evidence

## CRLF

- EVID_CRLF_OUTPUT_POINT: response header or cookie output point evidence
- EVID_CRLF_USER_INPUT_INTO_HEADER_COOKIE: user input entering header / cookie value evidence
- EVID_CRLF_CONTROL_CHAR_FILTERING_ENCODING: control character filtering, encoding, and host interception evidence

## FILE

- EVID_FILE_RESOLVED_TARGET: final read target path evidence
- EVID_FILE_PATH_NORMALIZATION: path concatenation and normalization evidence
- EVID_FILE_EXECUTION_BOUNDARY: read and execution boundary evidence

## WRITE

- EVID_WRITE_CALLSITE: write call site evidence
- EVID_WRITE_DESTPATH_JOIN_AND_NORMALIZATION: destination path normalization evidence
- EVID_WRITE_CONTENT_SOURCE_INTO_WRITE: write content source mapping evidence
- EVID_WRITE_EXECUTION_ACCESSIBILITY_PROOF: post-write accessibility / executability evidence

## UPLOAD

- EVID_UPLOAD_DESTPATH: storage path evidence
- EVID_UPLOAD_FILENAME_EXTENSION_PARSING_SANITIZE: file name and extension handling evidence
- EVID_UPLOAD_ACCESSIBILITY_PROOF: post-write accessibility surface evidence

## ARCHIVE

- EVID_ARCHIVE_EXTRACT_CALLSITE: extraction call site evidence
- EVID_ARCHIVE_ENTRY_NAME_SOURCE: archive entry name source evidence
- EVID_ARCHIVE_FINAL_TARGET: final resolved target path evidence

## XXE

- EVID_XXE_PARSER_CALL: XML parser call site evidence
- EVID_XXE_INPUT_SOURCE: input source evidence
- EVID_XXE_ENTITY_DOCTYPE_SAFETY_AND_ECHO: DOCTYPE / Entity safety options and echo evidence

## DESER

- EVID_DESER_CALLSITE: deserialization call site evidence
- EVID_DESER_INPUT_SOURCE: input source evidence
- EVID_DESER_OBJECT_TYPE_MAGIC_TRIGGER_CHAIN: type information and follow-up sensitive chain evidence

## TPL

- EVID_TPL_ENGINE_RENDER_OR_PARSE_ENTRY: template engine entry evidence
- EVID_TPL_TEMPLATE_OR_EXPR_CONTROL: template name or expression controllability evidence
- EVID_TPL_EXEC_CHAIN_ENTRY: template compilation, evaluation, or execution chain entry evidence

## SSTI

- EVID_SSTI_TEMPLATE_SOURCE: template source controllability evidence
- EVID_SSTI_SANDBOX_ESCAPE: sandbox escape evidence
- EVID_SSTI_USER_INPUT_TO_TEMPLATE: user input to template injection point evidence
- EVID_SSTI_RENDER_EXEC_CHAIN: template rendering execution chain evidence

## LDAP

- EVID_LDAP_EXEC_POINT: LDAP query execution point evidence
- EVID_LDAP_FILTER_STRING_CONSTRUCTION: Filter / DN construction evidence
- EVID_LDAP_USER_PARAM_TO_FILTER_FRAGMENT: user input to Filter fragment mapping evidence

## XPATH

- EVID_XPATH_EXEC_POINT: XPath query execution point evidence (e.g., `XPathNavigator.Select`, `XmlNode.SelectNodes`)
- EVID_XPATH_EXPR_CONSTRUCTION: XPath expression construction, concatenation, or interpolation evidence
- EVID_XPATH_USER_PARAM_TO_XPATH_FRAGMENT: user input to XPath fragment or predicate mapping evidence

## EXPR

- EVID_EXPR_EVAL_ENTRY: expression evaluation entry evidence
- EVID_EXPR_EXPR_CONTROL: expression string controllability evidence
- EVID_EXPR_EXEC_CHAIN_ENTRY: evaluation result entering sensitive semantics evidence

## AUTH

- EVID_AUTH_PATH_PROTECTED_MATCH: protected entry matching evidence
- EVID_AUTH_TOKEN_DECODE_JUDGMENT: authentication ticket parsing and judgment evidence
- EVID_AUTH_PERMISSION_CHECK_EXEC: Policy / Role / Claim check evidence
- EVID_AUTH_IDOR_OWNERSHIP_CONDITION: resource ownership validation evidence
- EVID_AUTH_ENUM_ENDPOINT_SURFACE: login / password-recovery / registration endpoint enumeration surface evidence
- EVID_AUTH_ENUM_OBSERVABLE_DIFF: observable difference between success / failure / nonexistent accounts (at least one of status code / response body / timing) evidence
- EVID_AUTH_ENUM_IMPACT_CONFIRM: impact closure evidence that account existence or authentication state can be inferred

## CSRF

- EVID_CSRF_STATE_CHANGE_HANDLER_EXEC: state-changing entry execution evidence
- EVID_CSRF_TOKEN_SOURCE: CSRF token generation source evidence
- EVID_CSRF_TOKEN_VERIFY: server-side verification evidence
- EVID_CSRF_BYPASS_BRANCH: bypass branch evidence

## SESS

- EVID_SESS_COOKIE_FLAGS: cookie flags evidence
- EVID_SESS_TICKET_REGEN_ROTATION: post-login ticket rotation evidence
- EVID_SESS_JWT_VERIFY_CLAIMS: JWT claims and signature verification evidence
- EVID_SESS_LOGOUT_CLEAR: logout cleanup evidence

## CFG

- EVID_CFG_CONFIG_LOCATION: configuration location evidence
- EVID_CFG_RUNTIME_SETTING_CODE: runtime setting code evidence
- EVID_CFG_IMPACT_ASSOCIATION: configuration impact point association evidence
- EVID_CFG_SECURITY_SWITCH_EVIDENCE: key security switch evidence
- EVID_CFG_SENSITIVE_ENDPOINT_EXPOSURE: unauthorized accessible surface of route / configuration / metadata endpoints evidence
- EVID_CFG_INTERNAL_INFO_DISCLOSURE: response actually exposing internal implementation / deployment configuration evidence (not merely endpoint existence)
- EVID_CFG_SECRET_MATERIAL_IN_RESPONSE: credential leakage evidence of secret material detected in the response

## CRYPTO

- EVID_CRYPTO_ALGO_SELECTION: algorithm selection evidence
- EVID_CRYPTO_KEY_SOURCE: key source evidence
- EVID_CRYPTO_MODE_PADDING_RANDOMNESS: mode, padding, randomness evidence
- EVID_CRYPTO_REPLAY_FRESHNESS_ABSENT: signature verification entry lacking nonce/timestamp/replay cache freshness check evidence
- EVID_CRYPTO_REPLAY_ACCEPTANCE: empirical replay evidence that the same signed request is accepted on second submission
- EVID_CRYPTO_REPLAY_IMPACT_CONFIRM: impact closure evidence that replay causes unauthorized operations / state changes

## SUPPLY (Supply Chain)

- EVID_SUPPLY_CVE_MATCH: dependency version match record against known CVE/GHSA databases evidence (CVE ID, affected version range, current/locked version, fixed version)
- EVID_SUPPLY_UNSAFE_SOURCE: package source protocol or origin risk evidence (source URL, protocol type, authentication method)
- EVID_SUPPLY_SIGNATURE_GAP: signature verification gap or configuration defect evidence (allowUntrustedRoot, trustedSigners not configured)
- EVID_SUPPLY_TRANSITIVE_PATH: transitive dependency exploitable path evidence (direct dependency → transitive dependency → exploitable interface)
- EVID_SUPPLY_SPOOF_DEP: dependency confusion / typosquatting / phantom dependency suspicion evidence (package name similarity, provenance declaration location)
- EVID_SUPPLY_TOOL_OUTPUT: raw tool scan output evidence (dotnet list package --vulnerable / osv-scanner / npm audit)
- EVID_SUPPLY_LOCK_GAP: lockfile missing or version drift evidence (declaration location, range, locked version)

## LOGIC / FS / LOG

- EVID_LOGIC_STATE_TRANSITION: state transition and business condition evidence
- EVID_LOGIC_NUMERIC_USER_SOURCE: source location evidence of user-controllable numeric values entering arithmetic operations
- EVID_LOGIC_ARITHMETIC_POINT: arithmetic operation point evidence (add/subtract/multiply / length offset / currency-points conversion, etc.)
- EVID_LOGIC_OVERFLOW_IMPACT: impact evidence of overflow or boundary bypass causing logic failure / availability loss
- EVID_FS_TOCTOU_OR_LINK_BEHAVIOR: filesystem race or link behavior evidence
- EVID_LOG_EVENT_COVERAGE_AND_SENSITIVE_DATA: log coverage and sensitive information evidence
- EVID_LOG_TAMPERABLE_FIELD_SOURCE: write-path evidence that controllable header/cookie/audit fields are actually written into audit records
- EVID_LOG_IDENTITY_MISATTRIBUTION_IMPACT: impact closure evidence of identity impersonation / misattribution
- EVID_LOG_FLOODING_EXHAUSTION_PATH: causal chain evidence of high-frequency / high-volume writes exhausting audit storage

## HTTP DESYNC

- EVID_DESYNC_CL_T_CONFLICT: Content-Length vs Transfer-Encoding conflict evidence
- EVID_DESYNC_PROXY_INCONSISTENCY: proxy-layer inconsistency evidence
- EVID_DESYNC_REQUEST_PREFIX_TRUNCATION: request prefix truncation evidence
- EVID_DESYNC_HTTP2_SMUGGLING: HTTP/2 request smuggling evidence
- EVID_DESYNC_RESPONSE_TAIL_INJECTION: response tail injection evidence

## SECOND-ORDER

- EVID_SECOND_ORDER_STORAGE: data secondary storage evidence
- EVID_SECOND_ORDER_TRIGGER: secondary trigger execution evidence
- EVID_SECOND_ORDER_STORE_ENTRANCE: storage entrance point evidence
- EVID_SECOND_ORDER_TRIGGER_ENTRANCE: trigger entrance point evidence
- EVID_SECOND_ORDER_DATA_FLOW_MAPPING: data flow mapping from storage to trigger evidence

## QUERY (Non-SQL Query Language Injection)

- EVID_QUERY_EXEC_POINT: non-SQL query execution point evidence (e.g., SOQL query submission, OData request execution, FetchXML execution)
- EVID_QUERY_STRING_CONSTRUCTION: non-SQL query string/structure construction or concatenation evidence
- EVID_QUERY_USER_PARAM_TO_FRAGMENT: user input to query fragment, condition, or structure mapping evidence

## EXPORT (Spreadsheet Formula Injection)

- EVID_EXPORT_FIELD_USER_CONTROLLED: evidence that exported fields come from user-controlled data
- EVID_EXPORT_FORMULA_SINK: export generation / cell write point evidence (CSV/Excel generators, concatenated writes)
- EVID_EXPORT_INTERPRETATION_PATH: path evidence that exported content will be interpreted by spreadsheets as formulas / commands / links

## PROMPT (AI Prompt Injection)

- EVID_PROMPT_UNTRUSTED_CONTENT: evidence of untrusted content (user input / RAG retrieval / tool returns) entering the prompt context
- EVID_PROMPT_BOUNDARY_CROSSING: evidence of untrusted content crossing the instruction/data boundary (system/developer/user/data role confusion)
- EVID_PROMPT_TOOL_PERMISSION_SCOPE: evidence of tool/function call permission scope and feasibility of overreach
- EVID_PROMPT_OUTPUT_HANDLING: evidence of LLM output being parsed, executed, or driving downstream actions

## NODE Namespace (EVID_NODE_*)

### PROTO (Prototype Chain Pollution)
- EVID_NODE_PROTO_MERGE_SINK: recursive merge / deep-copy convergence point evidence (merge/assign/clone/extend, etc.)
- EVID_NODE_PROTO_MAGIC_KEY_CONTROL: `__proto__`/`constructor`/`prototype` key name controllability evidence
- EVID_NODE_PROTO_KEY_FILTER_ABSENT_OR_BYPASS: key name filtering missing or bypassable evidence
- EVID_NODE_PROTO_GADGET_TRIGGER: post-pollution chain trigger surface evidence (options objects / template engines / child_process options, etc.)

### CMD
- EVID_NODE_CMD_EXEC_POINT: child_process.exec/execSync/spawn(shell:true)/execFile call site evidence
- EVID_NODE_CMD_STRING_CONSTRUCTION: command string concatenation evidence
- EVID_NODE_CMD_USER_PARAM_TO_CMD: user input to command fragment mapping evidence
- EVID_NODE_CMD_ARG_ARRAY_OR_ALLOWLIST: argument array-ification / whitelist protection evidence

### SSRF
- EVID_NODE_SSRF_HTTP_CALL_POINT: server-side HTTP client call site evidence (axios/fetch/got/request/undici/http.get)
- EVID_NODE_SSRF_URL_CONSTRUCTION: URL concatenation and normalization evidence
- EVID_NODE_SSRF_ALLOWLIST: protocol/host/IP allowlist and post-DNS-resolution validation evidence
- EVID_NODE_SSRF_REDIRECT_FOLLOW: redirect following configuration evidence (followRedirects/maxRedirects)

### NOSQL
- EVID_NODE_NOSQL_QUERY_POINT: driver/ODM query call site evidence
- EVID_NODE_NOSQL_RAW_OBJECT_PASS: req.body/req.query raw object passed straight into query evidence
- EVID_NODE_NOSQL_OPERATOR_INJECTION: $where/$regex/$gt and other operators entering query structure evidence
- EVID_NODE_NOSQL_TYPE_COERCE_GUARD: type coercion / schema validation protection evidence

### UPLOAD
- EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG: multer/busboy/formidable configuration point evidence
- EVID_NODE_UPLOAD_FILENAME_SANITIZE: file name sanitization / path traversal protection evidence
- EVID_NODE_UPLOAD_FILTER_LIMITS: fileFilter/limits/extension whitelist evidence
- EVID_NODE_UPLOAD_ACCESSIBILITY: post-write accessibility / executability surface evidence

### XSS
- EVID_NODE_XSS_OUTPUT_POINT: HTML output point evidence (res.send concatenation/res.render/dangerouslySetInnerHTML/v-html)
- EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT: user input entering output context evidence
- EVID_NODE_XSS_ENCODE_OR_SANITIZE: output encoding / sanitization (escape-html/DOMPurify/template auto-escaping) evidence
- EVID_NODE_XSS_SSR_HYDRATION: SSR hydration injection surface evidence (__NEXT_DATA__/__NUXT__)

### SSTI
- EVID_NODE_SSTI_RENDER_POINT: template engine render/compile call site evidence (ejs/pug/nunjucks/handlebars)
- EVID_NODE_SSTI_TEMPLATE_CONCAT: template string concatenated with user input evidence (non-expression parameterization)
- EVID_NODE_SSTI_TEMPLATE_NAME_CONTROL: template name / engine options controllability evidence

### SESS (Session & JWT)
- EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG: jwt.sign/jwt.verify configuration evidence
- EVID_NODE_SESS_JWT_ALG_PINNED: algorithm pinning / rejecting alg:none evidence
- EVID_NODE_SESS_SECRET_SOURCE: secret source and strength evidence
- EVID_NODE_SESS_COOKIE_FLAGS: cookie HttpOnly/Secure/SameSite/Domain/Path evidence
- EVID_NODE_SESS_LIFECYCLE: expiration / logout / session fixation handling evidence

### NODE-AUTH (Authentication & Enumeration)
- EVID_NODE_AUTH_ENUM_ENDPOINT_SURFACE: login / password-recovery / registration endpoint enumeration surface evidence
- EVID_NODE_AUTH_ENUM_OBSERVABLE_DIFF: observable difference between success / failure / nonexistent accounts (at least one of status code / response body / timing) evidence
- EVID_NODE_AUTH_ENUM_IMPACT_CONFIRM: impact closure evidence that account existence or authentication state can be inferred

### CFG (Framework Configuration & Control Plane)
- EVID_NODE_CFG_SECURITY_SWITCH: security switch / default configuration evidence (helmet, secure defaults, fail-open switches, CORS wildcard + credentials)
- EVID_NODE_CFG_RUNTIME_SETTING: runtime configuration evidence (process.env, dotenv, .env leakage, debug switches)
- EVID_NODE_CFG_MIDDLEWARE_ORDER: middleware / Guard / Interceptor order and short-circuit condition evidence
- EVID_NODE_CFG_SSR_MODE: SSR / isomorphic rendering mode configuration evidence (rendering mode, hydration data, edge runtime)
- EVID_NODE_CFG_ERR_HANDLER: error handling and stack leakage evidence (global exception catching, error responses containing internal paths / version fingerprints)
- EVID_NODE_CFG_SENSITIVE_ENDPOINT_EXPOSURE: unauthorized accessible surface of route / configuration / metadata endpoints evidence
- EVID_NODE_CFG_INTERNAL_INFO_DISCLOSURE: response actually exposing internal implementation / deployment configuration evidence (not merely endpoint existence)
- EVID_NODE_CFG_SECRET_MATERIAL_IN_RESPONSE: credential leakage evidence of secret material detected in the response

### SQL
- EVID_NODE_SQL_QUERY_POINT: driver/ORM query call site evidence (mysql/mysql2/knex/sequelize/pg/prisma)
- EVID_NODE_SQL_STRING_CONCAT: SQL text concatenation evidence (+ concatenation / template string interpolation / knex.raw / sequelize.literal / prisma.$queryRawUnsafe)
- EVID_NODE_SQL_PARAM_BINDING_GUARD: placeholder / parameter binding protection evidence (execute(?), prepared statement)
- EVID_NODE_SQL_STRUCTURE_POSITION: structure positions such as identifiers / sort keys entering SQL evidence

### XXE
- EVID_NODE_XXE_PARSE_POINT: XML parsing call site evidence (xml2js/sax/fast-xml-parser/libxmljs)
- EVID_NODE_XXE_EXTERNAL_ENTITY_FLAG: external entity / DOCTYPE handling configuration evidence (resolveEntities/noent/DTD switches)
- EVID_NODE_XXE_SAFE_PARSER_ALTERNATIVE: safe parsing configuration evidence (DTD disabled / external entities disabled / strict mode)

### DESER
- EVID_NODE_DESER_UNSAFE_CALL: unsafe deserialization call site evidence (node-serialize.unserialize/yaml.load unsafe/serialize-javascript deserialization/funcster)
- EVID_NODE_DESER_INPUT_CONTROL: deserialization data source controllability evidence
- EVID_NODE_DESER_GADGET_REACH: post-deserialization function/constructor trigger reachability evidence
- EVID_NODE_DESER_SAFE_ALTERNATIVE: safe alternative / schema validation protection evidence (JSON.parse + fixed schema, etc.)

### CSRF
- EVID_NODE_CSRF_STATE_CHANGE_ENDPOINT: state-changing endpoint evidence (POST/PUT/DELETE with side effects)
- EVID_NODE_CSRF_TOKEN_CHECK: CSRF token/origin/referer check existence and implementation evidence (self-built protection after csurf removal)
- EVID_NODE_CSRF_COOKIE_SAMESITE: cookie SameSite / signing configuration evidence (linked with the SESS group)
- EVID_NODE_CSRF_SECOND_CONFIRM: sensitive-operation second confirmation evidence

### CRYPTO
- EVID_NODE_CRYPTO_WEAK_ALGO: weak algorithm / weak mode call site evidence (md5/sha1/des/ecb/createCipheriv with weak parameters)
- EVID_NODE_CRYPTO_KEY_SOURCE: key source and hardcoding evidence (.env / source code literals / key management services)
- EVID_NODE_CRYPTO_RANDOM_SOURCE: randomness source evidence (Math.random used in security contexts vs crypto.randomBytes)
- EVID_NODE_CRYPTO_HASH_MODE: password hashing scheme evidence (pbkdf2/scrypt/bcrypt/argon2 vs single-pass sha256)
- EVID_NODE_CRYPTO_REPLAY_FRESHNESS_ABSENT: signature verification entry lacking nonce/timestamp/replay cache freshness check evidence
- EVID_NODE_CRYPTO_REPLAY_ACCEPTANCE: empirical replay evidence that the same signed request is accepted on second submission
- EVID_NODE_CRYPTO_REPLAY_IMPACT_CONFIRM: impact closure evidence that replay causes unauthorized operations / state changes

### LOGIC
- EVID_NODE_LOGIC_RACE_WINDOW: race window evidence (check and use not atomic, check-then-act)
- EVID_NODE_LOGIC_TOCTOU_PAIR: TOCTOU object evidence (validation point separated from use point)
- EVID_NODE_LOGIC_WORKFLOW_BYPASS: workflow step skipping / bypass evidence (client-controllable state machine, step parameter passed straight through)
- EVID_NODE_LOGIC_LIMIT_CONTROL: server-side re-check of amount / quantity / count limits evidence
- EVID_NODE_LOGIC_NUMERIC_USER_SOURCE: source location evidence of user-controllable numeric values entering arithmetic operations
- EVID_NODE_LOGIC_ARITHMETIC_POINT: arithmetic operation point evidence (add/subtract/multiply / length offset / currency-points conversion, etc.)
- EVID_NODE_LOGIC_OVERFLOW_IMPACT: impact evidence of overflow or boundary bypass causing logic failure / availability loss

### LOG
- EVID_NODE_LOG_INJECTION_POINT: log write point containing user input evidence (winston/pino/console template strings)
- EVID_NODE_LOG_SENSITIVE_DATA: sensitive data entering logs evidence (passwords/tokens/PII in plaintext)
- EVID_NODE_LOG_TAMPER_SURFACE: log forgery / injection surface evidence (newlines / structured field pollution)
- EVID_NODE_LOG_AUDIT_TRAIL: key-operation audit trail evidence
- EVID_NODE_LOG_TAMPERABLE_FIELD_SOURCE: write-path evidence that controllable header/cookie/audit fields are actually written into audit records
- EVID_NODE_LOG_IDENTITY_MISATTRIBUTION_IMPACT: impact closure evidence of identity impersonation / misattribution
- EVID_NODE_LOG_FLOODING_EXHAUSTION_PATH: causal chain evidence of high-frequency / high-volume writes exhausting audit storage

### FILE_READ
- EVID_NODE_FILE_READ_POINT: file read call site evidence (fs.readFile/readFileSync/createReadStream/sendFile)
- EVID_NODE_FILE_READ_PATH_CONSTRUCTION: read path construction evidence (path.join/concatenating user input)
- EVID_NODE_FILE_READ_TRAVERSAL_GUARD: traversal protection evidence (prefix validation after resolve / allowlist)
- EVID_NODE_FILE_READ_STATIC_ROOT: static directory boundary evidence (express.static/serve-static mount scope)

### FILE_WRITE
- EVID_NODE_FILE_WRITE_POINT: file write call site evidence (fs.writeFile/writeFileSync/appendFile/createWriteStream)
- EVID_NODE_FILE_WRITE_PATH_CONSTRUCTION: write path construction evidence (upload file names / parameters entering paths)
- EVID_NODE_FILE_WRITE_OVERWRITE_PROTECTION: overwrite / append protection evidence (existing-file conflict policy, flag configuration)
- EVID_NODE_FILE_WRITE_CONTENT_CONTROL: write content controllability evidence (content / extension / landing directory)

### ARCHIVE (Archive Extraction)
- EVID_NODE_ARCHIVE_EXTRACT_POINT: extraction call site evidence (unzipper/adm-zip/yauzl/tar-stream/extract-zip)
- EVID_NODE_ARCHIVE_ENTRY_PATH_SANITIZE: entry path sanitization evidence (entryName `../`, absolute paths, drive letters)
- EVID_NODE_ARCHIVE_ZIP_SLIP_GUARD: Zip Slip protection evidence (target root prefix validation / symlink policy)

### OPEN_REDIRECT
- EVID_NODE_REDIRECT_CALL: redirect call site evidence (res.redirect/location assignment/302 responses)
- EVID_NODE_REDIRECT_TARGET_CONTROL: redirect target controllability evidence
- EVID_NODE_REDIRECT_ALLOWLIST_VALIDATE: target allowlist / relative path validation evidence
- EVID_NODE_REDIRECT_ENCODING_BYPASS: encoding / protocol variant bypass analysis evidence (`///`, `\`, url-encoded, protocol-relative)

### CRLF
- EVID_NODE_CRLF_HEADER_WRITE_POINT: header write point evidence (setHeader/append/writeHead/cookie values)
- EVID_NODE_CRLF_PAYLOAD_CONTROL: `\r\n` controllable payload evidence (status line / header injection)
- EVID_NODE_CRLF_VALIDATE_STRIP: CRLF filtering / stripping implementation evidence

### LDAP
- EVID_NODE_LDAP_SEARCH_POINT: LDAP search / bind call site evidence (ldapjs search/bind)
- EVID_NODE_LDAP_FILTER_CONCAT: filter / DN concatenation evidence
- EVID_NODE_LDAP_ESCAPE_IMPLEMENTATION: escape implementation evidence (filter escape / DN escape, per RFC 4515)
- EVID_NODE_LDAP_BIND_ANONYMOUS_FALLBACK: anonymous bind / fallback behavior evidence

### EXPR
- EVID_NODE_EXPR_EVALUATE_POINT: expression engine evaluation call site evidence (expr-eval/mathjs/jexl/jsonata/vm)
- EVID_NODE_EXPR_STRING_CONCAT: expression string concatenated with user input evidence
- EVID_NODE_EXPR_SANDBOX_CONFIG: sandbox / function whitelist configuration evidence (expr-eval functions whitelist, vm context isolation)

### XPATH
- EVID_NODE_XPATH_SELECT_POINT: XPath query call site evidence (xpath.select/libxmljs/xmldom)
- EVID_NODE_XPATH_CONCAT: XPath expression concatenation evidence
- EVID_NODE_XPATH_PARAM_BINDING: parameterization / variable binding protection evidence

### SECOND_ORDER
- EVID_NODE_SECOND_ORDER_STORE_POINT: first-order storage point evidence (input enters storage without immediate trigger)
- EVID_NODE_SECOND_ORDER_TRIGGER_CONTEXT: second-order trigger context evidence (stored value retrieved into a dangerous operation)
- EVID_NODE_SECOND_ORDER_STORAGE_TYPE: storage type evidence (DB / cache / file / session)
- EVID_NODE_SECOND_ORDER_ENCODE_MISMATCH: encoding inconsistency between storage and use phases evidence

### DESYNC (HTTP Request Smuggling)
- EVID_NODE_DESYNC_FRONTEND_VARIANT: front-end / back-end CL-TE handling difference evidence (proxy / container / Node http parser)
- EVID_NODE_DESYNC_SMUGGLE_PRIMITIVE: smuggling primitive evidence (duplicate / ambiguous Content-Length, Transfer-Encoding mixing)
- EVID_NODE_DESYNC_PROXY_CHAIN: intermediate chain evidence (reverse proxy / load balancer / Node rawHeaders handling)
- EVID_NODE_DESYNC_HEADER_CONTROL: header normalization and retransmission control evidence

### FS (Filesystem Comprehensive Surface)
- EVID_NODE_FS_OPERATION_POINT: filesystem operation call site evidence (fs family / path handling)
- EVID_NODE_FS_PATH_JOIN_CONTROL: path.join/resolve user input participation evidence
- EVID_NODE_FS_SYMLINK_FOLLOW: symlink following behavior evidence (lstat/stat validation)
- EVID_NODE_FS_PERMISSION_SCOPE: runtime file permissions and directory scope evidence

### DOM_XSS
- EVID_NODE_DOM_SINK_POINT: DOM sink call site evidence (innerHTML/outerHTML/document.write/eval/location)
- EVID_NODE_DOM_SOURCE_TRACE: DOM source-to-sink flow evidence (location.hash/search/referrer/postMessage/name)
- EVID_NODE_DOM_FRAMEWORK_SAFE_API: framework safe API usage evidence (textContent/createElement/avoiding v-html)
- EVID_NODE_DOM_URL_PARAM_SINK: URL parameter entering sink directly evidence (postMessage origin validation missing)

### SUPPLY (Supply Chain)
- EVID_NODE_SUPPLY_TOOL_OUTPUT: supply chain tool scan raw output evidence (npm audit --json / osv-scanner)

### EXPORT (Spreadsheet Formula Injection)

- EVID_NODE_EXPORT_FIELD_USER_CONTROLLED: evidence that exported fields come from user-controlled data (req.body/query entering export data)
- EVID_NODE_EXPORT_FORMULA_SINK: export generation / cell write point evidence (exceljs/csv-stringify/handwritten CSV writes)
- EVID_NODE_EXPORT_INTERPRETATION_PATH: path evidence that exported content will be interpreted by spreadsheets as formulas / commands / links

### PROMPT (AI Prompt Injection)

- EVID_NODE_PROMPT_UNTRUSTED_CONTENT: evidence of untrusted content entering the prompt context
- EVID_NODE_PROMPT_BOUNDARY_CROSSING: evidence of untrusted content crossing the instruction/data boundary
- EVID_NODE_PROMPT_TOOL_PERMISSION_SCOPE: evidence of tool/function call (including MCP tools) permission scope and feasibility of overreach
- EVID_NODE_PROMPT_OUTPUT_HANDLING: evidence of LLM output being parsed, executed, or driving downstream actions

## Chain Closure Minimum Elements (minimum element checklist when determining evidence chain closure for each EVID_* group)

| EVID Group | Minimum Elements (all indispensable) |
| ---- | ---- |
| Injection class (SQL/NOSQL/KQL/XPATH/LDAP) | controllable parameter source + concatenation point code + boundary bypass analysis + path to execution point |
| CMD/EXPR/TPL/SSTI/DESER | controllable input + execution function call + escape / wrapping analysis + execution point reachability |
| SSRF/HTTP class | URL construction point + network request call + protocol restriction analysis |
| FILE/READ/WRITE/UPLOAD/ARCHIVE | path construction point + file operation call + normalization / traversal analysis |
| XSS/DOM-XSS/REDIR/CRLF | output point + encoding / escaping context + browser-side execution path |
| AUTH/CSRF/SESS | authorization decision point + middleware mount order + session / token lifecycle |
| CRYPTO/CFG/LOG/LOGIC | algorithm / configuration / log write point + weakness evidence + impact surface |
| SUPPLY (supply chain) | CVE match + version / provenance evidence + reachability analysis (EVID_SUPPLY_*) |
| SECOND_ORDER/DESYNC | storage and trigger dual-point evidence (or link resolution evidence) + timing / topology condition analysis |
| QUERY | query execution point + mapping of user input to executable query structure + query semantics / impact analysis |
| EXPORT | controllable export fields + export generation sink + spreadsheet interpretation and impact evidence |
| PROMPT | untrusted content evidence + boundary crossing evidence + tool permission / output handling impact (controllability alone must not confirm) |
