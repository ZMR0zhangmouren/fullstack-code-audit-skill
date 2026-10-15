# .NET Sink Reference (for pipeline and sub-skill alignment)

## SQL / ORM

### ADO.NET
- `System.Data.SqlClient.SqlCommand` — ExecuteReader / ExecuteScalar / ExecuteNonQuery / ExecuteXmlReader
- `System.Data.Common.DbCommand` — ExecuteReader / ExecuteScalar / ExecuteNonQuery
- `System.Data.SqlClient.SqlDataAdapter` — Fill / FillSchema / Update
- `Microsoft.Data.SqlClient.SqlCommand` — same as above (.NET Core replacement package)
- `System.Data.OleDb.OleDbCommand` — ExecuteReader / ExecuteNonQuery
- `System.Data.Odbc.OdbcCommand` — ExecuteReader / ExecuteNonQuery

### Entity Framework Core
- `RelationalDatabaseFacadeExtensions.ExecuteSqlRaw` / `ExecuteSqlRawAsync`
- `RelationalDatabaseFacadeExtensions.ExecuteSqlInterpolated` / `ExecuteSqlInterpolatedAsync`
- `RelationalQueryableExtensions.FromSqlRaw` / `FromSqlInterpolated`
- `Database.SqlQueryRaw<T>` / `SqlQuery<T>` (EF Core 7+)
- `DbContext.Database.GetDbConnection()` → manual CreateCommand
- `IQueryable.Where()` accepting string expressions (Dynamic LINQ)
- `IgnoreQueryFilters()` — bypasses global filters (multi-tenancy / soft delete)

### Dapper
- `SqlMapper.Query` / `Query<T>` / `QueryAsync<T>`
- `SqlMapper.Execute` / `ExecuteAsync`
- `SqlMapper.QueryMultiple` / `QueryMultipleAsync`
- `DynamicParameters` — dynamic parameter construction
- String concatenation + `$"SELECT ... WHERE {userInput}"` pattern

### Other ORM / Data Access
- `NHibernate.ISession.CreateSQLQuery` / `CreateQuery` (HQL injection)
- `ServiceStack.OrmLite` — SqlExpression string concatenation
- `PetaPoco.Database.Query` / `Execute` / `Fetch`
- `RepoDB.DbConnection.ExecuteQuery` / `ExecuteNonQuery`

### Dynamic Fragments (Cannot Be Parameterized)
- Sort field: `ORDER BY {column}`
- Table/column name: `FROM {tableName}`
- IN list: `WHERE id IN ({ids})`
- Condition fragment: `WHERE {dynamicCondition}`
- Pagination: `OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY`

### Identifier Injection (Cannot Be Parameterized; Whitelist Required)

- Sort field: `ORDER BY {column}` — externally controllable column name/alias entering the ORDER BY slot directly
- Group field: `GROUP BY {column}` — externally controllable column name entering the GROUP BY slot directly
- Column/table name dynamic replacement: `SELECT {userColumn} FROM {userTable}` — field or table name comes from user input
- Nested filter field: `WHERE {dynamicColumn} = value` — keys of nested objects/dictionaries used in SQL field slots; sub-levels validated independently during recursive resolution
- Note: parameterized queries (`@param`) do **not** protect identifier slots; identifier slots must rely on whitelist / enum mapping / strict validators

## NoSQL

### MongoDB (.NET Driver)
- `IMongoCollection<T>.Find` / `FindAsync` — FilterDefinition construction
- `Builders<T>.Filter` — Eq / Regex / Where (accepts string expressions)
- `BsonDocument` direct query-condition concatenation
- `IMongoCollection<T>.Aggregate` — pipeline construction
- `JsonFilterDefinition<T>` — filter constructed from a JSON string

### Azure Cosmos DB
- `Container.GetItemQueryIterator` — custom SQL query string
- `QueryDefinition` — constructed via string concatenation
- `Container.ReadItemAsync` — partition key injection

### Redis (StackExchange.Redis)
- `IDatabase.ScriptEvaluate` — Lua script injection
- `IDatabase.Execute` — raw command concatenation
- `ConnectionMultiplexer.GetServer().Keys()` — pattern injection

### Elasticsearch (NEST / Elastic.Clients)
- `ElasticClient.Search<T>` — QueryRawJson
- `QueryContainer` string concatenation
- `LowLevelClient.Search<T>` — raw JSON body

## KQL / Kusto Query Language

