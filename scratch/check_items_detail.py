import sys
import os
sys.path.insert(0, "/home/renkyu/project/K3-Day9-parknotech")

import json
from src.data_loader import OlistDataLoader

loader = OlistDataLoader.get_instance("data")

for i in [2, 25, 29, 32]:
    cid = f"EC_{i:03d}"
    inp_path = os.path.join("input", f"{cid}.json")
    with open(inp_path, "r", encoding="utf-8") as f:
        inp = json.load(f)
    oid = inp["customer_request"]["claimed_order_id"]
    order = loader.get_order(oid)
    items = loader.get_order_items(oid)
    
    print(f"=== {cid} (Order ID: {oid}) ===")
    print(f"Order Status: {order.get('order_status')}")
    print(f"Delivered Customer Date: {order.get('order_delivered_customer_date')}")
    print(f"Estimated Delivery Date: {order.get('order_estimated_delivery_date')}")
    print(f"Delivered Carrier Date: {order.get('order_delivered_carrier_date')}")
    print("Items:")
    for it in items:
        print(f"  Item {it.get('order_item_id')}: product={it.get('product_id')}, seller={it.get('seller_id')}, price={it.get('price')}, freight={it.get('freight_value')}, limit={it.get('shipping_limit_date')}")
    print()
