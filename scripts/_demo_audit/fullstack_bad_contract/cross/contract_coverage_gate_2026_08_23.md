# Contract Coverage Gate

Generated at: 2026_08_23_10_30

- matched_count: 4
- frontend_only_count: 1
- backend_only_count: 1
- contract_coverage_percent: 50%
- unnormalized_rate: 5%
- contract_coverage_status: COMPLETE

<!-- Contract drift counterexample (fullstack_bad_contract): three-bucket counts
     matched=4/frontend_only=1/backend_only=1, expected percent = 4/(4+1+1) = 66.7%,
     but declared as 50%, used to trigger check F2 FAIL "contract_coverage_percent
     does not match the three bucket counts". -->
