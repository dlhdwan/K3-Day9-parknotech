import os
import csv
from typing import Dict, List, Any, Optional

class OlistDataLoader:
    """
    Infrastructure Layer: In-memory data loader and indexer for Olist CSV datasets.
    Provides fast O(1) lookups by order_id and seller_id.
    """
    _instance = None
    _loaded = False

    orders_by_id: Dict[str, Dict[str, Any]] = {}
    items_by_order_id: Dict[str, List[Dict[str, Any]]] = {}
    payments_by_order_id: Dict[str, List[Dict[str, Any]]] = {}
    sellers_by_id: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls, data_dir: str = "data"):
        if cls._instance is None or not cls._loaded:
            cls._instance = cls()
            cls._instance.load_data(data_dir)
            cls._loaded = True
        return cls._instance

    def load_data(self, data_dir: str):
        orders_path = os.path.join(data_dir, "olist_orders_dataset.csv")
        items_path = os.path.join(data_dir, "olist_order_items_dataset.csv")
        payments_path = os.path.join(data_dir, "olist_order_payments_dataset.csv")
        sellers_path = os.path.join(data_dir, "olist_sellers_dataset.csv")

        # Load Orders
        if os.path.exists(orders_path):
            with open(orders_path, mode='r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.orders_by_id[row["order_id"]] = row

        # Load Order Items
        if os.path.exists(items_path):
            with open(items_path, mode='r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    oid = row["order_id"]
                    if oid not in self.items_by_order_id:
                        self.items_by_order_id[oid] = []
                    # Convert price and freight_value to float
                    try:
                        row["price"] = float(row["price"])
                        row["freight_value"] = float(row["freight_value"])
                    except (ValueError, TypeError):
                        pass
                    self.items_by_order_id[oid].append(row)

        # Load Order Payments
        if os.path.exists(payments_path):
            with open(payments_path, mode='r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    oid = row["order_id"]
                    if oid not in self.payments_by_order_id:
                        self.payments_by_order_id[oid] = []
                    try:
                        row["payment_value"] = float(row["payment_value"])
                    except (ValueError, TypeError):
                        pass
                    self.payments_by_order_id[oid].append(row)

        # Load Sellers
        if os.path.exists(sellers_path):
            with open(sellers_path, mode='r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.sellers_by_id[row["seller_id"]] = row

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        return self.orders_by_id.get(order_id)

    def get_order_items(self, order_id: str) -> List[Dict[str, Any]]:
        return self.items_by_order_id.get(order_id, [])

    def get_order_payments(self, order_id: str) -> List[Dict[str, Any]]:
        return self.payments_by_order_id.get(order_id, [])

    def get_seller(self, seller_id: str) -> Optional[Dict[str, Any]]:
        return self.sellers_by_id.get(seller_id)
