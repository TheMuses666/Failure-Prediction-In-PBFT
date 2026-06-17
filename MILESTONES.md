# Project Milestones
## ML-Assisted Predictive Monitoring in Byzantine Fault-Tolerant Consensus Protocols
**Student:** Yulun Miao | **ID:** L39601331  
**Deadline:** Friday 24 July 2026, 18:00  
**Today:** 16 June 2026 | **Days Remaining:** 38

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

- [ ] Confirm research question: *Consensus Degradation Prediction* (not just binary failure)
- [ ] Finalise 4 Byzantine fault types: Silent / Replay / Equivocation / Delay
- [ ] Finalise label schema with quantified thresholds (see below)
- [ ] Finalise 11 features across 3 groups (see below)
- [ ] Set up project folder structure
- [ ] Set up Python environment (`requirements.txt`)
- [ ] Write `config.py` with all global parameters

**Deliverable:** Project skeleton + config ready

---

## Week 2 — PBFT Simulator (Jun 23–29)

**Goal:** Working simulator that generates labelled behavioural data.

- [ ] Implement `node.py` — `Node` base class + `ByzantineNode` subclass
- [ ] Implement `network.py` — message passing, broadcast, metrics collection
- [ ] Implement `pbft.py` — 4 phases: Pre-prepare / Prepare / Commit / Reply
- [ ] Implement `fault_injector.py` — inject 4 fault types at configurable ratios
- [ ] Run 200 rounds per fault type (800+ rounds total)
- [ ] Include normal operation rounds (~400) for balance
- [ ] Output raw CSV to `data/raw/`
- [ ] Verify data distribution and label balance

**Deliverable:** `data/raw/consensus_data.csv` (~3000–5000 records)

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

| Parameter | Value |
|-----------|-------|
| Nodes | 7 (5 honest + 2 Byzantine) |
| Fault types | 4 (Silent, Replay, Equivocation, Delay) |
| Rounds per fault | 200 |
| Normal rounds | ~400 |
| Total records | ~3000–5000 |
| Train / Val / Test | 70% / 10% / 20% |
| Random seed | 42 |
| ML models | Decision Tree, Random Forest, XGBoost |
| Baseline | Threshold-based, Rule-based |
| Key novel metric | Prediction Lead Time |
| Explainability | SHAP (RF + XGBoost) |
| Scalability test | 7 / 10 / 13 nodes |

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

| Label | State | Criteria |
|-------|-------|----------|
| 0 | Normal | Consensus latency < 50ms, no view change |
| 1 | Degraded | 50ms ≤ latency < 150ms, OR view-change triggered |
| 2 | Failure | Consensus timeout, OR commit not reached |

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
- [ ] Reframe paper title around *Consensus Performance Degradation Prediction*
- [ ] Target submission: IEEE SRDS or ACM SAC
