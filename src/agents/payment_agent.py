from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.context import DisputeContext, round_currency
from src.tools import PaymentLookupTool

class PaymentAgent(BaseAgent):
    name = "PaymentAgent"
    version = "1.0.0"
    description = "Reconciles payment records against item and freight sums."
    owner = "Financial & Policy Engine"
    system_prompt = "You are a Financial Reconciliation Specialist. You compare payment receipt totals against itemized invoices within an allowable tolerance of 0.10 BRL."

    def __init__(self) -> None:
        self.payment_tool = PaymentLookupTool()


    def run(self, context: DisputeContext) -> DisputeContext:
        oid = context.claimed_order_id
        payment_rows = self.payment_tool.run(context, oid)
        context.payment.payment_rows = payment_rows
        
        total_payment = 0.0
        for row in payment_rows:
            val = float(row.get("payment_value", 0.0))
            total_payment += val
            seq = str(row.get("payment_sequential", "1"))
            context.candidate_evidences.append(f"payment:{oid}:{seq}")

        context.payment.payment_total_brl = round_currency(total_payment)
        context.payment.is_multiple_payments = len(payment_rows) >= 2

        expected_total = round_currency(context.order.item_total_brl + context.order.freight_total_brl)
        diff = round_currency(abs(context.payment.payment_total_brl - expected_total))
        context.payment.reconciliation_diff_brl = diff
        
        context.payment.is_reconciled = (diff <= 0.10)

        return context

    def get_trace_payload(self, context: DisputeContext) -> Dict[str, Any]:
        return {
            "payment_count": len(context.payment.payment_rows),
            "payment_total_brl": context.payment.payment_total_brl,
            "is_multiple_payments": context.payment.is_multiple_payments,
            "is_reconciled": context.payment.is_reconciled,
            "diff_brl": context.payment.reconciliation_diff_brl
        }

    def get_agent_context(self, context: DisputeContext) -> Dict[str, Any]:
        p = context.payment
        expected_total = round(context.order.item_total_brl + context.order.freight_total_brl, 2)
        return {
            "agent_thought": f"Reconciling payments. Found {len(p.payment_rows)} records totaling {p.payment_total_brl} BRL against expected item+freight {expected_total} BRL.",
            "reconciliation_result": "MATCH_WITHIN_TOLERANCE" if p.is_reconciled else f"MISMATCH_BY_{p.reconciliation_diff_brl}_BRL"
        }
