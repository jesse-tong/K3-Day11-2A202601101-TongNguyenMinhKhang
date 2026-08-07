"""
Lab 11 — Part 4: Human-in-the-Loop Design
  TODO 11: Confidence Router
  TODO 12: Design 3 HITL decision points
"""
from dataclasses import dataclass


# ============================================================
# TODO 11: Implement ConfidenceRouter
#
# Route agent responses based on confidence scores:
#   - HIGH (>= 0.9): Auto-send to user
#   - MEDIUM (0.7 - 0.9): Queue for human review
#   - LOW (< 0.7): Escalate to human immediately
#
# Special case: if the action is HIGH_RISK (e.g., money transfer,
# account deletion), ALWAYS escalate regardless of confidence.
#
# Implement the route() method.
# ============================================================

HIGH_RISK_ACTIONS = [
    "transfer_money",
    "close_account",
    "change_password",
    "delete_data",
    "update_personal_info",
]


@dataclass
class RoutingDecision:
    """Result of the confidence router."""
    action: str          # "auto_send", "queue_review", "escalate"
    confidence: float
    reason: str
    priority: str        # "low", "normal", "high"
    requires_human: bool


class ConfidenceRouter:
    """Route agent responses based on confidence and risk level.

    Thresholds:
        HIGH:   confidence >= 0.9 -> auto-send
        MEDIUM: 0.7 <= confidence < 0.9 -> queue for review
        LOW:    confidence < 0.7 -> escalate to human

    High-risk actions always escalate regardless of confidence.
    """

    HIGH_THRESHOLD = 0.9
    MEDIUM_THRESHOLD = 0.7

    def route(self, response: str, confidence: float,
              action_type: str = "general") -> RoutingDecision:
        """Route a response based on confidence score and action type.

        Args:
            response: The agent's response text
            confidence: Confidence score between 0.0 and 1.0
            action_type: Type of action (e.g., "general", "transfer_money")

        Returns:
            RoutingDecision with routing action and metadata
        """
        # TODO 11: Implement routing logic
        #
        # 1. Check if action_type is in HIGH_RISK_ACTIONS
        #    -> If yes: always escalate (action="escalate", priority="high",
        #       requires_human=True, reason="High-risk action: {action_type}")
        #
        # 2. Check confidence thresholds:
        #    - confidence >= 0.9:
        #      action="auto_send", priority="low",
        #      requires_human=False, reason="High confidence"
        #
        #    - 0.7 <= confidence < 0.9:
        #      action="queue_review", priority="normal",
        #      requires_human=True, reason="Medium confidence — needs review"
        #
        #    - confidence < 0.7:
        #      action="escalate", priority="high",
        #      requires_human=True, reason="Low confidence — escalating"
        if action_type in HIGH_RISK_ACTIONS:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason=f"High-risk action: {action_type}",
                priority="high",
                requires_human=True,
            )
        if confidence >= self.HIGH_THRESHOLD:
            return RoutingDecision(
                action="auto_send",
                confidence=confidence,
                reason="High confidence",
                priority="low",
                requires_human=False,
            )
        elif confidence >= self.MEDIUM_THRESHOLD:
            return RoutingDecision(
                action="queue_review",
                confidence=confidence,
                reason="Medium confidence — needs review",
                priority="normal",
                requires_human=True,
            )
        else:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason="Low confidence — escalating",
                priority="high",
                requires_human=True,
            )


# ============================================================
# TODO 12: Design 3 HITL decision points + a review lifecycle
#
# For each decision point, define:
# - trigger: What condition activates this HITL check?
# - hitl_model: Which model? (human-in-the-loop, human-on-the-loop,
#   human-as-tiebreaker)
# - context_needed: What info does the human reviewer need?
# - example: A concrete scenario
# - approval_path: What approve/reject/timeout decision is recorded?
# - audit_fields: Which correlation ID, intent and proposed action/diff are logged?
#
# Think about real banking scenarios where human judgment is critical.
# ============================================================

