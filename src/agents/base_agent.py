import time
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.context import DisputeContext

class BaseAgent(ABC):
    """
    BaseAgent abstract interface for all Multi-Agent components.
    Defines metadata and standardized run execution with duration logging.
    """
    name: str = "BaseAgent"
    version: str = "1.0.0"
    description: str = "Abstract agent interface"
    owner: str = "System"
    system_prompt: str = "You are an autonomous AI Agent operating within an enterprise e-commerce workflow."

    @abstractmethod
    def run(self, context: DisputeContext) -> DisputeContext:
        """
        Execute domain-specific logic and update assigned state ownership in context.
        """
        pass

    def run_with_trace(self, context: DisputeContext, step: int, from_agent: str) -> DisputeContext:
        """
        Wrapper to execute run() and record precise duration and rich trace events in context.
        """
        start_time = time.perf_counter()
        context = self.run(context)
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0

        payload = self.get_trace_payload(context)
        agent_ctx = self.get_agent_context(context)
        
        # Automatically inject persona / system prompt context into trace logs
        if "system_prompt" not in agent_ctx and self.system_prompt:
            agent_ctx["system_prompt"] = self.system_prompt

        context.add_trace_event(
            step=step,
            from_agent=from_agent,
            to_agent=self.name,
            action=f"EXECUTE_{self.name.upper()}",
            payload=payload,
            agent_context=agent_ctx,
            duration_ms=duration_ms
        )
        return context

    def get_trace_payload(self, context: DisputeContext) -> Dict[str, Any]:
        """
        Override to customize payload captured in event trace log.
        """
        return {"agent": self.name, "case_id": context.case_id}

    def get_agent_context(self, context: DisputeContext) -> Dict[str, Any]:
        """
        Override to provide rich agent context and thought processes for trace monitoring.
        """
        return {"llm_intent": context.llm_intent}
