import sys
import os
sys.path.insert(0, "/home/renkyu/project/K3-Day9-parknotech")

import json
import glob

REQUIRED_TOP_KEYS = {
    "case_id", "assessment", "affected_entities",
    "root_cause_analysis", "evidence_ids",
    "financial_resolution", "resolution_actions"
}

ALLOWED_PRIMARY_ISSUES = {
    "canceled_order_paid", "unavailable_order_paid",
    "late_delivery_seller", "late_delivery_logistics",
    "valid_split_payment", "unsupported_late_claim"
}

ALLOWED_ACTIONS = {
    "issue_full_refund", "refund_freight",
    "explain_valid_split_payment", "reject_late_refund"
}

ALLOWED_CAUSE_CODES = {
    "SELLER_HANDOFF_AFTER_LIMIT", "CARRIER_DELIVERED_AFTER_ESTIMATE",
    "ORDER_CANCELED_AFTER_PAYMENT", "ORDER_UNAVAILABLE_AFTER_PAYMENT",
    "MULTIPLE_PAYMENTS_RECONCILED", "DELIVERY_WITHIN_ESTIMATE"
}

out_files = sorted(glob.glob("output/EC_*.json"))
if not out_files:
    print("ERROR: output/ directory is empty! Run main.py first.")
    sys.exit(1)

errors = []
for filepath in out_files:
    cid = os.path.basename(filepath).replace(".json", "")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    keys = set(data.keys())
    if keys != REQUIRED_TOP_KEYS:
        errors.append(f"{cid}: Missing/extra top-level keys: {REQUIRED_TOP_KEYS - keys}")
        
    ass = data.get("assessment", {})
    issue = ass.get("primary_issue")
    status = ass.get("case_status")
    conf = ass.get("confidence")
    
    if issue not in ALLOWED_PRIMARY_ISSUES:
        errors.append(f"{cid}: Invalid primary_issue '{issue}'")
    if status not in ("action_required", "no_action"):
        errors.append(f"{cid}: Invalid case_status '{status}'")
    if not (0.0 <= conf <= 1.0):
        errors.append(f"{cid}: Invalid confidence '{conf}'")
        
    aff = data.get("affected_entities", {})
    if len(aff.get("order_ids", [])) > 5:
        errors.append(f"{cid}: order_ids > 5")
    if len(aff.get("item_ids", [])) > 5:
        errors.append(f"{cid}: item_ids > 5")
    if len(aff.get("seller_ids", [])) > 5:
        errors.append(f"{cid}: seller_ids > 5")
    if len(aff.get("payment_ids", [])) > 5:
        errors.append(f"{cid}: payment_ids > 5")
        
    rca = data.get("root_cause_analysis", {})
    causes = rca.get("ranked_causes", [])
    if len(causes) > 3:
        errors.append(f"{cid}: ranked_causes > 3")
    for c in causes:
        if c.get("cause_code") not in ALLOWED_CAUSE_CODES:
            errors.append(f"{cid}: Invalid cause_code '{c.get('cause_code')}'")
            
    resp = rca.get("responsible_parties", [])
    if len(resp) > 3:
        errors.append(f"{cid}: responsible_parties > 3")
    for r in resp:
        if r.get("party_type") not in ("seller", "platform", "logistics_provider"):
            errors.append(f"{cid}: Invalid party_type '{r.get('party_type')}'")
            
    evs = data.get("evidence_ids", [])
    if len(evs) > 10:
        errors.append(f"{cid}: evidence_ids > 10")
    for ev in evs:
        prefix = ev.split(":")[0]
        if prefix not in ("order", "item", "payment", "seller", "policy"):
            errors.append(f"{cid}: Invalid evidence_id prefix '{ev}'")
            
    fin = data.get("financial_resolution", {})
    if fin.get("currency") != "BRL":
        errors.append(f"{cid}: Invalid currency '{fin.get('currency')}'")
        
    acts = data.get("resolution_actions", [])
    if len(acts) > 5:
        errors.append(f"{cid}: resolution_actions > 5")
    for act in acts:
        if act not in ALLOWED_ACTIONS:
            errors.append(f"{cid}: Invalid action '{act}'")

if errors:
    print(f"FAILED SCHEMA CHECK: Found {len(errors)} errors:")
    for err in errors:
        print(" -", err)
else:
    print(f"ALL {len(out_files)} OUTPUT JSONs PASSED SCHEMA VERIFICATION 100% PERFECTLY!")
