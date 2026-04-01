---
title: Ecommerce Return Fraud Detection Environment
emoji: "📦"
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8000
---

# Ecommerce Return Fraud Detection Environment (OpenEnv)

## Real-World Motivation

E-commerce platforms constantly face a critical tradeoff:

* Approving fraudulent returns → **direct financial loss**
* Rejecting genuine returns → **customer dissatisfaction**

This environment simulates a **real-world return decision system** where an agent must balance **risk vs trust**, instead of simply performing binary classification.

---

##  Objective

Given a return request, the agent must decide:

| Action    | Description                                    |
| --------- | ---------------------------------------------- |
|  APPROVE | Accept return (risk: fraud loss)               |
|  REJECT  | Deny return (risk: unhappy customer)           |
|  REVIEW | Escalate ambiguous cases for manual inspection |

---

## What Makes This Environment Unique?

Most systems force binary decisions.

This environment introduces a **third action: REVIEW**

This reflects real-world workflows where:

* Not all cases are clear
* Ambiguous situations are escalated instead of guessed

---

## ⚙️ Observation Space

Each return request contains:

* `order_price`
* `days_since_delivery`
* `return_reason`
* `customer_return_count`
* `customer_fraud_score`
* `product_category`
* `delivery_confirmed`
* `image_match`

These features simulate real signals used in fraud detection pipelines.

---

## Task Design (Easy → Medium → Hard)

The environment includes **3 difficulty levels**:

| Level  | Description                             |
| ------ | --------------------------------------- |
| Easy   | Clear fraud/genuine signals             |
| Medium | Moderate ambiguity                      |
| Hard   | Conflicting signals requiring reasoning |

Each task has a **deterministic grader** producing scores between **0.0 and 1.0**.

---

## Reward Function (Key Strength)

The reward system models **real-world business impact**:

| Scenario         | Score | Impact                   |
| ---------------- | ----- | ------------------------ |
| Correct decision | +1.0  | Optimal                  |
| REVIEW           | +0.5  | Safe fallback            |
| Reject genuine   | -0.5  | Customer dissatisfaction |
| Approve fraud    | -1.0  | Financial loss           |

Final reward is scaled to:

```
[-10, +10]
```

---

## Why Asymmetric Rewards?

Approving fraud leads to immediate revenue loss.
Rejecting genuine customers impacts trust, but is less severe.

This creates a **realistic decision tradeoff**, not a toy problem.

---

## OpenEnv API Compliance

This environment fully implements the OpenEnv specification:

* `reset()` → returns initial observation
* `step(action)` → returns observation, reward, done
* `state()` → returns current state

Includes:

* Typed Pydantic models
* `openenv.yaml` configuration
* Validated using `openenv validate`

---

## Baseline Inference

A simple, reproducible baseline is implemented:

* High fraud score → REJECT
* Low fraud score → APPROVE
* Otherwise → REVIEW

### Sample Output

```
Episode 1: REVIEW → Reward 5
Episode 2: REJECT → Reward 10
Episode 3: APPROVE → Reward -10

Scores: [0.5, 1.0, -1.0, ...]
Average Score: ~0.7
```

---

##  Setup & Usage

### 1. Clone repository

```
git clone https://github.com/anagha-kumar/ecommerce-return-fraud-env.git
cd return_env
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Run server locally

```
uvicorn server.app:app --reload
```

### 4. Run inference

```
python inference.py
```

---

## Deployment

Deployed on Hugging Face Spaces using Docker.

https://huggingface.co/spaces/anagha-kumar/return-fraud-env

---

##  Key Design Decisions

* Introduced **REVIEW action** for handling ambiguity
* Designed **asymmetric reward function** reflecting real-world costs
* Added **explainable outputs for every decision**

---

##  Conclusion

This environment goes beyond classification and models **decision-making under uncertainty**, making it suitable for evaluating intelligent agents in real-world scenarios.

---

## Author

Anagha Kumar
