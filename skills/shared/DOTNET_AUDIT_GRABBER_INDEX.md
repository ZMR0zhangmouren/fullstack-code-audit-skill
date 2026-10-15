# .NET Audit Grabber Index

This file unifies the search keywords, priority enumeration targets, and common landing points across skills, reducing divergence between skills during the enumeration phase.

## Usage Rules

- Search with this index by the five layers: entry definition, binding/conversion, precondition controls, business execution, sensitive operations
- Search exact API / attribute / type names first, then project-internal wrapper names, infrastructure directories, extension methods, and registration code
- Each skill's "Enumeration Rules (Mandatory Refinement)" must at least cover the keywords, object types, and record fields corresponding to this index
- If the project has secondary encapsulation, the wrapper names must be appended back into this skill's output, forming a project-internal private grabber table

## Entry Definition Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| MVC / Web API | Controller, ControllerBase, ActionResult, Route, HttpGet, HttpPost, AcceptVerbs, Area, ApiVersion | Route template, HTTP method, authorization metadata, return type |
| Minimal API | MapGet, MapPost, MapGroup, RouteGroupBuilder, EndpointFilter, Results | Endpoint delegate, group prefix, filters, metadata |
| SignalR | Hub, HubFilter, OnConnectedAsync, SendAsync, Groups | Connection entry, Hub methods, broadcast scope |
| GraphQL | AddGraphQL, QueryType, MutationType, SubscriptionType, Resolver, DataLoader | Field entry, call type, authorization and batching |
| WCF | ServiceContract, OperationContract, BasicHttpBinding, WSHttpBinding, ServiceHost | Service contract, binding, security mode |

## Cross-File Call Chain Tools (Optional Acceleration)

If the target project has a CodeGraph index (`.codegraph/` directory exists), the following tools can accelerate cross-file call chain and symbol retrieval:

| Tool/Command | Purpose | Applicable Scenarios |
| ---- | ---- | ---- |
| `codegraph explore` | Get related symbol sources, call paths, impact radius | Route identification, Controller/Action enumeration, call chain tracing |
| `codegraph_callers` | Get callers of a symbol | Upstream call chain from entry to Sink |
| `codegraph_impact` | Analyze change impact radius | DI resolution chains, cross-file dependency tracing |
| `codegraph query --kind` | Retrieve symbols by kind | Class, method, interface enumeration |

Usage constraints:
- CodeGraph is only a supplement to information retrieval; it does not replace audit rules and evidence closure
- Without an index, fall back 100% to the existing static analysis process
- Symbols and call chains returned by CodeGraph still require cross-validation with source code snippets

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| MVC / Web API | Controller, ControllerBase, ActionResult, Route, HttpGet, HttpPost, AcceptVerbs, Area, ApiVersion | Route template, HTTP method, authorization metadata, return type |
| Minimal API | MapGet, MapPost, MapGroup, RouteGroupBuilder, EndpointFilter, Results | Endpoint delegate, group prefix, filters, metadata |
| SignalR | Hub, HubFilter, OnConnectedAsync, SendAsync, Groups | Connection entry, Hub methods, broadcast scope |
| GraphQL | AddGraphQL, QueryType, MutationType, SubscriptionType, Resolver, DataLoader | Field entry, call type, authorization and batching |
| WCF | ServiceContract, OperationContract, BasicHttpBinding, WSHttpBinding, ServiceHost | Service contract, binding, security mode |

## Binding and Conversion Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| Parameter sources | FromRoute, FromQuery, FromBody, FromForm, FromHeader, BindProperty, SupplyParameterFromQuery | Binding source, name mapping, default values |
| Complex binding | ModelBinder, IModelBinder, BinderProvider, ValueProvider, TryUpdateModel, UpdateModel | Complex object expanded fields, overridable fields |
| Type conversion | JsonConverter, TypeConverter, BindAsync, TryParse, IParsable, JsonPatchDocument | Conversion logic, exception swallowing, fallback behavior |
| File input | IFormFile, IFormFileCollection, MultipartReader, OpenReadStream, CopyToAsync | File name, content type, landing location |

