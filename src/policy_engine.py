from typing import Dict, Any, List

class PolicyEngine:
    """
    Evaluates business rules under EC_POLICY_V1 with 100% strict compliance.
    """
    @staticmethod
    def evaluate_order(
        order_status: str,
        is_delivery_late: bool,
        seller_handoff_late: bool,
        late_sellers: List[str],
        unique_sellers: List[str],
        payment_count: int,
        payment_diff: float,
        payment_total_brl: float,
        freight_total_brl: float
    ) -> Dict[str, Any]:
        """
        Strict Rule Hierarchy (README.md Section 4):
        1. canceled_order_paid
        2. unavailable_order_paid
        3. late_delivery_seller
        4. late_delivery_logistics
        5. valid_split_payment
        6. unsupported_late_claim
        """

        if order_status == "canceled" and payment_total_brl > 0:
            return {
                "primary_issue": "canceled_order_paid",
                "responsible_party_type": "platform",
                "responsible_party_id": "OLIST_PLATFORM",
                "recommended_refund_brl": round(payment_total_brl, 2),
                "action": "issue_full_refund",
                "root_cause_code": "ORDER_CANCELED_AFTER_PAYMENT",
                "case_status": "action_required"
            }

        if order_status == "unavailable" and payment_total_brl > 0:
            return {
                "primary_issue": "unavailable_order_paid",
                "responsible_party_type": "platform",
                "responsible_party_id": "OLIST_PLATFORM",
                "recommended_refund_brl": round(payment_total_brl, 2),
                "action": "issue_full_refund",
                "root_cause_code": "ORDER_UNAVAILABLE_AFTER_PAYMENT",
                "case_status": "action_required"
            }

        if is_delivery_late and seller_handoff_late:
            resp_seller = late_sellers[0] if late_sellers else (unique_sellers[0] if unique_sellers else "UNKNOWN_SELLER")
            return {
                "primary_issue": "late_delivery_seller",
                "responsible_party_type": "seller",
                "responsible_party_id": resp_seller,
                "recommended_refund_brl": round(freight_total_brl, 2),
                "action": "refund_freight",
                "root_cause_code": "SELLER_HANDOFF_AFTER_LIMIT",
                "case_status": "action_required"
            }

        if is_delivery_late and not seller_handoff_late:
            return {
                "primary_issue": "late_delivery_logistics",
                "responsible_party_type": "logistics_provider",
                "responsible_party_id": "LOGISTICS_PROVIDER",
                "recommended_refund_brl": round(freight_total_brl, 2),
                "action": "refund_freight",
                "root_cause_code": "CARRIER_DELIVERED_AFTER_ESTIMATE",
                "case_status": "action_required"
            }

        if payment_count >= 2 and payment_diff <= 0.10:
            return {
                "primary_issue": "valid_split_payment",
                "responsible_party_type": None,
                "responsible_party_id": None,
                "recommended_refund_brl": 0.0,
                "action": "explain_valid_split_payment",
                "root_cause_code": "MULTIPLE_PAYMENTS_RECONCILED",
                "case_status": "no_action"
            }

        return {
            "primary_issue": "unsupported_late_claim",
            "responsible_party_type": None,
            "responsible_party_id": None,
            "recommended_refund_brl": 0.0,
            "action": "reject_late_refund",
            "root_cause_code": "DELIVERY_WITHIN_ESTIMATE",
            "case_status": "no_action"
        }
