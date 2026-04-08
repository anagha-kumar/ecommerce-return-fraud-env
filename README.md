# Ecommerce Return Fraud Detection Environment (OpenEnv)

## Real-World Motivation

**The Problem:** E-commerce fraud costs businesses $48+ billion annually. Return fraud alone accounts for 5-10% of all returns, and detection requires human experts in most systems.

**Current Industry Gap:** Existing fraud detection systems use static rules or simple classifiers. They lack:
- Ability to handle ambiguous cases (when to escalate vs. decide)
- Understanding of asymmetric costs (fraud loss ≠ rejected genuine customer)
- Integration with real decision workflows (humans review flagged cases)

**This Environment:** Simulates the **real-world return decision system** where agents must:
1. Make decisions under uncertainty
2. Balance competing business objectives (fraud prevention vs. customer trust)
3. Know when to escalate rather than guess

E-commerce platforms, fraud prevention teams, and ML researchers would use this to train and evaluate agents.

---

## Objective

Given a return request, the agent must decide:

| Action    | Description                                    | Business Impact |
| --------- | ---------------------------------------------- | --- |
|  APPROVE | Accept return (risk: fraud loss)               | Simple but high cost if wrong |
|  REJECT  | Deny return (risk: unhappy customer)           | Moderate cost, damages trust |
|  REVIEW | Escalate ambiguous cases for manual inspection | Safe option, involves humans |

This **three-action design** is novel and reflects real fraud workflows where ambiguous cases are escalated rather than guessed on.

---

## What Makes This Environment Unique?

### Beyond Binary Classification

Unlike typical fraud detection (genuine/fraud binary), this environment:
- Introduces **ambiguity** through conflicting signals (high-value orders with suspicious histories)
- Models **real-world tradeoffs** where rejecting a genuine customer is costly but less severe than approving fraud
- Requires **multi-feature reasoning** that can't be solved by a single fraud score threshold

### The REVIEW Action

Most OpenEnv environments are binary. This one adds a **third action: REVIEW** that:
- Reflects how fraud teams actually work (manual review for ambiguous cases)
- Provides agents with an "escape hatch" for uncertainty
- Tests whether agents know when they don't know

### Asymmetric Reward Design

- Approving fraud: **-1.0** (direct revenue loss)
- Rejecting genuine: **-0.5** (trust damage, less severe)
- REVIEW action: **+0.5** (safe, escalates to human)

This teaches agents to be **risk-averse with fraud** but **customer-friendly with rejections**, matching real business logic.

---

## Environment Specification

### Observation Space

Each return request contains **8 features** reflecting real fraud signals:

| Feature | Type | Range | Meaning |
| --- | --- | --- | --- |
| `order_price` | float | Rs.100-Rs.15,000 | Higher values attract more fraud attempts |
| `days_since_delivery` | int | 1-30 days | Fraud claims often happen early or late |
| `return_reason` | string | defective, not_received, etc. | Text signal of fraud type |
| `customer_return_count` | int | 0-15 | Repeat offenders have higher fraud risk |
| `customer_fraud_score` | float | 0.0-1.0 | ML-derived fraud probability |
| `product_category` | string | electronics, fashion, home | Different categories have different fraud rates |
| `delivery_confirmed` | bool | true/false | Critical signal for "not received" fraud |
| `image_match` | bool | true/false | Does return match original order photo? |

### Action Space

Agents choose one of three actions:
- `APPROVE` - accept the return
- `REJECT` - deny the return
- `REVIEW` - escalate for manual review

### Episode Structure

- **Episode length:** 1 step (single decision per return)
- **Reset:** Loads a new return case from the task dataset
- **Grading:** Deterministic comparison (action vs. ground truth label)

---

## Task Design (Easy → Medium → Hard)

The environment includes **3 tasks with clear difficulty progression**:

### Easy Task (4 test cases)

**Characteristics:**
- Clear, unambiguous fraud/genuine signals
- High fraud scores (0.9-0.95) paired with fraud cases
- Low fraud scores (0.05-0.1) paired with genuine cases
- Additional confirmatory signals (image mismatch, delivery issues)

**Examples:**
- Case 1: fraud_score=0.95, customer_fraud_count=12, image_match=False → Fraud (obvious)
- Case 2: fraud_score=0.05, customer_fraud_count=0, image_match=True → Genuine (obvious)

**Expected Agent Performance:** 75-90% (agents should get most decisions right)

**Grading:**
- Correct decision (APPROVE genuine / REJECT fraud): +1.0
- REVIEW on easy cases: +0.5 (safe but unnecessary)
- Wrong decision: -0.5 to -1.0

---

### Medium Task (4 test cases)

**Characteristics:**
- **Borderline fraud scores** (0.2-0.6) that don't clearly signal fraud/genuine
- Mixed signals: one feature suggests fraud, another suggests genuine
- Requires reasoning across multiple features, not just fraud_score

