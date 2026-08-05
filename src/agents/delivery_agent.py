from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.llm_client import OllamaLLMClient
from src.trace_logger import TraceLogger

class LogisticsDeliveryInvestigator(BaseAgent):
    def __init__(self, llm_client: OllamaLLMClient, trace_logger: TraceLogger):
        system_prompt = (
            "You are the Logistics & Delivery Investigator Agent. "
            "Compare customer delivery timestamps against estimated delivery dates to determine whether delivery was late."
        )
        super().__init__("LogisticsDeliveryInvestigator", "delivery_timeline_investigation", system_prompt, llm_client, trace_logger)

    def process(self, case_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        analysis_text = f"Delivery late: {order_data.get('is_delivery_late')}. Delivered: {order_data.get('dates', {}).get('delivered_customer_date')} vs Estimated: {order_data.get('dates', {}).get('estimated_delivery_date')}."
        self.trace_logger.log_step(
            case_id=case_id,
            agent_name=self.name,
            action=self.role,
            input_payload={"order_id": order_data.get("order_id")},
            output_payload=analysis_text
        )
        return {
            "dates": order_data.get("dates"),
            "is_delivery_late": order_data.get("is_delivery_late"),
            "delivery_analysis": analysis_text
        }
