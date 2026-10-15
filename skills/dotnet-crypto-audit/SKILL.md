---
name: dotnet-crypto-audit
description: .NET cryptography and key security audit tool. Identifies weak algorithms, hardcoded keys, insecure modes, randomness, and signature verification flaws.
---

# .NET Cryptography and Key Security Audit

## Shared Grabber Index References

- By default, use shared/DOTNET_AUDIT_GRABBER_INDEX.md as this Skill's base retrieval index
- By default, use shared/DOTNET_SINK_REFERENCE.md as this specialty's sink type definition and trace-gate validation baseline
- By default, follow the common execution standard in `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, testing requirements)
- Enumeration must at least cover shared grabbers related to algorithm selection, key generation, key storage, DataProtection, certificates, and token signing
- If the project has secondary encapsulations such as CryptoHelper, KeyStore, TokenSigner, PasswordHasherWrapper, they must be added to the in-project grabbers section of the output
- When this Skill's specialty enumeration rules are more detailed than the shared index, this Skill prevails, but the shared index's base coverage must not be reduced

## Input Dependencies

- Required: `source_path`
- Optional: `route_mapping/routes_{timestamp}.md` and `route_mapping/params_{timestamp}.md` (used to correlate login, signature, and encryption/decryption call entries with `route_id`)
- Optional: `auth_audit/auth_mapping_{timestamp}.md` (used to correlate authentication, tickets, and permission boundaries)
- Optional: `route_tracer/{route_id}/trace_{timestamp}.md` and `route_tracer/{route_id}/trace_summary_{timestamp}.md` (can serve as cross evidence of algorithm/key flaws affecting specific entries; not a hard prerequisite)

Key checks:

- MD5, SHA1, DES, 3DES, RC2, ECB, CBC with fixed IV, weak PBKDF parameters, insecure HMAC, and custom encryption wrappers
- Usage boundaries and misuse of Random, Guid, timestamps, predictable nonces, RNGCryptoServiceProvider / RandomNumberGenerator
- Sources, rotation, and storage locations of keys, IVs, salts, peppers, JWT signing keys, DataProtection keys, encryption certificates, and API secrets
- Key management modes in ASP.NET Core DataProtection, DPAPI, Azure Key Vault, certificate stores, HSMs, User Secrets, and environment variables
- Whether encryption results lack integrity verification, AEAD, replay protection, version numbers, context binding, or tenant isolation
- Password hashing, token signing, file encryption, cookie protection, remember-me token, and magic link generation logic
- Whether sensitive key material is leaked in logs, exceptions, debug output, configuration snapshots, or frontend responses

## Key Checks

- Weak hash algorithms: MD5, SHA1 used for password storage or integrity checks
- Weak encryption algorithms: DES, 3DES, RC2, RC4, ECB mode
- Key management: hardcoded keys, plaintext keys in appsettings, Base64-encoded keys in code
- IV/salt issues: fixed IV, empty salt, insufficient salt length, IV reuse
- Randomness: using System.Random instead of RandomNumberGenerator for security-relevant values
- Password hashing: bcrypt/scrypt/Argon2/PBKDF2 not used, or insufficient iteration counts
- Signature verification: JWT algorithm confusion (none/HS256 vs RS256), webhook signatures not verified
- DataProtection: key rotation policy, cross-application shared keys, persistence location security

## Evidence References

- EVID_CRYPTO_ALGO_SELECTION
- EVID_CRYPTO_KEY_SOURCE
- EVID_CRYPTO_MODE_PADDING_RANDOMNESS

## Enumeration Rules (Mandatory Refinement)

- Enumerate all usage points of HashAlgorithm, Aes, RSA, ECDsa, ProtectedData, DataProtection, JwtSecurityTokenHandler, and custom CryptoHelpers
- Search with priority: MD5, SHA1, ECB, CBC, IV, salt, key, secret, signing, encrypt, decrypt, Protect, Unprotect, and other keywords
- Enumerate password hashing, ticket signing, file encryption, field encryption, magic links, remember-me tokens, API signatures, and webhook signature scenarios
- For each encryption point record: algorithm, mode, randomness source, key source, rotation policy, output usage scenario, and integrity protection status
- **Dimension bar (mandatory, 2026-09-20): signature replay** — item-by-item check of nonce uniqueness constraints at the signature/verification entry, timestamp window validation, and the replay cache trio (signature/verification-surface determination standard see the "Mechanism Extension: Signed Request Replay Protection" section of this file; request-processing surface — middleware order and signature entry reachability see the same-named dimension bar in `dotnet-webapi-audit` — the two files cross-reference each other and share one determination standard). Not-applicable determination condition: the target has no signature/verification/HMAC/webhook signature verification entry at all, and an rg negative-evidence citation (scope + pattern, e.g. `rg "HMACSHA256|VerifyData|SignData|SignatureVerification" {scope}` with zero hits) is attached before marking `Not Applicable`; otherwise a bare "not covered" is forbidden

## Barrier Verification Matrix (Mandatory)

Assess against the fail-close three-tier standard in `DOTNET_AUDIT_EXECUTION_STANDARD.md`:

| Tier | Check Item | Pass Criteria | Failure Degradation |
|------|--------|----------|----------|
| Tier 1 | Encryption/hash operations exist | HashAlgorithm/Aes/RSA/ProtectedData/DataProtection etc. exist and are actually used for security-sensitive data | BLOCKED → no encryption/hash operations; the specialty ends |
| Tier 2 | Weak algorithms/insecure modes are used | MD5/SHA1/DES/3DES/ECB/fixed IV/System.Random etc. are used for passwords/signatures/encryption | BLOCKED → algorithms and modes are safe; conclusion degraded |
| Tier 3 | Key management flaws enable actual exploitation | Hardcoded keys, plaintext keys in appsettings, no rotation policy, keys leaked to logs/exceptions/frontend | PARTIAL → only potential risks and verification steps are output |

## Two-Phase Determination Flow (Mandatory)

- **Phase 1 (Initial Screening Hit)**: encryption/hash operations + algorithm/mode configuration + key management hit; output `Hit ID: M{hash}`.
- **Phase 2 (Refined Confirmation)**:
  1. Trace in reverse: security-sensitive data → encryption/hash call → algorithm/mode → key source chain;
  2. Verify usage scenarios of weak algorithms/modes such as MD5/SHA1/DES/ECB/fixed IV/System.Random;
  3. Assess key/IV/salt sources (hardcoded/config/key vault), rotation policies, and leakage surfaces (logs/exceptions/frontend);
  4. If all three barrier tiers pass → `Confirmed Vulnerability`; if any fails → degrade per the matrix.

## Determination Rules and Priority (Mandatory)

1. **Confirmed Vulnerability**: encryption/hash operations exist + weak algorithm/insecure mode + key management flaw exploitable. Output `Confirmed Vulnerability`.
2. **Pending Confirmation**: encryption/hash operations exist but algorithm safety or key source evidence is insufficient. Output `Pending Confirmation`.
3. **False Positive / No Risk**: safe algorithms in use (AES-GCM/SHA-256/Argon2), RandomNumberGenerator, keys stored in KeyVault/HSM, rotation policy in place with no leakage. Output `False Positive` with determination basis.

## Testing Suggestions and Minimum Trigger Conditions (Mandatory)

- **Minimum Trigger Conditions**:
  - Encryption/hash/signature operations exist (HashAlgorithm/Aes/RSA/ProtectedData/DataProtection)
  - Weak algorithms (MD5/SHA1/DES/ECB) or insecure modes (fixed IV/System.Random) are used
  - Or keys are hardcoded/stored in plaintext/no rotation/leaked to logs
- **Test Case Suggestions**:
  - Happy Path: normal encryption/hash/signature operations use safe algorithms and key management
  - Edge/Ambiguity: JWT algorithm confusion (none/HS256 vs RS256), DataProtection cross-application shared keys, hardcoded key search, key leakage in logs
- Each hit output appends `Hit ID: M{hash}` and `test_id: T{hash}` for traceability.

## Evidence References

Evidence references:

- EVID_CRYPTO_ALGO_SELECTION
- EVID_CRYPTO_KEY_SOURCE
- EVID_CRYPTO_MODE_PADDING_RANDOMNESS

## Workflow (Input → Execution → Output)

1. Input: read `source_path` and upstream artifacts (e.g. `route_mapping` / `route_tracer` / `framework_audit`), confirm dependencies are available and timestamps are consistent.
2. Execution: complete the audit in the order "shared grabber index → this specialty's enumeration rules → evidence point references", recording hit points, evidence chains, and unclosed paths.
3. Output: write to the agreed path per the "Output" section of this file; conclusions must be annotated `Confirmed` / `⚠️Pending Verification`, with a missing-evidence list attached.

## Checkpoint Design (Mandatory)

- 🔴 **CHECKPOINT A (Algorithm Confirmation)**: the correspondence between algorithm/mode/padding and business purpose must be confirmed.
- 🔴 **CHECKPOINT B (Key Source Confirmation)**: source and rotation evidence for key/iv/salt must be given.
- 🔴 **CHECKPOINT C (Integrity Confirmation)**: whether signing/AEAD/replay protection exists must be confirmed.
- 🛑 **STOP**: if key source or integrity evidence is missing, outputting a high-severity "confirmed exploitable" conclusion is forbidden.

## Failure Scenarios and Fallbacks (if-then)

| Trigger Condition | First-Line Handling | Fallback if Still Failing |
|---|---|---|
| Only weak algorithm names found, actual call scenario unconfirmable | Fill in call evidence from algorithm to business data flow | Degrade to Pending Confirmation; no exploitable strong conclusion |
| Key/IV/salt source unclear | Trace to configuration/key vault/runtime injection sources | Mark rotation and source gaps; assess risk conservatively |
| Integrity protection chain unverifiable (signing/AEAD) | Fill in bidirectional encryption and verification evidence chains | Output only Environment-Dependent or Pending Confirmation conclusions |

🔴 **STOP: when any fallback is triggered, outputting "confirmed exploitable" is forbidden.**

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

- Anti-pattern: inferring global exploitability from algorithm names alone. Correct approach: judge together with call scenarios, key sources, and data flows.
- Anti-pattern: treating Base64/config values as "secure storage". Correct approach: distinguish encoding from key management.
- Anti-pattern: ignoring integrity protection (AEAD/signatures). Correct approach: review both confidentiality and integrity.
- Anti-pattern: judging "risk under control" with no rotation evidence. Correct approach: degrade and annotate the rotation gap.

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

- vuln_audit/crypto_{timestamp}.md
- Optional: vuln_poc/crypto_{timestamp}.md (if a reproduction request, weak-configuration verification steps, or an environment-dependent verification chain can be constructed)

## Mechanism Extension: Signed Request Replay Protection (2026-09-14 Ledger Round)

### Mechanism Description and Boundary

Untrusted signed request → freshness check missing (nonce/timestamp/replay cache) → replay succeeds. After capturing one legitimate signed request, the attacker resubmits it verbatim or with minor modifications; if the server only verifies the signature without checking freshness, the replayed request is processed as legitimate, causing repeated state changes such as duplicate charges or duplicate orders.

This Skill (dotnet-crypto-audit) focuses on the **signature/verification surface**: signature and verification implementation, `HMACSHA256` / `RSA` verification entries, and the coverage of signed material (timestamp/nonce/body). Request processing and middleware order issues are covered by the same-named extension in dotnet-webapi-audit; both share one determination standard.

Ledger boundary (verbatim): a valid signature ≠ a fresh request; must not be merged with HTTP query construction; signature algorithm or key management issues are out of scope for this extension.

### Key Checks and Enumeration Grabbers

Record for each hit: file, line number, verification/check point, and the missing freshness component.

- **Signature verification entry**: `HMACSHA256` / `RSA` / `ECDsa` verification call sites, `SignatureVerification` helper methods, custom middleware for API key + signature, webhook signature verification.
- **Freshness trio existence**:
  - Nonce storage and uniqueness validation: whether nonce records exist in `IDistributedCache` / `MemoryCache`, whether they are written after verification, and whether a second submission hits the stored record.
  - Timestamp window and skew tolerance: whether timestamp deviation from server time is validated with a limit, and whether the tolerance window is configurable and reasonable.
  - Replay cache expiration policy: whether nonce/timestamp records have an expiration time, and whether duplicates are forcibly rejected before expiration.
- **Signature coverage**: whether the signed string covers method, path, timestamp, nonce, and body; when only the body or only the path is signed, timestamp/nonce can be tampered with without breaking the signature.

### Verification Matrix

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **Nonce uniqueness enforcement** | Confirm that after verification passes, the nonce is written to storage and subsequent requests carrying the same nonce are rejected | Reject-on-use → ✅ Safe; duplicate nonces accepted or nonce not stored → 🔴 High-risk Pending Confirmation |
| **Timestamp window validation** | Confirm timestamp deviation validation exists, including a clock-skew tolerance limit, and out-of-window requests are rejected | Fail-close window validation → ✅ Safe; no window validation or unlimited tolerance → 🔴 High-risk Pending Confirmation |
| **Replay cache not bypassable** | Confirm cache miss (nonce absent) rejects by default rather than passing by default; behavior on cache failure | Miss-rejects-by-default → ✅ Safe; miss-passes-by-default or fail-open on failure → 🔴 High-risk Pending Confirmation |
| **Signature coverage completeness** | Verify the to-be-signed string construction, confirming method+path+timestamp+nonce+body full coverage | Full coverage and any missing element fails verification → ✅ Safe; timestamp/nonce not covered by the signature → 🔴 High-risk Pending Confirmation |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion "Confirmed Safe" or "False Positive" is forbidden.**

### Determination Rules

Confirmation requires simultaneously closing the following three EVIDs; none may be missing:

1. **Freshness absence closure**: evidence that the signature verification entry lacks nonce/timestamp/replay cache freshness validation (`EVID_CRYPTO_REPLAY_FRESHNESS_ABSENT`).
2. **Replay acceptance closure**: empirical evidence that the same signed request is accepted on a second submission (`EVID_CRYPTO_REPLAY_ACCEPTANCE`).
3. **Impact closure**: impact closure evidence that replay causes over-privileged operations/state changes (`EVID_CRYPTO_REPLAY_IMPACT_CONFIRM`).

🔴 **Confirmation threshold (ledger verbatim): must prove freshness validation is absent AND the replayed request is accepted.** Signature algorithm or key management issues are out of scope for this extension and are routed elsewhere.

### Testing Suggestions

- **Positive**: capture one legitimate signed request and resend it verbatim, confirming it is accepted; tamper with the timestamp or nonce and replay, confirming it still passes.
- **Negative**: when nonce uniqueness + timestamp window validation are complete, confirm a replayed request is rejected.
- **Regression**: when adding a signed endpoint (including webhooks, callbacks, open APIs), re-verify the freshness trio.

### Evidence References

- `EVID_CRYPTO_REPLAY_FRESHNESS_ABSENT`: evidence that the signature verification entry lacks nonce/timestamp/replay cache freshness validation
- `EVID_CRYPTO_REPLAY_ACCEPTANCE`: empirical evidence that the same signed request is accepted on a second submission
- `EVID_CRYPTO_REPLAY_IMPACT_CONFIRM`: impact closure evidence that replay causes over-privileged operations/state changes