**Examples:**
- Case 1: fraud_score=0.6, return_count=5, image_match=True, price=$2000 → Fraud (borderline)
- Case 2: fraud_score=0.3, return_count=6, image_match=True, price=$2500 → Fraud (deceptive: high return count contradicts low fraud score)
- Case 3: fraud_score=0.45, return_count=1, image_match=False → Fraud (conflicting: low history but mismatched image)

**Challenge:** Agents can't use simple heuristics like "if fraud_score > 0.5 then REJECT". They must reason about feature interactions.

**Expected Agent Performance:** 50-75% (harder, benefits from multi-feature reasoning)

**Grading:**
- Correct decision: +1.0
- REVIEW on ambiguous cases: +0.5 (appropriate caution)
- Wrong decision: -0.5 to -1.0

---

### Hard Task (4 test cases)

**Characteristics:**
- **Conflicting signals** across multiple features
- High-value orders (which attract fraud but are also legitimate)
- Delivery/image issues that contradict low fraud scores
- Tests whether agents can weigh evidence under extreme uncertainty

**Examples:**
- Case 1: price=$10,000, fraud_score=0.4, return_count=2, delivery_confirmed=False, image_match=False → Fraud (high value + delivery issues despite low fraud score)
- Case 2: price=$15,000, fraud_score=0.35, return_count=1, image_match=True → Genuine (high value + good history despite moderate fraud score)
- Case 3: fraud_score=0.5, return_count=3, delivery_confirmed=False, price=$5000 → Fraud (borderline score but delivery failure is critical)

**Challenge:** Agents must understand that delivery_confirmed=False is a stronger signal than fraud_score alone, and that honest customers don't file claims weeks after unconfirmed delivery.

**Expected Agent Performance:** 25-50% (very difficult, requires advanced reasoning)

**Grading:**
- Correct decision: +1.0
- REVIEW on hard cases: +0.5 (appropriate, acknowledges difficulty)
- Wrong decision: -0.5 to -1.0

---

## Reward Function (Key Strength)

The reward system models **real-world business impact**:

| Agent Decision | True Label | Score | Explanation |
| --- | --- | --- | --- |
| APPROVE | Genuine | +1.0 | Correct decision, customer satisfied |
| APPROVE | Fraud | -1.0 | **WORST:** Direct revenue loss |
| REJECT | Genuine | -0.5 | **BAD:** Customer dissatisfaction but no direct loss |
| REJECT | Fraud | +1.0 | Correct decision, fraud prevented |
| REVIEW | Any | +0.5 | Safe fallback, appropriate for ambiguous cases |

### Why Asymmetric Rewards?

1. **Approving fraud** = direct revenue loss + product cost + logistics cost
2. **Rejecting genuine** = customer trust damage but no direct loss
3. **Therefore:** Cost(approve fraud) > Cost(reject genuine)

This **asymmetry** forces agents to be more conservative with fraud detection—a realistic business constraint.

### Reward Normalization

Raw rewards are scaled to [-10, +10] range:
- Per-episode reward: [-1.0, +1.0]
- Per-task average: 0.0-1.0 (normalized for comparison)

---

## Grading Logic

### How Graders Work

Each task has a **deterministic grader** with no randomness:

```
Input:
  - Agent action: APPROVE / REJECT / REVIEW
  - Ground truth label: genuine / fraud

Output:
  - Reward score: -1.0, -0.5, +0.5, or +1.0
  - Done: true (single decision per episode)

Grading rule:
  if action == correct_action(label):
    return +1.0
  elif action == REVIEW:
    return +0.5
  elif action == opposite_of_correct_action(label):
    return -0.5 or -1.0 (based on cost asymmetry)
```

### Task-Specific Grading

All tasks use the same grading logic, but vary in:
- **Case difficulty** (easy: clear signals vs. hard: conflicting signals)
- **Expected agent performance** (easy: 75-90% vs. hard: 25-50%)
- **Exploration value** (hard cases teach more)

---

## OpenEnv API Compliance

This environment fully implements the OpenEnv specification:

### Required Endpoints

- **`reset()`** → Returns initial observation from current task
- **`step(action)`** → Executes decision, returns observation + reward + done + info
- **`state()`** → Returns current state (for debugging/analysis)

### Type Safety

- `ReturnAction`: Pydantic model with `decision: Decision` enum
- `ReturnObservation`: Pydantic model with all 8 features + metadata
- `ReturnState`: Current episode state for introspection

### Configuration

- `openenv.yaml`: Defines tasks, action/observation schemas
- Validated with: `openenv validate` (passes all checks)

---

## Baseline Inference

A reproducible baseline agent is provided with LLM integration:

### Strategy (Two-Tier Approach)

**Tier 1: LLM-Based (Primary)**
```python
# Uses OpenAI client to call LLM
response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[{"role": "user", "content": fraud_detection_prompt}],
)
decision = response.choices[0].message.content.strip().upper()
```

**Tier 2: Heuristic Fallback (Deterministic)**
If LLM API fails
```python
if fraud_score > 0.7:
    return REJECT
elif fraud_score < 0.2:
    return APPROVE
else:
    return REVIEW  # Safe fallback for ambiguous cases
```

