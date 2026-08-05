from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.context import DisputeContext
from src.data_loader import OlistDataLoader

class PaymentAgent(BaseAgent):
    name = "PaymentAgent"
    version = "1.0.0"
    description = "Reconciles payment records against item and freight sums."
    owner = "Financial & Policy Engine"

    def run(self, context: DisputeContext) -> DisputeContext:
        data_loader = OlistDataLoader.get_instance()
        oid = context.claimed_order_id
        
        payment_rows = data_loader.get_order_payments(oid)
        context.payment.payment_rows = payment_rows
        
        total_payment = 0.0
        for row in payment_rows:
            val = float(row.get("payment_value", 0.0))
            total_payment += val
            seq = str(row.get("payment_sequential", "1"))
            context.candidate_evidences.append(f"payment:{oid}:{seq}")

        context.payment.payment_total_brl = round(total_payment, 2)
        context.payment.is_multiple_payments = len(payment_rows) >= 2

        expected_total = round(context.order.item_total_brl + context.order.freight_total_brl, 2)
        diff = round(abs(context.payment.payment_total_brl - expected_total), 2)
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
