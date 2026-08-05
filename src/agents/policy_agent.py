from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.context import DisputeContext, PolicyDecision

class PolicyAgent(BaseAgent):
    name = "PolicyAgent"
    version = "1.0.0"
    description = "Deterministic Rule Engine applying EC_POLICY_V1 in strict priority order."
    owner = "Financial & Policy Engine"
    system_prompt = "You are a Chief Policy Adjudicator operating under EC_POLICY_V1. You strictly execute policy rules in order of priority to resolve customer claims neutrally and accurately."


    def run(self, context: DisputeContext) -> DisputeContext:
        order = context.order
        delivery = context.delivery
        payment = context.payment

        status = order.order_status
        is_late = delivery.delivered_after_estimate
        carrier_late = delivery.carrier_received_after_limit
        payment_val = payment.payment_total_brl
        freight_val = order.freight_total_brl

        decision = PolicyDecision(
            primary_issue="unsupported_late_claim",
            cause_code="DELIVERY_WITHIN_ESTIMATE",
            responsible_party_type=None,
            responsible_party_id=None,
            recommended_refund_brl=0.0,
            actions=["reject_late_refund"],
            confidence=1.0,
            matched_rule="unsupported_late_claim",
            evidence_used=["delivery completed within estimated timeframe or no actionable delay found"]
        )

        if status == "canceled" and payment_val > 0:
            decision.primary_issue = "canceled_order_paid"
            decision.cause_code = "ORDER_CANCELED_AFTER_PAYMENT"
            decision.responsible_party_type = "platform"
            decision.responsible_party_id = "OLIST_PLATFORM"
            decision.recommended_refund_brl = payment_val
            decision.actions = ["issue_full_refund"]
            decision.matched_rule = "canceled_order_paid"
            decision.confidence = 1.0
            decision.evidence_used = [f"order_status is canceled with paid amount {payment_val} BRL"]

        elif status == "unavailable" and payment_val > 0:
            decision.primary_issue = "unavailable_order_paid"
            decision.cause_code = "ORDER_UNAVAILABLE_AFTER_PAYMENT"
            decision.responsible_party_type = "platform"
            decision.responsible_party_id = "OLIST_PLATFORM"
            decision.recommended_refund_brl = payment_val
            decision.actions = ["issue_full_refund"]
            decision.matched_rule = "unavailable_order_paid"
            decision.confidence = 1.0
            decision.evidence_used = [f"order_status is unavailable with paid amount {payment_val} BRL"]

        elif is_late and carrier_late:
            seller_id = delivery.violating_seller_id or (order.sellers[0].get("seller_id", "SELLER_ID") if order.sellers else "SELLER_ID")
            decision.primary_issue = "late_delivery_seller"
            decision.cause_code = "SELLER_HANDOFF_AFTER_LIMIT"
            decision.responsible_party_type = "seller"
            decision.responsible_party_id = seller_id
            decision.recommended_refund_brl = freight_val
            decision.actions = ["refund_freight"]
            decision.matched_rule = "late_delivery_seller"
            decision.confidence = 1.0
            decision.evidence_used = ["order delivered after estimated delivery date", f"carrier received item after shipping_limit_date from seller {seller_id}"]

        elif is_late and not carrier_late:
            decision.primary_issue = "late_delivery_logistics"
            decision.cause_code = "CARRIER_DELIVERED_AFTER_ESTIMATE"
            decision.responsible_party_type = "logistics_provider"
            decision.responsible_party_id = "LOGISTICS_PROVIDER"
            decision.recommended_refund_brl = freight_val
            decision.actions = ["refund_freight"]
            decision.matched_rule = "late_delivery_logistics"
            decision.confidence = 1.0
            decision.evidence_used = ["order delivered after estimated delivery date", "carrier received item within shipping_limit_date"]

        elif payment.is_multiple_payments and payment.is_reconciled:
            decision.primary_issue = "valid_split_payment"
            decision.cause_code = "MULTIPLE_PAYMENTS_RECONCILED"
            decision.responsible_party_type = None
            decision.responsible_party_id = None
            decision.recommended_refund_brl = 0.0
            decision.actions = ["explain_valid_split_payment"]
            decision.matched_rule = "valid_split_payment"
            decision.confidence = 0.98
            decision.evidence_used = [f"order has {len(payment.payment_rows)} payment rows matching sum of items and freight within 0.10 BRL"]

        else:
            decision.primary_issue = "unsupported_late_claim"
            decision.cause_code = "DELIVERY_WITHIN_ESTIMATE"
            decision.responsible_party_type = None
            decision.responsible_party_id = None
            decision.recommended_refund_brl = 0.0
            decision.actions = ["reject_late_refund"]
            decision.matched_rule = "unsupported_late_claim"
            decision.confidence = 0.95
            decision.evidence_used = ["order delivery completed on or before estimated date and payments reconciled"]

        if not order.order_id:
            decision.confidence = 0.5

        # Strictly follow Section 5 of README: policy:<root_cause_code>
        context.candidate_evidences.append(f"policy:{decision.cause_code}")
        context.decision = decision
        context.record_tool_call(
            self.name,
            "ec_policy.evaluate_v1",
            {
                "order_status": status,
                "delivered_after_estimate": is_late,
                "carrier_received_after_limit": carrier_late,
                "payment_total_brl": payment_val,
                "multiple_payments": payment.is_multiple_payments,
                "payment_reconciled": payment.is_reconciled,
            },
            {
                "primary_issue": decision.primary_issue,
                "cause_code": decision.cause_code,
                "recommended_refund_brl": decision.recommended_refund_brl,
            },
        )
        return context


    def get_trace_payload(self, context: DisputeContext) -> Dict[str, Any]:
        d = context.decision
        if not d:
            return {"status": "no_decision"}
        return {
            "primary_issue": d.primary_issue,
            "cause_code": d.cause_code,
            "matched_rule": d.matched_rule,
            "recommended_refund_brl": d.recommended_refund_brl,
            "confidence": d.confidence,
            "actions": d.actions
        }

    def get_agent_context(self, context: DisputeContext) -> Dict[str, Any]:
        d = context.decision
        if not d:
            return {}
        return {
            "agent_thought": f"Applied EC_POLICY_V1 rules hierarchy. Matched rule: '{d.matched_rule}' with confidence {d.confidence}.",
            "policy_evidence_used": d.evidence_used,
            "recommended_refund_brl": d.recommended_refund_brl
        }
