from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import datetime

@dataclass
class OrderSubContext:
    order_id: Optional[str] = None
    order_status: Optional[str] = None
    items: List[Dict[str, Any]] = field(default_factory=list)
    sellers: List[Dict[str, Any]] = field(default_factory=list)
    item_total_brl: float = 0.0
    freight_total_brl: float = 0.0
    shipping_limit_dates: Dict[str, str] = field(default_factory=dict)
    order_delivered_carrier_date: Optional[str] = None
    order_delivered_customer_date: Optional[str] = None
    order_estimated_delivery_date: Optional[str] = None

@dataclass
class DeliverySubContext:
    carrier_delivered_date: Optional[str] = None
    customer_delivered_date: Optional[str] = None
    estimated_delivery_date: Optional[str] = None
    delivered_after_estimate: bool = False
    carrier_received_after_limit: bool = False
    violating_seller_id: Optional[str] = None
    delivery_status_summary: str = ""

@dataclass
class PaymentSubContext:
    payment_rows: List[Dict[str, Any]] = field(default_factory=list)
    payment_total_brl: float = 0.0
    is_multiple_payments: bool = False
    is_reconciled: bool = False
    reconciliation_diff_brl: float = 0.0

@dataclass
class PolicyDecision:
    primary_issue: str
    cause_code: str
    responsible_party_type: Optional[str]
    responsible_party_id: Optional[str]
    recommended_refund_brl: float
    actions: List[str] = field(default_factory=list)
    confidence: float = 1.0
    matched_rule: str = ""
    evidence_used: List[str] = field(default_factory=list)

@dataclass
class DisputeContext:
    case_id: str
    opened_at: str
    customer_request: Dict[str, Any]
    claimed_order_id: str
    
    # LLM Intent & Reasoning Context
    llm_intent: Optional[str] = None
    llm_reasoning: Optional[str] = None

    # Sub-contexts owned by specific agents
    order: OrderSubContext = field(default_factory=OrderSubContext)
    delivery: DeliverySubContext = field(default_factory=DeliverySubContext)
    payment: PaymentSubContext = field(default_factory=PaymentSubContext)
    decision: Optional[PolicyDecision] = None
    
    # Evidence Builder Pipeline
    candidate_evidences: List[str] = field(default_factory=list)
    final_evidence_ids: List[str] = field(default_factory=list)
    
    # Final serialized structure
    final_output: Optional[Dict[str, Any]] = None
    
    # Event Traces and Error logging
    trace_events: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_trace_event(self, step: int, from_agent: str, to_agent: str, action: str, payload: Dict[str, Any], agent_context: Optional[Dict[str, Any]] = None, duration_ms: float = 0.0):
        event = {
            "case_id": self.case_id,
            "step": step,
            "from": from_agent,
            "to": to_agent,
            "action": action,
            "payload": payload,
            "agent_context": agent_context or {},
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.trace_events.append(event)
