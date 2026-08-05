import json
from typing import Dict, Any, List
from src.agent_framework import BaseAgent, GroqLLMClient, TraceLogger
from src.data_tools import OlistDataLoader

class CoordinatorAgent(BaseAgent):
    def __init__(self, llm_client: GroqLLMClient, trace_logger: TraceLogger):
        system_prompt = (
            "You are the Coordinator Agent of a multi-agent e-commerce dispute resolution system. "
            "Your job is to analyze customer claims, extract claimed_order_id, and coordinate domain investigators."
        )
        super().__init__("CoordinatorAgent", "dispute_intake", system_prompt, llm_client, trace_logger)

    def process(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        case_id = case_data.get("case_id", "")
        customer_req = case_data.get("customer_request", {})
        claimed_order_id = customer_req.get("claimed_order_id", "")
        message = customer_req.get("message", "")

        prompt = f"Analyze customer dispute request for case {case_id} on order {claimed_order_id}: '{message}'. Formulate investigation plan for domain agents."
        analysis_text = self.run(case_id, prompt, case_data)

        return {
            "case_id": case_id,
            "claimed_order_id": claimed_order_id,
            "customer_message": message,
            "intake_analysis": analysis_text
        }

class OrderSellerInvestigator(BaseAgent):
    def __init__(self, llm_client: GroqLLMClient, trace_logger: TraceLogger):
        system_prompt = (
            "You are the Order & Seller Investigator Agent. "
            "Analyze order status, item details, seller IDs, and check if carrier handoff exceeded seller's shipping_limit_date."
        )
        super().__init__("OrderSellerInvestigator", "fulfillment_investigation", system_prompt, llm_client, trace_logger)

    def process(self, case_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = "Evaluate order status, seller handoff timeliness against limit dates, item listings, and seller IDs."
        analysis = self.run(case_id, prompt, order_data)

        return {
            "order_status": order_data.get("order_status"),
            "items": order_data.get("items"),
            "item_ids": order_data.get("item_ids"),
            "seller_ids": order_data.get("seller_ids"),
            "seller_handoff_late": order_data.get("seller_handoff_late"),
            "late_sellers": order_data.get("late_sellers"),
            "fulfillment_analysis": analysis
        }

class FinancialReconciler(BaseAgent):
    def __init__(self, llm_client: GroqLLMClient, trace_logger: TraceLogger):
        system_prompt = (
            "You are the Financial & Payment Reconciler Agent. "
            "Reconcile item costs, freight values, and total payment amounts. Check for split payment reconciliation tolerances (within 0.10 BRL)."
        )
        super().__init__("FinancialReconciler", "financial_reconciliation", system_prompt, llm_client, trace_logger)

    def process(self, case_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = "Reconcile payment totals against item total + freight total. Evaluate payment count and split payment validity."
        analysis = self.run(case_id, prompt, order_data)

        return {
            "item_total_brl": order_data.get("item_total_brl"),
            "freight_total_brl": order_data.get("freight_total_brl"),
            "payment_total_brl": order_data.get("payment_total_brl"),
            "payment_ids": order_data.get("payment_ids"),
            "payment_count": len(order_data.get("payments", [])),
            "payment_diff": order_data.get("payment_diff"),
            "reconciliation_analysis": analysis
        }

class LogisticsDeliveryInvestigator(BaseAgent):
    def __init__(self, llm_client: GroqLLMClient, trace_logger: TraceLogger):
        system_prompt = (
            "You are the Logistics & Delivery Investigator Agent. "
            "Compare customer delivery timestamps against estimated delivery dates to determine whether delivery was late."
        )
        super().__init__("LogisticsDeliveryInvestigator", "delivery_timeline_investigation", system_prompt, llm_client, trace_logger)

    def process(self, case_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = "Evaluate delivery timeline: compare customer delivery date vs estimated delivery date."
        analysis = self.run(case_id, prompt, order_data)

        return {
            "dates": order_data.get("dates"),
            "is_delivery_late": order_data.get("is_delivery_late"),
            "delivery_analysis": analysis
        }

class AdversarialAuditor(BaseAgent):
    def __init__(self, llm_client: GroqLLMClient, trace_logger: TraceLogger):
        system_prompt = (
            "You are the Adversarial Auditor Agent. "
            "Cross-examine customer claims against domain findings. Audit for false claims, edge cases, and discrepancies."
        )
        super().__init__("AdversarialAuditor", "claim_cross_examination", system_prompt, llm_client, trace_logger)

    def process(self, case_id: str, intake: Dict[str, Any], order_inv: Dict[str, Any], fin_inv: Dict[str, Any], del_inv: Dict[str, Any], order_data: Dict[str, Any]) -> Dict[str, Any]:
        audit_context = {
            "customer_message": intake.get("customer_message"),
            "order_status": order_inv.get("order_status"),
            "is_delivery_late": del_inv.get("is_delivery_late"),
            "seller_handoff_late": order_inv.get("seller_handoff_late"),
            "payment_diff": fin_inv.get("payment_diff"),
            "evaluated_rule": order_data.get("evaluated_rule")
        }

        prompt = "Perform adversarial audit: challenge the claim, verify evidence validity, confirm ground-truth issue."
        audit_findings = self.run(case_id, prompt, audit_context)

        return {
            "audit_context": audit_context,
            "audit_findings": audit_findings
        }

class PolicyAdjudicator(BaseAgent):
    def __init__(self, llm_client: GroqLLMClient, trace_logger: TraceLogger):
        system_prompt = (
            "You are the Policy Adjudicator Agent for EC_POLICY_V1. "
            "Synthesize domain investigations and audit findings. Apply strict policy rules to output final resolution assessment."
        )
        super().__init__("PolicyAdjudicator", "policy_adjudication", system_prompt, llm_client, trace_logger)

    def process(self, case_id: str, order_data: Dict[str, Any], audit_res: Dict[str, Any]) -> Dict[str, Any]:
        evaluated = order_data["evaluated_rule"]
        prompt = (
            f"Adjudicate case under EC_POLICY_V1. Primary issue determined by deterministic evaluation: {evaluated['primary_issue']}. "
            "Confirm resolution actions, financial amounts, root causes, and responsible parties."
        )

        adjudication_text = self.run(case_id, prompt, {"evaluated_rule": evaluated, "audit_res": audit_res})

        return {
            "evaluated_rule": evaluated,
            "adjudication_text": adjudication_text
        }

class ComplianceGuard(BaseAgent):
    def __init__(self, llm_client: GroqLLMClient, trace_logger: TraceLogger):
        system_prompt = (
            "You are the Compliance & Schema Guard Agent. "
            "Verify all evidence IDs, formatting rules, entity list size bounds, confidence scores, and JSON schema constraints."
        )
        super().__init__("ComplianceGuard", "output_verification", system_prompt, llm_client, trace_logger)

    def process(self, case_id: str, order_id: str, order_data: Dict[str, Any], adjudication: Dict[str, Any]) -> Dict[str, Any]:
        rule = order_data["evaluated_rule"]

        # Build clean deterministic output schema complying 100% with README specs
        primary_issue = rule["primary_issue"]
        case_status = rule["case_status"]
        confidence = 0.95 if case_status == "action_required" else 0.98

        # Affected entities (max 5 per list)
        order_ids = [order_id][:5]
        item_ids = order_data.get("item_ids", [])[:5]
        seller_ids = order_data.get("seller_ids", [])[:5]
        payment_ids = order_data.get("payment_ids", [])[:5]

        # Financial resolution
        item_total = float(order_data.get("item_total_brl", 0.0))
        freight_total = float(order_data.get("freight_total_brl", 0.0))
        payment_total = float(order_data.get("payment_total_brl", 0.0))
        rec_refund = float(rule.get("recommended_refund_brl", 0.0))

        # Root cause analysis
        root_cause_code = rule["root_cause_code"]
        ranked_causes = [{"cause_code": root_cause_code, "rank": 1}][:3]

        responsible_parties = []
        if rule.get("responsible_party_type") and rule.get("responsible_party_id"):
            responsible_parties.append({
                "party_type": rule["responsible_party_type"],
                "party_id": rule["responsible_party_id"]
            })
        responsible_parties = responsible_parties[:3]

        # Evidence IDs: order:<id>, item:<id>:<seq>, payment:<id>:<seq>, seller:<id>, policy:<code >
        evidence_ids = []
        evidence_ids.append(f"order:{order_id}")
        for i_id in item_ids:
            evidence_ids.append(f"item:{i_id}")
        for p_id in payment_ids:
            evidence_ids.append(f"payment:{p_id}")
        for s_id in seller_ids:
            evidence_ids.append(f"seller:{s_id}")
        evidence_ids.append(f"policy:{root_cause_code}")

        # Limit evidence_ids to max 10
        evidence_ids = sorted(list(dict.fromkeys(evidence_ids)))[:10]

        resolution_actions = [rule["action"]][:5]

        final_output = {
            "case_id": case_id,
            "assessment": {
                "primary_issue": primary_issue,
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
                "ranked_causes": ranked_causes,
                "responsible_parties": responsible_parties
            },
            "evidence_ids": evidence_ids,
            "financial_resolution": {
                "currency": "BRL",
                "item_total_brl": item_total,
                "freight_total_brl": freight_total,
                "payment_total_brl": payment_total,
                "recommended_refund_brl": rec_refund
            },
            "resolution_actions": resolution_actions
        }

        # Validate with LLM Guard
        guard_prompt = "Validate final output structure and verify adherence to EC_POLICY_V1."
        self.run(case_id, guard_prompt, {"output": final_output})

        return final_output
