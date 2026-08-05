from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.context import DisputeContext

class DeliveryAgent(BaseAgent):
    name = "DeliveryAgent"
    version = "1.0.0"
    description = "Analyzes actual vs estimated delivery dates and seller handoff limits."
    owner = "Data Engineering"
    system_prompt = "You are a Logistics & Delivery Auditor. Your mission is to analyze carrier delivery milestones, shipping limit dates, and determine if delays originate from seller handoff or courier transit."


    def run(self, context: DisputeContext) -> DisputeContext:
        order = context.order
        delivery = context.delivery

        carrier_date = order.order_delivered_carrier_date
        customer_date = order.order_delivered_customer_date
        estimate_date = order.order_estimated_delivery_date

        delivery.carrier_delivered_date = carrier_date
        delivery.customer_delivered_date = customer_date
        delivery.estimated_delivery_date = estimate_date

        is_late = False
        if customer_date and estimate_date:
            is_late = str(customer_date) > str(estimate_date)
        elif not customer_date and estimate_date:
            is_late = str(context.opened_at) > str(estimate_date)
        
        delivery.delivered_after_estimate = is_late

        carrier_late = False
        violating_seller = None

        for item in order.items:
            limit_date = str(item.get("shipping_limit_date", ""))
            seller_id = str(item.get("seller_id", ""))

            if limit_date and carrier_date:
                if str(carrier_date) > str(limit_date):
                    carrier_late = True
                    violating_seller = seller_id
                    break
            elif limit_date and not carrier_date and order.order_status not in ("canceled", "unavailable"):
                if str(context.opened_at) > str(limit_date):
                    carrier_late = True
                    violating_seller = seller_id
                    break
        
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
