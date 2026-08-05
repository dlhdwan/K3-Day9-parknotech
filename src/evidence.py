import re
from typing import List

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
    
    @classmethod
    def normalize(cls, candidates: List[str]) -> List[str]:
        normalized = []
        for cand in candidates:
            if not cand or not isinstance(cand, str):
                continue
            item = cand.strip()
            # Check if matches any valid prefix format
            if any(item.startswith(p) and len(item) > len(p) for p in cls.VALID_PREFIXES):
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
    def build(cls, candidate_evidences: List[str], max_limit: int = 10) -> List[str]:
        step1 = cls.normalize(candidate_evidences)
        step2 = cls.deduplicate(step1)
        step3 = cls.sort_by_priority(step2)
        return step3[:max_limit]
