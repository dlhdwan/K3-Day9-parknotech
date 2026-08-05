from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.llm_client import OllamaLLMClient
from src.trace_logger import TraceLogger

class FinancialReconciler(BaseAgent):
    def __init__(self, llm_client: OllamaLLMClient, trace_logger: TraceLogger):
        system_prompt = (
            "You are the Financial & Payment Reconciler Agent. "
            "Reconcile item costs, freight values, and total payment amounts. Check for split payment reconciliation tolerances (within 0.10 BRL)."
        )
        super().__init__("FinancialReconciler", "financial_reconciliation", system_prompt, llm_client, trace_logger)

    def process(self, case_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        analysis_text = f"Payment total: {order_data.get('payment_total_brl')} BRL. Item + Freight: {order_data.get('expected_total_brl')} BRL. Diff: {order_data.get('payment_diff')} BRL."
        self.trace_logger.log_step(
            case_id=case_id,
            agent_name=self.name,
            action=self.role,
            input_payload={"order_id": order_data.get("order_id")},
            output_payload=analysis_text
        )
        return {
            "item_total_brl": order_data.get("item_total_brl"),
            "freight_total_brl": order_data.get("freight_total_brl"),
            "payment_total_brl": order_data.get("payment_total_brl"),
            "payment_ids": order_data.get("payment_ids"),
            "payment_count": len(order_data.get("payments", [])),
            "payment_diff": order_data.get("payment_diff"),
            "reconciliation_analysis": analysis_text
        }
