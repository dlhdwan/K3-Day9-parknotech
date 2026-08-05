from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.llm_client import OllamaLLMClient
from src.trace_logger import TraceLogger

class PolicyAdjudicator(BaseAgent):
    def __init__(self, llm_client: OllamaLLMClient, trace_logger: TraceLogger):
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
