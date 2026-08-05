from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.llm_client import OllamaLLMClient
from src.trace_logger import TraceLogger

class OrderSellerInvestigator(BaseAgent):
    def __init__(self, llm_client: OllamaLLMClient, trace_logger: TraceLogger):
        system_prompt = (
            "You are the Order & Seller Investigator Agent. "
            "Analyze order status, item details, seller IDs, and check if carrier handoff exceeded seller's shipping_limit_date."
        )
        super().__init__("OrderSellerInvestigator", "fulfillment_investigation", system_prompt, llm_client, trace_logger)

    def process(self, case_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        analysis_text = f"Order status is {order_data.get('order_status')}. Seller handoff late: {order_data.get('seller_handoff_late')}."
        self.trace_logger.log_step(
            case_id=case_id,
            agent_name=self.name,
            action=self.role,
            input_payload={"order_id": order_data.get("order_id")},
            output_payload=analysis_text
        )
        return {
            "order_status": order_data.get("order_status"),
            "items": order_data.get("items"),
            "item_ids": order_data.get("item_ids"),
            "seller_ids": order_data.get("seller_ids"),
            "seller_handoff_late": order_data.get("seller_handoff_late"),
            "late_sellers": order_data.get("late_sellers"),
            "fulfillment_analysis": analysis_text
        }
