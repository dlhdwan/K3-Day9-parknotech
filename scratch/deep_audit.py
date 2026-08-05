import sys
import os
sys.path.insert(0, "/home/renkyu/project/K3-Day9-parknotech")

import json
import glob
from src.data_loader import OlistDataLoader

loader = OlistDataLoader.get_instance("data")

print(f"{'Case':<7} | {'Status':<11} | {'Delivered':<19} | {'Estimate':<19} | {'IsLate':<7} | {'CarrierHandoff':<19} | {'ShipLimit':<19} | {'CarrierLate':<11} | {'PayRows':<7} | {'CurrentIssue':<24}")
print("=" * 160)

for i in range(1, 51):
    cid = f"EC_{i:03d}"
    inp_path = os.path.join("input", f"{cid}.json")
    with open(inp_path, "r", encoding="utf-8") as f:
        inp = json.load(f)
    oid = inp["customer_request"]["claimed_order_id"]
    
    order = loader.get_order(oid) or {}
    items = loader.get_order_items(oid)
    pays = loader.get_order_payments(oid)
    
    status = order.get("order_status", "")
    del_date = order.get("order_delivered_customer_date", "")
    est_date = order.get("order_estimated_delivery_date", "")
    carrier_date = order.get("order_delivered_carrier_date", "")
    
    ship_limits = [it.get("shipping_limit_date", "") for it in items if it.get("shipping_limit_date")]
    max_ship_limit = max(ship_limits) if ship_limits else ""
    
    is_late = False
    if del_date and est_date:
        is_late = del_date > est_date
        
    carrier_late = False
    if carrier_date and max_ship_limit:
        carrier_late = carrier_date > max_ship_limit
        
    out_path = os.path.join("output", f"{cid}.json")
    cur_issue = ""
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            cur_issue = json.load(f)["assessment"]["primary_issue"]
            
    print(f"{cid:<7} | {status:<11} | {del_date[:19]:<19} | {est_date[:19]:<19} | {str(is_late):<7} | {carrier_date[:19]:<19} | {max_ship_limit[:19]:<19} | {str(carrier_late):<11} | {len(pays):<7} | {cur_issue:<24}")
