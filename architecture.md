# Multi-Agent Architecture

## System Flow

```text
Input JSON
    |
    v
CoordinatorAgent -- local LLM intent summary (optional, non-authoritative)
    |
    v
OrderAgent ------ `olist.get_order_bundle`
    |
    v
DeliveryAgent --- `delivery.audit_timeline`
    |
    v
PaymentAgent ---- `olist.get_order_payments`
    |
    v
PolicyAgent ----- `ec_policy.evaluate_v1`
    |
    v
VerifierAgent --- `olist.reload_case_ground_truth`, independent repair and validation
    |
    +--> output/EC_NNN.json
    +--> logging/trace.jsonl
```

The shared `DisputeContext` is the handoff contract. Each domain agent owns a
separate sub-context, calls an explicit tool and appends evidence candidates.
Every tool invocation records its name, arguments and a bounded result summary
in the agent trace. The Coordinator controls execution order but does not make
the final business decision.

## Agent Responsibilities

| Agent | Reads | Writes | Responsibility |
| --- | --- | --- | --- |
| CoordinatorAgent | Input JSON, optional local LLM | Initial context, trace | Validate routing fields and orchestrate handoffs |
| OrderAgent | `olist.get_order_bundle` | `context.order`, evidence candidates | Load order state, items, sellers, totals and shipping limits |
| DeliveryAgent | `delivery.audit_timeline` | `context.delivery` | Compare delivery, estimate and carrier handoff timestamps |
| PaymentAgent | `olist.get_order_payments`, order totals | `context.payment`, evidence candidates | Sum payment rows and reconcile within 0.10 BRL |
| PolicyAgent | `ec_policy.evaluate_v1` inputs | `context.decision` | Apply EC_POLICY_V1 in documented priority order |
| VerifierAgent | `olist.reload_case_ground_truth`, candidate evidence | Final output JSON | Reload CSV facts independently, repair context and decision mismatches, validate evidence references and financial rounding |

## Data Access Boundaries

- `OlistDataLoader` is the only component that reads CSV files directly.
- `OrderAgent` accesses order, item and seller indexes.
- `PaymentAgent` accesses payment indexes.
- `DeliveryAgent` and `PolicyAgent` operate only on handed-off context.
- `VerifierAgent` independently reloads order, item, seller and payment facts;
  it does not trust domain sub-contexts when producing the final output.
- `VerifierAgent` is the only agent that writes case output files.
- The local LLM only summarizes customer intent. It cannot override CSV facts,
  policy ordering, financial values or evidence IDs.

## Verification Contract

Before export, `VerifierAgent` reloads the source records and repairs corrupted
domain facts as `[Verifier Fact Repair]`. It then independently derives the
expected primary issue, root cause, responsible party, refund, action and
confidence. Any decision mismatch is repaired and recorded as
`[Verifier Repair]` in the case trace. Evidence IDs must match their full documented format and refer
to an actual order, item, payment or seller record; policy evidence must equal
the selected root-cause code.

Evidence selection is rule-scoped to avoid false positives:

| Issue family | Evidence retained |
| --- | --- |
| Canceled or unavailable paid order | order, payments, policy |
| Seller-caused late delivery | order, items, payments, responsible seller, policy |
| Logistics-caused late delivery | order, items, payments, policy |
| Valid split payment | order, items, payments, policy |
| Unsupported late claim | order, items, payments, policy |

Evidence is rule-scoped, but `affected_entities` remains a complete inventory
of the order records: all existing item, seller and payment IDs are emitted.
This keeps evidence precision independent from entity completeness.

Financial values use `Decimal` with `ROUND_HALF_UP` to two decimal places.
Entity, cause, party, evidence and action lists are truncated to the limits in
the output contract.

## Failure Handling

- If Ollama is unavailable, intent extraction uses a deterministic fallback;
  policy decisions are unaffected.
- Runtime errors are stored in `context.errors` and routed through the verifier
  for a bounded output attempt.
- `main.py` refuses to package a submission unless inputs and outputs contain
  exactly `EC_001.json` through `EC_050.json`.
- `output.zip` contains only the 50 output JSON files at the archive root.
