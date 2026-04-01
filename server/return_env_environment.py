import random
import uuid
from openenv.core.env_server import Environment
from models import ReturnAction, ReturnObservation, ReturnState


# TASK DATASET
TASKS = {
    "easy": [
        # clear genuine
        {
            "order_price": 500,
            "days_since_delivery": 2,
            "return_reason": "defective",
            "customer_return_count": 1,
            "customer_fraud_score": 0.1,
            "product_category": "clothing",
            "delivery_confirmed": True,
            "image_match": True,
            "label": "genuine"
        },
        {
            "order_price": 800,
            "days_since_delivery": 1,
            "return_reason": "size issue",
            "customer_return_count": 0,
            "customer_fraud_score": 0.05,
            "product_category": "clothing",
            "delivery_confirmed": True,
            "image_match": True,
            "label": "genuine"
        },

        # clear fraud
        {
            "order_price": 3000,
            "days_since_delivery": 1,
            "return_reason": "wrong item",
            "customer_return_count": 10,
            "customer_fraud_score": 0.9,
            "product_category": "electronics",
            "delivery_confirmed": True,
            "image_match": False,
            "label": "fraud"
        },
        {
            "order_price": 7000,
            "days_since_delivery": 2,
            "return_reason": "not received",
            "customer_return_count": 12,
            "customer_fraud_score": 0.95,
            "product_category": "electronics",
            "delivery_confirmed": True,
            "image_match": False,
            "label": "fraud"
        }
    ],

    "medium": [
        # borderline fraud score
        {
            "order_price": 2000,
            "days_since_delivery": 5,
            "return_reason": "not satisfied",
            "customer_return_count": 5,
            "customer_fraud_score": 0.6,
            "product_category": "fashion",
            "delivery_confirmed": True,
            "image_match": True,
            "label": "fraud"
        },

        # looks genuine but suspicious history
        {
            "order_price": 2500,
            "days_since_delivery": 3,
            "return_reason": "quality issue",
            "customer_return_count": 6,
            "customer_fraud_score": 0.45,
            "product_category": "home",
            "delivery_confirmed": True,
            "image_match": True,
            "label": "fraud"
        },

        # low fraud score but mismatch
        {
            "order_price": 1500,
            "days_since_delivery": 4,
            "return_reason": "wrong item",
            "customer_return_count": 1,
            "customer_fraud_score": 0.2,
            "product_category": "fashion",
            "delivery_confirmed": True,
            "image_match": False,
            "label": "fraud"
        },

        # genuine but slightly risky
        {
            "order_price": 1800,
            "days_since_delivery": 2,
            "return_reason": "damaged",
            "customer_return_count": 2,
            "customer_fraud_score": 0.3,
            "product_category": "home",
            "delivery_confirmed": True,
            "image_match": True,
            "label": "genuine"
        }
    ],

    "hard": [
        # conflicting signals
        {
            "order_price": 10000,
            "days_since_delivery": 3,
            "return_reason": "damaged",
            "customer_return_count": 2,
            "customer_fraud_score": 0.4,
            "product_category": "electronics",
            "delivery_confirmed": True,
            "image_match": True,
            "label": "fraud"
        },

        # high value but genuine
        {
            "order_price": 15000,
            "days_since_delivery": 4,
            "return_reason": "defective",
            "customer_return_count": 1,
            "customer_fraud_score": 0.35,
            "product_category": "electronics",
            "delivery_confirmed": True,
            "image_match": True,
            "label": "genuine"
        },

        # delivery not confirmed (critical signal)
        {
            "order_price": 5000,
            "days_since_delivery": 6,
            "return_reason": "not received",
            "customer_return_count": 3,
            "customer_fraud_score": 0.5,
            "product_category": "electronics",
            "delivery_confirmed": False,
            "image_match": False,
            "label": "fraud"
        },

        # tricky mixed signals
        {
            "order_price": 2200,
            "days_since_delivery": 3,
            "return_reason": "not satisfied",
            "customer_return_count": 4,
            "customer_fraud_score": 0.5,
            "product_category": "fashion",
            "delivery_confirmed": True,
            "image_match": True,
            "label": "genuine"
        }
    ]
}

