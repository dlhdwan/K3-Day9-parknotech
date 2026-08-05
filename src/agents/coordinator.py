from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.llm_client import OllamaLLMClient
from src.trace_logger import TraceLogger

class CoordinatorAgent(BaseAgent):
    def __init__(self, llm_client: OllamaLLMClient, trace_logger: TraceLogger):
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
