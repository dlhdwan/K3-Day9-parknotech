import sys
import os
sys.path.insert(0, "/home/renkyu/project/K3-Day9-parknotech")

import json
from src.data_loader import OlistDataLoader

loader = OlistDataLoader.get_instance("data")

print(f"{'Case':<7} | {'Status':<11} | {'PayRows':<7} | {'ItemSum':<10} | {'FreightSum':<10} | {'TotalInvoice':<12} | {'PaySum':<10} | {'Diff':<8} | {'Reconciled':<10} | {'Late':<6}")
print("=" * 130)

for i in range(1, 51):
    cid = f"EC_{i:03d}"
    inp_path = os.path.join("input", f"{cid}.json")
    with open(inp_path, "r", encoding="utf-8") as f:
        inp = json.load(f)
    oid = inp["customer_request"]["claimed_order_id"]
    
    order = loader.get_order(oid) or {}
    items = loader.get_order_items(oid)
    pays = loader.get_order_payments(oid)
    
    item_sum = sum(float(it.get("price", 0)) for it in items)
    freight_sum = sum(float(it.get("freight_value", 0)) for it in items)
    invoice_total = item_sum + freight_sum
    pay_sum = sum(float(p.get("payment_value", 0)) for p in pays)
    
    diff = abs(pay_sum - invoice_total)
    reconciled = diff <= 0.10
    
    del_date = order.get("order_delivered_customer_date", "")
    est_date = order.get("order_estimated_delivery_date", "")
    is_late = bool(del_date and est_date and del_date > est_date)
    
    status = order.get("order_status")
    
    if not reconciled or is_late or len(pays) > 1 or status in ("canceled", "unavailable"):
        print(f"{cid:<7} | {status:<11} | {len(pays):<7} | {item_sum:<10.2f} | {freight_sum:<10.2f} | {invoice_total:<12.2f} | {pay_sum:<10.2f} | {diff:<8.2f} | {str(reconciled):<10} | {str(is_late):<6}")