## Precondition Control Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| Middleware | UseRouting, UseAuthentication, UseAuthorization, UseCors, UseSession, UseWhen, MapWhen, ForwardedHeaders | Order, short-circuit conditions, context modification |
| MVC / API filters | Authorize, AllowAnonymous, ActionFilter, ResultFilter, ExceptionFilter, ValidateAntiForgeryToken | Execution order, short-circuit, parameter/result modification |
| Endpoint / Hub / GraphQL | EndpointFilter, HubFilter, AuthorizeView, GraphQL middleware | Scope, authorization coverage, field-level restrictions |
| WCF behaviors | MessageInspector, ServiceAuthorizationManager, BehaviorExtension | Message modification, identity validation, exception output |

## Sensitive Operation Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| SQL | SqlCommand, DbCommand, FromSqlRaw, ExecuteSqlRaw, Query, Execute | SQL source, parameter objects, dynamic fragments |
| NoSQL | BsonDocument, FilterDefinition, Builders, Cosmos query | Query object source, concatenated fragments |
| KQL | LogsQueryClient, QueryWorkspace, QueryResource, MetricsQueryClient, OperationalInsightsDataClient, AnalyticsClient, TelemetryClient.Query | KQL source, parameter objects, dynamic fragments (table/column names/where/extend/project/pipeline appends) |
| CMD | Process.Start, cmd.exe, powershell, ArgumentList | Command construction, shell involvement |
| CMD | Process.Start, cmd.exe, powershell, ArgumentList | Command construction, shell involvement |
| SSRF | HttpClient, WebRequest.Create, HttpWebRequest, RestClient | URL source, protocol/host restrictions |
| File | File.ReadAllText, File.WriteAllText, PhysicalFile, CopyToAsync, ExtractToDirectory | Path source, normalization, write or read location |
| XML / XXE | XmlReader, XmlDocument, XDocument, XslCompiledTransform, DtdProcessing | Parser configuration, external entity switches |
| Deserialization | BinaryFormatter, NetDataContractSerializer, TypeNameHandling, LosFormatter | Type information, input source, whitelist |
| Template / expression | Razor, MarkupString, CSharpScript, Dynamic LINQ, DataTable.Compute | Template source, context, execution privileges |

## Security Configuration Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| Authentication / authorization | AddAuthentication, AddAuthorization, Authorize, Policy, Role, Claim | Scheme selection, policy binding, anonymous exceptions |
| Session & cookie | AddSession, CookieOptions, SameSite, HttpOnly, SecurePolicy | Attributes, scope, cross-site behavior |
| CSRF | AddAntiforgery, ValidateAntiForgeryToken, AutoValidateAntiforgeryToken, IgnoreAntiforgeryToken | Token generation and validation, exception paths |
| Configuration | appsettings, web.config, Configure(T), BindConfiguration, Environment | Security switches, environment overrides, runtime rewriting |
| Logging | ILogger, LogInformation, LogError, BeginScope, Serilog, NLog | Sensitive fields, exceptions, audit trails |

## Project-Internal Encapsulation Supplement Requirements

- When secondary encapsulations such as Repository, Client, Gateway, Manager, Executor, Dispatcher, Helper, Extension are found, the wrapper names must be added to the "Project-Internal Grabbers" section of the current skill's output
- Unified exception-handling middleware, unified authentication wrappers, unified HttpClient factories, and unified template renderers must be repeatedly referenced as cross-skill common grabbers
- If the same project has MVC, Minimal API, SignalR, GraphQL, and WCF simultaneously, separate grabber subsets must be built for each; mixing them into a single entry model is forbidden

## Supply Chain Tool References (dotnet-supply-chain-audit Integration)

| Tool | Usage | Evidence Landing Point |
| ---- | ---- | ---- |
| dotnet list package --vulnerable | Built into .NET 8+; `dotnet list <sln/csproj> package --vulnerable` | EVID_SUPPLY_CVE_MATCH / EVID_SUPPLY_TOOL_OUTPUT |
| osv-scanner | `osv-scanner --format json --lockfile NuGet.lock.json`; offline `--offline-vulnerabilities` | EVID_SUPPLY_TOOL_OUTPUT |
| NuGet Advisory offline comparison | Manual comparison against advisory sources package by package | EVID_SUPPLY_CVE_MATCH (labeled Pending Verification) |