### Azure Monitor Query SDK
- `LogsQueryClient.QueryWorkspaceAsync` — workspace + KQL query string
- `LogsQueryClient.QueryWorkspace` — synchronous version
- `LogsQueryClient.QueryResource` / `QueryResourceAsync` — resource-level queries
- `MetricsQueryClient.QueryResource` — Metrics queries (KQL variant)
- `Response<T>.Value` — query results

### Application Insights SDK
- `TelemetryClient.Query` / `AnalyticsClient.Query` — classic AI queries
- `ApplicationInsightsDataClient.QueryAsync` — programmatic query interface

### Legacy Log Analytics
- `Microsoft.Azure.OperationalInsights.OperationalInsightsDataClient.Query` — legacy SDK
- `Microsoft.Azure.OperationalInsights.OperationalInsightsDataClient.QueryAsync`

### KQL Injection Patterns
- KQL string concatenation: `$"traces | where message contains '{userInput}'"`
- Dynamic table name: `$"{userTable} | where ..."`
- Dynamic column/field name: `$"traces | project {userColumns}"`
- `extend` / `project` dynamic fields: `$"traces | extend {userField} = ..."`
- `where` condition fragment concatenation: `$"traces | where {userCondition}"`
- Pipeline injection: injecting extra pipeline operations via `\n` (`| take 10000\n| union (traces | take 10000)`)
- Unvalidated strings mixed into `contains` / `has` / `startswith` / `matches regex`

## CMD / Command Injection
- `ElasticClient.Search<T>` — QueryRawJson
- `QueryContainer` string concatenation
- `LowLevelClient.Search<T>` — raw JSON body

## CMD / Command Injection

### Process Startup
- `System.Diagnostics.Process.Start`
- `ProcessStartInfo` — FileName / Arguments / ArgumentList
- `ProcessStartInfo.UseShellExecute = true` — shell interpretation risk

### Shell Invocation Patterns
- `cmd.exe /c {command}` — Windows command concatenation
- `powershell.exe -Command {script}` — PowerShell injection
- `/bin/bash -c {command}` — Linux shell concatenation
- Shell invocations under `RuntimeInformation.IsOSPlatform()` conditional branches

### Indirect Command Execution
- `Microsoft.Extensions.Hosting.IHostedService` — command execution in background tasks
- `Hangfire.BackgroundJob.Enqueue` — parameter passing in deferred execution
- `System.Management.ManagementObject.InvokeMethod` — WMI commands
- `System.DirectoryServices.DirectoryEntry.Invoke` — ADSI commands

## SSRF / Server-Side Request Forgery

### HttpClient Family
- `HttpClient.SendAsync` / `GetAsync` / `PostAsync` / `PutAsync` / `DeleteAsync`
- `HttpClient.GetStringAsync` / `GetStreamAsync` / `GetByteArrayAsync`
- `IHttpClientFactory.CreateClient` — typed/named client
- `HttpMessageHandler` / `DelegatingHandler` — request interception and modification

### Legacy APIs
- `System.Net.WebRequest.Create` / `HttpWebRequest`
- `System.Net.WebClient.DownloadString` / `DownloadFile` / `UploadString`

### Third-Party HTTP Clients
- `RestSharp.RestClient.Execute` / `ExecuteAsync`
- `Flurl.Http.FlurlClient` — GetAsync / PostAsync
- `Refit` — dynamic URL construction

### Special Scenarios
- Webhook callback URL — user-provided callback address
- GraphQL remote schema stitching — remote URL pulling
- PDF generators (wkhtmltopdf / Puppeteer) — URL rendering
- Image/avatar download — user-provided image URL
- RSS/Atom feed pulling — user-provided feed URL
- SOAP/WCF client — dynamic endpoint address
- `SmtpClient` — user-controlled SMTP server address
- `TcpClient` / `Socket` — user-controlled host:port

## XSS / Output Injection

### Razor Views
- `Html.Raw()` — encoding-disabled output
- `IHtmlContent` / `HtmlString` — HTML marked as safe
- Unencoded variables in `@:` and `<text>` blocks
- `TagHelper` output — output.Content of custom TagHelpers
- `ViewComponent` / `Partial` / `DisplayTemplate` — nested rendering

### Blazor
- `MarkupString` — equivalent to Html.Raw
- `RenderFragment` — dynamic component content
- `IJSRuntime.InvokeAsync` — JS interop callback
- `NavigationManager.NavigateTo` — client-side navigation injection
- Prerender hybrid rendering — server/client boundary

