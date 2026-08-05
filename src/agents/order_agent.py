from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
from src.context import DisputeContext, round_currency
from src.tools import OrderLookupTool

class OrderAgent(BaseAgent):
    name = "OrderAgent"
    version = "1.0.0"
    description = "Handles order status, items, seller information and shipping deadlines."
    owner = "Data Engineering"
    system_prompt = "You are an E-commerce Order Data Investigator. Your mandate is to accurately extract order states, seller identities, and shipping deadlines without hallucination."

    def __init__(self) -> None:
        self.order_tool = OrderLookupTool()


    def run(self, context: DisputeContext) -> DisputeContext:
        oid = context.claimed_order_id
        bundle = self.order_tool.run(context, oid)
        order_row = bundle["order"]
        if not order_row:
            context.errors.append(f"DATA_MISSING: Order ID {oid} not found in dataset.")
            return context

        context.order.order_id = oid
        context.order.order_status = order_row.get("order_status")
        context.order.order_delivered_carrier_date = order_row.get("order_delivered_carrier_date")
        context.order.order_delivered_customer_date = order_row.get("order_delivered_customer_date")
        context.order.order_estimated_delivery_date = order_row.get("order_estimated_delivery_date")
        
        context.candidate_evidences.append(f"order:{oid}")

        items = bundle["items"]
        context.order.items = items
        
        item_total = 0.0
        freight_total = 0.0
        sellers_map = {}

        for item in items:
            item_id = str(item.get("order_item_id", ""))
            seller_id = str(item.get("seller_id", ""))
            limit_date = str(item.get("shipping_limit_date", ""))

            price = float(item.get("price", 0.0))
            freight = float(item.get("freight_value", 0.0))

            item_total += price
            freight_total += freight

            if item_id:
                context.order.shipping_limit_dates[item_id] = limit_date
                context.candidate_evidences.append(f"item:{oid}:{item_id}")
            
            if seller_id and seller_id not in sellers_map:
                seller_info = next((seller for seller in bundle["sellers"] if seller.get("seller_id") == seller_id), {"seller_id": seller_id})
                sellers_map[seller_id] = seller_info
                context.candidate_evidences.append(f"seller:{seller_id}")

        context.order.sellers = list(sellers_map.values())
        context.order.item_total_brl = round_currency(item_total)
        context.order.freight_total_brl = round_currency(freight_total)
        
        return context

    def get_trace_payload(self, context: DisputeContext) -> Dict[str, Any]:
        return {
            "order_id": context.order.order_id,
            "status": context.order.order_status,
            "item_count": len(context.order.items),
            "item_total_brl": context.order.item_total_brl,
            "freight_total_brl": context.order.freight_total_brl
        }

    def get_agent_context(self, context: DisputeContext) -> Dict[str, Any]:
        return {
            "agent_thought": f"Analyzed order {context.order.order_id}. Found status='{context.order.order_status}', {len(context.order.items)} items, and {len(context.order.sellers)} sellers.",
            "llm_customer_intent": context.llm_intent,
            "shipping_limits_identified": list(context.order.shipping_limit_dates.values())
        }
