from typing import Any, Dict, List

from src.context import DisputeContext, round_currency
from src.data_loader import OlistDataLoader


class OrderLookupTool:
    name = "olist.get_order_bundle"

    def __init__(self) -> None:
        self.loader = OlistDataLoader.get_instance()

    def run(self, context: DisputeContext, order_id: str) -> Dict[str, Any]:
        order = self.loader.get_order(order_id)
        items = self.loader.get_order_items(order_id)
        seller_ids = sorted({str(item.get("seller_id", "")) for item in items if item.get("seller_id")})
        sellers = [self.loader.get_seller(seller_id) or {"seller_id": seller_id} for seller_id in seller_ids]
        result = {"order": order, "items": items, "sellers": sellers}
        context.record_tool_call(
            "OrderAgent",
            self.name,
            {"order_id": order_id},
            {"order_found": order is not None, "item_count": len(items), "seller_count": len(sellers)},
        )
        return result


class PaymentLookupTool:
    name = "olist.get_order_payments"

    def __init__(self) -> None:
        self.loader = OlistDataLoader.get_instance()

    def run(self, context: DisputeContext, order_id: str) -> List[Dict[str, Any]]:
        rows = self.loader.get_order_payments(order_id)
        context.record_tool_call(
            "PaymentAgent",
            self.name,
            {"order_id": order_id},
            {"payment_count": len(rows), "payment_total_brl": round_currency(sum(float(row.get("payment_value", 0.0)) for row in rows))},
        )
        return rows


class DeliveryAuditTool:
    name = "delivery.audit_timeline"

    def run(
        self,
        context: DisputeContext,
        order: Dict[str, Any],
        items: List[Dict[str, Any]],
        opened_at: str,
    ) -> Dict[str, Any]:
        carrier_date = order.get("order_delivered_carrier_date") or ""
        customer_date = order.get("order_delivered_customer_date") or ""
        estimate_date = order.get("order_estimated_delivery_date") or ""
        status = order.get("order_status") or ""
        is_late = bool(estimate_date and ((customer_date and customer_date > estimate_date) or (not customer_date and opened_at > estimate_date)))
        carrier_late = False
        violating_seller_id = None
        for item in items:
            limit_date = str(item.get("shipping_limit_date", ""))
            if limit_date and carrier_date and carrier_date > limit_date:
                carrier_late = True
                violating_seller_id = str(item.get("seller_id", ""))
                break
            if limit_date and not carrier_date and status not in ("canceled", "unavailable") and opened_at > limit_date:
                carrier_late = True
                violating_seller_id = str(item.get("seller_id", ""))
                break
        result = {
            "carrier_date": carrier_date,
            "customer_date": customer_date,
            "estimate_date": estimate_date,
            "delivered_after_estimate": is_late,
            "carrier_received_after_limit": carrier_late,
            "violating_seller_id": violating_seller_id,
        }
        context.record_tool_call(
            "DeliveryAgent",
            self.name,
            {"order_id": context.claimed_order_id, "opened_at": opened_at},
            {key: result[key] for key in ("delivered_after_estimate", "carrier_received_after_limit", "violating_seller_id")},
        )
        return result


class IndependentCaseAuditTool:
    name = "olist.reload_case_ground_truth"

    def __init__(self) -> None:
        self.loader = OlistDataLoader.get_instance()
        self.delivery_tool = DeliveryAuditTool()

    def run(self, context: DisputeContext) -> Dict[str, Any]:
        order_id = context.claimed_order_id
        order = self.loader.get_order(order_id) or {}
        items = self.loader.get_order_items(order_id)
        payments = self.loader.get_order_payments(order_id)
        sellers = [self.loader.get_seller(seller_id) or {"seller_id": seller_id} for seller_id in sorted({str(item.get("seller_id", "")) for item in items if item.get("seller_id")})]

        carrier_date = order.get("order_delivered_carrier_date") or ""
        customer_date = order.get("order_delivered_customer_date") or ""
        estimate_date = order.get("order_estimated_delivery_date") or ""
        status = order.get("order_status") or ""
        delivered_after_estimate = bool(estimate_date and ((customer_date and customer_date > estimate_date) or (not customer_date and context.opened_at > estimate_date)))
        carrier_received_after_limit = False
        violating_seller_id = None
        for item in items:
            limit_date = str(item.get("shipping_limit_date", ""))
            if limit_date and carrier_date and carrier_date > limit_date:
                carrier_received_after_limit = True
                violating_seller_id = str(item.get("seller_id", ""))
                break
            if limit_date and not carrier_date and status not in ("canceled", "unavailable") and context.opened_at > limit_date:
                carrier_received_after_limit = True
                violating_seller_id = str(item.get("seller_id", ""))
                break

        result = {
            "order": order,
            "items": items,
            "payments": payments,
            "sellers": sellers,
            "item_total_brl": round_currency(sum(float(item.get("price", 0.0)) for item in items)),
            "freight_total_brl": round_currency(sum(float(item.get("freight_value", 0.0)) for item in items)),
            "payment_total_brl": round_currency(sum(float(row.get("payment_value", 0.0)) for row in payments)),
            "delivered_after_estimate": delivered_after_estimate,
            "carrier_received_after_limit": carrier_received_after_limit,
            "violating_seller_id": violating_seller_id,
        }
        context.record_tool_call(
            "VerifierAgent",
            self.name,
            {"order_id": order_id},
            {"order_found": bool(order), "item_count": len(items), "payment_count": len(payments)},
        )
        return result
