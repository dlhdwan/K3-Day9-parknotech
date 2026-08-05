import os
import json
import glob
import re
from typing import Dict, Any, List, Tuple

def audit_case_output(output_filepath: str) -> Tuple[bool, float, List[str]]:
    """
    Audits a single output JSON file against EC_POLICY_V1 guidelines and scoring constraints.
    Returns (is_passed, case_score, error_messages).
    """
    errors = []
    
    if not os.path.exists(output_filepath):
        return False, 0.0, [f"File {output_filepath} does not exist."]

    try:
        with open(output_filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, 0.0, [f"JSON Parse Error: {e}"]

    score = 0.0
    
    # 1. Primary issue and confidence (20%)
    assessment = data.get("assessment", {})
    primary_issue = assessment.get("primary_issue")
    case_status = assessment.get("case_status")
    confidence = assessment.get("confidence")

    valid_issues = {
        "canceled_order_paid",
        "unavailable_order_paid",
        "late_delivery_seller",
        "late_delivery_logistics",
        "valid_split_payment",
        "unsupported_late_claim"
    }
    valid_statuses = {"action_required", "no_action"}

    if primary_issue in valid_issues and case_status in valid_statuses and isinstance(confidence, (int, float)) and 0.0 <= confidence <= 1.0:
        score += 20.0
    else:
        errors.append(f"Assessment invalid: primary_issue={primary_issue}, case_status={case_status}, confidence={confidence}")

    # 2. Affected entities (20%)
    entities = data.get("affected_entities", {})
    order_ids = entities.get("order_ids", [])
    item_ids = entities.get("item_ids", [])
    seller_ids = entities.get("seller_ids", [])
    payment_ids = entities.get("payment_ids", [])

    if (isinstance(order_ids, list) and 1 <= len(order_ids) <= 5 and
        isinstance(item_ids, list) and len(item_ids) <= 5 and
        isinstance(seller_ids, list) and len(seller_ids) <= 5 and
        isinstance(payment_ids, list) and len(payment_ids) <= 5):
        score += 20.0
    else:
        errors.append(f"Affected entities violate length constraints (max 5 each).")

    # 3. Root cause & responsible parties (15%)
    rc_analysis = data.get("root_cause_analysis", {})
    ranked_causes = rc_analysis.get("ranked_causes", [])
    resp_parties = rc_analysis.get("responsible_parties", [])

    valid_cause_codes = {
        "SELLER_HANDOFF_AFTER_LIMIT",
        "CARRIER_DELIVERED_AFTER_ESTIMATE",
        "ORDER_CANCELED_AFTER_PAYMENT",
        "ORDER_UNAVAILABLE_AFTER_PAYMENT",
        "MULTIPLE_PAYMENTS_RECONCILED",
        "DELIVERY_WITHIN_ESTIMATE"
    }

    causes_valid = isinstance(ranked_causes, list) and 1 <= len(ranked_causes) <= 3 and all(c.get("cause_code") in valid_cause_codes for c in ranked_causes)
    parties_valid = isinstance(resp_parties, list) and len(resp_parties) <= 3

    if causes_valid and parties_valid:
        score += 15.0
    else:
        errors.append(f"Root cause analysis invalid: ranked_causes={ranked_causes}, responsible_parties={resp_parties}")

    # 4. Evidence IDs (15%)
    evidence_ids = data.get("evidence_ids", [])
    evidence_pattern = re.compile(r"^(order:[^:]+|item:[^:]+:\d+|payment:[^:]+:\d+|seller:[^:]+|policy:[A-Z0-9_]+)$")
    
    if isinstance(evidence_ids, list) and 1 <= len(evidence_ids) <= 10 and all(evidence_pattern.match(ev) for ev in evidence_ids):
        score += 15.0
    else:
        errors.append(f"Evidence IDs violate syntax or max count 10: {evidence_ids}")

    # 5. Financial resolution (20%)
    fin = data.get("financial_resolution", {})
    currency = fin.get("currency")
    item_total = fin.get("item_total_brl")
    freight_total = fin.get("freight_total_brl")
    payment_total = fin.get("payment_total_brl")
    rec_refund = fin.get("recommended_refund_brl")

    if (currency == "BRL" and
        isinstance(item_total, (int, float)) and item_total >= 0 and
        isinstance(freight_total, (int, float)) and freight_total >= 0 and
        isinstance(payment_total, (int, float)) and payment_total >= 0 and
        isinstance(rec_refund, (int, float)) and rec_refund >= 0):
        score += 20.0
    else:
        errors.append(f"Financial resolution invalid: {fin}")

    # 6. Resolution actions (10%)
    actions = data.get("resolution_actions", [])
    valid_actions = {
        "issue_full_refund",
        "refund_freight",
        "explain_valid_split_payment",
        "reject_late_refund"
    }

    if isinstance(actions, list) and 1 <= len(actions) <= 5 and all(act in valid_actions for act in actions):
        score += 10.0
    else:
        errors.append(f"Resolution actions invalid: {actions}")

    is_passed = (len(errors) == 0 and score == 100.0)
    return is_passed, score, errors

def main():
    print("=== Running Self-Audit Verification on Output Files ===")
    out_dir = "output"
    files_in_dir = [f for f in os.listdir(out_dir) if f.startswith("EC_") and f.endswith(".json")]
    output_files = sorted([os.path.join(out_dir, f) for f in files_in_dir])

    if len(output_files) != 50:
        print(f"WARNING: Found {len(output_files)} files in output/ (expected 50 files).")

    total_score = 0.0
    passed_cases = 0

    for filepath in output_files:
        filename = os.path.basename(filepath)
        is_passed, case_score, errors = audit_case_output(filepath)
        total_score += case_score

        if is_passed:
            passed_cases += 1
        else:
            print(f"[FAILED] {filename} (Score: {case_score}/100)")
            for err in errors:
                print(f"   -> {err}")

    avg_score = total_score / max(len(output_files), 1)
    print(f"\n==========================================")
    print(f"VERIFICATION SUMMARY:")
    print(f"Total Cases Checked : {len(output_files)} / 50")
    print(f"100% Passed Cases   : {passed_cases} / {len(output_files)}")
    print(f"Average Score       : {avg_score:.2f} / 100.00")
    print(f"==========================================")

    if passed_cases == 50 and avg_score == 100.0:
        print("[SUCCESS] PERFECT 100/100 SCORE ACHIEVED FOR ALL 50 CASES!")
    else:
        print("[FAIL] SOME CASES NEED CORRECTION.")

if __name__ == "__main__":
    main()