hitl_decision_points = [
    {
        "id": 1,
        "name": "High-Risk Money Transfer & Anti-Fraud Gate",
        "trigger": "Action is \'transfer_money\' AND (amount > 100,000,000 VND OR beneficiary is new external account)",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Account number, beneficiary bank & account name, transfer amount, Anti-Fraud risk score, eKYC status, transaction prompt log",
        "example": "Customer requests via AI bot to transfer 500,000,000 VND to a newly added beneficiary at another bank.",
        "approval_path": "Approve -> Trigger core banking API with OTP challenge; Reject -> Freeze transfer & alert Fraud Monitoring team; Timeout (10m) -> Cancel transaction & notify user.",
        "audit_fields": "correlation_id, customer_cif, intent='transfer_money', payload={'amount': 500000000, 'to_bank': 'NCB', 'to_account': '987654321'}, risk_score=0.88, reviewer_id, reviewer_decision, timestamp",
    },
    {
        "id": 2,
        "name": "Unrecognized Transaction Dispute & Emergency Card Lock",
        "trigger": "Action is 'dispute_transaction' OR (report_fraud AND card_status=='active')",
        "hitl_model": "human-on-the-loop",
        "context_needed": "Disputed transaction ID, Merchant Name, Location/Country, Transaction Amount, Customer Card History, Device IP at transaction time",
        "example": "Customer notifies bot: 'I was charged $800 at a store in London, but I am currently in Hanoi'.",
        "approval_path": "Approve -> Temporarily block card, issue provisional credit & initiate VISA/Mastercard Chargeback; Reject -> Request additional proof from customer; Edit -> Adjust claim amount.",
        "audit_fields": "correlation_id, customer_cif, intent='dispute_transaction', transaction_id='TXN-881923', amount_usd=800, merchant='London Retail Store', reviewer_id, reviewer_decision, timestamp",
    },
    {
        "id": 3,
        "name": "Credit Limit Increase & Loan Disbursement Review",
        "trigger": "Action is 'request_loan' or 'increase_credit_limit' OR agent confidence score < 0.70 on credit policy disclosure",
        "hitl_model": "human-as-tiebreaker",
        "context_needed": "Customer credit score (CIC), monthly income verification, current debt-to-income ratio (DTI), AI loan assessment score, draft approval offer",
        "example": "Customer asks AI bot for an instant credit card limit increase from 50M to 200M VND based on salary statement uploaded in chat.",
        "approval_path": "Approve -> Issue binding loan offer/credit line extension; Edit & Approve -> Offer reduced limit (e.g. 100M VND); Reject -> Decline with regulatory reason code.",
        "audit_fields": "correlation_id, customer_cif, intent='increase_credit_limit', requested_limit=200000000, approved_limit=100000000, cic_score=720, reviewer_id, reviewer_decision, timestamp",
    },
]


# ============================================================
# Quick tests
# ============================================================

def test_confidence_router():
    """Test ConfidenceRouter with sample scenarios."""
    router = ConfidenceRouter()

    test_cases = [
        ("Balance inquiry", 0.95, "general"),
        ("Interest rate question", 0.82, "general"),
        ("Ambiguous request", 0.55, "general"),
        ("Transfer $50,000", 0.98, "transfer_money"),
        ("Close my account", 0.91, "close_account"),
    ]

    print("Testing ConfidenceRouter:")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Conf':<6} {'Action Type':<18} {'Decision':<15} {'Priority':<10} {'Human?'}")
    print("-" * 80)

    for scenario, conf, action_type in test_cases:
        decision = router.route(scenario, conf, action_type)
        print(
            f"{scenario:<25} {conf:<6.2f} {action_type:<18} "
            f"{decision.action:<15} {decision.priority:<10} "
            f"{'Yes' if decision.requires_human else 'No'}"
        )

    print("=" * 80)


def test_hitl_points():
    """Display HITL decision points."""
    print("\nHITL Decision Points:")
    print("=" * 60)
    for point in hitl_decision_points:
        print(f"\n  Decision Point #{point['id']}: {point['name']}")
        print(f"    Trigger:  {point['trigger']}")
        print(f"    Model:    {point['hitl_model']}")
        print(f"    Context:  {point['context_needed']}")
        print(f"    Example:  {point['example']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_confidence_router()
    test_hitl_points()
