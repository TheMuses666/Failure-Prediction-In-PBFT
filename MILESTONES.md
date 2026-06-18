# Project Milestones

## ML-Assisted Predictive Monitoring in Byzantine Fault-Tolerant Consensus Protocols

**Student:** Yulun Miao | **ID:** L39601331  
**Deadline:** Friday 24 July 2026, 18:00  
**Today:** 18 June 2026 | **Days Remaining:** 36

---

## Overview

```
Week 1 (Jun 16–22)    → Design & Setup
Week 2 (Jun 23–29)    → PBFT Simulator
Week 3 (Jun 30–Jul 6) → Data + ML Models
Week 4 (Jul 7–13)     → Baseline + Evaluation
Week 5 (Jul 14–20)    → Report Writing
Week 6 (Jul 21–24)    → Final Polish + Submit
```

---

## Week 1 — Design & Environment Setup (Jun 16–22)

**Goal:** Finalise all design decisions before writing any code.

- [x] Confirm research question: _Consensus Degradation Prediction_ (not just binary failure)
- [x] Finalise 4 Byzantine fault types: Silent / Replay / Equivocation / Delay
- [x] Finalise label schema with quantified thresholds (see below)
- [x] Finalise 11 features across 3 groups (see below)
- [x] Set up project folder structure
- [x] Set up Python environment (`requirements.txt`)
- [x] Write `config.py` with all global parameters

**Deliverable:** Project skeleton + config ready

---

## Week 2 — PBFT Simulator (Jun 23–29)

**Goal:** Working simulator that generates labelled behavioural data.

### Step 1 — Node Message Logging

- [x] Implement `simulation/node.py` — `Node` base class + `Byzantine_Node` subclass
- [x] Store `prepare_log` and `commit_log` by `round_id`
- [x] Avoid duplicate sender counts for replayed prepare/commit messages
- [x] Smoke test `node.py`

Test:

```bash
python3 -c "from simulation.node import Node; n=Node(1); n.receive_message({'type':'prepare','sender_id':2,'round_id':1,'content':'x'}); n.receive_message({'type':'prepare','sender_id':3,'round_id':1,'content':'x'}); print(n.prepare_log)"
```

Expected:

```text
{1: [2, 3]}
```

### Step 2 — Fault Injection

- [x] Implement `simulation/fault_injector.py` — create honest and Byzantine nodes
- [x] Support four fault types: `silent`, `replay`, `equivocation`, `delay`
- [x] Smoke test `fault_injector.py`

Test:

```bash
python3 -c "from simulation.fault_injector import FaultInjector; nodes=FaultInjector().create_nodes('silent'); print(len(nodes)); print(sum(n.is_Byzantine for n in nodes)); print([type(n).__name__ for n in nodes])"
```

Expected:

```text
7
2
```

### Step 3 — PBFT Round Execution

- [x] Implement `simulation/pbft.py` — Pre-prepare / Prepare / Commit flow
- [x] Add or document simplified Reply phase decision
- [x] Implement `simulation/network.py` — one round calls PBFT phases and consensus check
- [x] Extract round metrics before calling `reset_nodes()`
- [ ] Smoke test `network.py`

Test:

```bash
python3 -c "from simulation.fault_injector import FaultInjector; from simulation.network import Network; nodes=FaultInjector().create_nodes('silent'); print(Network(nodes).run_round(1))"
```

Expected:

```text
A metrics dictionary containing round_id, success, duration_ms, timeout, success_count, consensus_agreement_time, timeout_frequency, and response_time.
```

### Step 4 — Label Generation

- [x] Implement `collection/label_generator.py`
- [x] Convert one metrics dictionary into label `0`, `1`, or `2`
- [x] Smoke test `label_generator.py`

Initial rule:

```text
Failure  = timeout OR not success
Degraded = duration_ms >= 50
Normal   = otherwise
```

Test:

```bash
python3 -c "from collection.label_generator import generate_label; print(generate_label({'timeout': False, 'success': True, 'duration_ms': 20})); print(generate_label({'timeout': False, 'success': True, 'duration_ms': 80})); print(generate_label({'timeout': True, 'success': False, 'duration_ms': 200}))"
```

Expected:

```text
0
1
2
```

### Step 5 — Feature Extraction

- [x] Implement `collection/feature_extractor.py`
- [x] Return all 11 feature columns with numeric values
- [x] Remove all `None` feature placeholders from generated records
- [x] Smoke test `feature_extractor.py`

Test:

```bash
python3 -c "from collection.feature_extractor import extract_features; print(extract_features({'duration_ms': 20, 'timeout': False, 'success': True, 'success_count': 5}))"
```

Expected:

```text
A dictionary containing all 11 feature columns with no None values.
```

### Step 6 — Integrate Features and Labels into `network.py`

- [ ] Update `simulation/network.py` so `run_round()` returns one complete dataset row
- [ ] Include `round_id`, status fields, 11 features, and `label`
- [ ] Smoke test one `delay` round

Test:

```bash
python3 -c "from simulation.fault_injector import FaultInjector; from simulation.network import Network; nodes=FaultInjector().create_nodes('delay'); row=Network(nodes).run_round(1); print(row); print(row['label'])"
```

Expected:

```text
No error, no feature value is None, and label exists.
```

### Step 7 — Small Runner in `main.py`

- [ ] Implement `main.py` small-run mode
- [ ] Run 5 normal rounds and 5 rounds per fault type
- [ ] Print row count and label distribution
- [ ] Smoke test `main.py`

Test:

```bash
python3 main.py
```

Expected:

```text
total rows: 25
label distribution: ...
```

### Step 8 — Save Raw CSV

- [ ] Save generated rows to `data/raw/consensus_data.csv`
- [ ] Verify CSV shape, columns, and label distribution

Test:

```bash
python3 main.py
python3 -c "import pandas as pd; df=pd.read_csv('data/raw/consensus_data.csv'); print(df.shape); print(df.head()); print(df['label'].value_counts())"
```

Expected:

```text
CSV exists, contains 11 feature columns plus label, and labels are not all one class.
```

### Step 9 — Full Simulation Run

- [ ] Run 200 rounds per fault type
- [ ] Include normal operation rounds (~400) for balance
- [ ] Verify data distribution and label balance

Test:

```bash
python3 main.py
python3 -c "import pandas as pd; df=pd.read_csv('data/raw/consensus_data.csv'); print(df.shape); print(df['fault_type'].value_counts()); print(df['label'].value_counts())"
```

Expected:

```text
1200 rows total: 400 normal rows and 200 rows for each fault type.
```

**Deliverable:** `data/raw/consensus_data.csv` (initial full run: 1200 records; optional extended run can target ~3000–5000 records)

---

## Week 3 — Data Processing & ML Models (Jun 30–Jul 6)

**Goal:** Trained and validated ML models.

- [ ] Implement `preprocessing.py`:
  - Feature normalisation (Min-Max)
  - Train / Val / Test split (70 / 10 / 20), seed=42
  - Feature correlation analysis
- [ ] Implement `models.py`:
  - Decision Tree (interpretability baseline)
  - Random Forest (performance + interpretability)
  - XGBoost (performance upper bound)
- [ ] Train all 3 models
- [ ] Implement SHAP analysis for RF + XGBoost
- [ ] Initial evaluation on validation set

**Deliverable:** Trained models + SHAP plots

---

## Week 4 — Baseline Comparison & Evaluation (Jul 7–13)

**Goal:** Full comparative results ready for writing.

- [ ] Implement `static_detection.py`:
  - Threshold-based detection (mean + 2σ from normal data)
  - Rule-based detection
- [ ] Run all models + baselines on same test set
- [ ] Calculate all metrics:
  - Accuracy, Precision, Recall, F1-score
  - Response Time
  - **Prediction Lead Time** (key novel metric)
- [ ] Generate all figures:
  - Confusion matrices (per model)
  - Performance comparison bar chart
  - SHAP feature importance plot
  - Prediction Lead Time comparison
  - Robustness degradation curve
- [ ] Ablation experiment: remove features one by one, measure impact
- [ ] Robustness test: Byzantine ratio 10% → 20% → 30%, observe degradation
- [ ] Per-fault-type analysis: which fault type is hardest to predict?
- [ ] **Scalability test**: repeat key experiments at 7 / 10 / 13 nodes, compare Accuracy + Lead Time + Response Time
- [ ] **Feature Importance Ranking**: output SHAP ranking for RF + XGBoost, discuss which consensus behaviours best predict failure

**Deliverable:** `results/figures/` complete, all numbers confirmed

---

## Week 5 — Report Writing (Jul 14–20)

**Goal:** Complete draft of Report + Reflection.

**Report Structure:**

- [ ] 1. Title + Abstract
- [ ] 2. Introduction & Background
- [ ] 3. Related Work (reference A1 literature)
- [ ] 4. System Design (simulator architecture + updated network diagram)
- [ ] 5. Methodology (features, label definition, ML models, evaluation metrics)
- [ ] 6. Experimental Results (tables + figures)
- [ ] 7. Discussion & Limitations
- [ ] 8. Conclusion
- [ ] 9. References (Harvard, alphabetical)
- [ ] Appendix A: AI Declaration (AMBER sections declared)