### MVC / API Output
- `Controller.Content()` — custom Content-Type output
- `Controller.Json()` — JSON serialization output
- `FileContentResult` / `FileStreamResult` — file name injection
- `ContentResult` with `text/html` — manual HTML concatenation

### Encoders
- `HtmlEncoder` / `JavaScriptEncoder` / `UrlEncoder` — custom or disabled
- `JavaScriptEncoder.UnsafeRelaxedJsonEscaping` — relaxed JSON encoding
- `System.Text.Encodings.Web.TextEncoderSettings` — custom allowed characters

### Frontend Interaction
- `data-*` attribute injection — read and executed by frontend JS
- `onclick` / `onload` and other event attribute concatenation
- Server-side variable embedding in `<script>` blocks
- JSON serialized then embedded in `<script>` — XSS via JSON

## REDIR / Open Redirect

### ASP.NET Core
- `Controller.Redirect(url)` — unvalidated redirect
- `Controller.LocalRedirect(url)` — local redirect (still requires validation)
- `Controller.RedirectToAction` / `RedirectToRoute` / `RedirectToPage`
- `Results.Redirect(url)` — Minimal API redirect
- `HttpResponse.Redirect(url)`

### Authentication Flows
- `Challenge()` — external login callback ReturnUrl
- `SignOut()` — post-logout redirect
- OAuth/OIDC `redirect_uri` / `post_logout_redirect_uri`
- SAML `RelayState` — callback address

### Common Parameter Names
- `returnUrl` / `ReturnUrl` / `return_url`
- `redirect` / `redirectUrl` / `next` / `goto` / `continue`
- `callbackUrl` / `callback`

## CRLF / Response Header Injection

### Response Header Operations
- `HttpResponse.Headers.Append` / `Add`
- `HttpResponse.Headers["X-Custom"]` = userInput
- `Response.Cookies.Append` — cookie value injection

### High-Risk Headers
- `Location` — redirect header
- `Set-Cookie` — cookie injection
- `Content-Disposition` — file name injection
- `X-Forwarded-*` — proxy header passthrough
- Custom security headers — CSP / X-Frame-Options override

### File Download Scenarios
- `Content-Disposition: attachment; filename="{userInput}"` — file name CRLF
- Proxy passthrough headers — upstream headers written to the response unfiltered

## FILE / File Read and Path Traversal

### File Read APIs
- `System.IO.File.ReadAllText` / `ReadAllBytes` / `ReadAllLines` / `ReadLines`
- `System.IO.File.OpenRead` / `Open` / `OpenText`
- `System.IO.FileStream` constructors
- `System.IO.StreamReader` constructors
- `System.IO.Path.Combine` — path concatenation (does not prevent traversal)
- `System.IO.Path.GetFullPath` — normalization (can be used for defense or bypassed)

### ASP.NET File Returns
- `PhysicalFile` / `PhysicalFileResult` — physical path file return
- `VirtualFileResult` — virtual path file return
- `File(stream, contentType, fileName)` — streaming file return
- `IFileProvider.GetFileInfo` / `GetDirectoryContents`
- `StaticFileMiddleware` — static file directory exposure

