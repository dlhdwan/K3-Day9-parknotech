import re
from typing import List, Optional, Set

class EvidenceBuilder:
    """
    EvidenceBuilder pipeline: candidate_evidences -> normalize -> deduplicate -> sort -> truncate (max 10).
    Only allows valid evidence IDs directly constructible from CSV / policy codes:
    - order:<order_id>
    - item:<order_id>:<order_item_id>
    - payment:<order_id>:<payment_sequential>
    - seller:<seller_id>
    - policy:<root_cause_code>
    """
    VALID_PREFIXES = ["order:", "item:", "payment:", "seller:", "policy:"]
    VALID_POLICY_CODES = {
        "SELLER_HANDOFF_AFTER_LIMIT",
        "CARRIER_DELIVERED_AFTER_ESTIMATE",
        "ORDER_CANCELED_AFTER_PAYMENT",
        "ORDER_UNAVAILABLE_AFTER_PAYMENT",
        "MULTIPLE_PAYMENTS_RECONCILED",
        "DELIVERY_WITHIN_ESTIMATE",
    }
    PATTERNS = {
        "order": re.compile(r"^order:([^:]+)$"),
        "item": re.compile(r"^item:([^:]+):([^:]+)$"),
        "payment": re.compile(r"^payment:([^:]+):([^:]+)$"),
        "seller": re.compile(r"^seller:([^:]+)$"),
        "policy": re.compile(r"^policy:([^:]+)$"),
    }
    
    @classmethod
    def normalize(cls, candidates: List[str]) -> List[str]:
        normalized = []
        for cand in candidates:
            if not cand or not isinstance(cand, str):
                continue
            item = cand.strip()
            prefix = item.split(":", 1)[0]
            pattern = cls.PATTERNS.get(prefix)
            if pattern and pattern.fullmatch(item):
                normalized.append(item)
        return normalized

    @classmethod
    def deduplicate(cls, items: List[str]) -> List[str]:
        seen = set()
        deduped = []
        for item in items:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped

    @classmethod
    def sort_by_priority(cls, items: List[str]) -> List[str]:
        priority = {
            "order": 1,
            "item": 2,
            "payment": 3,
            "seller": 4,
            "policy": 5
        }
        def get_priority(item: str) -> tuple:
            prefix = item.split(":")[0]
            return (priority.get(prefix, 99), item)
        return sorted(items, key=get_priority)

    @classmethod
    def validate_references(
        cls,
        items: List[str],
        order_id: str,
        item_ids: Set[str],
        payment_ids: Set[str],
        seller_ids: Set[str],
        policy_code: Optional[str],
    ) -> List[str]:
        valid = []
        for item in items:
            prefix = item.split(":", 1)[0]
            parts = item.split(":")
            if prefix == "order" and parts[1] == order_id:
                valid.append(item)
            elif prefix == "item" and parts[1] == order_id and parts[2] in item_ids:
                valid.append(item)
            elif prefix == "payment" and parts[1] == order_id and parts[2] in payment_ids:
                valid.append(item)
            elif prefix == "seller" and parts[1] in seller_ids:
                valid.append(item)
            elif prefix == "policy" and parts[1] == policy_code and parts[1] in cls.VALID_POLICY_CODES:
                valid.append(item)
        return valid

    @classmethod
    def build(
        cls,
        candidate_evidences: List[str],
        max_limit: int = 10,
        *,
        order_id: Optional[str] = None,
        item_ids: Optional[Set[str]] = None,
        payment_ids: Optional[Set[str]] = None,
        seller_ids: Optional[Set[str]] = None,
        policy_code: Optional[str] = None,
    ) -> List[str]:
        step1 = cls.normalize(candidate_evidences)
        step2 = cls.deduplicate(step1)
        if order_id is not None:
            step2 = cls.validate_references(
                step2,
                order_id,
                item_ids or set(),
                payment_ids or set(),
                seller_ids or set(),
                policy_code,
            )
        step3 = cls.sort_by_priority(step2)
        return step3[:max_limit]
