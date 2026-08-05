from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.context import DisputeContext
from src.tools import DeliveryAuditTool

class DeliveryAgent(BaseAgent):
    name = "DeliveryAgent"
    version = "1.0.0"
    description = "Analyzes actual vs estimated delivery dates and seller handoff limits."
    owner = "Data Engineering"
    system_prompt = "You are a Logistics & Delivery Auditor. Your mission is to analyze carrier delivery milestones, shipping limit dates, and determine if delays originate from seller handoff or courier transit."

    def __init__(self) -> None:
        self.delivery_tool = DeliveryAuditTool()


    def run(self, context: DisputeContext) -> DisputeContext:
        order = context.order
        delivery = context.delivery
        raw_order = {
            "order_status": order.order_status,
            "order_delivered_carrier_date": order.order_delivered_carrier_date,
            "order_delivered_customer_date": order.order_delivered_customer_date,
            "order_estimated_delivery_date": order.order_estimated_delivery_date,
        }
        audit = self.delivery_tool.run(context, raw_order, order.items, context.opened_at)
        carrier_date = audit["carrier_date"]
        customer_date = audit["customer_date"]
        estimate_date = audit["estimate_date"]

        delivery.carrier_delivered_date = carrier_date
        delivery.customer_delivered_date = customer_date
        delivery.estimated_delivery_date = estimate_date

        is_late = audit["delivered_after_estimate"]
        delivery.delivered_after_estimate = is_late
        carrier_late = audit["carrier_received_after_limit"]
        violating_seller = audit["violating_seller_id"]
        
        delivery.carrier_received_after_limit = carrier_late
        if violating_seller:
            delivery.violating_seller_id = violating_seller
        elif order.items:
            delivery.violating_seller_id = str(order.items[0].get("seller_id", ""))

        if is_late:
            if carrier_late:
                delivery.delivery_status_summary = f"Late Delivery: Seller handed off after limit ({carrier_date} > limit)."
            else:
                delivery.delivery_status_summary = f"Late Delivery: Logistics delay (handoff within limit)."
        else:
            delivery.delivery_status_summary = "Delivery on time or within estimate."

        return context

    def get_trace_payload(self, context: DisputeContext) -> Dict[str, Any]:
        return {
            "delivered_after_estimate": context.delivery.delivered_after_estimate,
            "carrier_received_after_limit": context.delivery.carrier_received_after_limit,
            "violating_seller_id": context.delivery.violating_seller_id,
            "summary": context.delivery.delivery_status_summary
        }

    def get_agent_context(self, context: DisputeContext) -> Dict[str, Any]:
        d = context.delivery
        return {
            "agent_thought": f"Compared timestamps: delivered={d.customer_delivered_date} vs estimated={d.estimated_delivery_date}. Handoff late={d.carrier_received_after_limit}.",
            "delay_responsibility": "Seller" if d.carrier_received_after_limit else ("Logistics" if d.delivered_after_estimate else "None (On Time)")
        }