### Path Traversal Patterns
- `../` / `..\` — directory traversal
- URL encoding: `%2e%2e%2f` / `%2e%2e%5c`
- Double encoding: `%252e%252e%252f`
- Null bytes: `%00` truncation (legacy .NET Framework)

## WRITE / File Write

### Write APIs
- `System.IO.File.WriteAllText` / `WriteAllBytes` / `WriteAllLines`
- `System.IO.File.AppendAllText` / `AppendAllLines`
- `System.IO.FileStream` — FileMode.Create / CreateNew / Append
- `System.IO.StreamWriter` — constructors and Write/WriteLine
- `System.IO.BinaryWriter`

### Upload Persistence
- `IFormFile.CopyTo` / `CopyToAsync` — uploaded file save
- `IFormFile.OpenReadStream` → FileStream — streaming save
- Temp file → final path move/rename

### Dangerous Patterns
- User-controlled file name + write into a web-accessible directory → WebShell
- User-controlled path + write into a configuration directory → configuration override
- Log write to user-controlled path → log injection + path traversal

## UPLOAD / File Upload

### Receiving APIs
- `IFormFile` / `IFormFileCollection` / `List<IFormFile>`
- `MultipartReader` — manual multipart parsing
- `Request.Form.Files` — direct access to the file collection
- `Request.Body` — streaming upload (no multipart)

### Key Checkpoints
- File name: `IFormFile.FileName` — client-provided, can be forged
- Extension: whitelist vs blacklist vs double-extension bypass
- Content-Type: `IFormFile.ContentType` — client-provided, can be forged
- File size: `IFormFile.Length` — limit checks
- Magic bytes: file header validation
- Landing path: whether in a web-accessible directory
- Renaming strategy: GUID vs original file name

## ARCHIVE / Archive Extraction

### Extraction APIs
- `System.IO.Compression.ZipFile.ExtractToDirectory`
- `System.IO.Compression.ZipArchive` — per-entry extraction
- `ZipArchiveEntry.FullName` — entry name (may contain `../`)
- `SharpZipLib` — ICSharpCode.SharpZipLib
- `SharpCompress` — multi-format archive library
- `System.Formats.Tar.TarFile.ExtractToDirectory` (.NET 7+)

### Zip Slip Patterns
- `entry.FullName` contains `../` → written outside the target directory
- Symlink entries → pointing to sensitive files
- Overlong paths → path truncation

## XXE / XML External Entities

### XML Parsers
- `System.Xml.XmlDocument.LoadXml` / `Load`
- `System.Xml.XPath.XPathDocument`
- `System.Xml.Linq.XDocument.Load` / `Parse`
- `System.Xml.XmlReader.Create` — check XmlReaderSettings
- `System.Xml.Xsl.XslCompiledTransform.Load` — XSLT injection

### Key Settings
- `XmlReaderSettings.DtdProcessing` — Prohibit / Ignore / Parse
- `XmlReaderSettings.XmlResolver` — null is safe
- `XmlDocument.XmlResolver` — set to null to disable external entities
- `XmlTextReader.DtdProcessing` — legacy API

### Dangerous Defaults
- Before .NET Framework 4.5.1: `XmlDocument` allows DTD by default
- .NET Framework 4.5.2+: disabled by default (but explicitly enabling remains dangerous)
- .NET Core / .NET 5+: safe by default (DtdProcessing.Prohibit)

## DESER / Deserialization

### High-Risk Serializers (Prohibited Class)
- `System.Runtime.Serialization.Formatters.Binary.BinaryFormatter`
- `System.Runtime.Serialization.NetDataContractSerializer`
- `System.Web.UI.LosFormatter` / `ObjectStateFormatter` (legacy WebForms)
- `System.Runtime.Serialization.Formatters.Soap.SoapFormatter`

### Conditionally Dangerous Serializers
- `Newtonsoft.Json` — dangerous when `TypeNameHandling != None`
- `System.Text.Json` — custom JsonConverter may introduce type confusion
- `System.Runtime.Serialization.DataContractSerializer` — improper known-type lists
- `System.Xml.Serialization.XmlSerializer` — dangerous when the type parameter is controllable
- `MessagePack` — dangerous when typeless mode is enabled
- `protobuf-net` — dangerous when using `DynamicType`

### Gadget Chain Entry Points
- `ISerializable.GetObjectData` — custom serialization
- `IDeserializationCallback.OnDeserialization` — deserialization callback
- Methods marked with `[OnDeserialized]` / `[OnDeserializing]`
- `TypeNameHandling.All` / `Auto` / `Objects` / `Arrays`

## TPL / Template Injection and Expression Injection

### Razor Runtime Compilation
- `Microsoft.AspNetCore.Mvc.Razor.RuntimeCompilation` — dynamic templates
- `RazorEngine` / `RazorLight` — third-party Razor engines
- User-controlled template content → server-side code execution

### Expression Evaluation
- `Microsoft.CodeAnalysis.CSharp.Scripting.CSharpScript.EvaluateAsync`
- `System.Linq.Dynamic.Core` — Dynamic LINQ expressions
- `System.Data.DataTable.Compute` — expression computation
- `System.Data.DataColumn.Expression` — column expressions

### Other Template Engines
- `Scriban` — template injection
- `Fluid` — Liquid template engine
- `DotLiquid` — Liquid template engine
- `Handlebars.NET` — Handlebars templates
- Email template engines — user-controlled template variables or the template itself

## LDAP / Directory Service Injection

### Query APIs
- `System.DirectoryServices.DirectorySearcher.Filter` — LDAP filter concatenation
- `System.DirectoryServices.DirectorySearcher.FindAll` / `FindOne`
- `System.DirectoryServices.AccountManagement.PrincipalContext`
- `System.DirectoryServices.Protocols.SearchRequest` — filter parameter

### Injection Patterns
- Filter string concatenation: `$"(uid={userInput})"` — special characters not escaped
- DN concatenation: `$"CN={userInput},DC=corp,DC=local"` — DN injection
- Special characters: `*` / `(` / `)` / `\` / `NUL` — LDAP metacharacters

## EXPR / Expression Injection (Non-Template)

### Evaluation Entry Points
- `System.Linq.Dynamic.Core.DynamicQueryableExtensions` — Where / OrderBy / Select
- `Microsoft.CodeAnalysis.CSharp.Scripting.CSharpScript` — EvaluateAsync / RunAsync
- `System.Data.DataTable.Compute` — expression computation
- `System.Data.DataTable.Select` — filter expressions
- `System.ComponentModel.DataAnnotations.RegularExpressionAttribute` — ReDoS

### Indirect Expressions
- `System.Reflection.Assembly.Load` / `LoadFrom` — dynamic loading
- `Activator.CreateInstance` — controllable type name
- `Type.GetType` — controllable type string
- `MethodInfo.Invoke` — reflective invocation

## AUTH / Authentication and Authorization

### Authentication Mechanisms
- `[Authorize]` / `[AllowAnonymous]` — attribute declarations
- `AuthorizationPolicy` / `IAuthorizationRequirement` / `IAuthorizationHandler`
- `ClaimsPrincipal` / `ClaimsIdentity` — identity information
- JWT: `TokenValidationParameters` — signature algorithm, issuer, audience validation
- Cookie: `CookieAuthenticationOptions` — expiration, sliding window, encryption

### Authorization Checks
- `IAuthorizationService.AuthorizeAsync` — manual authorization check
- `HttpContext.User.IsInRole` / `HasClaim` — role/claim checks
- `[Authorize(Policy = "...")]` / `[Authorize(Roles = "...")]`
- Resource ownership check — `userId == resource.OwnerId` pattern

### IDOR / Broken Object Level Authorization
- Path parameter `{id}` without ownership validation
- Query parameters used directly in database queries without owner filtering
- Bulk-operation endpoints without per-item permission checks
- Admin endpoints hidden only on the frontend without backend validation

## CSRF / Cross-Site Request Forgery

### Protection Mechanisms
- `[ValidateAntiForgeryToken]` — MVC Action level
- `[AutoValidateAntiforgeryToken]` — global automatic
- `[IgnoreAntiforgeryToken]` — exemption marker
- `IAntiforgery.ValidateRequestAsync` — manual validation

### Bypass Scenarios
- API controllers do not enable Antiforgery by default
- `[HttpPost]` without `[ValidateAntiForgeryToken]`
- Content-Type bypass: `text/plain` does not trigger CORS preflight
- Subdomain cookie injection → token override

## SESS / Session and Cookie

### Cookie Configuration
- `CookieOptions.HttpOnly` — prevents XSS reads
- `CookieOptions.Secure` — HTTPS-only transport
- `CookieOptions.SameSite` — cross-site restrictions
- `CookieOptions.Expires` / `MaxAge` — expiration policy
- `CookieOptions.Domain` / `Path` — scope

### JWT Configuration
- `TokenValidationParameters.ValidateIssuerSigningKey` — signature validation
- `TokenValidationParameters.ValidAlgorithms` — algorithm whitelist
- `TokenValidationParameters.ClockSkew` — time skew
- `TokenValidationParameters.RequireExpirationTime` — expiration enforced

### Session Management
- `ISession` — server-side session
- Session ID rotation after login
- Cookie / Token / Session cleanup at logout
- Refresh token rotation and revocation

## CFG / Security Configuration

### CORS
- `AddCors` / `UseCors` — CORS policies
- `AllowAnyOrigin` + `AllowCredentials` — dangerous combination
- `WithOrigins("*")` — wildcard
- `SetIsOriginAllowed(_ => true)` — allow all

### Error Handling
- `UseDeveloperExceptionPage` — developer exception page (leaks in production)
- `UseExceptionHandler` — custom exception handling
- `app.Environment.IsDevelopment()` — environment check
- Detailed error information returned to clients

### Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` / `SAMEORIGIN`
- `Content-Security-Policy`
- `Strict-Transport-Security` (HSTS)
- `X-XSS-Protection` (deprecated but still checked)
- `Referrer-Policy`
- `Permissions-Policy`

