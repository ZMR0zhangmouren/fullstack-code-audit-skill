---
name: node-nestjs-audit
description: Node.js NestJS framework specialty audit tool. Performs white-box audits of NestJS decorator routes and parameter binding, the Guard / Interceptor / Pipe / Filter pipeline, ValidationPipe configuration, module injection boundaries, and runtime configuration.
---

# NestJS Framework Specialty Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the NestJS-related grabbers of entry definitions (`@Controller` / `@Get` decorator routes), parameter binding (`@Body` / `@Query` / `@Param`), the Guard / Interceptor / Pipe / Filter pipeline, ValidationPipe configuration, module injection, and global configuration
- If the project has unified decorator wrappers, base class controllers, dynamically registered modules (`forRoot` / `forFeature`), or global Guard / Pipe factories, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (core input of this specialty: align decorator route entries with `@Param` / `@Query` / `@Body` parameter bindings and `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware / Guard coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to align anonymous entries, P0/P1 bucketing, and Guard coverage)
- Optional: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` (used to cross-reference parameter binding risks with specific entries and side-effect chains)
- Optional: `node/vuln_audit/*_{timestamp}.md` (used to corroborate with vulnerability specialties such as nosql / cmd / upload / xss)
- Optional: `cross/api_contract_map_{timestamp}.md` (used to align BFF forwarding or isomorphic parameter sources)

## Key Checks

- Decorator parameter binding not sanitized by default: `@Body()` / `@Query()` / `@Param()` binding objects / fields directly into business logic or sinks without explicit validation
- ValidationPipe not enabled or `whitelist: true` not configured: extra fields passing through (mass assignment), missing DTO validation
- Guard → Interceptor → Pipe → Handler → Interceptor → Filter execution order and short-circuits: Guards execute before Pipes (route-level combinations where validation can pass but authentication comes later), coverage gaps between global and route-level Guards
- Global Guard / global prefix configuration: the interplay of `app.useGlobalGuards` / `setGlobalPrefix` with controller-level `@UseGuards` (missing global Guard → coverage relying on per-controller mounting)
- Exception Filter default behavior: without a custom `ExceptionFilter`, default responses output stacks / internal paths (coordinating with `EVID_NODE_CFG_ERR_HANDLER`)
- `@UploadedFile()` upload chain: `FileInterceptor` / `FileFieldsInterceptor` configuration and landing paths (coordinating with node-file-upload-audit)
- Module injection boundaries: `forRoot` / `forFeature` dynamic modules, `@Global()` modules, provider overrides (`useValue` / `useFactory`) causing authentication / validation injection replacement

## Enumeration Rules (Mandatory Refinement)

### 1. Framework Boundary Layer

- Enumerate entry definition styles: `@Controller()` controllers and `@Get` / `@Post` / `@Put` / `@Delete` / `@All` method decorators, `@Header` / `@Redirect` response decorators, dynamic routes (`:param` wildcards, `*splat` wildcards)
- Enumerate parameter binding points: field extraction of `@Body()` / `@Query()` / `@Param()` / `@Headers()` / `@Req()` and paths passing straight into business logic / sinks
- Identify request lifecycle boundaries: request → Middleware → Guard → Interceptor(pre) → Pipe → Handler → Interceptor(post) → ExceptionFilter → response, annotating the short-circuit condition of each level
- Identify module injection boundaries: `@Module` imports / controllers / providers, `forRoot` / `forFeature` dynamic registration, `@Global()` modules and provider overrides (`useClass` / `useValue` / `useFactory`)

### 2. Runtime Configuration Layer

- Enumerate ValidationPipe configuration: `whitelist` / `forbidNonWhitelisted` / `transform` options of `app.useGlobalPipes(new ValidationPipe(...))`, DTO class-validator decorator (`@IsString` / `@IsInt`, etc.) coverage
- Enumerate global configuration: `app.setGlobalPrefix`, `app.enableCors` (wildcard + `credentials` combination), `app.useGlobalGuards` / `app.useGlobalInterceptors` / `app.useGlobalFilters` and their superposition with route-level decorators
- Enumerate exception handling configuration: whether `@Catch()` / `AllExceptionsFilter` / `HttpExceptionFilter` are customized, whether default responses contain stacks and internal paths (`EVID_NODE_CFG_ERR_HANDLER`)
- Enumerate environment variable read points: `isGlobal` / `validationSchema` of `ConfigModule` / `@nestjs/config`, direct `process.env` reads, `.env` file sensitive items
- Enumerate upload configuration: `limits` / `fileFilter` / `dest` of `FileInterceptor` / `FileFieldsInterceptor` / `AnyFilesInterceptor` and `@UploadedFile()` landing paths (coordinating with node-file-upload-audit)

### 3. Precondition Control Plane Layer

- Enumerate Guard coverage: whether `@UseGuards(AuthGuard)` is global `useGlobalGuards` or per-controller / per-method, `@Public()` / `@SkipAuth()` exemption decorators, Guard coverage of dynamically registered routes
- Identify Guard short-circuit conditions: fail-close branches of Guard `canActivate` return values / thrown exceptions, default behavior when reflection metadata (`@Roles`, etc.) reads fail
- Enumerate Interceptors and Filters: execution timing of `@UseInterceptors` (logging / rate limiting / transformation) and `@UseFilters`, handling of exceptions swallowed by Interceptors or raw errors passed through
- Enumerate rate limiting and request size limits: `@nestjs/throttler` configuration, body size limits, upload file size limits

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| ValidationPipe | `app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true }))` | Check whether the global Pipe is registered, whether `whitelist` is enabled, and whether DTO classes carry class-validator decorators | `whitelist` enabled with DTO coverage → ✅ safe; Pipe not registered or `whitelist` missing → 🔴 high risk of extra field passthrough |
| Guard coverage | `app.useGlobalGuards(AuthGuard)` or per-controller `@UseGuards` | Compare the route / controller list with Guard coverage, including dynamically registered modules and `@Public` exemption surfaces | global or per-route fail-close → ✅ safe; reachable routes without Guards exist → 🔴 high risk |
| pipeline order | default pipeline with Guard executing before Pipe | Check the registration layers of Guards and ValidationPipe, confirming authentication short-circuits before parameter binding / validation | authentication before business execution with unconditional passage → ✅ safe; validation first allowing authentication bypass → ⚠️ to be confirmed |
| exception Filter | `@Catch()` custom `AllExceptionsFilter` | Check whether a custom global Filter is registered and whether responses contain stacks / internal paths | custom Filter with sanitized responses → ✅ safe; missing or passing through default errors → 🔴 default stack leakage (fail-open) |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Risk Candidate`: missing framework configuration or control plane may allow external input to bypass, privilege escalation, or sensitive information exposure
- `Pending`: the context shows a suspicious pattern, but the entry coverage, barrier behavior, or call chain is unclear
- `False Positive`: the configuration has fail-close explicitly enabled, or the risk point is already covered by another control plane

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found linking the framework control plane to a specific entry / sink → `Confirmed Risk`
- Fixed whitelist mapping / fail-close evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_CFG_SECURITY_SWITCH` shows ValidationPipe not registered or `whitelist` missing, with `@Body()` binding objects straight into business / sinks and extra fields consumed (mass assignment)
- `EVID_NODE_CFG_MIDDLEWARE_ORDER` shows Guards mounted only on some controllers (`@UseGuards` per route rather than global) or reachable routes without Guards exist, and the `@Public` exemption surface is overly broad
- `EVID_NODE_CFG_ERR_HANDLER` shows no custom ExceptionFilter, with default error responses containing stacks / internal paths (fail-open)
- `EVID_NODE_CFG_RUNTIME_SETTING` shows missing global configuration (`setGlobalPrefix` / `useGlobalGuards` / `enableCors`) or CORS wildcard + `credentials` combination with a protected interface carrying cookies
- The `@UploadedFile()` upload chain lacks `fileFilter` / `limits` and the landing path contains user input → coordinate with node-file-upload-audit to confirm (`EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG`)

### ⚠️Pending Verification

- The superposition behavior of Guards and Pipes (validation first causing authentication to come later) depends on framework versions and decorator combinations; not all short-circuit paths can be confirmed statically (`EVID_NODE_CFG_MIDDLEWARE_ORDER`)
- Provider overrides (`useValue` / `useFactory`) in dynamic modules (`forRoot` / `forFeature`) cause authentication / validation replacement; the real injection chain needs unwrapping for confirmation
- Whether missing class-validator validation is exploitable depends on the fields actually consumed by DTOs; tracing to the sink is needed for confirmation
- Whether default error responses leak stacks depends on the runtime `NODE_ENV` and framework version behaviors; the deployment environment cannot be confirmed statically
- AuthGuard / JWT strategy configuration (`jwt.verify` algorithm / key source, cookie flags) depends on versions and deployment behaviors; not all validation surfaces can be confirmed statically (`EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG` / `EVID_NODE_SESS_COOKIE_FLAGS`)

### False Positive

- ValidationPipe globally registered with `whitelist: true` + `forbidNonWhitelisted: true`, and DTO class validation decorators covering all consumed fields
- Guard global `useGlobalGuards` before all controllers and fail-close (unauthenticated requests directly rejected), with the `@Public` exemption surface minimized
- Custom ExceptionFilter registered and response content sanitized (no stacks / internal paths)
- The `@UploadedFile()` chain configures a `fileFilter` whitelist and size `limits`, with a fixed landing path

## Testing Recommendations (Mandatory)

### Positive Testing

- Send a body with extra fields to a route with ValidationPipe → should be stripped / rejected (whitelist / forbidNonWhitelisted effective)
- Request a controller route without Guards and without authentication → should be rejected (401 / 403), verifying Guard coverage
- Trigger an exception request → the response should be a sanitized error without stacks / internal paths
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- Legitimate requests with valid tokens pass through Guard / Pipe normally into the handler
- Legitimate bodies pass DTO validation and are consumed normally, without wrongful rejection
- In production mode (`NODE_ENV=production`), exception responses do not leak stacks

### Regression Testing

- Newly added controllers / methods must be included in the Guard coverage list before retesting
- Re-verify extra field passthrough and DTO validation after ValidationPipe configuration changes
- Re-verify coverage and cross-origin surfaces after global configuration (prefix / Guard / CORS) changes

## Evidence References

- `EVID_NODE_CFG_MIDDLEWARE_ORDER` (Guard / Interceptor / Pipe execution order and short-circuit condition evidence)
- `EVID_NODE_CFG_SECURITY_SWITCH` (ValidationPipe whitelist, CORS, global configuration switch evidence)
- `EVID_NODE_CFG_ERR_HANDLER` (exception Filter and stack leakage evidence)
- `EVID_NODE_CFG_RUNTIME_SETTING` (ConfigModule / environment variable visibility evidence)
- `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG` (`@UploadedFile()` upload chain configuration surface, coordinating with node-file-upload-audit)
- `EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG` and `EVID_NODE_SESS_COOKIE_FLAGS` (AuthGuard / JWT strategy configuration surface, coordinating with node-auth-audit / node-session-cookie-audit)

## Output

- `node/framework_audit/nestjs_{timestamp}.md`
- Must state: entry types and mount styles (decorator routes / controllers), parameter binding points and sanitization status, Guard / Interceptor / Pipe / Filter pipeline order and short-circuit conditions, ValidationPipe configuration, global vs route-level guard coverage, exception Filter behavior, upload chain configuration, module injection boundaries
- Must state environment differences: `NODE_ENV` branches, global configuration and development / production differences, framework version behavior differences
- Consumption relationships: when affecting strong vulnerability conclusions, it must be explicitly stated how it is consumed by `node/route_tracer`, each `node-vuln-audit` specialty (nosql / cmd / upload / xss, etc.), and `node-audit-pipeline`
