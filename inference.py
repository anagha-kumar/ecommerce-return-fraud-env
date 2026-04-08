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
            print("ERROR:", response.status_code, flush=True)
            return None

        return response.json()

    except Exception as e:
        print("Request failed:", e, flush=True)
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
def run_episode(task_name, episode_num):
    reset = safe_post(f"{BASE_URL}/reset")

    if not reset:
        return None

    obs = reset["observation"]

    decision = get_decision(obs)

    step = safe_post(
        f"{BASE_URL}/step",
        {"action": {"decision": decision}}
    )

    if not step:
        return None

    reward = step.get("reward", 0)
    return reward


# 🔹 RUN TASK (multiple episodes, emit structured output)
def run_task(task_name, num_episodes=5):
    print(f"[START] task={task_name}", flush=True)

    total_reward = 0
    step_count = 0

    for episode in range(1, num_episodes + 1):
        reward = run_episode(task_name, episode)

        if reward is not None:
            total_reward += reward
            step_count += 1
            normalized_reward = reward / 10.0
            print(f"[STEP] step={step_count} reward={normalized_reward:.2f}", flush=True)

    # Calculate final score (0.0-1.0)
    final_score = total_reward / (step_count * 10.0) if step_count > 0 else 0.0

    print(f"[END] task={task_name} score={final_score:.2f} steps={step_count}", flush=True)

    return final_score


# 🔹 MAIN
def main():
    # Run 3 tasks: easy, medium, hard
    tasks = ["easy", "medium", "hard"]
    scores = []

    for task_name in tasks:
        score = run_task(task_name, num_episodes=3)
        scores.append(score)

    # Print final summary
    avg_score = sum(scores) / len(scores) if scores else 0.0
    print(f"\nFinal average score: {avg_score:.2f}", flush=True)


if __name__ == "__main__":
    main()