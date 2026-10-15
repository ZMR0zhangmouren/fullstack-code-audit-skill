---
name: node-crypto-audit
description: Node.js cryptography and key audit tool. Identifies risks such as md5/sha1 misuse in security contexts, weak createCipheriv parameters, Math.random for token generation, single-pass sha256 password hashing, and weak JWT secret configuration; outputs severity rating, evidence, and remediation recommendations.
---

# Node.js Cryptography and Key Audit

## Shared Grabber Index Reference

- By default, use `shared/NODE_AUDIT_GRABBER_INDEX.md` as the basic retrieval index for this skill
- By default, use `shared/NODE_SINK_REFERENCE.md` as the baseline for this specialty's Sink type definitions and trace-gate validation
- **By default, follow the general execution standard in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` (two-phase determination, fail-close determination, hit ID conventions, testing requirements)**
- By default, use `shared/SEVERITY_RATING.md` as the severity rating and ID convention baseline
- By default, use `shared/IO_PATH_CONVENTION.md` as the artifact path and naming convention
- Enumeration must at least cover the shared grabbers related to algorithm selection, randomness sources, key generation and storage, and password hashing
- If the project has secondary encapsulations such as cryptoUtil, hashService, tokenHelper, or passwordHasher, they must be added to the project-internal grabbers section of the output
- When this skill's specialty enumeration rules are finer-grained than the shared index, this skill takes precedence, but the shared index's basic coverage must not be reduced

## Input Dependencies

- Required: `node_source_path`
- Optional: `node/route_mapping/routes_{timestamp}.md` and `node/route_mapping/params_{timestamp}.md` (used to align login, signing, and encryption / decryption entries with `route_id`)
- Optional: `node/route_mapping/middleware_inventory_{timestamp}.md` (used to confirm middleware coverage order and short-circuit conditions)
- Optional: `node/auth_audit/auth_mapping_{timestamp}.md` (used to supplement anonymous entries, P0/P1 bucketing, authentication boundaries, or business preconditions)
- Optional: `node/framework_audit/*_{timestamp}.md` (used to supplement the host, framework control plane, static directories, or runtime boundaries)
- Optional: `cross/api_contract_map_{timestamp}.md` (used for cross-stack parameter sources, field mappings, and upstream/downstream linkage analysis)
- This specialty is **static-evidence-driven**: `node/route_tracer/{route_id}/trace_{timestamp}.md` and `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` serve only as cross-reference evidence, not as hard preconditions
- If executed via `dotnet-audit-pipeline` (Node.js extension mode), the `route_id` referenced by this specialty should be consistent with `node/cross_analysis/high_risk_routes_{timestamp}.md`
- Responsibility boundary: JWT / cookie session configuration (algorithm pinning, expiration, logout) belongs to `node-session-cookie-audit`; this specialty covers algorithm primitives, randomness sources, and key material

## Key Checks

- md5 / sha1 used in security contexts such as signatures, integrity checks, and password storage
- Weak `createCipheriv` parameters: `des`, `des3`, `aes-*-ecb`, fixed IVs, empty salts
- `Math.random` generating tokens, verification codes, or reset links (should use `crypto.randomBytes` / `getRandomValues`)
- Passwords stored with single-pass `sha256` / `md5` (should use bcrypt / scrypt / argon2 / pbkdf2 slow hashing)
- JWT secrets as weak password literals, committed to the repository, or hardcoded defaults
- Hardcoded keys / IVs / salts, Base64 literals used as keys, unsalted hashing
- Webhook / payment callback signatures not validated, or HMAC comparison using `==` instead of `crypto.timingSafeEqual`

## Enumeration Rules (Mandatory Refinement)

- rg searches: `createHash(`, `createCipheriv(`, `createDecipheriv(`, `createHmac(`, `randomBytes(`, `Math.random(`, `pbkdf2`, `scrypt`, `bcrypt`, `argon2`, `jwt.sign(`, `secret`, `md5`, `sha1`, `des-`, `ecb`
- For each cryptographic point record: algorithm, mode, iv / salt sources, key source (environment / key service / literal), randomness source, and output purpose (password hash / signature / integrity / encryption)
- Distinguish security contexts from non-security contexts: md5 / sha1 used for cache keys or ETags do not count as risks; used for passwords, tickets, or check values they count as risks
- Enumerate complete call chains of password hashing, signing, encryption, verification codes, and reset links
- If secondary encapsulation exists, it must be unwrapped layer by layer to the real `crypto` / third-party library call sites

## Barrier Verification Matrix (Mandatory)

| Barrier Type | Typical Implementation | Verification Action | Determination Criteria |
| ---- | ---- | ---- | ---- |
| Password hashing scheme | bcrypt / scrypt / argon2 / pbkdf2 | Confirm the hash function and cost / iteration parameters used for password storage | adaptive slow hashing with adequate parameters → ✅ safe; single-pass md5 / sha256 → 🔴 high risk |
| Randomness source | `crypto.randomBytes` / `getRandomValues` | Verify the randomness sources of tokens, verification codes, and reset links | CSPRNG with sufficient length → ✅ safe; `Math.random` / timestamps → 🔴 high risk |
| Algorithm and mode | `createCipheriv` parameter string | Verify the algorithm identifier, mode, IV source, and uniqueness | AES-GCM / CBC with random IV → ✅ safe; des / ecb / fixed IV → 🔴 high risk |
| Key source | Environment injection / key management services / literals | Trace secret and key declaration locations and default fallbacks | injected without weak defaults → ✅ safe; hardcoded or committed → 🔴 high risk |

## Two-Phase Determination (Mandatory)

This specialty follows the two-phase determination process in `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`:

> The general execution standard takes `shared/AUDIT_EXECUTION_COMMON.md` as its source of truth (shared evolution decision 3); this section retains node-stack-specific differences.

### Phase 1: Interim Conclusion

For each hit, first give one of three interim conclusions:

- `Confirmed Vulnerability Candidate`: weak algorithms, weak randomness, or weak keys appear to be used in security-sensitive contexts such as passwords, tokens, or encryption
- `Pending`: the context shows a suspicious pattern, but the external input source, barrier behavior, or call chain is unclear
- `False Positive`: the input comes from fixed constants / enum mappings, or the barrier has been verified as fail-close

### Phase 2: Mandatory Evidence Chasing

If Phase 1 is "Pending", you must continue chasing at least one more hop of the call chain or downstream parser until any of the following holds:

- Evidence is found that externally controllable input enters the Sink position → `Confirmed Vulnerability`
- Fixed whitelist mapping / fail-close evidence is found → `False Positive`
- A key call chain is still missing → remain `Pending`, but you must state which hop is missing

**fail-close semantics**: barriers, whitelists, validators, and filters must be evaluated in their failure mode. Unknown / illegal input must throw an exception, return empty, refuse execution, or trigger a log alert — it must never pass through the raw value; any silent-fallback or fail-open behavior is treated as high risk.

## Determination Rules (Mandatory Refinement)

### Confirmed

- `EVID_NODE_CRYPTO_WEAK_ALGO` + `EVID_NODE_CRYPTO_HASH_MODE`: passwords stored with single-pass md5 / sha256 and no slow hashing
- `EVID_NODE_CRYPTO_RANDOM_SOURCE`: `Math.random` generating session tokens, verification codes, or password reset links
- `EVID_NODE_CRYPTO_WEAK_ALGO` + `EVID_NODE_CRYPTO_KEY_SOURCE`: des / ecb or fixed-IV encryption with hardcoded, committed keys
- `EVID_NODE_CRYPTO_KEY_SOURCE`: the JWT secret is a weak password literal without environment injection override

### ⚠️Pending Verification

- `createHash('sha1')` is hit but the business purpose (cache key vs integrity check) is unclear
- Encryption calls exist, but IV / key sources need call chain supplementation to confirm
- Password hashing goes through secondary encapsulation not yet unwrapped to the real bcrypt / argon2 call

### False Positive

- Tokens are all generated by `crypto.randomBytes(32)`, and passwords use bcrypt with cost >= 10
- md5 / sha1 are used only in non-security contexts such as ETags and cache keys, with no security semantics
- Keys are injected via environment or key management services with rotation records, and the algorithm is AES-GCM

## Testing Recommendations (Mandatory)

### Positive Testing

- Use known-password collisions against md5 / sha256 stores to verify password recoverability; sample `Math.random` multiple times to verify token predictability
- Decrypt ciphertext with weak keys to verify the exploitability of weak `createCipheriv` parameters
- Test cases carry a `test_id` associated with the hit ID

### Negative Testing

- bcrypt / scrypt passwords cannot be rainbow-table recovered; `crypto.randomBytes` tokens cannot be predicted from historical sequences
- The service refuses to start when environment-injected keys are missing (fail-close)

### Regression Testing

- Retest after remediation, confirming algorithms and randomness sources have not regressed; retest that no new literals appear after key source switching
- Newly added cryptographic points default to the CSPRNG and slow-hashing standards

## Evidence References

- `EVID_NODE_CRYPTO_WEAK_ALGO`
- `EVID_NODE_CRYPTO_KEY_SOURCE`
- `EVID_NODE_CRYPTO_RANDOM_SOURCE`
- `EVID_NODE_CRYPTO_HASH_MODE`

## Output

- `node/vuln_audit/crypto_{timestamp}.md`
- `node/vuln_poc/crypto_{timestamp}.md` (Confirmed / Pending Verification / Environment-Dependent PoC)

## Mechanism Extension: Signed-Request Replay Protection (2026-09-14 Ledger Round)

### Mechanism Description and Boundary

Untrusted signed request → missing freshness validation (nonce / timestamp / replay cache) → replay succeeds. After capturing one legitimate signed request, an attacker resubmits it verbatim or with minor modifications; if the server only verifies the signature without checking freshness, the replayed request is treated as legitimate, causing repeated deductions, repeated orders, and other state changes.

This skill (node-crypto-audit) focuses on the **signing / verification surface**: `crypto.createHmac` / `crypto.createVerify` verification implementations, verification entries of API key + signature routes, and the coverage of signed material (timestamp / nonce / body). Request handling and middleware order issues belong to the same-named extension of node-webapi-audit (pending extension — node-webapi-audit has not yet integrated this round's mechanism extension; until delivered, this chapter's signing / verification surface criteria govern), with the same determination criteria.

Ledger boundary (verbatim): a valid signature ≠ a fresh request; do not merge with HTTP query construction; signature algorithm or key management issues are not part of this extension.

### Key Checks and Enumeration Grabbers

Record for each hit: file, line number, verification / validation point, and missing freshness component.

- **Signature verification entries**: `crypto.createHmac('sha256', key).update(...).digest()` verification call sites, express / fastify signature middleware, API key + signature routes, webhook signature validation.
- **Freshness three-piece existence**:
  - nonce storage and uniqueness validation: whether nonce records exist in an in-memory Map / Redis replay cache, whether they are written after verification, and whether a second submission hits an existing record.
  - timestamp window and skew tolerance: whether the deviation between timestamp and server time is checked against an upper bound, and whether the tolerance window is configurable and reasonable.
  - replay cache expiration policy: whether nonce / timestamp records have expiration times, and whether duplicates are forcibly rejected before expiration.
- **Signature coverage**: whether the signed string includes method, path, timestamp, nonce, and body; when only the body or only the path is signed, timestamp / nonce can be tampered without breaking the signature.

### Verification Matrix

| Barrier Type | Verification Action | Determination Criteria |
|-------------|---------|---------|
| **nonce uniqueness enforcement** | Confirm that after verification the nonce is written to storage, and subsequent requests carrying the same nonce are rejected | used-once-then-rejected → ✅ safe; duplicate nonce passing or nonce not stored → 🔴 high-risk candidate |
| **timestamp window validation** | Confirm timestamp deviation validation exists, including a clock-skew tolerance upper bound, with out-of-window requests rejected | window validation fail-close → ✅ safe; no window validation or unlimited tolerance → 🔴 high-risk candidate |
| **replay cache non-bypassability** | Confirm a cache miss (nonce absent) defaults to rejection rather than allowance; the behavior on cache failure | miss defaults to rejection → ✅ safe; miss defaults to allowance or failure fail-open → 🔴 high-risk candidate |
| **signature coverage completeness** | Verify the signed-string construction, confirming full coverage of method + path + timestamp + nonce + body | full coverage with any missing element failing verification → ✅ safe; timestamp / nonce not in the signature → 🔴 high-risk candidate |

🔴 **STOP: when any barrier verifies as `silent-fallback` or `fail-open`, marking the conclusion as "Confirmed Safe" or "False Positive" is forbidden.**

### Determination Rules

Confirmation requires closing all three of the following EVIDs, all indispensable:

1. **Freshness absence closure**: evidence that the signature verification entry lacks nonce / timestamp / replay cache freshness validation (`EVID_NODE_CRYPTO_REPLAY_FRESHNESS_ABSENT`).
2. **Replay acceptance closure**: empirical evidence that the same signed request is accepted on second submission (`EVID_NODE_CRYPTO_REPLAY_ACCEPTANCE`).
3. **Impact closure**: evidence that replay causes unauthorized operations / state changes (`EVID_NODE_CRYPTO_REPLAY_IMPACT_CONFIRM`).

🔴 **Confirmation threshold (ledger verbatim): it must be proven that freshness validation is missing and replayed requests can be accepted.** Signature algorithm or key management issues are not part of this extension and are tracked separately.

### Testing Recommendations

- **Positive**: capture one legitimate signed request and resend it verbatim, confirming acceptance; tamper with the timestamp or nonce and replay, confirming it still passes.
- **Negative**: with nonce uniqueness + timestamp window validation complete, replayed requests are rejected.
- **Regression**: when new signed endpoints are added (including webhooks, callbacks, and open APIs), re-verify the freshness three-piece set.

### Evidence References

- `EVID_NODE_CRYPTO_REPLAY_FRESHNESS_ABSENT`: evidence that the signature verification entry lacks nonce / timestamp / replay cache freshness validation
- `EVID_NODE_CRYPTO_REPLAY_ACCEPTANCE`: empirical evidence that the same signed request is accepted on second submission
- `EVID_NODE_CRYPTO_REPLAY_IMPACT_CONFIRM`: evidence that replay causes unauthorized operations / state changes