# GRADER
def grade(decision: str, true_label: str) -> float:
    decision = decision.upper()

    # Correct decisions
    if decision == "APPROVE" and true_label == "genuine":
        return 1.0

    if decision == "REJECT" and true_label == "fraud":
        return 1.0

    # REVIEW (safe fallback)
    if decision == "REVIEW":
        return 0.5

    # WRONG DECISIONS (asymmetric penalties)

    # WORST: approving fraud
    if decision == "APPROVE" and true_label == "fraud":
        return -1.0

    # Less severe: rejecting genuine
    if decision == "REJECT" and true_label == "genuine":
        return -0.5

    return 0.0


class ReturnEnv(Environment):

    def __init__(self):
        self.current_case = None
        self._state = ReturnState()

    def reset(self) -> ReturnObservation:
        difficulty = random.choice(["easy", "medium", "hard"])
        self.current_case = random.choice(TASKS[difficulty])

        self._state = ReturnState(
            episode_id=str(uuid.uuid4()),
            step_count=0,
            true_label=self.current_case["label"]
        )

        return ReturnObservation(
            done=False,
            reward=None,
            explanation=f"New case loaded ({difficulty}). Choose APPROVE / REJECT / REVIEW.",
            order_price=self.current_case["order_price"],
            days_since_delivery=self.current_case["days_since_delivery"],
            return_reason=self.current_case["return_reason"],
            customer_return_count=self.current_case["customer_return_count"],
            customer_fraud_score=self.current_case["customer_fraud_score"],
            product_category=self.current_case["product_category"],
            delivery_confirmed=self.current_case["delivery_confirmed"],
            image_match=self.current_case["image_match"]
        )

    def step(self, action: ReturnAction) -> ReturnObservation:

        if self.current_case is None:
            difficulty = random.choice(["easy", "medium", "hard"])
            self.current_case = random.choice(TASKS[difficulty])

            self._state = ReturnState(
        episode_id=str(uuid.uuid4()),
        step_count=0,
        true_label=self.current_case["label"]
    )


        decision = "REVIEW"

        try:
            if isinstance(action, dict):
                if "decision" in action:
                    decision = action["decision"]
                elif "action" in action:
                    decision = action["action"].get("decision", "REVIEW")

            elif hasattr(action, "decision"):
                val = action.decision
                decision = val.value if hasattr(val, "value") else val

        except Exception:
            decision = "REVIEW"

        decision = str(decision).upper()

        self._state.step_count += 1
        true_label = self.current_case["label"]

        score = grade(decision, true_label)
        reward = score * 10

        explanation = f"Decision: {decision}\nOutcome: {'Fraudulent' if true_label=='fraud' else 'Genuine'}\n\n"

        if decision == "APPROVE":
            explanation += "✔ Correct" if true_label == "genuine" else "✖ Incorrect: Fraud approved"

        elif decision == "REJECT":
            explanation += "✔ Correct" if true_label == "fraud" else "✖ Incorrect: Genuine rejected"

        else:
            explanation += "➜ Sent to review (partial credit)"

        explanation += f"\n\nScore: {score} | Reward: {reward}"

        return ReturnObservation(
            done=True,
            reward=reward,
            explanation=explanation,
            order_price=self.current_case["order_price"],
            days_since_delivery=self.current_case["days_since_delivery"],
            return_reason=self.current_case["return_reason"],
            customer_return_count=self.current_case["customer_return_count"],
            customer_fraud_score=self.current_case["customer_fraud_score"],
            product_category=self.current_case["product_category"],
            delivery_confirmed=self.current_case["delivery_confirmed"],
            image_match=self.current_case["image_match"]
        )

    @property
    def state(self) -> ReturnState:
        return self._state

    def info(self) -> dict:
        return {
            "environment": "Return Fraud Detection",
            "actions": ["APPROVE", "REJECT", "REVIEW"],
            "note": "REVIEW handles ambiguous cases"
        }