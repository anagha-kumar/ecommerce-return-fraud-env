import os
import requests
from openai import OpenAI

# 🔹 ENV VARIABLES (as required)
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

BASE_URL = "https://anagha-kumar-return-fraud-env.hf.space"

# 🔹 INIT CLIENT (safe)
client = None
if API_KEY:
    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY
    )

DECISIONS = ["APPROVE", "REJECT", "REVIEW"]


# 🔹 SAFE HTTP CALL
def safe_post(url, payload=None):
    try:
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code != 200:
            print("ERROR:", response.status_code)
            return None

        return response.json()

    except Exception as e:
        print("Request failed:", e)
        return None


# 🔹 SIMPLE BASELINE (IMPORTANT)
def heuristic_decision(obs):
    if obs["customer_fraud_score"] > 0.7:
        return "REJECT"
    elif obs["customer_fraud_score"] < 0.2:
        return "APPROVE"
    else:
        return "REVIEW"


# 🔹 LLM DECISION (optional, falls back safely)
def get_decision(obs):
    if client:
        try:
            prompt = f"""
            Decide APPROVE, REJECT, or REVIEW for this return:

            Price: {obs['order_price']}
            Fraud Score: {obs['customer_fraud_score']}
            Return Reason: {obs['return_reason']}

            Only output one word.
            """

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=10
            )

            decision = response.choices[0].message.content.strip().upper()

            if decision in DECISIONS:
                return decision

        except Exception:
            pass

    # 🔥 fallback → heuristic (NOT random anymore)
    return heuristic_decision(obs)


# 🔹 RUN ONE EPISODE
def run_episode(i):
    reset = safe_post(f"{BASE_URL}/reset")

    if not reset:
        print(f"Episode {i}: RESET FAILED")
        return 0

    obs = reset["observation"]

    decision = get_decision(obs)

    step = safe_post(
        f"{BASE_URL}/step",
        {"action": {"decision": decision}}
    )

    if not step:
        print(f"Episode {i}: STEP FAILED")
        return 0

    reward = step.get("reward", 0)
    explanation = step["observation"].get("explanation", "")

    print(f"\n--- Episode {i} ---")
    print("Decision:", decision)
    print("Reward:", reward)
    print("Explanation:", explanation.strip())

    return reward / 10


# 🔹 MAIN
def main():
    scores = []

    for i in range(1, 6):
        score = run_episode(i)
        scores.append(score)

    avg_score = sum(scores) / len(scores)

    print("\n======================")
    print("Scores:", scores)
    print("Average Score:", avg_score)
    print("======================")


if __name__ == "__main__":
    main()