# Counterexample: node_wrong_status

## Counterexample Intent (Contract Drift Regression Reference)

Simulates a **contract drift** scenario in a node audit output tree: the
single-route report in route_tracer has the complete 10-section skeleton, but
`trace_status: COMPLETE` is not in the node five-state domain (legal domain:
NOT_STARTED / IN_PROGRESS / DONE_OPEN / DONE_CLOSED / BLOCKED, see the
node-route-tracer SKILL.md).

`COMPLETE` is a legal value on the dotnet side, not the node side — this
counterexample also regresses the "cross-stack status-domain confusion" type of
contract drift: if the node side misuses dotnet's COMPLETE semantics, check N
must intercept it.

Used to regression-test the detection ability of `validate_audit.py` check N
(node trace contract) for the "trace_status outside the value domain" type of
drift.

## Target Stack

`--stack node`

## Expected Exit Code

`1` (FAIL exists)

## Violated Checks

- **Check N (node trace contract)**: the `trace_status: COMPLETE` in
  `route_tracer/R2/trace_2026_08_23.md` is not one of the five states → FAIL
  "Illegal node trace_status value: COMPLETE"

## Attribution Design

- The 5 minimal sections (Parameter Controllability Matrix / Sink Location /
  Sink Summary / Trace Completeness Statement / Sink Evidence Type Checklist)
  are complete; the checklist cites only a registered EVID
  (EVID_NODE_NOSQL_QUERY_POINT)
- quality/ (gate + pipeline_execution) and the final report are all compliant
- Therefore the FAIL has a single attribution: only the "illegal trace_status
  value" item

## Regression Command

```bash
python scripts/validate_audit.py scripts/_demo_audit/node_wrong_status --stack node
```
