from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
from src.llm_client import OllamaLLMClient
from src.trace_logger import TraceLogger

class ComplianceGuard(BaseAgent):
    def __init__(self, llm_client: OllamaLLMClient, trace_logger: TraceLogger):
        system_prompt = (
            "You are the Compliance & Schema Guard Agent. "
            "Verify all evidence IDs, formatting rules, entity list size bounds, confidence scores, and JSON schema constraints."
        )
        super().__init__("ComplianceGuard", "output_verification", system_prompt, llm_client, trace_logger)

    def process(self, case_id: str, order_id: str, order_data: Dict[str, Any], adjudication: Dict[str, Any]) -> Dict[str, Any]:
        rule = order_data["evaluated_rule"]

        primary_issue = rule["primary_issue"]
        case_status = rule["case_status"]
        confidence = 0.95 if case_status == "action_required" else 0.98

        order_ids = [order_id][:5]
        item_ids = order_data.get("item_ids", [])[:5]
        seller_ids = order_data.get("seller_ids", [])[:5]
        payment_ids = order_data.get("payment_ids", [])[:5]
        late_sellers = order_data.get("late_sellers", [])

        item_total = float(order_data.get("item_total_brl", 0.0))
        freight_total = float(order_data.get("freight_total_brl", 0.0))
        payment_total = float(order_data.get("payment_total_brl", 0.0))
        rec_refund = float(rule.get("recommended_refund_brl", 0.0))

        root_cause_code = rule["root_cause_code"]
        ranked_causes = [{"cause_code": root_cause_code, "rank": 1}][:3]

        responsible_parties = []
        if rule.get("responsible_party_type") and rule.get("responsible_party_id"):
            responsible_parties.append({
                "party_type": rule["responsible_party_type"],
                "party_id": rule["responsible_party_id"]
            })
        responsible_parties = responsible_parties[:3]

        evidence_ids = []
        evidence_ids.append(f"order:{order_id}")
        for i_id in item_ids:
            evidence_ids.append(f"item:{i_id}")
        for p_id in payment_ids:
            evidence_ids.append(f"payment:{p_id}")
            
        if primary_issue == "late_delivery_seller":
            target_sellers = late_sellers if late_sellers else seller_ids
            for s_id in target_sellers[:5]:
                evidence_ids.append(f"seller:{s_id}")
                
        evidence_ids.append(f"policy:{root_cause_code}")

        unique_ev = []
        for ev in evidence_ids:
            if ev not in unique_ev:
                unique_ev.append(ev)
        evidence_ids = unique_ev[:10]

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

        guard_prompt = "Validate final output structure and verify adherence to EC_POLICY_V1."
        self.run(case_id, guard_prompt, {"output": final_output})

        return final_output
