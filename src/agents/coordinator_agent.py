import time
from typing import Dict, Any, List
from src.context import DisputeContext
from src.agents.order_agent import OrderAgent
from src.agents.delivery_agent import DeliveryAgent
from src.agents.payment_agent import PaymentAgent
from src.agents.policy_agent import PolicyAgent
from src.agents.verifier_agent import VerifierAgent
from src.llm_client import OllamaClient

class WorkflowEngine:
    """
    Orchestrates the sequential execution state machine across specialized domain agents.
    """
    def __init__(self, output_dir: str = "output"):
        self.order_agent = OrderAgent()
        self.delivery_agent = DeliveryAgent()
        self.payment_agent = PaymentAgent()
        self.policy_agent = PolicyAgent()
        self.verifier_agent = VerifierAgent(output_dir=output_dir)

    def run_workflow(self, context: DisputeContext) -> DisputeContext:
        try:
            # Step 1: Init & Handoff to OrderAgent
            context.add_trace_event(
                step=1,
                from_agent="Coordinator",
                to_agent="OrderAgent",
                action="INIT_AND_DISPATCH_ORDER",
                payload={"claimed_order_id": context.claimed_order_id},
                agent_context={
                    "system_prompt": "You are the Chief Coordinator Orchestrator. Your objective is to process customer dispute intents via Local LLM and coordinate domain agent handoffs.",
                    "agent_thought": "Received customer dispute case. Dispatched to OrderAgent to fetch order status and item records.",
                    "llm_intent_extracted": context.llm_intent,
                    "raw_customer_message": context.customer_request.get("message", "")
                },
                duration_ms=0.5
            )
            context = self.order_agent.run_with_trace(context, step=2, from_agent="Coordinator")
            context = self.delivery_agent.run_with_trace(context, step=3, from_agent="OrderAgent")
            context = self.payment_agent.run_with_trace(context, step=4, from_agent="DeliveryAgent")
            context = self.policy_agent.run_with_trace(context, step=5, from_agent="PaymentAgent")
            context = self.verifier_agent.run_with_trace(context, step=6, from_agent="PolicyAgent")

            # --- ACTOR-CRITIC SELF-CORRECTION HANDOFF LOOP ---
            step_counter = 7
            while context.verification_failed and context.retry_count < 2:
                context.retry_count += 1
                context.add_trace_event(
                    step=step_counter,
                    from_agent="VerifierAgent",
                    to_agent="PolicyAgent",
                    action="REJECT_AND_RETRY_POLICY",
                    payload={"retry_attempt": context.retry_count, "feedback": context.verification_feedback},
                    agent_context={
                        "agent_thought": f"[Actor-Critic Loop] Verifier rejected decision due to audit failure. Handoff backwards to PolicyAgent (Attempt {context.retry_count}/2).",
                        "verification_feedback": context.verification_feedback
                    },
                    duration_ms=0.3
                )
                step_counter += 1
                context = self.policy_agent.run_with_trace(context, step=step_counter, from_agent="VerifierAgent")
                step_counter += 1
                context = self.verifier_agent.run_with_trace(context, step=step_counter, from_agent="PolicyAgent")
                step_counter += 1

        except Exception as e:
            context.errors.append(f"RUNTIME_ERROR: Workflow exception: {str(e)}")
            if not context.final_output:
                context = self.verifier_agent.run_with_trace(context, step=99, from_agent="FallbackEngine")
                
        return context


class CoordinatorAgent:
    """
    Coordinator Agent receiving cases from input, invoking real Ollama Local LLM analysis, and triggering WorkflowEngine.
    """
    def __init__(self, output_dir: str = "output"):
        self.workflow_engine = WorkflowEngine(output_dir=output_dir)
        self.llm_client = OllamaClient.get_instance()

    def process_case(self, raw_input: Dict[str, Any]) -> DisputeContext:
        case_id = raw_input.get("case_id", "EC_UNKNOWN")
        opened_at = raw_input.get("opened_at", "")
        cust_req = raw_input.get("customer_request", {})
        claimed_order_id = cust_req.get("claimed_order_id", "")
        vi_message = cust_req.get("message", "")

        # Call REAL Ollama Local (qwen2.5:7b) to analyze customer complaint intent
        llm_intent = self.llm_client.analyze_case_intent(vi_message, claimed_order_id)

        context = DisputeContext(
            case_id=case_id,
            opened_at=opened_at,
            customer_request=cust_req,
            claimed_order_id=claimed_order_id,
            llm_intent=llm_intent
        )
        
        context = self.workflow_engine.run_workflow(context)
        return context
