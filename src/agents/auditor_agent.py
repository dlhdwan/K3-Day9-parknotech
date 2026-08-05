from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.llm_client import OllamaLLMClient
from src.trace_logger import TraceLogger

class AdversarialAuditor(BaseAgent):
    def __init__(self, llm_client: OllamaLLMClient, trace_logger: TraceLogger):
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
