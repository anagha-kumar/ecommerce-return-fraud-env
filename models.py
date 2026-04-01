from openenv.core.env_server import Action, Observation, State
from enum import Enum


class Decision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REVIEW = "REVIEW"


class ReturnAction(Action):
    decision: Decision = Decision.REVIEW


class ReturnObservation(Observation):
    done: bool
    reward: float | None
    explanation: str | None = None 

    order_price: float
    days_since_delivery: int
    return_reason: str
    customer_return_count: int
    customer_fraud_score: float
    product_category: str
    delivery_confirmed: bool
    image_match: bool


class ReturnState(State):
    episode_id: str | None = None
    step_count: int = 0
    true_label: str = ""