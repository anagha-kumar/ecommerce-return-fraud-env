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

Unlike simple classification problems, this environment introduces ambiguity through conflicting signals such as fraud score, customer history, and product characteristics.

Agents must balance risk and uncertainty rather than relying on a single feature.

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

### 2. Install dependencies (Local)

```
pip install -r requirements.txt
```

### 3. Run server locally

```
uvicorn server.app:app --reload --port 8000
```

### 4. Run inference (in another terminal)

```
export HF_TOKEN="your-huggingface-token"
python inference.py
```

---

## 🐳 Docker Setup & Deployment

### Building the Docker Image

```bash
docker build -t return-fraud-env .
```

### Running with Docker

**Option 1: Using docker run (with environment variables)**

```bash
docker run -p 8000:8000 \
  -e HF_TOKEN="your-huggingface-token" \
  -e API_BASE_URL="https://router.huggingface.co/v1" \
  -e MODEL_NAME="meta-llama/Llama-2-70b-chat-hf" \
  return-fraud-env
```

**Option 2: Using docker-compose (Recommended)**

1. Create a `.env` file in the project root:
```
HF_TOKEN=your-huggingface-token
API_BASE_URL=https://router.huggingface.co/v1
MODEL_NAME=meta-llama/Llama-2-70b-chat-hf
```

2. Run with docker-compose:
```bash
docker-compose up
```

The server will start at `http://localhost:8000`

### Environment Variables in Docker

All containers have these variables configured:

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | (empty) | **REQUIRED**: Your HuggingFace API token |
| `API_BASE_URL` | `https://router.huggingface.co/v1` | LLM API endpoint |
| `MODEL_NAME` | `meta-llama/Llama-2-70b-chat-hf` | Model to use |

---

## 🚀 HuggingFace Spaces Configuration

When deploying to HuggingFace Spaces, configure these **environment secrets** in your Space settings:

### Required Environment Variables

1. **HF_TOKEN** (Required)
   - Your HuggingFace API token for accessing inference APIs
   - Get it from: https://huggingface.co/settings/tokens
   - Must have "read" permission

2. **API_BASE_URL** (Optional)
   - Default: `https://router.huggingface.co/v1`
   - Use HuggingFace Inference Router for API calls
   - Can override with your own OpenAI-compatible endpoint

3. **MODEL_NAME** (Optional)
   - Default: `meta-llama/Llama-2-70b-chat-hf`
   - Set to any HuggingFace API-available model
   - Examples: `mistralai/Mistral-7B-Instruct-v0.1`, `meta-llama/Llama-2-7b-chat-hf`

### How to Set Secrets in HF Spaces

1. Go to your Space settings (⚙️ Settings tab)
2. Find "Repository secrets" section
3. Add each secret:
   - **Name:** `HF_TOKEN`, **Value:** your token
   - **Name:** `API_BASE_URL`, **Value:** `https://router.huggingface.co/v1`
   - **Name:** `MODEL_NAME`, **Value:** `meta-llama/Llama-2-70b-chat-hf`

The inference script will automatically use these at runtime.

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
