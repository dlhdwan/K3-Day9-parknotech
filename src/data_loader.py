import os
import pandas as pd
from typing import Dict, Any, List
from src.config import Config
from src.policy_engine import PolicyEngine

class OlistDataLoader:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or Config.DATA_DIR
        self._load_datasets()

    def _load_datasets(self):
        print("Loading Olist CSV datasets into memory...")
        self.orders = pd.read_csv(os.path.join(self.data_dir, "olist_orders_dataset.csv"))
        self.order_items = pd.read_csv(os.path.join(self.data_dir, "olist_order_items_dataset.csv"))
        self.order_payments = pd.read_csv(os.path.join(self.data_dir, "olist_order_payments_dataset.csv"))
        self.sellers = pd.read_csv(os.path.join(self.data_dir, "olist_sellers_dataset.csv"))
        self.products = pd.read_csv(os.path.join(self.data_dir, "olist_products_dataset.csv"))
        self.customers = pd.read_csv(os.path.join(self.data_dir, "olist_customers_dataset.csv"))
        self.order_reviews = pd.read_csv(os.path.join(self.data_dir, "olist_order_reviews_dataset.csv"))
        print("Olist datasets loaded successfully.")

    def get_order_analysis(self, order_id: str) -> Dict[str, Any]:
        """
        Retrieves all relevant records for order_id across Olist CSVs.
        Handles edge cases such as missing item rows.
        """
        order_rows = self.orders[self.orders["order_id"] == order_id]
        if order_rows.empty:
            return {"exists": False, "error": f"Order {order_id} not found."}

        order_info = order_rows.iloc[0].to_dict()
        order_status = str(order_info.get("order_status", "")).strip().lower()

        delivered_carrier_date = str(order_info.get("order_delivered_carrier_date", "") or "").strip()
        delivered_customer_date = str(order_info.get("order_delivered_customer_date", "") or "").strip()
        estimated_delivery_date = str(order_info.get("order_estimated_delivery_date", "") or "").strip()

        # Items lookup
        items_rows = self.order_items[self.order_items["order_id"] == order_id]
        items_list = []
        item_ids = []
        seller_ids = set()
        item_total_brl = 0.0
        freight_total_brl = 0.0
        seller_handoff_late = False
        late_sellers = []

        if not items_rows.empty:
            for _, row in items_rows.iterrows():
                item_seq = int(row["order_item_id"])
                product_id = str(row["product_id"])
                seller_id = str(row["seller_id"])
                price = float(row["price"])
                freight = float(row["freight_value"])
                shipping_limit = str(row["shipping_limit_date"]).strip()

                item_id_str = f"{order_id}:{item_seq}"
                item_ids.append(item_id_str)
                seller_ids.add(seller_id)

                item_total_brl += price
                freight_total_brl += freight

                if delivered_carrier_date and shipping_limit and delivered_carrier_date > shipping_limit:
                    seller_handoff_late = True
                    late_sellers.append(seller_id)

                items_list.append({
                    "item_id": item_id_str,
                    "order_item_id": item_seq,
                    "product_id": product_id,
                    "seller_id": seller_id,
                    "price": price,
                    "freight_value": freight,
                    "shipping_limit_date": shipping_limit
                })

        item_total_brl = round(item_total_brl, 2)
        freight_total_brl = round(freight_total_brl, 2)
        unique_seller_ids = sorted(list(seller_ids))

        # Payments lookup
        payments_rows = self.order_payments[self.order_payments["order_id"] == order_id]
        payments_list = []
        payment_ids = []
        payment_total_brl = 0.0

        if not payments_rows.empty:
            for _, row in payments_rows.iterrows():
                seq = int(row["payment_sequential"])
                p_type = str(row["payment_type"])
                p_installments = int(row["payment_installments"])
                p_val = float(row["payment_value"])

                pay_id_str = f"{order_id}:{seq}"
                payment_ids.append(pay_id_str)
                payment_total_brl += p_val

                payments_list.append({
                    "payment_id": pay_id_str,
                    "payment_sequential": seq,
                    "payment_type": p_type,
                    "payment_installments": p_installments,
                    "payment_value": p_val
                })

        payment_total_brl = round(payment_total_brl, 2)
        expected_total_brl = round(item_total_brl + freight_total_brl, 2)
        payment_diff = round(abs(payment_total_brl - expected_total_brl), 2)

        is_delivery_late = False
        if delivered_customer_date and estimated_delivery_date and delivered_customer_date > estimated_delivery_date:
            is_delivery_late = True

        # Policy Rule Evaluation
        evaluated_rule = PolicyEngine.evaluate_order(
            order_status=order_status,
            is_delivery_late=is_delivery_late,
            seller_handoff_late=seller_handoff_late,
            late_sellers=late_sellers,
            unique_sellers=unique_seller_ids,
            payment_count=len(payments_list),
            payment_diff=payment_diff,
            payment_total_brl=payment_total_brl,
            freight_total_brl=freight_total_brl
        )

        return {
            "exists": True,
            "order_id": order_id,
            "order_status": order_status,
            "dates": {
                "delivered_carrier_date": delivered_carrier_date,
                "delivered_customer_date": delivered_customer_date,
                "estimated_delivery_date": estimated_delivery_date
            },
            "items": items_list,
            "item_ids": item_ids[:5],
            "seller_ids": unique_seller_ids[:5],
            "item_total_brl": item_total_brl,
            "freight_total_brl": freight_total_brl,
            "seller_handoff_late": seller_handoff_late,
            "late_sellers": late_sellers,
            "payments": payments_list,
            "payment_ids": payment_ids[:5],
            "payment_total_brl": payment_total_brl,
            "expected_total_brl": expected_total_brl,
            "payment_diff": payment_diff,
            "is_delivery_late": is_delivery_late,
            "evaluated_rule": evaluated_rule
        }
