# Counterexample: dotnet_missing_section

## Counterexample Intent (Contract Drift Regression Reference)

Simulates a **contract drift** scenario in a dotnet audit output tree: the
single-route report in route_tracer is missing the mandatory section
`## 7) Sink Summary`. That section is one of the 5 mandatory sections of the
dotnet trace contract (dotnet-route-tracer SKILL.md single-route report
template); its absence is judged as contract drift.

Used to regression-test the detection ability of `validate_audit.py` check A
(trace contract) for the "missing section" type of drift.

## Target Stack

`--stack dotnet`

## Expected Exit Code

`1` (FAIL exists)

## Violated Checks

- **Check A (trace contract)**: `route_tracer/R1/trace_2026_08_23.md` lacks the
  `## 7) Sink Summary` section → FAIL "Trace file is missing mandatory sections: ## 7) Sink Summary"

## Attribution Design

- trace_status: COMPLETE is a legal dotnet value; `## 9)` cites only a registered
  EVID (EVID_SQL_EXEC_POINT)
- quality/ (gate + pipeline_execution) and the final report are all compliant
- Therefore the FAIL has a single attribution: only the "missing ## 7) Sink
  Summary" item

## Regression Command

```bash
python scripts/validate_audit.py scripts/_demo_audit/dotnet_missing_section --stack dotnet
```
