import os
import json
from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
from src.context import DisputeContext, PolicyDecision, round_currency
from src.evidence import EvidenceBuilder
from src.tools import IndependentCaseAuditTool

class VerifierAgent(BaseAgent):
    name = "VerifierAgent"
    version = "1.0.0"
    description = "Independently recomputes policy outcomes, repairs mismatches, and validates output evidence and arithmetic."
    owner = "QA & Deliverables"
    system_prompt = "You are a Quality Assurance Lead. Independently recompute EC_POLICY_V1 outcomes, repair mismatches, and validate evidence references before export."


    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.audit_tool = IndependentCaseAuditTool()

    def _reload_and_repair_facts(self, context: DisputeContext) -> None:
        truth = self.audit_tool.run(context)
        order_row = truth["order"]
        fact_mismatches = []
        comparisons = {
            "order_status": (context.order.order_status, order_row.get("order_status")),
            "item_total_brl": (round_currency(context.order.item_total_brl), truth["item_total_brl"]),
            "freight_total_brl": (round_currency(context.order.freight_total_brl), truth["freight_total_brl"]),
            "payment_total_brl": (round_currency(context.payment.payment_total_brl), truth["payment_total_brl"]),
            "delivered_after_estimate": (context.delivery.delivered_after_estimate, truth["delivered_after_estimate"]),
            "carrier_received_after_limit": (context.delivery.carrier_received_after_limit, truth["carrier_received_after_limit"]),
        }
        for name, (actual, expected) in comparisons.items():
            if actual != expected:
                fact_mismatches.append(f"{name}: {actual!r} != {expected!r}")
        if fact_mismatches:
            context.errors.append("[Verifier Fact Repair] " + " | ".join(fact_mismatches))

        context.order.order_id = context.claimed_order_id if order_row else None
        context.order.order_status = order_row.get("order_status")
        context.order.order_delivered_carrier_date = order_row.get("order_delivered_carrier_date")
        context.order.order_delivered_customer_date = order_row.get("order_delivered_customer_date")
        context.order.order_estimated_delivery_date = order_row.get("order_estimated_delivery_date")
        context.order.items = truth["items"]
        context.order.sellers = truth["sellers"]
        context.order.item_total_brl = truth["item_total_brl"]
        context.order.freight_total_brl = truth["freight_total_brl"]
        context.order.shipping_limit_dates = {
            str(item.get("order_item_id", "")): str(item.get("shipping_limit_date", ""))
            for item in truth["items"]
        }
        context.payment.payment_rows = truth["payments"]
        context.payment.payment_total_brl = truth["payment_total_brl"]
        context.payment.is_multiple_payments = len(truth["payments"]) >= 2
        expected_total = round_currency(truth["item_total_brl"] + truth["freight_total_brl"])
        context.payment.reconciliation_diff_brl = round_currency(abs(truth["payment_total_brl"] - expected_total))
        context.payment.is_reconciled = context.payment.reconciliation_diff_brl <= 0.10
        context.delivery.carrier_delivered_date = order_row.get("order_delivered_carrier_date")
        context.delivery.customer_delivered_date = order_row.get("order_delivered_customer_date")
        context.delivery.estimated_delivery_date = order_row.get("order_estimated_delivery_date")
        context.delivery.delivered_after_estimate = truth["delivered_after_estimate"]
        context.delivery.carrier_received_after_limit = truth["carrier_received_after_limit"]
        context.delivery.violating_seller_id = truth["violating_seller_id"] or (str(truth["items"][0].get("seller_id", "")) if truth["items"] else None)

        oid = context.claimed_order_id
        context.candidate_evidences.append(f"order:{oid}")
        for item in truth["items"]:
            context.candidate_evidences.append(f"item:{oid}:{item.get('order_item_id')}")
            context.candidate_evidences.append(f"seller:{item.get('seller_id')}")
        for payment in truth["payments"]:
            context.candidate_evidences.append(f"payment:{oid}:{payment.get('payment_sequential')}")

    def _expected_decision(self, context: DisputeContext) -> PolicyDecision:
        order = context.order
        delivery = context.delivery
        payment = context.payment

        if order.order_status == "canceled" and payment.payment_total_brl > 0:
            return PolicyDecision("canceled_order_paid", "ORDER_CANCELED_AFTER_PAYMENT", "platform", "OLIST_PLATFORM", payment.payment_total_brl, ["issue_full_refund"], 1.0)
        if order.order_status == "unavailable" and payment.payment_total_brl > 0:
            return PolicyDecision("unavailable_order_paid", "ORDER_UNAVAILABLE_AFTER_PAYMENT", "platform", "OLIST_PLATFORM", payment.payment_total_brl, ["issue_full_refund"], 1.0)
        if delivery.delivered_after_estimate and delivery.carrier_received_after_limit:
            return PolicyDecision("late_delivery_seller", "SELLER_HANDOFF_AFTER_LIMIT", "seller", delivery.violating_seller_id, order.freight_total_brl, ["refund_freight"], 1.0)
        if delivery.delivered_after_estimate:
            return PolicyDecision("late_delivery_logistics", "CARRIER_DELIVERED_AFTER_ESTIMATE", "logistics_provider", "LOGISTICS_PROVIDER", order.freight_total_brl, ["refund_freight"], 1.0)
        if payment.is_multiple_payments and payment.is_reconciled:
            return PolicyDecision("valid_split_payment", "MULTIPLE_PAYMENTS_RECONCILED", None, None, 0.0, ["explain_valid_split_payment"], 0.98)
        return PolicyDecision("unsupported_late_claim", "DELIVERY_WITHIN_ESTIMATE", None, None, 0.0, ["reject_late_refund"], 0.95)

    def _audit_and_repair_decision(self, context: DisputeContext) -> None:
        expected = self._expected_decision(context)
        actual = context.decision
        fields = (
            "primary_issue", "cause_code", "responsible_party_type",
            "responsible_party_id", "recommended_refund_brl", "actions", "confidence",
        )
        mismatches = []
        if actual is None:
            mismatches.append("missing policy decision")
        else:
            for field in fields:
                actual_value = getattr(actual, field)
                expected_value = getattr(expected, field)
                if field == "recommended_refund_brl":
                    actual_value = round_currency(actual_value)
                    expected_value = round_currency(expected_value)
                if actual_value != expected_value:
                    mismatches.append(f"{field}: {actual_value!r} != {expected_value!r}")

        if mismatches:
            context.errors.append("[Verifier Repair] " + " | ".join(mismatches))
            expected.matched_rule = expected.primary_issue
            expected.evidence_used = ["independently recomputed by VerifierAgent"]
            context.decision = expected
            context.candidate_evidences.append(f"policy:{expected.cause_code}")

    def run(self, context: DisputeContext) -> DisputeContext:
        self._reload_and_repair_facts(context)
        order = context.order
        payment = context.payment
        self._audit_and_repair_decision(context)
        decision = context.decision

        # --- FINANCIAL RESOLUTION WITH ROUND_HALF_UP PRECISION ---
        item_total = round_currency(order.item_total_brl)
        freight_total = round_currency(order.freight_total_brl)
        payment_total = round_currency(payment.payment_total_brl)
        refund_total = round_currency(decision.recommended_refund_brl) if decision else 0.0

        if not order.items:
            item_total = 0.0
            freight_total = 0.0

        case_status = "action_required" if refund_total > 0 else "no_action"

        confidence = decision.confidence if decision else 0.5
        confidence = max(0.0, min(1.0, float(confidence)))

        valid_item_ids = {str(item.get("order_item_id", "")) for item in order.items}
        valid_payment_ids = {str(row.get("payment_sequential", "")) for row in payment.payment_rows}
        valid_seller_ids = {str(item.get("seller_id", "")) for item in order.items}
        evidence_prefixes = {"order", "payment", "policy"}
        if decision.primary_issue in {
            "late_delivery_seller",
            "late_delivery_logistics",
            "valid_split_payment",
            "unsupported_late_claim",
        }:
            evidence_prefixes.add("item")
        if decision.primary_issue == "late_delivery_seller":
            evidence_prefixes.add("seller")

        minimal_candidates = [
            evidence
            for evidence in context.candidate_evidences
            if evidence.split(":", 1)[0] in evidence_prefixes
        ]
        final_evidences = EvidenceBuilder.build(
            minimal_candidates,
            max_limit=10,
            order_id=context.claimed_order_id,
            item_ids=valid_item_ids,
            payment_ids=valid_payment_ids,
            seller_ids=valid_seller_ids,
            policy_code=decision.cause_code,
        )
        context.final_evidence_ids = final_evidences

        oid = context.claimed_order_id
        order_ids = [oid] if oid else []
        
        item_ids = []
        seller_ids = []
        for item in order.items:
            iid = str(item.get("order_item_id", ""))
            sid = str(item.get("seller_id", ""))
            if iid:
                formatted_iid = f"{oid}:{iid}"
                if formatted_iid not in item_ids:
                    item_ids.append(formatted_iid)
            if sid and sid not in seller_ids:
                seller_ids.append(sid)

        payment_ids = []
        for p in payment.payment_rows:
            seq = str(p.get("payment_sequential", "1"))
            formatted_pid = f"{oid}:{seq}"
            if formatted_pid not in payment_ids:
                payment_ids.append(formatted_pid)

        order_ids = order_ids[:5]
        item_ids = item_ids[:5]
        seller_ids = seller_ids[:5]
        payment_ids = payment_ids[:5]

        ranked_causes = []
        responsible_parties = []
        if decision:
            ranked_causes.append({"cause_code": decision.cause_code, "rank": 1})
            if decision.responsible_party_type:
                responsible_parties.append({
                    "party_type": decision.responsible_party_type,
                    "party_id": decision.responsible_party_id
                })

        actions = decision.actions[:5] if decision else ["reject_late_refund"]

        final_output = {
            "case_id": context.case_id,
            "assessment": {
                "primary_issue": decision.primary_issue if decision else "unsupported_late_claim",
                "case_status": case_status,
                "confidence": confidence
            },
            "affected_entities": {
                "order_ids": order_ids,
                "item_ids": item_ids,
                "seller_ids": seller_ids,
                "payment_ids": payment_ids
            },
            "root_cause_analysis": {
                "ranked_causes": ranked_causes[:3],
                "responsible_parties": responsible_parties[:3]
            },
            "evidence_ids": final_evidences,
            "financial_resolution": {
                "currency": "BRL",
                "item_total_brl": item_total,
                "freight_total_brl": freight_total,
                "payment_total_brl": payment_total,
                "recommended_refund_brl": refund_total
            },
            "resolution_actions": actions
        }

        context.final_output = final_output

        output_file_path = os.path.join(self.output_dir, f"{context.case_id}.json")
        with open(output_file_path, mode="w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)

        return context


    def get_trace_payload(self, context: DisputeContext) -> Dict[str, Any]:
        output = context.final_output
        if not output:
            return {"status": "error_no_output"}
        return {
            "case_id": output.get("case_id"),
            "case_status": output.get("assessment", {}).get("case_status"),
            "evidence_count": len(output.get("evidence_ids", [])),
            "refund_brl": output.get("financial_resolution", {}).get("recommended_refund_brl")
        }

    def get_agent_context(self, context: DisputeContext) -> Dict[str, Any]:
        output = context.final_output or {}
        assessment = output.get("assessment", {})
        return {
            "agent_thought": f"Executed Verification Matrix auto-correction. Verified schema, rounded amounts to 2 decimals, clamped confidence to {assessment.get('confidence')}, and generated output file.",
            "final_evidences_selected": context.final_evidence_ids,
            "verification_repairs": [error for error in context.errors if error.startswith("[Verifier")],
            "output_file": f"output/{context.case_id}.json"
        }