This ensures **reproducibility** (fallback is deterministic) while leveraging LLM when available.

### Sample Output

The inference script outputs structured logs for real-time parsing:

```
[START] task=easy
[STEP] step=1 reward=0.50
[STEP] step=2 reward=0.75
[STEP] step=3 reward=1.00
[END] task=easy score=0.75 steps=3
[START] task=medium
[STEP] step=1 reward=0.50
[STEP] step=2 reward=0.50
[STEP] step=3 reward=0.25
[END] task=medium score=0.42 steps=3
[START] task=hard
[STEP] step=1 reward=0.50
[STEP] step=2 reward=0.50
[STEP] step=3 reward=0.50
[END] task=hard score=0.50 steps=3

Final average score: 0.56
```

---

## Setup & Usage

### Local Development

**1. Clone repository**

```bash
git clone https://github.com/anagha-kumar/ecommerce-return-fraud-env.git
cd ecommerce-return-fraud-env
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Run server**

```bash
uvicorn server.app:app --reload --port 8000
```

Server starts at `http://localhost:8000` with interactive API docs at `/docs`

**4. Run inference (in another terminal)**

```bash
export HF_TOKEN="your-huggingface-token"
python inference.py
```

### Docker Deployment

**Build image:**

```bash
docker build -t return-fraud-env .
```

**Run container:**

```bash
docker run -p 8000:8000 \
  -e HF_TOKEN="your-huggingface-token" \
  -e API_BASE_URL="https://router.huggingface.co/v1" \
  -e MODEL_NAME="meta-llama/Llama-2-70b-chat-hf" \
  return-fraud-env
```

Server starts at `http://localhost:8000`

### Environment Variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `HF_TOKEN` | YES | - | HuggingFace API token (for LLM calls) |
| `API_BASE_URL` | NO | `https://router.huggingface.co/v1` | LLM API endpoint |
| `MODEL_NAME` | NO | `meta-llama/Llama-2-70b-chat-hf` | Model to use |

---

## HuggingFace Spaces (Cloud Deployment)

**Space URL:** https://huggingface.co/spaces/anagha-kumar/return-fraud-env

### For Existing Deployment

Environment secrets are already configured in the Space:
- ✓ HF_TOKEN
- ✓ API_BASE_URL
- ✓ MODEL_NAME

The inference script automatically uses these at runtime. No additional setup needed.

### For New Deployments

If deploying to a new Space, configure these environment secrets:

**1. Go to Space settings**

2. Find "Repository secrets" section

3. Add these secrets:
   - **Name:** `HF_TOKEN`, **Value:** your HuggingFace API token
   - **Name:** `API_BASE_URL`, **Value:** `https://router.huggingface.co/v1`
   - **Name:** `MODEL_NAME`, **Value:** `meta-llama/Llama-2-70b-chat-hf`

The inference script will automatically use these at runtime.

---

## Why This Matters

### For Industry

- **Real problem:** E-commerce fraud is a $48B+ annual problem with no good automated solutions
- **Practical impact:** Reduces manual review burden while improving fraud detection
- **Immediate use:** Companies like Amazon, Shopify, AliExpress could train agents on this

### For AI Research

- **Novel challenge:** Moves beyond binary classification to decision-making under uncertainty
- **Research value:** Tests whether agents can reason about asymmetric costs and conflicting signals
- **Benchmark potential:** Standard testbed for evaluating fraud detection agents

### For OpenEnv

- **Technical innovation:** Introduces REVIEW action, asymmetric rewards, and feature interactions
- **Difficulty progression:** Clear easy→medium→hard progression teaches agents progressively
- **Reproducibility:** Deterministic graders, structured output, baseline agent make this reproducible

---

## Key Design Decisions

1. **Introduced REVIEW action**
   - Real fraud teams escalate ambiguous cases, not guess
   - Gives agents an "uncertainty escape hatch"
   - Tests whether agents know when they don't know

2. **Asymmetric reward function**
   - Models real business logic (fraud cost ≠ rejection cost)
   - Forces agents to be risk-averse with fraud
   - Creates realistic decision tradeoffs

3. **Multi-feature observations**
   - No single feature determines fraud
   - Requires reasoning across order_price, fraud_score, delivery_confirmed, customer_history, etc.
   - Teaches agents to synthesize evidence

4. **Clear difficulty progression**
   - Easy: tests basic signal detection
   - Medium: tests multi-feature reasoning
   - Hard: tests reasoning under extreme uncertainty

---

## Conclusion

This environment goes beyond fraud classification and models **real-world decision-making under uncertainty**. It's suitable for:

- Training RL agents on realistic fraud detection workflows
- Evaluating whether LLM agents can reason about competing business objectives
- Benchmarking robustness to conflicting signals and edge cases
- Research on how agents handle asymmetric cost structures

The REVIEW action, asymmetric rewards, and feature interactions make this a **challenging and realistic** environment for agent evaluation.

---

## Author

Anagha Kumar