### Dangerous Switches
- `Kestrel.Limits` — request size, timeouts
- `ForwardedHeadersOptions.ForwardLimit` — proxy trust
- `HostFilteringOptions` — host header filtering
- `JsonSerializerOptions.PropertyNameCaseInsensitive` — case confusion
- `appsettings.Development.json` overriding production configuration

## CRYPTO / Cryptography and Keys

### Weak Algorithms
- `MD5` / `SHA1` — hash collisions
- `DES` / `3DES` / `RC2` / `RC4` — weak encryption
- `RNGCryptoServiceProvider` vs `RandomNumberGenerator.Create` — randomness

### Key Management
- Hardcoded keys / connection strings
- Plaintext keys in `appsettings.json`
- `IDataProtectionProvider` — data protection API
- `X509Certificate2` — certificate loading and private key protection
- Azure Key Vault / AWS Secrets Manager integration

### Encryption Modes
- `CipherMode.ECB` — insecure mode
- `PaddingMode.PKCS7` — padding oracle
- IV reuse / fixed IV
- `Aes.Create()` — whether default parameters are safe

## LOGIC / Business Logic

### Mass Assignment
- `[Bind]` / `[BindNever]` — binding control
- `TryUpdateModel` / `TryUpdateModelAsync` — model update
- DTO sensitive fields missing `[JsonIgnore]` / `[BindNever]`
- `JsonPatchDocument.ApplyTo` — JSON Patch override

