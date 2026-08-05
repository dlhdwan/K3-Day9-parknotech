import json
from typing import Dict, Any
from src.llm_client import OllamaLLMClient
from src.trace_logger import TraceLogger

class BaseAgent:
    def __init__(self, name: str, role: str, system_prompt: str, llm_client: OllamaLLMClient, trace_logger: TraceLogger):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm_client = llm_client
        self.trace_logger = trace_logger

    def run(self, case_id: str, prompt: str, context: Dict[str, Any]) -> str:
        full_user_prompt = f"Context:\n{json.dumps(context, indent=2, ensure_ascii=False)}\n\nPrompt:\n{prompt}\n\nNote: Respond in 1-2 concise sentences."
        response = self.llm_client.chat_completion(
            system_prompt=self.system_prompt,
            user_prompt=full_user_prompt
        )
        self.trace_logger.log_step(
            case_id=case_id,
            agent_name=self.name,
            action=self.role,
            input_payload={"prompt": prompt, "context_keys": list(context.keys())},
            output_payload=response
        )
        return response