**Also:**

- [ ] Reflection section (~300–500 words)
- [ ] Prepare Presentation slides (deadline: **Friday 20 July**)
- [ ] Record 3–5 minute presentation video

**Deliverable:** Full draft report + presentation video submitted by Jul 20

---

## Week 6 — Final Polish & Submission (Jul 21–24)

**Goal:** Clean, complete submission package.

- [ ] Proofread report (grammar, formatting: Arial 12pt, 1.5 spacing)
- [ ] Check all Harvard references (alphabetical order)
- [ ] Verify Castro & Liskov (1999) reference format
- [ ] Check word count within limits
- [ ] Prepare ZIP package:
  - [ ] All Python code (well-commented)
  - [ ] `data/` folder (raw + processed)
  - [ ] `results/figures/` folder
  - [ ] `README.md` (setup + run instructions)
  - [ ] Ethics form
- [ ] Final submission to Teams by **18:00, Friday 24 July**

---

## Key Parameters (Reference)

| Parameter          | Value                                   |
| ------------------ | --------------------------------------- |
| Nodes              | 7 (5 honest + 2 Byzantine)              |
| Fault types        | 4 (Silent, Replay, Equivocation, Delay) |
| Rounds per fault   | 200                                     |
| Normal rounds      | ~400                                    |
| Total records      | ~3000–5000                              |
| Train / Val / Test | 70% / 10% / 20%                         |
| Random seed        | 42                                      |
| ML models          | Decision Tree, Random Forest, XGBoost   |
| Baseline           | Threshold-based, Rule-based             |
| Key novel metric   | Prediction Lead Time                    |
| Explainability     | SHAP (RF + XGBoost)                     |
| Scalability test   | 7 / 10 / 13 nodes                       |

---

## Prediction Lead Time — Formal Definition

> **Lead Time = Failure Timestamp − Prediction Timestamp**
> Unit: Consensus Rounds

**Example:**

```
Failure occurs at round 150
Model flags risk at round 142
→ Lead Time = 8 rounds
```

**Target output:**

```
Decision Tree : X.X rounds avg
Random Forest : X.X rounds avg
XGBoost       : X.X rounds avg
Threshold     : X.X rounds avg (or 0 if reactive)
```

A higher Lead Time = more time for intervention before failure.

---

## Label Definition (Quantified)

| Label | State    | Criteria                                         |
| ----- | -------- | ------------------------------------------------ |
| 0     | Normal   | Consensus latency < 50ms, no view change         |
| 1     | Degraded | 50ms ≤ latency < 150ms, OR view-change triggered |
| 2     | Failure  | Consensus timeout, OR commit not reached         |

---

## Feature Set (11 Features)

**Network Layer (3)**
| Feature | Description |
|---------|-------------|
| `message_latency` | Average message delay between nodes (ms) |
| `message_drop_rate` | Proportion of messages not delivered |
| `propagation_pattern` | Variance in message propagation time |

**Consensus Layer (5)**
| Feature | Description |
|---------|-------------|
| `consensus_agreement_time` | Total time from request to commit (ms) |
| `phase_completion_time` | Time to complete Prepare + Commit phases |
| `timeout_frequency` | Number of timeouts per round |
| `leader_change_frequency` | Number of view changes per round |
| `response_time` | Time for node to respond to messages |

**Behaviour Layer (3)**
| Feature | Description |
|---------|-------------|
| `voting_consistency` | Ratio of consistent votes across replicas |
| `message_consistency` | Agreement between sent and received message content |
| `vote_deviation` | Standard deviation of voting patterns across nodes |

---

## Model Pipeline

```
PBFT Simulator
    ↓
4 Byzantine Fault Types
    ↓
11 Consensus Features (3 groups)
    ↓
3-State Labels (quantified thresholds)
    ↓
┌─────────────┬──────────────┬───────────┐
│Decision Tree│ Random Forest│  XGBoost  │
└─────────────┴──────────────┴───────────┘
    ↓               ↓              ↓
              SHAP Analysis
    ↓
Prediction Lead Time + Robustness Analysis
    ↓
Comparison vs Threshold-based / Rule-based
```

---

## Post-Submission (Conference Extension)

> After UA92 deadline — for publication target (IEEE SRDS or ACM SAC)

- [ ] Redesign data as time-series (sliding window) format
- [ ] Add Bi-LSTM model, compare with RF + XGBoost
- [ ] Set up Hyperledger Fabric testnet for real data collection
- [ ] Add SHAP temporal explainability
- [ ] Reframe paper title around _Consensus Performance Degradation Prediction_
- [ ] Target submission: IEEE SRDS or ACM SAC
