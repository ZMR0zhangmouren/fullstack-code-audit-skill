---
name: dotnet-grpc-audit
description: .NET gRPC microservice communication security audit tool. Performs white-box auditing of gRPC service framework boundaries, Proto file parsing, metadata security, streaming communication, and service-to-service authentication.
---

# gRPC Microservice Communication Security Audit

## Shared Grabber Index References

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as this Skill's base retrieval index
- By default, use shared/DOTNET_SINK_REFERENCE.md as this specialty's sink type definition and trace-gate validation baseline
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover gRPC-related entry definitions, binding conversions, pre-controls, sensitive operations, and security configuration grabbers
- If the project has gRPC secondary encapsulation, unified interceptors, a client factory, or a service registration wrapper layer, they must be added to the in-project grabbers section of the output
- When this Skill's specialty enumeration rules are more detailed than the shared index, this Skill prevails, but the shared index's base coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` (if the project has gRPC-HTTP mapped entries, used to align Proto methods with route mappings)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (if service-to-service mTLS, token authorization, or CallCredentials need to be aligned)
- Optional: `route_tracer/{route_id}/trace_{timestamp}.md` (if the gRPC control plane needs to be cross-referenced with specific entries and side-effect chains)
- Recommended scan: `*.proto` files (Proto definitions and service contracts)

## Key Checks

### gRPC Server Entry Points

- Grpc.Core bindings: `Server.*\.BindService` / `ServerBuilder` / `Grpc.Core.Server`
- Grpc.Net.Client clients: `GrpcChannel` / `CallInvoker` / `HttpMessageHandler` configuration
- Proto-generated code: `GrpcClientBase` / `ClientBase` inheritance chains
- Service registration: `AddGrpc()` / `UseGrpcWeb()` middleware configuration

### Proto Files and Service Contracts

- Proto file paths and content: `import`, `package`, `service`, `rpc` definitions
- Unsafe field types in Proto-generated code: `bytes`, `repeated`, nested messages
- Proto option safety: `deprecated`, `client_streaming`, `server_streaming` markers
- Unencrypted fields: whether passwords, tokens, and key fields are exposed in plaintext

### gRPC Metadata Security

- `Metadata` reads: `context.RequestHeaders` / `ServerCallContext.RequestHeaders`
- Metadata propagation chains: client → server / service-to-service forwarding
- Sensitive headers: `authorization`, `x-forwarded-*`, `custom-auth` propagation
- Metadata injection: controllable points of `Metadata.Add()`
- gRPC-Web scenarios: `Grpc-Web-Authorization` header handling

### Streaming RPC Security

- Server streaming: handling of `stream`-typed parameters and responses
- Client streaming: request aggregation and boundary control
- Bidirectional streams: use of `IAsyncStreamReader<T>` / `IServerStreamWriter<T>`
- Flow control: `WriteOptions` / `WriteOptions.Flags` configuration
- Streaming denial of service: stream count limits, timeout configuration

### Service-to-Service Authentication (CallCredentials)

- `CallCredentials` configuration: `CallCredentials.FromInterceptor` / `CallCredentials.FromMetadataProvider`
- Token propagation: `Authorization` header construction and refresh
- mTLS configuration: `SslCredentials` / TLS settings in `GrpcChannelOptions`
- Cross-service delegation: `CallCredentials.Interceptorception` chains
- Credential leakage: whether credentials are written to logs or exposed in traces

### gRPC-Web Security

- gRPC-Web middleware: `UseGrpcWeb()` configuration and CORS integration
- Proxy forwarding: `grpc-web-text` encoding handling
- HTTP/1.1 downgrade: security differences from HTTP/2 gRPC
- Preflight requests: `OPTIONS` method and cross-origin configuration

### Proto Code Generation Risks

- Unsafe Proto generation: use of `google/protobuf/any.proto`
- Dynamic type deserialization: `google.protobuf.Any` type resolution
- Proto-to-DTO mapping: injection risks of automatic mapping tools
- Version compatibility: Proto changes and backward compatibility

## Enumeration Rules (Mandatory Refinement)

### gRPC Entry Detection

Search the following keywords and record:

```
Grpc.Core.Server
Grpc.Core.BindService
ServerBuilder.AddService
Grpc.Net.Client.GrpcChannel
Grpc.Net.Client.CallInvoker
HttpRequestHandler (gRPC-Web)
AddGrpc()
UseGrpcWeb()
```

### Proto File Scanning

Scan `*.proto` files and record:

```
service {service_name} {{
  rpc {method_name}({input_type}) returns ({output_type});
}}
// mark unsafe fields
// mark streaming methods
```

### Metadata Security Check

Search the following patterns:

```
Metadata.FromIncomingHeaders()
context.RequestHeaders
ServerCallContext.RequestHeaders
Metadata.Add(
GrpcWeb-Authorization
authorization
x-forwarded
```

### Authentication and Credential Check

Search the following patterns:

```
CallCredentials
SslCredentials
GrpcChannelOptions
ChannelCredentials
MetadataCredentials
UseEncryption
InsecureServerOption
```

### Streaming Method Identification

Search the following patterns and record stream types:

```
IAsyncStreamReader
IServerStreamWriter
IStreamObserver
stream rpc
ClientStreamingMethod
ServerStreamingMethod
BidiStreamingMethod
```

### gRPC-Web Configuration Check

Search the following patterns:

```
UseGrpcWeb()
EnableGrpcWeb()
GrpcWebOptions
CorsPolicy (for gRPC)
```

## Barrier Verification Matrix (Mandatory)

Assess against the fail-close three-tier standard in `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Tier | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Tier 1 | gRPC service exists and is reachable | Grpc.Core.Server/GrpcChannel exists and a client can actually establish a connection and call it | BLOCKED → no reachable gRPC service; the specialty is deprioritized |
| Tier 2 | Metadata/credentials have security issues | Metadata/CallCredentials propagation chain broken, InsecureServerOption enabled, or mTLS configuration missing | BLOCKED → metadata and credential chains are complete and safe; conclusion degraded |
| Tier 3 | Streaming/Proto risks are exploitable | Streaming methods unauthorized/unthrottled, Proto bytes types cause deserialization risks, or gRPC-Web downgrade introduces cross-origin issues | PARTIAL → only potential risks and verification steps are output |

## Two-Phase Determination Flow (Mandatory)

- **Phase 1 (Initial Screening Hit)**: gRPC service binding + metadata/credential configuration + streaming/Proto risk hit; output `Hit ID: M{hash}`.
- **Phase 2 (Refined Confirmation)**:
  1. Trace in reverse: Proto service/rpc → gRPC service binding → interceptor/credentials chain;
  2. Verify the Metadata/CallCredentials/SslCredentials propagation chain and InsecureServerOption configuration;
  3. Assess streaming method authorization/throttling, Proto bytes deserialization, and gRPC-Web CORS downgrade risks;
  4. If all three barrier tiers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priority (Mandatory)

1. **Confirmed Vulnerability**: gRPC service reachable + metadata/credentials unsafe + streaming/Proto risk exploitable. Output `Confirmed Vulnerability`.
2. **Pending Confirmation**: gRPC/metadata/streaming evidence partially exists, but interceptor order or scale-out behavior cannot be proven. Output `Pending Confirmation`.
3. **False Positive / No Risk**: gRPC service unreachable or protected, mTLS/CallCredentials complete, streaming has authorization and throttling, Proto definitions safe. Output `False Positive` with determination basis.

## Testing Suggestions and Minimum Trigger Conditions (Mandatory)

- **Minimum Trigger Conditions**:
  - A gRPC service exists (Grpc.Core/Grpc.Net.Client)
  - A client can establish a connection and call rpc methods
  - Or the Metadata/CallCredentials propagation chain is broken, InsecureServerOption enabled
  - Or streaming methods are unauthorized, Proto bytes types are unsafe
- **Test Case Suggestions**:
  - Happy Path: a normal gRPC request is processed through mTLS and CallCredentials, returning a correct response
  - Edge/Ambiguity: Metadata header injection, InsecureServerOption plaintext transmission, unthrottled streaming DoS, Proto Any type deserialization, gRPC-Web CORS bypass
- Each hit output appends `Hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Evidence References
```

## Evidence References

- EVID_GRPC_SERVER_BIND: gRPC service binding entry evidence
- EVID_GRPC_METADATA_SOURCE: Metadata source and propagation chain evidence
- EVID_GRPC_STREAM_HANDLER: streaming handler entry evidence
- EVID_GRPC_CREDS_CONFIG: CallCredentials / TLS configuration evidence
- EVID_GRPC_PROTO_DEFINITION: Proto definition and service contract evidence
- EVID_GRPC_WEB_ENDPOINT: gRPC-Web endpoint exposure evidence
- EVID_AUTH_PATH_PROTECTED_MATCH: protected entry match evidence (cross-specialty)
- EVID_SESS_JWT_VERIFY_CLAIMS: JWT validation evidence (cross-specialty)

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (e.g. `route_mapping` / `route_tracer` / `framework_audit`), confirm dependencies are available and timestamps are consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: write to the agreed path per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing-evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (Service Entry Confirmation)**: must confirm gRPC service binding points and Proto method mapping.
- 🔴 **CHECKPOINT B (Metadata and Credentials Confirmation)**: must confirm the Metadata/CallCredentials propagation chain.
- 🔴 **CHECKPOINT C (Streaming Boundary Confirmation)**: must confirm the authorization and throttling boundaries of streaming methods.
- 🛑 **STOP**: if the service contract and authentication chain are not closed, the conclusion is degraded to `⚠️Pending Verification / Environment-Dependent`.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback if Still Failing |
|---|---|---|
| Proto contract and service binding mapping incomplete | Fill in `service/rpc -> bind/register` evidence | Degrade to `⚠️Pending Verification / Environment-Dependent` |
| Metadata/credential propagation chain broken | Trace key header propagation from client to server | Do not output a bypass confirmation yet; give only a verification path |
| Insufficient streaming authorization and throttling evidence | Fill in streaming method permissions and quota configuration | Assess the risk conservatively; no strong conclusion |

🔴 **STOP: when any fallback is triggered, outputting a strong "authentication bypassable" conclusion is forbidden.**

## Resource References & Reachability Validation (Mandatory)

- Required shared index references: `skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md` (grabber sources) and `skills/shared/EVIDENCE_POINT_IDS.md` (evidence criteria).
- Output criteria validation: on-disk paths and naming must align with `skills/shared/IO_PATH_CONVENTION.md`; custom deviations from the directory structure are not allowed.
- Evidence consistency validation: if severity-graded conclusions are cited, they must be consistent with `skills/shared/SEVERITY_RATING.md`.
- Reachability check: before submission, confirm at least once that key referenced files are accessible (e.g. `DOTNET_AUDIT_GRABBER_INDEX.md`, `IO_PATH_CONVENTION.md`).

## Measured Test Cases and Pass Criteria (Mandatory)

- Execute at least 2 typical test cases before each output (happy path + 1 edge/ambiguity scenario), and record expected vs actual differences.
- `full_test >= 1` is required by default; if only `dry_run` is possible, `confidence=LOW` must be marked in the conclusion, with a make-up test plan and owner.
- Pass criteria: key fields complete, evidence chain traceable, conclusion level consistent with gate status; if any fails, marking "passed/deliverable" is forbidden.

## Overall Architecture and Redundancy Control (Mandatory)

- Section organization must keep the three-layer skeleton: `Input Constraints` → `Execution Steps` → `Output and Acceptance`; no layer may be missing or mixed across layers.
- A single paragraph should not exceed 6 lines; synonymous rules must not appear more than twice; duplicated content must be merged into a single source-of-truth section.
- AI-isms and empty filler transitions are forbidden (e.g. "first/second/finally/in summary/put simply/in other words"); any found must be rewritten as executable statements.

## Quality Gate & Assessment Consistency (Mandatory)

- A minimal gate self-check must be executed before producing output: `input completeness`, `key evidence hit`, `output path valid` — all three must be PASS.
- If any of `key evidence missing`, `chain not closed`, `consistency_check_status=BLOCKED` holds, the conclusion must be degraded to `BLOCKED`; outputting "confirmed exploitable/deliverable" is forbidden.
- The report must explicitly record: `gate_status`, `blocked_reasons`, `recheck_action`, and be traceably aligned with the `quality/*` artifacts.

## Do NOT Do (Anti-Pattern Blacklist)

- Anti-pattern: only looking at Proto definitions without the runtime interceptor chain. Correct approach: audit together with service bindings, interceptors, and credential configuration.
- Anti-pattern: ignoring Metadata pass-through pollution. Correct approach: trace key headers from client to server.
- Anti-pattern: equating gRPC-Web security with native gRPC security. Correct approach: distinguish HTTP/1.1 downgrade and cross-origin boundaries.
- Anti-pattern: judging authentication bypassable with insufficient evidence. Correct approach: degrade to `⚠️Pending Verification / Environment-Dependent`.

## Executable Parameters and Output Templates (Mandatory)

- Audit conclusion level: `Confirmed` / `⚠️Pending Verification` / `Not Applicable` (choose exactly one; leaving blank is forbidden).
- Minimum evidence set: must include at least the five items `entry point`, `controllable parameters`, `key calls`, `security boundary`, `missing evidence`.
- Output file naming: uniformly use `{topic}_{timestamp}.md`, aligned with `IO_PATH_CONVENTION.md`.
- Softening wording is forbidden: e.g. "possibly at risk / worth noting / depends on the situation / very likely"; when evidence is insufficient, must explicitly write `⚠️Pending Verification` and the next follow-up confirmation action.

Minimal output snippet (directly reusable):

```md
- Audit conclusion level: Confirmed
- Minimum evidence set: entry point=...; controllable parameters=...; key calls=...; security boundary=...; missing evidence=none
- Next action: if gaps exist, supplement parameter propagation evidence for trace_id=...
```

## Output

- framework_audit/grpc_{timestamp}.md
- Must state: service entry types, Proto contract mapping, Metadata security surface, streaming communication risks, authentication configuration, and linkage with the authentication/session specialties
- If credential leakage or an authentication bypass is found, additionally output `vuln_poc/grpc_{timestamp}.md`

## Linkage with Other Specialties

- The `route_id` or `service_id` produced by this Skill can be passed to `dotnet-auth-audit` for service-to-service authentication checks
- Tokens in `Metadata` can be passed to `dotnet-session-cookie-audit` for session validation
- `bytes` types in Proto definitions may involve risks related to `dotnet-deser-audit`