### Race Conditions
- `lock` / `Monitor` / `Semaphore` — concurrency control
- Database optimistic / pessimistic locking
- check-then-act patterns on balance / inventory / counters
- File operation TOCTOU (Time-of-check to time-of-use)

### State Machine Flaws
- State transitions in order / payment / approval flows
- Enum values bound directly from requests → illegal state transitions
- Operation endpoints missing precondition state validation

## LOG / Security Logging

### Log Injection
- `ILogger.LogInformation($"{userInput}")` — log forgery
- Newline injection → forged log entries
- Format string injection

### Sensitive Information Leakage
- Passwords, tokens, keys written to logs
- Full request/response body logging
- Connection strings in exception stacks
- PII data not desensitized

### Audit Coverage
- Authentication success/failure events
- Authorization denial events
- Sensitive operations (delete, permission change, export) events
- Administrator operation events

## QUERY / Non-SQL Query Languages

### SOQL (Salesforce Ecosystem)
- `ForceClient.QueryAsync<T>(soql)` — SOQL query string
- `SforceService.query(soql)` / REST `/query?q=` — query parameter concatenation
- SOQL string concatenation: `$"SELECT Id FROM Account WHERE Name = '{userInput}'"`

### OData
- OData URL concatenation: `$filter=` / `$orderby=` / `$select=` / `$expand=` parameters containing user input
- `ODataClient` / `Container` LINQ provider escaping into raw query strings
- Web API OData: `[EnableQuery]` + raw query option passthrough

### FetchXML (Dynamics 365 Ecosystem)
- `QueryExpression` condition values from user input (`new ConditionExpression(attr, op, userInput)`)
- FetchXML string concatenation: `<filter><condition value='{userInput}'>` direct concatenation
- `RetrieveMultiple(QueryBase)` / FetchXML execution entry points

### Injection Patterns
- Query fragments concatenated into executable structures (condition values, filter expressions, query bodies)
- Misuse of structured APIs: condition values of strongly-typed query objects without type/range validation

## EXPORT / Spreadsheet Export

### CSV/Excel Generators
- `CsvWriter` (CsvHelper) writing field values without formula neutralization
- `ExcelPackage` / `EPPlus`, `ClosedXML`, `NPOI` writing user data directly into cells without setting text format
- `StringWriter` / handwritten CSV concatenation: `string.Join(",", values)` direct output

### Formula Injection Patterns
- Cell values starting with `=` `+` `-` `@` interpreted by spreadsheets as formulas
- DDE payloads: `=cmd|' /C calc'!A1`-style command execution chains
- Hyperlink injection: `HYPERLINK("https://evil", "click")` phishing chains

## PROMPT / AI Prompt Assembly and Tool Calls

### Prompt Assembly
- PromptTemplate / template string interpolation containing user input (Semantic Kernel `KernelFunction`, Azure.AI.OpenAI `ChatCompletion`)
- RAG pipelines: vector retrieval results (untrusted document content) concatenated directly into the prompt context
- Missing system prompt / data boundary: retrieved or tool-returned content placed in a system-instruction role slot

### Tool/Function Calls
- Function calling definitions: tool permission scope larger than the task requires
- LLM output JSON parsed and directly driving downstream actions (queries, sends, execution)
- Output entering sensitive operations without validation / human confirmation gates
