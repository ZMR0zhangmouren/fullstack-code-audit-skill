# Counterexample: fullstack_bad_contract

## Counterexample Intent (Contract Drift Regression Reference)

Simulates a **contract drift** scenario in a full-stack audit output tree: the
three-bucket counts of cross/contract_coverage_gate do not match the percent —
`matched_count=4 / frontend_only_count=1 / backend_only_count=1` (total=6),
the expected `contract_coverage_percent = 4/6 = 66.7%`, but it is declared as
`50%`.

Contract alignment rule (cross-stack-contract-mapper SKILL.md): percent must
equal `matched/(matched+frontend_only+backend_only)`. A deviation between the
declared and expected values exceeding 0.5% is judged as drift.

Used to regression-test the detection ability of `validate_audit.py` check F2
(contract three-bucket counts) for the "counts vs percent mismatch" type of
drift.

## Target Stack

`--stack fullstack`

## Expected Exit Code

`1` (FAIL exists)

## Violated Checks

- **Check F2 (contract three-bucket counts)**: the
  `contract_coverage_percent: 50%` of
  `cross/contract_coverage_gate_2026_08_23.md` does not match the three-bucket
  counts (expected 66.7%) → FAIL "contract_coverage_percent=50.0% does not
  match the three bucket counts (expected 66.7% = matched/total)"

## Attribution Design

- The output tree structure follows the compliant fullstack_ok sample: the gate
  artifacts of the dotnet/ and node/ subtrees and the four declarations of the
  final report are all compliant
- The contract gate's contract_coverage_status and unnormalized_rate are both
  declared normally
- Therefore the FAIL has a single attribution: only the "percent vs three-bucket
  counts mismatch" item

## Regression Command

```bash
python scripts/validate_audit.py scripts/_demo_audit/fullstack_bad_contract --stack fullstack
```
